"""Panel en vivo del puente: variables con nombre, entradas/salidas de la placa y escritura, en el navegador.
Lo sirve puente_local.py en http://127.0.0.1:8088 (solo loopback). Lee y escribe por Modbus TCP con UNA conexion
persistente por placa (abrir y cerrar conexiones sin parar hace perder descriptores al servidor Modbus de OpenPLC)."""
import re, json, time, socket, struct, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PINES_E = ["D2", "D3", "D4", "D5", "D6", "D7", "D12", "D13"]
PINES_S = ["D8", "D9", "D10", "D11"]
REG_FORZ = 2024     # %MW1000..%MW1003: mascara/valor de entradas, mascara/valor de salidas (ver la capa de hardware)

class Modbus:
    def __init__(self, ip, puerto=502): self.ip = ip; self.puerto = puerto; self.s = None; self.tid = 0; self.l = threading.Lock()
    def _pet(self, fc, a, v):
        for intento in (0, 1):
            try:
                if self.s is None: self.s = socket.create_connection((self.ip, self.puerto), timeout=3)
                self.tid = (self.tid + 1) % 65536
                self.s.sendall(struct.pack(">HHHBBHH", self.tid, 0, 6, 1, fc, a, v))
                r = self.s.recv(512)
                if len(r) < 9: raise OSError("respuesta corta")
                return r
            except OSError:
                try: self.s.close()
                except Exception: pass
                self.s = None
                if intento: raise
    def leer(self, fc, a, n):
        with self.l: return self._pet(fc, a, n)
    def escribir(self, fc, a, v):
        with self.l: return self._pet(fc, a, v)

def variables_de(st):
    """Variables con ubicacion (AT %...) del primer PROGRAM de un texto estructurado."""
    out = []
    if isinstance(st, bytes): st = st.decode("utf-8", "replace")      # el puente guarda el programa tal como llega (bytes)
    for m in re.finditer(r"\b(\w+)\s+AT\s+%([IQM])([XWD])(\d+)(?:\.(\d+))?\s*:\s*(\w+)", st or "", re.I):
        nom, area, tam, n, bit, tipo = m.group(1), m.group(2).upper(), m.group(3).upper(), int(m.group(4)), m.group(5), m.group(6).upper()
        loc = "%%%s%s%d%s" % (area, tam, n, ("." + bit) if bit is not None else "")
        out.append({"nombre": nom, "ubicacion": loc, "area": area, "tam": tam, "n": n, "bit": int(bit) if bit is not None else None, "tipo": tipo})
    return out

def valor_de(mb, v):
    a, t = v["area"], v["tam"]
    if t == "X" and v["bit"] is not None:
        idx = v["n"] * 8 + v["bit"]
        if a == "I": return mb.leer(2, idx, 1)[9] & 1
        if a == "Q": return mb.leer(1, idx, 1)[9] & 1
        return None                              # %MX no esta expuesto por Modbus en este nucleo
    if t == "W":
        base = {"I": ("IR", 0), "Q": ("HR", 0), "M": ("HR", 1024)}[a]
        r = mb.leer(4 if a == "I" else 3, base[1] + v["n"], 1)
        return struct.unpack(">h" if v["tipo"] == "INT" else ">H", r[9:11])[0]
    return None

