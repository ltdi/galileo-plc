#!/usr/bin/env python3
"""Puente local OpenPLC Editor <-> Galileo (para correr en el MISMO PC que el editor, sin servidor aparte).

El editor 4.x cree que habla con un OpenPLC Runtime v3; este programa:
  1. busca en la red local las Galileo con la imagen del PLC (puerto 9101 abierto y respuesta propia del receptor);
  2. a cada una le da una direccion local (127.0.0.2, 127.0.0.3, ...) y la anuncia al editor cuando este hace «Search»;
  3. al recibir un programa («Build and upload») lo compila con matiec y lo carga en esa placa.
Todo queda en loopback: nada se abre hacia la red salvo el escaneo saliente de las placas. No hace falta sudo,
ni IP virtuales, ni servidor del laboratorio, ni escribir la IP de las placas (sirve con DHCP).

Uso:  python3 puente_local.py [--redes 10.42.0.0/24,192.168.1.0/24] [--puerto-api 8443]
Lo normal es lanzarlo con lanzar_plc.py, que tambien abre el editor y lo detiene al cerrarlo."""
import sys, os, re, json, ssl, time, socket, ipaddress, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import servidor_runtime as sr

PUERTO_CARGA = 9101
CACHE = os.path.join(os.path.expanduser("~"), ".config", "galileo-plc")
ARCH_MAPA = os.path.join(CACHE, "direcciones.json")          # MAC -> 127.0.0.N, para que cada placa conserve su direccion
cerrojo = threading.Lock()
mapa = {}                      # mac -> direccion local
escuchas = {}                  # direccion local -> servidor HTTPS
ctx = None
puerto_api = int(sr.arg("--puerto-api", 8443))
ultimo_escaneo = 0.0

def log(msg): sys.stderr.write("[puente %s] %s\n" % (time.strftime("%H:%M:%S"), msg)); sys.stderr.flush()

# ------------------------------------------------------------------ red local
def comando(*c):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=5).stdout
    except Exception: return ""

def direcciones_propias():
    ips = {"127.0.0.1"}
    for l in comando("ip", "-4", "-o", "addr").splitlines():
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", l)
        if m: ips.add(m.group(1))
    return ips

def redes_a_escanear():
    pedido = sr.arg("--redes", "")
    if pedido: return [ipaddress.ip_network(r.strip(), strict=False) for r in pedido.split(",") if r.strip()]
    redes = []
    for l in comando("ip", "-4", "-o", "addr", "show", "scope", "global").splitlines():
        m = re.search(r"^\d+:\s+(\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/(\d+)", l)
        if not m: continue
        nombre, ip, pref = m.group(1), m.group(2), int(m.group(3))
        if re.match(r"(docker|br-|veth|virbr|tun|tap)", nombre): continue
        red = ipaddress.ip_network("%s/%d" % (ip, max(pref, 22)), strict=False)       # nunca mas de 1022 direcciones
        if red.is_private and red not in redes: redes.append(red)
    redes.append(ipaddress.ip_network("127.1.0.0/28"))      # placas virtuales de prueba (placa_virtual.py), si estan en marcha
    return redes

puertos_modbus = {}            # ip -> puerto Modbus (502 en las placas reales; las virtuales de prueba anuncian otro)

def es_galileo(ip):
    """Puerto 9101 abierto y respuesta propia del receptor de la imagen (rx_aplicar.sh)."""
    try:
        s = socket.create_connection((ip, PUERTO_CARGA), timeout=0.6)
        s.settimeout(1.5); s.sendall(b"quien\n")
        r = s.recv(128); s.close()
        m = re.search(rb"puerto=(\d+)", r)
        puertos_modbus[ip] = int(m.group(1)) if m else 502
        return r.startswith(b"ERROR")
    except OSError:
        return False

def mac_de(ip):
    if ip.startswith("127."):                      # placas virtuales de prueba: sin ARP, MAC ficticia estable
        o = ip.split("."); return "00:00:00:00:%02x:%02x" % (int(o[2]), int(o[3]))
    m = re.search(r"lladdr (\S+)", comando("ip", "neigh", "show", ip))
    return m.group(1).lower() if m else None

