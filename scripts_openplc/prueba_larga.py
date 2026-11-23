#!/usr/bin/env python3
"""Prueba de resistencia de OpenPLC en la Galileo: ciclo de scan con E/S y trafico de red a la vez.

Carga: (a) un 'SCADA' que consulta por Modbus TCP cada 100 ms (coils, entradas y registros);
(b) un segundo cliente que arranca y para el relé cada 20 s (MARCHA, 5 s despues PARO).
Al final: quit() por el puerto 9101 (reenvia al servidor interactivo) y lee el resumen que
imprime OpenPLC en el log (puerto 9102): tiempo de ciclo y latencia de despertar, max/min/prom.
Uso: python3 -u prueba_larga.py <segundos> <salida.txt> [ip]"""
import sys, time, socket, struct, threading, statistics, re

SEG = int(sys.argv[1]); SALIDA = sys.argv[2]
IP = sys.argv[3] if len(sys.argv) > 3 else "10.42.0.151"
tid = [0]
lock = threading.Lock()

local = threading.local()

def pet(fc, dir_, v):
    """Peticion Modbus por una conexion PERSISTENTE (una por hilo), como lo haria un SCADA real.
    Abrir una conexion nueva por peticion paga hasta 100 ms: el servidor de OpenPLC acepta con sleepms(100)."""
    with lock:
        tid[0] = (tid[0] + 1) % 65536; t = tid[0]   # el id de transaccion Modbus es de 16 bits
    for intento in (0, 1):
        try:
            if getattr(local, "c", None) is None:
                local.c = socket.create_connection((IP, 502), timeout=3)
                local.c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            local.c.sendall(struct.pack(">HHHBBHH", t, 0, 6, 1, fc, dir_, v))
            d = local.c.recv(64)
            if not d: raise ConnectionError("cerrada")
            return d
        except Exception:
            try: local.c.close()
            except Exception: pass
            local.c = None
            if intento: raise

lat, errores, ciclos = [], [0], [0]
parar = threading.Event()

def scada():
    while not parar.is_set():
        t0 = time.perf_counter()
        try:
            pet(1, 0, 8); pet(2, 0, 2); pet(3, 1024, 1)
            lat.append((time.perf_counter() - t0) * 1000 / 3)
        except Exception:
            errores[0] += 1
        time.sleep(max(0, 0.1 - (time.perf_counter() - t0)))

def operador():
    while not parar.is_set():
        try:
            pet(5, 1, 0xFF00); time.sleep(0.3); pet(5, 1, 0)       # MARCHA
            if parar.wait(5): break
            pet(5, 2, 0xFF00); time.sleep(0.3); pet(5, 2, 0)       # PARO
            ciclos[0] += 1
        except Exception:
            errores[0] += 1
        parar.wait(14.4)

def log_remoto(cmd=None):
    s = socket.create_connection((IP, 9101 if cmd else 9102), timeout=5)
    if cmd:
        s.sendall((cmd + "\n").encode()); time.sleep(2)
    s.settimeout(5); out = b""
    try:
        while True:
            d = s.recv(65536)
            if not d: break
            out += d
    except Exception:
        pass
    s.close(); return out.decode(errors="replace")

t0 = time.time()
print("inicio: %d s de prueba" % SEG, flush=True)
hilos = [threading.Thread(target=scada, daemon=True), threading.Thread(target=operador, daemon=True)]
for h in hilos: h.start()
ult = 0
while time.time() - t0 < SEG:
    time.sleep(5)
    if time.time() - ult > 300:
        ult = time.time()
        print("  %4.0f s: %d consultas, %d ciclos de relé, %d errores" % (time.time() - t0, len(lat), ciclos[0], errores[0]), flush=True)
parar.set(); time.sleep(1.5)
try: pet(5, 2, 0xFF00); time.sleep(0.4); pet(5, 2, 0)
except Exception: pass

lat.sort(); n = len(lat)
res = ["Prueba de resistencia de %d s" % SEG,
       "Consultas Modbus (SCADA, cada 100 ms): %d, errores: %d, ciclos de rele: %d" % (n, errores[0], ciclos[0]),
       "Latencia por consulta (ms): min=%.2f p50=%.2f p99=%.2f max=%.2f" % (lat[0], lat[n // 2], lat[int(n * .99)], lat[-1])]
try:
    txt = log_remoto()
    pat = re.compile(r"SCAN (\d+) ciclos: periodo us min/prom/max = (\d+)/(\d+)/(\d+); >25ms: (\d+); >30ms: (\d+); E/S max us: (\d+)")
    filas = [tuple(map(int, m.groups())) for m in pat.finditer(txt)]
    if filas:
        total = sum(f[0] for f in filas)
        res.append("Scan (periodo real entre ciclos) en %d ventanas de 60 s, %d ciclos en total:" % (len(filas), total))
        res.append("  periodo us: min=%d  prom=%d  max=%d" % (min(f[1] for f in filas),
                    sum(f[0] * f[2] for f in filas) // total, max(f[3] for f in filas)))
        res.append("  ciclos con periodo >25 ms: %d  | >30 ms: %d" % (sum(f[4] for f in filas), sum(f[5] for f in filas)))
        res.append("  tiempo maximo de E/S en un scan (us): %d" % max(f[6] for f in filas))
        res.append("  peor ventana: max=%d us" % max(f[3] for f in filas))
    else:
        res.append("(no se encontraron lineas SCAN en el log)")
    log_remoto("quit()")
except Exception as e:
    res.append("No se pudo leer el log: %s" % e)
open(SALIDA, "w").write("\n".join(res) + "\n")
print("\n".join(res))
