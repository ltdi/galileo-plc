#!/usr/bin/env python3
"""Runtime virtual para OpenPLC Editor 4.x: el editor «cree» que habla con un OpenPLC Runtime v3 y en realidad
este servidor (una sola maquina Ubuntu del laboratorio) compila el programa con matiec y lo carga en la Galileo
elegida. El alumno usa el editor oficial: boton «Search» (lista de placas), boton «Upload».

Protocolo imitado (sacado del codigo del editor 4.3.5, GPL-3.0):
  - descubrimiento: broadcast UDP 33333 con el texto OPENPLC_DISCOVER_V1; se responde un JSON por placa;
  - API REST por HTTPS (8443, certificado autofirmado): /api/get-users-info, /api/login, /api/create-user,
    /api/capabilities, /api/version, /api/upload-file (multipart, campo «file» = program.st),
    /api/compilation-status, /api/start-plc, /api/stop-plc, /api/status.
El editor identifica cada runtime por la IP de origen de la respuesta, asi que cada placa tiene una IP virtual
(alias en la tarjeta de red del servidor, ver configurar_alias.sh). La conexion HTTPS se asigna a la placa por la
IP a la que llega.

Uso:  python3 servidor_runtime.py [--config placas.json] [--escuchar IP_https] [--escuchar-udp 0.0.0.0] [--puerto-api 8443]
      (el broadcast solo llega a un socket en 0.0.0.0; la API HTTPS conviene atarla a la IP de la red de laboratorio)
Seguridad: red de laboratorio aislada. Cualquier usuario/clave entra salvo que placas.json defina "clave"."""
import sys, os, re, json, ssl, time, hmac, base64, hashlib, socket, struct, subprocess, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PLC_PY = os.path.join(AQUI, "plc.py")
CARGAR = os.path.join(AQUI, "plc_cargar.py")
VERSION = "3.0.0"
MAX_BYTES = 2_000_000
DISCOVERY_PORT = 33333
MAGIA = b"OPENPLC_DISCOVER_V1"
SECRETO = os.urandom(32)                       # firma de los tokens; cambia en cada arranque
cerrojo_compilar = threading.Lock()            # un compilador a la vez (el servidor es chico)

def arg(nombre, defecto):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto

# ---------------------------------------------------------------- configuracion y estado de las placas
class Placa:
    def __init__(self, d):
        self.nombre = d["nombre"]; self.ip = d["ip"]; self.virtual = d.get("virtual")
        self.estado = "IDLE"; self.logs = []; self.exit_code = None; self.proyecto = ""; self.fin = 0
        self.cerrojo = threading.Lock()
    def log(self, nivel, texto):
        for linea in str(texto).splitlines():
            if linea.strip(): self.logs.append("[%s] %s" % (nivel, linea.rstrip()))
    def en_marcha(self):
        # El editor consulta /api/status cada ~1 s. Cada consulta real abriria y cerraria una conexion Modbus a la
        # placa, y el servidor Modbus de OpenPLC pierde descriptores con ese patron: se guarda el resultado 30 s.
        if time.time() - getattr(self, "_t_marcha", 0) < 30: return self._marcha
        self._t_marcha = time.time()
        self._marcha = self._sondear()
        return self._marcha
    def _sondear(self):
        try:
            socket.create_connection((self.ip, 502), timeout=1.5).close(); return True
        except OSError:
            return False

RED_PERMITIDA = None

def cargar_config(ruta):
    global RED_PERMITIDA
    import ipaddress
    d = json.load(open(ruta))
    # solo se contesta el descubrimiento a quien viene de la red de laboratorio (por defecto, la /24 de la primera placa)
    RED_PERMITIDA = ipaddress.ip_network(d.get("red") or (d["placas"][0]["ip"] + "/24"), strict=False)
    placas = [Placa(p) for p in d["placas"]]
    for p in placas:                                                       # solo IP privadas
        import ipaddress
        a = ipaddress.ip_address(p.ip)
        if a.version != 4 or not a.is_private or a.is_loopback:
            raise SystemExit("Placa %s: la IP %s no es una IP privada IPv4" % (p.nombre, p.ip))
    global ESTADO_EDITOR
    ESTADO_EDITOR = d.get("estado_editor", "STOPPED")      # "STOPPED", "RUNNING" o "REAL" (el estado verdadero de la placa)
    return placas, d.get("clave")

