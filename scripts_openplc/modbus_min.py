"""Cliente Modbus TCP minimo (sockets crudos) para las pruebas."""
import socket, struct, time
IP = "10.42.0.151"
_tid = 0
def pet(fc, dir_, v, ip=None):
    global _tid
    _tid += 1
    c = socket.create_connection((ip or IP, 502), timeout=3)
    c.sendall(struct.pack(">HHHBBHH", _tid, 0, 6, 1, fc, dir_, v))
    d = c.recv(64); c.close(); return d
def coil(n):    return pet(1, n, 1)[9] & 1
def entrada(n): return pet(2, n, 1)[9] & 1
def reg(n):     return struct.unpack(">H", pet(3, n, 1)[9:11])[0]
def escribir(n, v): pet(5, n, 0xFF00 if v else 0)
