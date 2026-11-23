#!/usr/bin/env python3
"""Galileo virtual para probar el puente y el panel sin la placa real (todo en loopback, sin root).

    python3 placa_virtual.py [--n 2] [--base 127.1.0.11]

Cada placa virtual vive en una direccion propia (127.1.0.11, 127.1.0.12, ...) y imita lo que ve el puente:
  - receptor de la imagen: 9100 (recibe el ejecutable y lo descarta), 9101 («quien» -> ERROR..., «aplicar md5» -> OK);
  - Modbus TCP en el puerto 1502 (el 502 pide root), que el receptor anuncia en su respuesta («puerto=1502»);
  - un «PLC» simulado cada 20 ms: las salidas %QX0.0..3 siguen a las entradas %IX0.0..3, %MW0 cuenta segundos y %MW1 las
    cargas recibidas; la entrada %IX0.0 parpadea sola cada 3 s; admite el forzado del panel (%MW1000..1003).
No ejecuta el programa que se le sube: sirve para revisar la interfaz, el descubrimiento y la carga."""
import sys, socket, struct, threading, time, ipaddress

PUERTO_MB = 1502
def arg(n, d): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d

class Placa:
    def __init__(self, ip, indice):
        self.ip, self.i = ip, indice
        self.ent = [0] * 8; self.sal = [0] * 4; self.hold = [0] * 8192; self.coils = [0] * 8192; self.mbent = [0] * 8192
        self.cargas = 0; self.l = threading.Lock(); self.t0 = time.time()
    def ciclo(self):
        while True:
            with self.l:
                t = time.time() - self.t0
                base = [int(t / 3) % 2 if self.i == 0 else int(t / 5) % 2, 0, 0, 0, 0, 0, 0, 0]       # la entrada 0 parpadea
                fm, fv = self.hold[2024], self.hold[2025]
                self.ent = [((fv >> k) & 1) if (fm >> k) & 1 else base[k] for k in range(8)]
                for k in range(4): self.sal[k] = self.ent[k]
                self.hold[1024] = int(t) & 0xFFFF; self.hold[1025] = self.cargas & 0xFFFF
                sm, sv = self.hold[2026], self.hold[2027]
                for k in range(4):
                    if (sm >> k) & 1: self.sal[k] = (sv >> k) & 1
            time.sleep(0.02)
    def mb(self, d):
        tid, _, _, uid, fc = struct.unpack(">HHHBB", d[:8]); a = struct.unpack(">H", d[8:10])[0]; n = struct.unpack(">H", d[10:12])[0]
        def resp(pdu): return struct.pack(">HHHB", tid, 0, len(pdu) + 1, uid) + pdu
        with self.l:
            if fc in (1, 2):
                fuente = (self.sal + self.coils[4:]) if fc == 1 else (self.ent + self.mbent[8:])
                bits = [fuente[a + k] if a + k < len(fuente) else 0 for k in range(n)]
                by = bytes(sum(bits[8 * j + k] << k for k in range(8) if 8 * j + k < n) for j in range((n + 7) // 8))
                return resp(bytes([fc, len(by)]) + by)
            if fc in (3, 4):
                regs = self.hold[a:a + n]
                return resp(bytes([fc, 2 * n]) + b"".join(struct.pack(">H", r) for r in regs))
            if fc == 5:
                v = 1 if n == 0xFF00 else 0
                if a < 4: self.sal[a] = v
                else: self.coils[a] = v
                return resp(d[7:12])
            if fc == 6:
                self.hold[a] = n; return resp(d[7:12])
        return resp(bytes([fc | 0x80, 1]))

def servir_mb(p):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((p.ip, PUERTO_MB)); s.listen(8)
    def atender(c):
        try:
            while True:
                d = c.recv(260)
                if len(d) < 12: break
                c.sendall(p.mb(d))
        except OSError: pass
        finally: c.close()
    while True:
        c, _ = s.accept(); threading.Thread(target=atender, args=(c,), daemon=True).start()

def servir_carga(p):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((p.ip, 9100)); s.listen(4)
    def atender(c):
        try:
            while c.recv(65536): pass
        except OSError: pass
        c.close()
    while True:
        c, _ = s.accept(); threading.Thread(target=atender, args=(c,), daemon=True).start()

def servir_aplicar(p):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((p.ip, 9101)); s.listen(4)
    def atender(c):
        try:
            c.settimeout(5); linea = c.makefile().readline().split()
            if linea[:1] == ["aplicar"]:
                p.cargas += 1; c.sendall(b"OK\n")
            else:
                c.sendall(b"ERROR: orden o programa ausente puerto=%d\n" % PUERTO_MB)
        except (OSError, IndexError): pass
        c.close()
    while True:
        c, _ = s.accept(); threading.Thread(target=atender, args=(c,), daemon=True).start()

if __name__ == "__main__":
    base = ipaddress.ip_address(arg("--base", "127.1.0.11")); n = int(arg("--n", 2))
    for i in range(n):
        p = Placa(str(base + i), i)
        for f in (p.ciclo, lambda p=p: servir_mb(p), lambda p=p: servir_carga(p), lambda p=p: servir_aplicar(p)):
            threading.Thread(target=f if f == p.ciclo else f, daemon=True).start()
        print("placa virtual %d en %s (Modbus %d, carga 9100/9101)" % (i + 1, p.ip, PUERTO_MB), flush=True)
    while True: time.sleep(3600)
