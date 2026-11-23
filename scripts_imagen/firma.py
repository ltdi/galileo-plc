#!/usr/bin/env python3
"""Firma y verificacion de activos de la flash de la Galileo (formato 'HSC_'), en Python puro.

Reimplementa asset-signing-tool/sign.c de intel/Galileo-Runtime:
  encabezado de 1024 bytes = csh (64) + clave publica (4+4+256+4) + firma RSA-PSS (256) + relleno de ceros
  firma = RSA-PSS(SHA-256(csh || cuerpo)), salt maximo (222 bytes, aleatorio), clave de 2048 bits.
No requiere OpenSSL ni Python 2. Se valida contra los activos originales de Intel."""
import os, sys, struct, hashlib, base64

ID_HSC = 0x5F435348
TAM_ENC = 1024
TAM_CSH = 64

# ------------------------------------------------------------------ clave RSA (PEM, PKCS#1)
def _der(datos, i=0):
    """Lee un TLV DER; devuelve (tag, valor, indice_siguiente)."""
    tag = datos[i]; i += 1
    n = datos[i]; i += 1
    if n & 0x80:
        k = n & 0x7F
        n = int.from_bytes(datos[i:i + k], "big"); i += k
    return tag, datos[i:i + n], i + n

def cargar_clave(ruta_pem):
    txt = open(ruta_pem).read()
    cuerpo = "".join(l for l in txt.splitlines() if not l.startswith("-----"))
    der = base64.b64decode(cuerpo)
    tag, seq, _ = _der(der)
    assert tag == 0x30, "no es una secuencia DER"
    ints, i = [], 0
    while i < len(seq):
        t, v, i = _der(seq, i)
        assert t == 0x02
        ints.append(int.from_bytes(v, "big"))
    # [0]=version, 1=n, 2=e, 3=d, ...
    return {"n": ints[1], "e": ints[2], "d": ints[3]}

# ------------------------------------------------------------------ RSA-PSS (RFC 8017) con SHA-256
def _mgf1(semilla, largo):
    out = b""; c = 0
    while len(out) < largo:
        out += hashlib.sha256(semilla + struct.pack(">I", c)).digest(); c += 1
    return out[:largo]

def pss_codificar(mhash, n_bits, salt):
    em_len = (n_bits + 7) // 8                 # 256 para 2048 bits (n_bits=2048)
    h_len = 32
    ms_bits = (n_bits - 1) & 7
    mprima = b"\x00" * 8 + mhash + salt
    h = hashlib.sha256(mprima).digest()
    ps = b"\x00" * (em_len - len(salt) - h_len - 2)
    db = ps + b"\x01" + salt
    mascara = _mgf1(h, em_len - h_len - 1)
    masked = bytes(a ^ b for a, b in zip(db, mascara))
    if ms_bits:
        masked = bytes([masked[0] & (0xFF >> (8 - ms_bits))]) + masked[1:]
    return masked + h + b"\xbc"

def pss_verificar(em, mhash, n_bits):
    em_len = (n_bits + 7) // 8
    h_len = 32
    ms_bits = (n_bits - 1) & 7
    if len(em) != em_len or em[-1] != 0xBC:
        return False, "relleno final incorrecto"
    masked, h = em[:em_len - h_len - 1], em[em_len - h_len - 1:-1]
    if ms_bits and masked[0] & (0xFF << ms_bits) & 0xFF:
        return False, "bits altos no nulos"
    mascara = _mgf1(h, len(masked))
    db = bytearray(a ^ b for a, b in zip(masked, mascara))
    if ms_bits:
        db[0] &= 0xFF >> (8 - ms_bits)
    i = 0
    while i < len(db) and db[i] == 0: i += 1
    if i >= len(db) or db[i] != 1:
        return False, "falta el separador 0x01"
    salt = bytes(db[i + 1:])
    h2 = hashlib.sha256(b"\x00" * 8 + mhash + salt).digest()
    return (h2 == h), ("ok, salt de %d bytes" % len(salt)) if h2 == h else "hash distinto"

# ------------------------------------------------------------------ activos
def armar_csh(tam_cuerpo, svn_index, svn=0, tam_enc=TAM_ENC, version=1):
    campos = [ID_HSC, version, tam_cuerpo + tam_enc, svn_index, svn, 0, 0x8086, 0, tam_enc, 1, 1, 268, 256, 0, 0, 0]
    return struct.pack("<16I", *campos)

def firmar(cuerpo, svn_index, clave, svn=0, tam_enc=TAM_ENC, salt=None):
    """Devuelve encabezado(1024) + cuerpo, firmado como lo haria sign.c."""
    csh = armar_csh(len(cuerpo), svn_index, svn, tam_enc)
    n, e, d = clave["n"], clave["e"], clave["d"]
    n_bits = n.bit_length()
    assert n_bits == 2048
    mhash = hashlib.sha256(csh + cuerpo).digest()
    salt = salt if salt is not None else os.urandom(256 - 32 - 2)
    em = pss_codificar(mhash, n_bits, salt)
    firma = pow(int.from_bytes(em, "big"), d, n).to_bytes(256, "big")
    clave_pub = struct.pack("<II", 256, 4) + n.to_bytes(256, "big") + e.to_bytes(4, "big")
    enc = csh + clave_pub + firma
    return enc + b"\x00" * (tam_enc - len(enc)) + cuerpo

def leer_encabezado(datos, off=0):
    f = struct.unpack("<16I", datos[off:off + TAM_CSH])
    mod_size, exp_size = struct.unpack("<II", datos[off + 64:off + 72])
    modulo = int.from_bytes(datos[off + 72:off + 72 + 256], "big")
    expo = int.from_bytes(datos[off + 72 + 256:off + 72 + 260], "big")
    firma = datos[off + 72 + 260:off + 72 + 260 + 256]
    return {"id": f[0], "version": f[1], "module_size": f[2], "svn_index": f[3], "svn": f[4], "header_size": f[8],
            "modulo": modulo, "exponente": expo, "firma": firma, "csh": datos[off:off + TAM_CSH]}

def verificar(datos, off=0):
    """Verifica un activo: devuelve (ok, mensaje)."""
    h = leer_encabezado(datos, off)
    if h["id"] != ID_HSC: return False, "no empieza con HSC_"
    cuerpo = datos[off + h["header_size"]: off + h["module_size"]]
    mhash = hashlib.sha256(h["csh"] + cuerpo).digest()
    em = pow(int.from_bytes(h["firma"], "big"), h["exponente"], h["modulo"]).to_bytes(256, "big")
    return pss_verificar(em, mhash, h["modulo"].bit_length())

if __name__ == "__main__":
    ayuda = "uso: firma.py verificar <archivo> [offset_hex]"
    if len(sys.argv) >= 3 and sys.argv[1] == "verificar":
        d = open(sys.argv[2], "rb").read()
        off = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0
        print(verificar(d, off))
    else:
        print(ayuda)
