#!/usr/bin/env python3
"""Copia a la RAM de la placa (por telnet temporal + tcpsvd) los archivos de la imagen para probarlos antes de flashear.
Uso: empujar_ram.py <imagen_cpio> [--ip IP]   (omite el paso de red de plc.sh para no cortar el acceso)"""
import sys, os, socket, subprocess, time, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts_imagen"))
import cpio_newc as C
AQUI = os.path.dirname(os.path.abspath(__file__)); TEL = os.path.join(AQUI, "..", "tel.py")
ip = sys.argv[sys.argv.index("--ip") + 1] if "--ip" in sys.argv else "10.42.0.151"
ents, _ = C.leer(open(sys.argv[1], "rb").read())
dat = {h["nombre"]: h["datos"] for h in ents}
def tel(c): return subprocess.run([sys.executable, "-I", TEL, "--ip", ip, c], capture_output=True, text=True).stdout
tel("killall tcpsvd 2>/dev/null; mkdir -p /opt/plc /etc/plc; (tcpsvd 0.0.0.0 9100 sh -c 'cat > /tmp/openplc.new' > /tmp/rx.log 2>&1 &)"); time.sleep(1)
for n in ("etc/init.d/plc.sh", "opt/plc/rx_recibir.sh", "opt/plc/rx_aplicar.sh", "opt/plc/openplc", "etc/plc/mac"):
    d = dat[n]
    if n.endswith("plc.sh"): d = d.replace(b"    red &", b"    : &")
    s = socket.create_connection((ip, 9100)); s.sendall(d); s.close(); time.sleep(1)
    out = tel("mv -f /tmp/openplc.new /%s; chmod 755 /%s; md5sum /%s" % (n, n, n))
    ok = hashlib.md5(d).hexdigest() in out
    print(("OK  " if ok else "FALLA"), n)
tel("killall tcpsvd")
