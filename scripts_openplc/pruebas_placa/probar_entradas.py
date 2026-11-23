#!/usr/bin/env python3
"""Vigila las 8 entradas por Modbus (conexion persistente) y muestra cada cambio con el nombre del pin.
Uso: probar_entradas.py [segundos] [IP]  -- para probar: unir cada pin a GND con un cable, uno por vez."""
import socket, struct, sys, time
SEG = float(sys.argv[1]) if len(sys.argv) > 1 else 300
IP = sys.argv[2] if len(sys.argv) > 2 else "10.42.0.151"
PINES = ["D2", "D3", "D4", "D5", "D6", "D7", "D12", "D13"]
c = socket.create_connection((IP, 502), timeout=5); tid = 0
def leer():
    global tid; tid = (tid + 1) % 65536
    c.sendall(struct.pack(">HHHBBHH", tid, 0, 6, 1, 2, 0, 8)); b = c.recv(64)[9]
    return [(b >> i) & 1 for i in range(8)]
ant = leer(); t0 = time.time(); vistos = {}
print("reposo:", " ".join("%s=%d" % (p, v) for p, v in zip(PINES, ant)), flush=True)
while time.time() - t0 < SEG:
    try: act = leer()
    except Exception as e: print("error Modbus:", e, flush=True); time.sleep(1); continue
    for i in range(8):
        if act[i] != ant[i]:
            print("%6.1f s  %-3s (%%IX0.%d) -> %s" % (time.time() - t0, PINES[i], i, "ACTIVA" if act[i] else "inactiva"), flush=True)
            if act[i]: vistos[PINES[i]] = vistos.get(PINES[i], 0) + 1
    ant = act; time.sleep(0.05)
print("pines que se activaron:", ", ".join("%s(x%d)" % kv for kv in vistos.items()) or "ninguno", flush=True)