def escanear():
    global ultimo_escaneo
    hosts = [str(h) for r in redes_a_escanear() for h in r.hosts()]
    propias = direcciones_propias()
    hallados = []
    with ThreadPoolExecutor(max_workers=64) as ex:
        for ip, ok in zip(hosts, ex.map(lambda h: h not in propias and es_galileo(h), hosts)):
            if ok: hallados.append(ip)
    ultimo_escaneo = time.time()
    for ip in hallados:
        mac = mac_de(ip) or ("ip-" + ip)
        registrar(mac, ip)
    return hallados

# ------------------------------------------------------------------ placas y direcciones locales
def cargar_mapa():
    try: return json.load(open(ARCH_MAPA))
    except Exception: return {}

def guardar_mapa():
    try:
        os.makedirs(CACHE, exist_ok=True); json.dump(mapa, open(ARCH_MAPA, "w"), indent=1)
    except OSError: pass

def direccion_libre():
    usadas = set(mapa.values())
    for n in range(2, 250):
        d = "127.0.0.%d" % n
        if d not in usadas: return d
    raise SystemExit("demasiadas placas")

def nombre_de(mac):
    return "Galileo-" + mac.replace(":", "")[-4:].upper() if re.match(r"([0-9a-f]{2}:){5}[0-9a-f]{2}$", mac) else "Galileo-" + mac[-6:]

def registrar(mac, ip):
    with cerrojo:
        if mac not in mapa:
            mapa[mac] = direccion_libre(); guardar_mapa()
        local = mapa[mac]
        placa = next((p for p in sr.PLACAS if p.virtual == local), None)
        if placa is None:
            placa = sr.Placa({"nombre": nombre_de(mac), "ip": ip, "virtual": local}); sr.PLACAS.append(placa)
            log("placa encontrada: %s en %s (direccion local %s)" % (placa.nombre, ip, local))
        placa.mb_puerto = puertos_modbus.get(ip, 502)
        if placa.ip != ip:
            log("%s cambio de IP: %s -> %s" % (placa.nombre, placa.ip, ip)); placa.ip = ip
        if local not in escuchas:
            srv = ThreadingHTTPServer((local, puerto_api), sr.Manejador)
            srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
            escuchas[local] = srv
            threading.Thread(target=srv.serve_forever, daemon=True).start()

def escaneo_periodico():
    while True:
        try: escanear()
        except Exception as e: log("error al escanear: %s" % e)
        time.sleep(15)

# ------------------------------------------------------------------ descubrimiento del editor (UDP 33333)
def descubrimiento():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", sr.DISCOVERY_PORT))
    salientes = {}
    while True:
        datos, origen = s.recvfrom(1024)
        if datos.strip() != sr.MAGIA: continue
        if origen[0] not in direcciones_propias(): continue            # solo se atiende al editor de este mismo PC
        if time.time() - ultimo_escaneo > 10:
            try: escanear()
            except Exception: pass
        for p in list(sr.PLACAS):
            t = salientes.get(p.virtual)
            if t is None:
                t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try: t.bind((p.virtual, 0))
                except OSError as e: log("no se pudo usar %s: %s" % (p.virtual, e)); continue
                salientes[p.virtual] = t
            anuncio = {"service": "openplc-runtime", "hostname": p.nombre, "runtime_version": sr.VERSION, "api_port": puerto_api}
            try: t.sendto(json.dumps(anuncio).encode(), origen)
            except OSError as e: log("respuesta de descubrimiento fallida: %s" % e)

# ------------------------------------------------------------------ principal
if __name__ == "__main__":
    mapa.update(cargar_mapa())
    sr.CLAVE = "plc"                       # relleno: el editor lo pide por protocolo; no hay red expuesta
    sr.ESTADO_EDITOR = "STOPPED"
    cert, clave = sr.certificado()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert, clave)
    log("redes a escanear: %s" % ", ".join(str(r) for r in redes_a_escanear()) or "ninguna")
    threading.Thread(target=escaneo_periodico, daemon=True).start()
    import panel_vivo
    try:
        panel_vivo.servir(lambda: list(sr.PLACAS), int(sr.arg("--puerto-panel", 8088)))
        log("panel en vivo: http://127.0.0.1:%s" % sr.arg("--puerto-panel", 8088))
    except OSError as e:
        log("no se pudo abrir el panel en vivo: %s" % e)
    log("listo: el editor puede hacer «Search» (usuario cualquiera, contraseña plc)")
    descubrimiento()
