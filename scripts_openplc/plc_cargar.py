#!/usr/bin/env python3
"""Carga un programa compilado en el PLC (imagen propia) por red, sin telnet ni Arduino IDE.

Uso: python3 plc_cargar.py <ejecutable_openplc> [--ip 10.42.0.151]

Protocolo del receptor de la imagen (/opt/plc/rx_*.sh, lanzado por plc.sh con tcpsvd):
  puerto 9100: se envia el ejecutable tal cual (la conexion se cierra al terminar);
  puerto 9101: se envia "aplicar <md5>\\n"; la placa verifica la suma, reemplaza el programa y el
               supervisor relanza OpenPLC. Responde "OK" o "ERROR: ...".
Si el programa nuevo muere en menos de 10 s, la placa vuelve sola al programa de fabrica.
(La version anterior, por telnet, quedo en archivo/codigo_obsoleto/plc_cargar_telnet.py (placas con el cargador por Arduino).)"""
import sys, time, socket, hashlib

args = sys.argv[1:]
ip = "10.42.0.151"
if "--ip" in args:
    i = args.index("--ip"); ip = args[i + 1]; del args[i:i + 2]
if not args:
    print(__doc__); sys.exit(2)
datos = open(args[0], "rb").read()
md5 = hashlib.md5(datos).hexdigest()
t0 = time.time()
def paso(txt): print("[%5.1f s] %s" % (time.time() - t0, txt), flush=True)

try:
    s = socket.create_connection((ip, 9100), timeout=8)
    s.sendall(datos); s.close()
    paso("programa enviado (%d bytes)" % len(datos))
    time.sleep(0.5)
    s = socket.create_connection((ip, 9101), timeout=8)
    s.sendall(("aplicar %s\n" % md5).encode())
    s.settimeout(15)
    resp = b""
    while not resp.endswith(b"\n"):
        c = s.recv(256)
        if not c: break
        resp += c
    s.close()
except OSError as e:
    paso("ERROR de red: %s (¿placa encendida, IP correcta y con la imagen del PLC?)" % e); sys.exit(1)
resp = resp.decode(errors="replace").strip()
if resp != "OK":
    paso("ERROR: la placa respondió: %s" % (resp or "(nada)")); sys.exit(1)
paso("verificado (md5 %s...) y aplicado: OpenPLC se reinicia con el programa nuevo (≈5 s)" % md5[:8])
