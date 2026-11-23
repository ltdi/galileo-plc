#!/usr/bin/env python3
"""Ejecuta comandos en la Galileo por telnet y muestra solo su salida.
Uso: python3 -I tel.py [--ip IP] [--t SEGUNDOS] "comando 1" "comando 2" ...
Cada comando se corre en la misma sesion (cd y variables persisten)."""
import sys, time, telnetlib

args = sys.argv[1:]
ip, espera = "10.42.0.151", 30
while args and args[0] in ("--ip", "--t"):
    if args[0] == "--ip": ip = args[1]
    else: espera = float(args[1])
    args = args[2:]

tn = telnetlib.Telnet(ip, 23, timeout=8)
tn.read_until(b"login:", timeout=8)
tn.write(b"root\n"); time.sleep(1.5); tn.read_very_eager()
tn.write(b"stty cols 250; export PS1='# '\n"); time.sleep(0.6); tn.read_very_eager()

def correr(cmd):
    marca = "__F''IN__"                      # partida en el eco, entera en la salida
    tn.write((cmd + "; echo " + marca + "\n").encode())
    fin = time.time() + espera
    buf = b""
    while time.time() < fin:
        buf += tn.read_very_eager()
        if b"\n__FIN__" in buf.replace(b"\r", b""):
            break
        time.sleep(0.1)
    txt = buf.decode(errors="replace").replace("\r", "")
    lineas = txt.split("\n")
    # descartar el eco del comando (hasta la linea que contiene la marca partida)
    while lineas and ("__F''IN__" in lineas[0] or cmd[:20] in lineas[0] or not lineas[0].strip()):
        lineas.pop(0)
        if not lineas: break
    salida = [l for l in lineas if l.strip() != "__FIN__" and not l.startswith("# ")]
    return "\n".join(salida).rstrip()

for c in args:
    print("$ " + c)
    print(correr(c))
    print()
tn.write(b"exit\n")