# ---------------------------------------------------------------- tokens (JWT HS256 minimo)
def b64(x): return base64.urlsafe_b64encode(x).rstrip(b"=").decode()
def b64d(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def crear_token(usuario):
    cab = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    carga = b64(json.dumps({"sub": usuario, "iat": int(time.time()), "exp": int(time.time()) + 900}).encode())
    firma = b64(hmac.new(SECRETO, ("%s.%s" % (cab, carga)).encode(), hashlib.sha256).digest())
    return "%s.%s.%s" % (cab, carga, firma)
def token_valido(token):
    try:
        cab, carga, firma = token.split(".")
        esperado = b64(hmac.new(SECRETO, ("%s.%s" % (cab, carga)).encode(), hashlib.sha256).digest())
        return hmac.compare_digest(firma, esperado) and json.loads(b64d(carga))["exp"] > time.time()
    except Exception:
        return False

# ---------------------------------------------------------------- multipart minimo
def parte_archivo(cuerpo, tipo):
    m = re.search(r'boundary=("?)([^";]+)\1', tipo)
    if not m: return None
    sep = b"--" + m.group(2).encode()
    for parte in cuerpo.split(sep):
        cab, _, datos = parte.partition(b"\r\n\r\n")
        if b'name="file"' in cab:
            return datos[:-2] if datos.endswith(b"\r\n") else datos
    return None

# ---------------------------------------------------------------- trabajo: compilar y cargar en la placa
def trabajo(placa, programa_st):
    placa.estado = "COMPILING"; placa.logs = []; placa.exit_code = None
    placa.st = programa_st                                               # para el panel en vivo (nombres de variables)
    placa.log("INFO", "Recibido program.st (%d bytes) para %s (%s)" % (len(programa_st), placa.nombre, placa.ip))
    try:                                                                   # copia del ultimo programa recibido (diagnostico)
        d = os.path.join(AQUI, "datos_servidor"); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "ultimo_programa_%s.st" % re.sub(r"[^A-Za-z0-9_-]", "_", placa.nombre)), "wb").write(programa_st)
    except OSError:
        pass
    try:
        with cerrojo_compilar, tempfile.TemporaryDirectory(prefix="editor_") as tmp:
            st = os.path.join(tmp, "programa.st")
            open(st, "wb").write(programa_st)
            r = subprocess.run([sys.executable, "-I", PLC_PY, st, "--solo-compilar"], capture_output=True, text=True, timeout=150)
            salida = (r.stdout + r.stderr).replace(tmp, "")
            if r.returncode != 0:
                placa.log("ERROR", salida.strip() or "Error de compilacion"); placa.estado = "FAILED"; placa.exit_code = 1; return
            placa.log("INFO", salida.strip())
            exe = os.path.splitext(st)[0] + ".openplc"
            placa.log("INFO", "Cargando en la placa %s ..." % placa.ip)
            r = subprocess.run([sys.executable, "-I", CARGAR, exe, "--ip", placa.ip], capture_output=True, text=True, timeout=60)
            salida = (r.stdout + r.stderr).strip()
            if r.returncode != 0:
                placa.log("ERROR", salida); placa.estado = "FAILED"; placa.exit_code = 1; return
            placa.log("INFO", salida)
            placa.estado = "SUCCESS"; placa.exit_code = 0; placa.fin = time.time()
    except subprocess.TimeoutExpired:
        placa.log("ERROR", "Se agoto el tiempo de compilacion o de carga"); placa.estado = "FAILED"; placa.exit_code = 1
    except Exception as e:
        placa.log("ERROR", "Error interno: %s" % e); placa.estado = "FAILED"; placa.exit_code = 1

# ---------------------------------------------------------------- API HTTPS
PLACAS = []; CLAVE = None; ESTADO_EDITOR = "STOPPED"