PAGINA = r"""<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Panel en vivo - PLC Galileo</title>
<style>
:root{--f:#fff;--t:#1c1c1e;--b:#c8c8cc;--p:#f4f5f7;--on:#1a7f37;--ac:#0a5ad4}
@media(prefers-color-scheme:dark){:root{--f:#17181a;--t:#ececec;--b:#3a3b3f;--p:#212225;--on:#5fd07a;--ac:#6ea8ff}}
body{background:var(--f);color:var(--t);font:15px/1.4 system-ui,sans-serif;margin:0;padding:16px;max-width:900px;margin-inline:auto}
h1{font-size:1.2rem;margin:.2rem 0 1rem}h2{font-size:1rem;margin:1.2rem 0 .4rem}
.fila{display:flex;gap:10px;flex-wrap:wrap}
.led{border:1px solid var(--b);background:var(--p);border-radius:8px;padding:6px 10px;min-width:64px;text-align:center}
.led b{display:block;font-size:.8rem;font-weight:600}.led i{display:inline-block;width:14px;height:14px;border-radius:50%;border:1px solid var(--b);background:transparent}
.led.on i{background:var(--on);border-color:var(--on)}
table{border-collapse:collapse;width:100%}td,th{border:1px solid var(--b);padding:5px 8px;text-align:left}th{background:var(--p)}
button,select,input{font:inherit;padding:4px 10px;border-radius:6px;border:1px solid var(--b);background:var(--p);color:var(--t)}button{cursor:pointer}
.led.fz{border-color:#e08a00;box-shadow:0 0 0 2px #e08a0055}.bt button{padding:1px 7px;margin:2px 1px;font-size:.8rem}.v{font-variant-numeric:tabular-nums;font-weight:600}.nota{color:var(--b);font-size:.85rem}.e{color:#c62828}
</style>
<h1>Panel en vivo <select id="placa"></select> <span id="est" class="nota"></span></h1>
<h2>Entradas</h2><div class="fila" id="ent"></div>
<h2>Salidas</h2><div class="fila" id="sal"></div>
<h2>Variables del programa</h2>
<table><thead><tr><th>Nombre</th><th>Ubicación</th><th>Tipo</th><th>Valor</th><th>Escribir</th></tr></thead><tbody id="vars"></tbody></table>
<p class="nota" id="nota"></p>
<script>
const $=i=>document.getElementById(i);let placa="";
async function api(u,o){const r=await fetch(u,o);return r.json()}
async function cargar(){const l=await api("/api/placas");const s=$("placa");const a=s.value;s.innerHTML=l.map(p=>`<option>${p}</option>`).join("");if(a&&l.includes(a))s.value=a;placa=s.value}
$("placa").onchange=()=>{placa=$("placa").value};
function ledHTML(id,n,pin,tipo,i){return `<div class="led" id="${id}"><b>${n}</b><i></i><div class="nota">${pin}</div><div class="bt"><button onclick="forzar('${tipo}',${i},'1')">1</button><button onclick="forzar('${tipo}',${i},'0')">0</button><button onclick="forzar('${tipo}',${i},'x')">×</button></div></div>`}
async function forzar(tipo,n,modo){await api("/api/escribir",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({placa,tipo,n,modo})})}
async function escribir(tipo,n,valor){await api("/api/escribir",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({placa,tipo,n,valor})})}
// La pagina se actualiza 2,5 veces por segundo SIN reconstruir los botones (si se reconstruyeran, un clic se perderia a mitad).
let firma="",firmaPlaca="";
function ponerLed(id,on,forz,base){const e=$(id);if(!e)return;e.classList.toggle("on",!!on);e.classList.toggle("fz",!!forz);e.querySelector("b").textContent=base+(forz?" (forzada)":"")}
async function ciclo(){
  if(!placa){await cargar();if(!placa){$("est").textContent="(sin placas: haga Search en el editor o espere al escaneo)";return}}
  try{const d=await api("/api/estado?placa="+encodeURIComponent(placa));
    if(d.error){$("est").innerHTML=`<span class=e>${d.error}</span>`;return}
    $("est").textContent="conectada: "+d.ip;
    if(firmaPlaca!==placa){firmaPlaca=placa;
      $("ent").innerHTML=d.pines_e.map((p,i)=>ledHTML("e"+i,"%IX0."+i,p,"e",i)).join("");
      $("sal").innerHTML=d.pines_s.map((p,i)=>ledHTML("s"+i,"%QX0."+i,p,"s",i)).join("");firma=""}
    d.entradas.forEach((v,i)=>ponerLed("e"+i,v,d.fe>>i&1,"%IX0."+i));
    d.salidas.forEach((v,i)=>ponerLed("s"+i,v,d.fs>>i&1,"%QX0."+i));
    const f=JSON.stringify(d.vars.map(v=>[v.nombre,v.ubicacion,v.tipo]));
    if(f!==firma){firma=f;
      $("vars").innerHTML=d.vars.map((v,k)=>{let w="";
        if(v.tam=="X"&&v.area!="M"&&v.n==0){const t=v.area=="I"?"e":"s";w=`<button onclick="forzar('${t}',${v.bit},'1')">forzar 1</button> <button onclick="forzar('${t}',${v.bit},'0')">forzar 0</button> <button onclick="forzar('${t}',${v.bit},'x')">soltar</button>`}
        if(v.area=="M"&&v.tam=="W")w=`<input size=6 id="w${v.n}" value=""> <button onclick="escribir('mw',${v.n},document.getElementById('w${v.n}').value)">escribir</button>`;
        return `<tr><td>${v.nombre}</td><td>${v.ubicacion}</td><td>${v.tipo}</td><td class="v" id="v${k}"></td><td>${w}</td></tr>`}).join("")||`<tr><td colspan=5>Sin variables con ubicación (cargue un programa con «AT %…»).</td></tr>`}
    d.vars.forEach((v,k)=>{const c=$("v"+k);if(c)c.textContent=v.valor===null?"-":v.valor;
      const i=$("w"+v.n);if(i&&v.area=="M"&&document.activeElement!==i&&!i.dataset.t)i.value=v.valor??""});
    $("nota").textContent=d.programa?"Forzar = el valor se impone a la entrada o a la salida aunque el programa diga otra cosa (se libera con «×» o «soltar»; también al reiniciar el PLC). Programa cargado desde el editor en esta sesión.":"Aún no se subió ningún programa en esta sesión: se muestran solo las entradas y salidas."
  }catch(e){$("est").innerHTML=`<span class=e>sin respuesta del puente</span>`}
}
cargar();setInterval(ciclo,400);
</script></html>"""

