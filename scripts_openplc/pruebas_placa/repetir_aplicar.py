#!/usr/bin/env python3
"""Aplica N veces, alternando dos programas, y comprueba Modbus tras cada una (prueba del receptor en la placa)."""
import subprocess, sys, time, os
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, "..", "..")
sys.path.insert(0, os.path.join(AQUI, ".."))
import modbus_min as m
progs = [os.path.join(RAIZ, "ejemplos_alumno/prueba_es.openplc"), os.path.join(RAIZ, "openplc_galileo_8e4s/openplc")]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
for n in range(N):
    p = progs[n % 2]
    r = subprocess.run([sys.executable, "-I", os.path.join(AQUI, "..", "plc_cargar.py"), p], capture_output=True, text=True)
    ok = "aplicado" in r.stdout
    time.sleep(12)
    try:
        m.entrada(0); res = "modbus ok"
    except Exception as e:
        res = "modbus FALLA: %s" % e
    print(n + 1, os.path.basename(p), "aplicado" if ok else "NO aplicado: " + (r.stdout + r.stderr)[-100:], res, flush=True)
