#!/usr/bin/env python3
"""Lector y escritor de archivos cpio en formato 'newc' (070701), en Python puro, sin root.
Conserva modo, uid/gid, mtime y numeros de dispositivo de cada entrada, para reempaquetar un
initramfs sin perder permisos ni nodos de dispositivo."""
import struct

MAGIA = b"070701"
CAMPOS = ("ino", "mode", "uid", "gid", "nlink", "mtime", "filesize", "devmajor", "devminor", "rdevmajor", "rdevminor", "namesize", "check")

def _alinear(n): return (4 - n % 4) % 4

def leer(datos):
    """Devuelve una lista de dicts: {'nombre', 'mode', ..., 'datos'}. Se detiene en TRAILER!!!."""
    i, ents = 0, []
    while i + 110 <= len(datos):
        if datos[i:i + 6] != MAGIA:
            break
        vals = [int(datos[i + 6 + 8 * k:i + 14 + 8 * k], 16) for k in range(13)]
        h = dict(zip(CAMPOS, vals))
        i += 110
        nombre = datos[i:i + h["namesize"] - 1].decode("utf-8", "surrogateescape")
        i += h["namesize"]; i += _alinear(110 + h["namesize"])
        cont = datos[i:i + h["filesize"]]
        i += h["filesize"]; i += _alinear(h["filesize"])
        if nombre == "TRAILER!!!":
            return ents, i
        h["nombre"] = nombre; h["datos"] = bytes(cont)
        ents.append(h)
    return ents, i

def escribir(ents, relleno_bloque=512):
    """Serializa las entradas (en el orden dado) y agrega TRAILER!!!. Conserva los inodos originales
    (necesario para los enlaces duros); las entradas nuevas con ino=0 reciben un numero libre."""
    out = bytearray()
    def entrada(h, nombre, cont):
        nb = nombre.encode("utf-8", "surrogateescape") + b"\0"
        vals = [h[c] for c in CAMPOS]
        vals[CAMPOS.index("filesize")] = len(cont)
        vals[CAMPOS.index("namesize")] = len(nb)
        vals[CAMPOS.index("check")] = 0
        out.extend(MAGIA + b"".join(b"%08X" % v for v in vals))
        out.extend(nb); out.extend(b"\0" * _alinear(110 + len(nb)))
        out.extend(cont); out.extend(b"\0" * _alinear(len(cont)))
    libre = max([h["ino"] for h in ents] + [0]) + 1
    for h in ents:
        h = dict(h)
        if h["ino"] == 0:
            h["ino"] = libre; libre += 1
        entrada(h, h["nombre"], h["datos"])
    trailer = {c: 0 for c in CAMPOS}; trailer["nlink"] = 1
    entrada(trailer, "TRAILER!!!", b"")
    if relleno_bloque:
        out.extend(b"\0" * ((-len(out)) % relleno_bloque))
    return bytes(out)

def es_dir(h): return (h["mode"] & 0o170000) == 0o040000
def es_enlace(h): return (h["mode"] & 0o170000) == 0o120000
def es_regular(h): return (h["mode"] & 0o170000) == 0o100000

def nueva_entrada(nombre, datos, mode, mtime=0):
    h = {c: 0 for c in CAMPOS}
    h.update(nombre=nombre, datos=datos, mode=mode, nlink=1, mtime=mtime)
    return h