def servir(obtener_placas, puerto=8088):
    class H(BaseHTTPRequestHandler):
        def _j(self, o, c=200):
            b = json.dumps(o).encode(); self.send_response(c); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        def _placa(self, nombre):
            for p in obtener_placas():
                if p.nombre == nombre:
                    if not hasattr(p, "mb"): p.mb = Modbus(p.ip, getattr(p, "mb_puerto", 502))
                    p.mb.ip = p.ip; p.mb.puerto = getattr(p, "mb_puerto", 502)
                    return p
        def do_GET(self):
            ruta, _, q = self.path.partition("?")
            if ruta == "/":
                b = PAGINA.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
            if ruta == "/api/placas": return self._j([p.nombre for p in obtener_placas()])
            if ruta == "/api/estado":
                nombre = re.sub(r"%([0-9A-F]{2})", lambda m: chr(int(m.group(1), 16)), q.split("=", 1)[-1]) 
                p = self._placa(nombre)
                if p is None: return self._j({"error": "placa desconocida"})
                try:
                    e = p.mb.leer(2, 0, 8)[9]; s = p.mb.leer(1, 0, 4)[9]
                    fr = p.mb.leer(3, REG_FORZ, 4)
                    fz = struct.unpack(">4H", fr[9:17]) if len(fr) >= 17 else (0, 0, 0, 0)
                    vars_ = []
                    for v in variables_de(getattr(p, "st", "")):
                        try: val = valor_de(p.mb, v)
                        except (OSError, struct.error, IndexError): val = None
                        vars_.append(dict(v, valor=val))
                    return self._j({"ip": p.ip, "entradas": [e >> i & 1 for i in range(8)], "salidas": [s >> i & 1 for i in range(4)],
                                    "pines_e": PINES_E, "pines_s": PINES_S, "fe": fz[0], "fs": fz[2], "vars": vars_, "programa": bool(getattr(p, "st", None))})
                except OSError as ex:
                    return self._j({"error": "sin respuesta de la placa (%s)" % ex})
                except Exception as ex:                       # nunca dejar caer la pagina por un error inesperado
                    return self._j({"error": "error interno del panel: %r" % (ex,)})
            self._j({"error": "no encontrado"}, 404)
        def do_POST(self):
            if self.path != "/api/escribir": return self._j({"error": "no encontrado"}, 404)
            try:
                d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                p = self._placa(d["placa"]); n = int(d["n"])
                if p is None: return self._j({"error": "placa desconocida"})
                if d["tipo"] in ("e", "s"):                              # forzar / liberar una entrada o una salida
                    base = REG_FORZ + (0 if d["tipo"] == "e" else 2)
                    r = p.mb.leer(3, base, 2); m, v = struct.unpack(">2H", r[9:13]); bit = 1 << n
                    modo = str(d["modo"])
                    if modo == "x": m &= ~bit; v &= ~bit
                    else: m |= bit; v = (v | bit) if modo == "1" else (v & ~bit)
                    p.mb.escribir(6, base + 1, v & 0xFFFF); p.mb.escribir(6, base, m & 0xFFFF)
                    return self._j({"ok": True})
                if d["tipo"] == "q": p.mb.escribir(5, n, 0xFF00 if int(d["valor"]) else 0)
                elif d["tipo"] == "mw": p.mb.escribir(6, 1024 + n, int(d["valor"]) & 0xFFFF)
                else: return self._j({"error": "tipo no soportado"})
                return self._j({"ok": True})
            except (ValueError, KeyError, OSError) as ex:
                return self._j({"error": str(ex)})
        def log_message(self, *a): pass
    srv = ThreadingHTTPServer(("127.0.0.1", puerto), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
