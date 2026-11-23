#!/usr/bin/env python3
"""Monitor en vivo de la Galileo por Modbus TCP: entradas, salidas y registros %MW, y forzado desde el teclado.

    python3 monitor_plc.py [--ip 10.42.0.151]     (sin --ip, busca la placa en la red del PC)

Ordenes (escribir y Enter):  q0 1 | q1 0 ...  fuerza la salida %QX0.n (la pisa el programa si lo escribe el programa)
                              mw 0 123         escribe el registro %MW0
                              salir
Las salidas que el programa de la placa escribe cada ciclo no se pueden forzar desde aqui (las reescribe el programa)."""
import sys, os, time, socket, struct, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts_openplc"))
args = sys.argv[1:]
ip = args[args.index("--ip") + 1] if "--ip" in args else None
if ip is None:
    import puente_local as P
    for red in P.redes_a_escanear():
        for h in red.hosts():
            if P.es_galileo(str(h)): ip = str(h); break
        if ip: break
    if ip is None: print("No encuentro ninguna Galileo con la imagen del PLC. Usa --ip."); sys.exit(2)
NOMBRES_E = ["D2", "D3", "D4", "D5", "D6", "D7", "D12", "D13"]
NOMBRES_S = ["D8", "D9", "D10", "D11"]
c = socket.create_connection((ip, 502), timeout=3); tid = 0; cerrojo = threading.Lock()
def pet(fc, a, v):
    global tid
    with cerrojo:
        tid = (tid + 1) % 65536
        c.sendall(struct.pack(">HHHBBHH", tid, 0, 6, 1, fc, a, v)); return c.recv(256)
def leer():
    e = pet(2, 0, 8)[9]; s = pet(1, 0, 4)[9]
    r = pet(3, 1024, 4); mw = struct.unpack(">4H", r[9:17]) if len(r) >= 17 else (0,)*4
    return e, s, mw
vivo = True
def pantalla():
    while vivo:
        try: e, s, mw = leer()
        except Exception as ex: print("\rerror Modbus:", ex); time.sleep(1); continue
        f = lambda n, m: " ".join("%s=%s" % (n[i], "#" if m >> i & 1 else ".") for i in range(len(n)))
        sys.stdout.write("\r\x1b[K entradas: %s | salidas: %s | MW0..3: %s   > " % (f(NOMBRES_E, e), f(NOMBRES_S, s), " ".join(map(str, mw))))
        sys.stdout.flush(); time.sleep(0.25)
threading.Thread(target=pantalla, daemon=True).start()
print("Conectado a %s. Ordenes: q<n> 0|1, mw <n> <valor>, salir" % ip)
try:
    for linea in sys.stdin:
        p = linea.split()
        if not p: continue
        try:
            if p[0] == "salir": break
            elif p[0].startswith("q") and len(p) == 2: pet(5, int(p[0][1:]), 0xFF00 if p[1] != "0" else 0)
            elif p[0] == "mw" and len(p) == 3: pet(6, 1024 + int(p[1]), int(p[2]) & 0xFFFF)
            else: print("\norden no entendida")
        except Exception as ex: print("\nerror:", ex)
finally:
    vivo = False; print()
