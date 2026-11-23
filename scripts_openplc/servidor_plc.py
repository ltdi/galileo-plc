#!/usr/bin/env python3
"""Servidor de compilacion y carga del laboratorio (una sola maquina Ubuntu).

El alumno, desde Windows o Ubuntu, abre http://<servidor>:8080 en el navegador, pega o sube su
programa .st (lo exporta el editor de OpenPLC), elige la placa y pulsa «Comprobar» o «Cargar».
El servidor usa plc.py (matiec + compilador cruzado + carga por red), asi que ningun puesto
necesita toolchain. Solo biblioteca estandar de Python.

    python3 servidor_plc.py [--puerto 8080] [--placas 10.42.0.151,10.42.0.152]

Seguridad: red de laboratorio aislada, sin autenticacion. Solo acepta IP privadas."""
import sys, os, re, json, tempfile, subprocess, threading, ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PLC = os.path.join(AQUI, "plc.py")
MAX_BYTES = 200_000
cerrojo = threading.Lock()          # una compilacion a la vez (el compilador es pesado en un servidor chico)
args = sys.argv[1:]
PUERTO = int(args[args.index("--puerto") + 1]) if "--puerto" in args else 8080
PLACAS = (args[args.index("--placas") + 1] if "--placas" in args else "10.42.0.151").split(",")

PAGINA = """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PLC didáctico LTDI</title>
<style>
:root{--fondo:#fff;--texto:#1c1c1e;--borde:#c8c8cc;--acento:#0a5ad4;--ok:#1a7f37;--mal:#c62828;--panel:#f4f5f7}
@media(prefers-color-scheme:dark){:root{--fondo:#17181a;--texto:#ececec;--borde:#3a3b3f;--acento:#6ea8ff;--ok:#5fd07a;--mal:#ff7b72;--panel:#212225}}
body{background:var(--fondo);color:var(--texto);font:16px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:880px;margin-inline:auto}
h1{font-size:1.4rem;margin:.2rem 0 1rem}
textarea{width:100%;height:320px;font:14px/1.4 ui-monospace,monospace;background:var(--panel);color:var(--texto);border:1px solid var(--borde);border-radius:6px;padding:8px;box-sizing:border-box}
.fila{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:12px 0}
select,input[type=text],button{font:inherit;padding:8px 12px;border-radius:6px;border:1px solid var(--borde);background:var(--panel);color:var(--texto)}
button{cursor:pointer}button.pri{background:var(--acento);color:#fff;border-color:var(--acento)}
button:disabled{opacity:.5;cursor:wait}
pre{background:var(--panel);border:1px solid var(--borde);border-radius:6px;padding:10px;white-space:pre-wrap;min-height:4em}
.ok{color:var(--ok)}.mal{color:var(--mal)}
</style>
<h1>PLC didáctico — cargar programa</h1>
<p>Pegá tu programa en texto estructurado (.st) o elegí el archivo exportado desde el editor.</p>
<input type="file" id="archivo" accept=".st,.txt">
<textarea id="codigo" spellcheck="false" placeholder="PROGRAM prog0 ..."></textarea>
<div class="fila">
 <label>Placa <select id="placa">%PLACAS%</select></label>
 <button id="b1">Comprobar (no carga)</button>
 <button id="b2" class="pri">Cargar al PLC</button>
</div>
<pre id="salida" aria-live="polite">Listo.</pre>
<script>
const $=id=>document.getElementById(id);
$("archivo").onchange=async e=>{const f=e.target.files[0]; if(f) $("codigo").value=await f.text();};
async function enviar(cargar){
  $("b1").disabled=$("b2").disabled=true; $("salida").className=""; $("salida").textContent="Trabajando…";
  try{
    const r=await fetch("/api/programa",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({codigo:$("codigo").value,placa:$("placa").value,cargar})});
    const j=await r.json(); $("salida").textContent=j.salida; $("salida").className=j.ok?"ok":"mal";
  }catch(e){$("salida").textContent="No se pudo hablar con el servidor: "+e; $("salida").className="mal";}
  $("b1").disabled=$("b2").disabled=false;
}
$("b1").onclick=()=>enviar(false); $("b2").onclick=()=>enviar(true);
</script></html>"""

def ip_privada(txt):
    try:
        a = ipaddress.ip_address(txt)
    except ValueError:
        return False
    return a.version == 4 and a.is_private and not a.is_loopback

def procesar(codigo, placa, cargar):
    if not codigo.strip():
        return False, "El programa está vacío."
    if len(codigo.encode()) > MAX_BYTES:
        return False, "El programa es demasiado grande."
    if cargar and (placa not in PLACAS or not ip_privada(placa)):
        return False, "Placa no permitida."
    with cerrojo, tempfile.TemporaryDirectory(prefix="alumno_") as tmp:
        st = os.path.join(tmp, "programa.st")
        open(st, "w").write(codigo)
        cmd = [sys.executable, "-I", PLC, st] + (["--ip", placa] if cargar else ["--solo-compilar"])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        except subprocess.TimeoutExpired:
            return False, "Se agotó el tiempo (150 s)."
        salida = (r.stdout + r.stderr).replace(tmp, "").strip()
        return r.returncode == 0, salida or "(sin salida)"

class Manejador(BaseHTTPRequestHandler):
    def _enviar(self, codigo, tipo, cuerpo):
        self.send_response(codigo); self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo))); self.end_headers(); self.wfile.write(cuerpo)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            opciones = "".join('<option>%s</option>' % p for p in PLACAS)
            self._enviar(200, "text/html; charset=utf-8", PAGINA.replace("%PLACAS%", opciones).encode())
        else:
            self._enviar(404, "text/plain", b"no encontrado")
    def do_POST(self):
        if self.path != "/api/programa":
            return self._enviar(404, "text/plain", b"no encontrado")
        n = int(self.headers.get("Content-Length", "0"))
        if n > MAX_BYTES * 2:
            return self._enviar(413, "text/plain", b"demasiado grande")
        try:
            d = json.loads(self.rfile.read(n))
            ok, salida = procesar(str(d.get("codigo", "")), str(d.get("placa", "")), bool(d.get("cargar")))
        except Exception as e:
            ok, salida = False, "Petición inválida: %s" % e
        self._enviar(200, "application/json", json.dumps({"ok": ok, "salida": salida}).encode())
    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % a))

if __name__ == "__main__":
    print("Servidor en http://0.0.0.0:%d  (placas: %s)" % (PUERTO, ", ".join(PLACAS)), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PUERTO), Manejador).serve_forever()
