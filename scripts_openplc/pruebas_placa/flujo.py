#!/usr/bin/env python3
"""Corre un comando en la placa por telnet y muestra la salida EN VIVO con hora; avisa si la conexion se corta.
Uso: flujo.py "<comando>" [segundos]"""
import sys, time, telnetlib, socket
ip = "10.42.0.151"; cmd = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 40
tn = telnetlib.Telnet(ip, 23, timeout=8)
tn.read_until(b"login:", timeout=8); tn.write(b"root\n"); time.sleep(1.2); tn.read_very_eager()
tn.write((cmd + "\n").encode()); t0 = time.time()
try:
    while time.time() - t0 < dur:
        b = tn.read_very_eager()
        if b: print("[%5.1f] %s" % (time.time() - t0, b.decode(errors="replace").replace("\r", "").rstrip()), flush=True)
        time.sleep(0.2)
    print("-- fin sin cortes")
except (EOFError, ConnectionError, socket.error) as e:
    print("-- CONEXION CORTADA a los %.1f s: %s" % (time.time() - t0, e))