class Manejador(BaseHTTPRequestHandler):
    server_version = "OpenPLC-LTDI"
    def placa(self):
        ip_local = self.connection.getsockname()[0]
        for p in PLACAS:
            if p.virtual == ip_local: return p
        return PLACAS[0] if len(PLACAS) == 1 else None
    def responder(self, codigo, obj, extra=None):
        cuerpo = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(codigo); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("x-openplc-runtime-version", VERSION)
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(cuerpo)
    def autorizado(self):
        a = self.headers.get("Authorization", "")
        return a.startswith("Bearer ") and token_valido(a[7:])
    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/api/get-users-info": return self.responder(200, {"hasUsers": True})
        if ruta == "/api/capabilities": return self.responder(200, {"runtimeVersion": VERSION, "projectSnapshot": False})
        if ruta == "/api/version": return self.responder(200, {"version": VERSION})
        if not self.autorizado(): return self.responder(401, {"msg": "token ausente o vencido"})
        p = self.placa()
        if p is None: return self.responder(404, {"error": "placa desconocida para esta IP"})
        if ruta == "/api/status":
            # Con "estado_editor": "STOPPED" (por defecto) el editor no pide «parar el PLC» antes de compilar: esa
            # precaucion es para runtimes que compilan EN la placa; aqui se compila en el servidor.
            real = "RUNNING" if p.en_marcha() else "STOPPED"
            return self.responder(200, {"status": "COMPILING" if p.estado == "COMPILING" else (real if ESTADO_EDITOR == "REAL" else ESTADO_EDITOR)})
        if ruta == "/api/compilation-status":
            return self.responder(200, {"status": p.estado if p.estado != "IDLE" else "SUCCESS", "logs": p.logs, "exit_code": p.exit_code})
        if ruta == "/api/start-plc":
            return self.responder(200, {"status": "COMMAND:BUSY" if p.estado == "COMPILING" else "START:OK"})
        if ruta == "/api/stop-plc":
            # El editor pide parar el PLC antes de compilar «en el dispositivo». Aqui se compila en el servidor y el
            # programa nuevo reemplaza al anterior al cargarse, asi que parar no hace falta: se acepta la orden.
            return self.responder(200, {"status": "STOP:OK"})
        return self.responder(404, {"error": "no encontrado"})
    def do_POST(self):
        ruta = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length", "0"))
        if n > MAX_BYTES: return self.responder(413, {"error": "demasiado grande"})
        cuerpo = self.rfile.read(n)
        if ruta == "/api/login":
            try: d = json.loads(cuerpo)
            except Exception: return self.responder(400, {"error": "json invalido"})
            if CLAVE and d.get("password") != CLAVE: return self.responder(401, {"msg": "clave incorrecta"})
            return self.responder(200, {"access_token": crear_token(str(d.get("username", "alumno")))})
        if ruta == "/api/create-user": return self.responder(201, {"msg": "ok"})
        if not self.autorizado(): return self.responder(401, {"msg": "token ausente o vencido"})
        p = self.placa()
        if p is None: return self.responder(404, {"error": "placa desconocida para esta IP"})
        if ruta == "/api/upload-file":
            st = parte_archivo(cuerpo, self.headers.get("Content-Type", ""))
            if not st or not st.strip(): return self.responder(400, {"error": "falta el archivo program.st"})
            if p.estado == "COMPILING": return self.responder(409, {"error": "la placa esta ocupada"})
            threading.Thread(target=trabajo, args=(p, st), daemon=True).start()
            return self.responder(200, {"CompilationStatus": "COMPILING"})
        return self.responder(404, {"error": "no encontrado"})
    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % a))

# ---------------------------------------------------------------- descubrimiento UDP
def descubrimiento(escuchar):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((escuchar, DISCOVERY_PORT))
    salientes = {}
    def socket_de(virtual):
        if virtual not in salientes:
            t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                if virtual: t.bind((virtual, 0))
            except OSError as e:
                sys.stderr.write("AVISO: no se puede usar la IP virtual %s (%s); falta el alias?\n" % (virtual, e))
                t.close(); t = None
            salientes[virtual] = t
        return salientes[virtual]
    while True:
        datos, origen = s.recvfrom(1024)
        if datos.strip() != MAGIA: continue
        import ipaddress
        if ipaddress.ip_address(origen[0]) not in RED_PERMITIDA and not ipaddress.ip_address(origen[0]).is_loopback: continue
        for p in PLACAS:
            t = socket_de(p.virtual)
            if t is None: continue
            anuncio = {"service": "openplc-runtime", "hostname": p.nombre, "runtime_version": VERSION, "api_port": int(arg("--puerto-api", 8443))}
            if p.proyecto: anuncio["project_name"] = p.proyecto
            t.sendto(json.dumps(anuncio).encode(), origen)

# ---------------------------------------------------------------- arranque
def certificado():
    d = os.path.join(AQUI, "datos_servidor"); os.makedirs(d, exist_ok=True)
    cert, clave = os.path.join(d, "cert.pem"), os.path.join(d, "clave.pem")
    if not os.path.exists(cert):
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", clave, "-out", cert,
                        "-days", "3650", "-subj", "/CN=plc-ltdi"], check=True, capture_output=True)
        os.chmod(clave, 0o600)
    return cert, clave

if __name__ == "__main__":
    PLACAS, CLAVE = cargar_config(arg("--config", os.path.join(AQUI, "placas.json")))
    escuchar = arg("--escuchar", "0.0.0.0"); escuchar_udp = arg("--escuchar-udp", "0.0.0.0"); puerto = int(arg("--puerto-api", 8443))
    cert, clave = certificado()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert, clave)
    # Una escucha HTTPS por cada IP virtual (o una sola en --escuchar si no hay IP virtuales).
    direcciones = sorted({p.virtual for p in PLACAS if p.virtual}) or [escuchar]
    servidores = []
    for ip in direcciones:
        srv = ThreadingHTTPServer((ip, puerto), Manejador)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        servidores.append(srv)
    threading.Thread(target=descubrimiento, args=(escuchar_udp,), daemon=True).start()
    print("Runtime virtual: https en %s puerto %d, descubrimiento UDP %d, placas: %s" % (
        ", ".join(direcciones), puerto, DISCOVERY_PORT, ", ".join("%s=%s (virtual %s)" % (p.nombre, p.ip, p.virtual or "-") for p in PLACAS)), flush=True)
    for srv in servidores[1:]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    servidores[0].serve_forever()
