#!/usr/bin/env python3
"""Construye una imagen de flash (.bin) y una capsula (.cap) para la Galileo Gen 1, a partir de las oficiales de
Intel (firmware 1.1.1), cambiando SOLO el initramfs:
  - quita la pila Bluetooth (no hace falta en un PLC) para hacer lugar,
  - agrega el ejecutable de OpenPLC, la MAC de la placa y un script de arranque (rc5.d/S85plc.sh).
El initramfs conserva EXACTAMENTE el tamano original (se rellena con ceros, que el kernel ignora) para no
mover ningun otro componente de la capsula. Se vuelven a firmar el activo y la capsula con la clave por
defecto de Intel, igual que hacia sign.c.

Uso: construir_imagen.py <dir_flash_intel> <key.pem> <openplc> <mac> <dir_salida>"""
import os, sys, subprocess, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firma, cpio_newc as C

D_INTEL, KEY, OPENPLC, MAC, SALIDA = sys.argv[1:6]
os.makedirs(SALIDA, exist_ok=True)

BIN_ORIG = open(os.path.join(D_INTEL, "Flash-missingPDAT-Release-1.1.1.bin"), "rb").read()
CAP_ORIG = open(os.path.join(D_INTEL, "Flash-missingPDAT-Release-1.1.1.cap"), "rb").read()
OFF_BIN, OFF_CAP, TAM_ACTIVO = 0x260000, 0x224590, 2722981      # initramfs (svn_index 7)
clave = firma.cargar_clave(KEY)

# ---------------------------------------------------------------- 1. initramfs original
act = BIN_ORIG[OFF_BIN:OFF_BIN + TAM_ACTIVO]
assert act == CAP_ORIG[OFF_CAP:OFF_CAP + TAM_ACTIVO], "el initramfs de la imagen y el de la capsula deben ser iguales"
assert firma.verificar(act)[0], "la firma original no verifica"
lzma_orig = act[1024:]
cpio = subprocess.run(["xz", "--format=lzma", "-dc"], input=lzma_orig, capture_output=True, check=True).stdout
ents, _ = C.leer(cpio)

# ---------------------------------------------------------------- 2. modificaciones
PREF_BT = ("lib/modules/3.8.7-yocto-standard/kernel/net/bluetooth/",)
ARCH_BT = ("lib/modules/3.8.7-yocto-standard/kernel/drivers/bluetooth/",)
quitar = [h["nombre"] for h in ents if h["nombre"].startswith(PREF_BT + ARCH_BT)]
ents = [h for h in ents if not h["nombre"].startswith(PREF_BT + ARCH_BT)]
n_quitados = len(quitar)

for h in ents:                                   # la lista de modulos de la Gen 1 ya no pide btusb
    if h["nombre"] == "etc/modules-load.quark/galileo.conf":
        h["datos"] = b"".join(l + b"\n" for l in h["datos"].split(b"\n") if l.strip() and l.strip() != b"btusb")

PLC_SH = r"""#!/bin/sh
# Arranque automatico del PLC didactico (OpenPLC) en la Galileo Gen 1, con supervisor.
# Corre en el nivel 5, despues de quark-init (modulos) y galileod (cargador de sketches).
PLC_BIN=/opt/plc/openplc       # programa de fabrica: todas las salidas apagadas (programa_fabrica_seguro.st)
PLC_USR=/tmp/openplc_user      # programa cargado por el alumno (vive en RAM: se pierde al apagar)
PIDPLC=/tmp/openplc.pid
LOG=/tmp/openplc.log
PIDSUP=/tmp/plc_supervisor.pid
MAX_FD=900          # el limite de Linux es 1024: se reinicia antes de agotarlo
MAX_LOG=262144      # 256 KB: el log vive en RAM
log() { echo "PLC: $*" > /dev/console 2>/dev/null; }

# Salidas a nivel inactivo (por sysfs): GPIO de D8 D9 D10 D11. Si no estan exportadas no hace nada.
salidas_apagar() {
    for g in 26 19 16 25; do echo 0 > /sys/class/gpio/gpio$g/value 2>/dev/null; done
}

# Consulta Modbus de prueba (leer 8 coils): devuelve cuantos bytes contesta el servidor
salud() {
    printf '\000\001\000\000\000\006\001\001\000\000\000\010' | timeout -t 3 nc 127.0.0.1 502 2>/dev/null | wc -c
}

lanzar() {
    cd /tmp
    # En el arranque el modulo i2c-dev se carga ~1 s despues: sin /dev/i2c-0 OpenPLC no puede poner el pull-up
    # a las entradas del Cypress (D4..D7 quedarian flotantes). Se espera hasta 30 s.
    n=0; while [ ! -e /dev/i2c-0 ] && [ $n -lt 30 ]; do sleep 1; n=$((n+1)); done
    BIN="$PLC_BIN"; [ -x "$PLC_USR" ] && BIN="$PLC_USR"
    setsid "$BIN" >> "$LOG" 2>&1 < /dev/null &
    PID=$!
    echo $PID > "$PIDPLC"
    sleep 3
    # El servidor de control de OpenPLC lee UNA orden por mensaje.
    ( echo 'start_modbus(502)'; sleep 1; echo 'start_pstorage(2)'; sleep 1 ) | timeout -t 5 nc 127.0.0.1 43628 > /dev/null 2>&1
}

# Parada ordenada de OpenPLC por su puerto de control. NUNCA se le envian senales (SIGTERM/SIGKILL/SIGSTOP) salvo como
# ultimo recurso: en esta placa dejaron colgado el sistema. Si ya murio, no hace nada.
parar_plc() {
    kill -0 $PID 2>/dev/null || return 0
    ( echo 'quit()'; sleep 2 ) | timeout -t 4 nc 127.0.0.1 43628 > /dev/null 2>&1
    n=0; while kill -0 $PID 2>/dev/null && [ $n -lt 8 ]; do sleep 1; n=$((n+1)); done
    if kill -0 $PID 2>/dev/null; then log "OpenPLC no respondio a quit(): ultimo recurso"; kill -9 $PID 2>/dev/null; fi
}

supervisar() {
    ifconfig lo 127.0.0.1 up 2>/dev/null     # el puerto de control de OpenPLC escucha en 127.0.0.1
    red &                                    # la red no debe demorar al PLC
    receptor &
    while true; do
        lanzar
        log "OpenPLC en marcha (pid $PID, $BIN)"
        malas=0
        t0=$(cut -d. -f1 /proc/uptime)
        while kill -0 $PID 2>/dev/null; do
            sleep 5
            n=$(ls /proc/$PID/fd 2>/dev/null | wc -l)
            if [ "$n" -gt "$MAX_FD" ]; then log "demasiados descriptores ($n): reinicio"; break; fi
            t=$(wc -c < "$LOG" 2>/dev/null); [ "${t:-0}" -gt "$MAX_LOG" ] && : > "$LOG"
            if [ "$(salud)" -lt 9 ]; then malas=$((malas+1)); else malas=0; fi
            if [ "$malas" -ge 3 ]; then log "Modbus no responde: reinicio"; break; fi
        done
        parar_plc
        salidas_apagar
        # un programa de alumno que muere en menos de 10 s se descarta: vuelve el de fabrica
        if [ "$BIN" = "$PLC_USR" ] && [ $(( $(cut -d. -f1 /proc/uptime) - t0 )) -lt 10 ]; then
            rm -f "$PLC_USR"; log "el programa cargado fallo al arrancar: vuelve el de fabrica"
        fi
        log "OpenPLC se reinicia"
        sleep 2
    done
}

red() {
    # En esta placa eth0 arranca con MAC 00:00:00:00:00:00: se fija la de la etiqueta.
    if [ -f /etc/plc/mac ]; then
        ifconfig eth0 down
        ifconfig eth0 hw ether "$(cat /etc/plc/mac)"
    fi
    ifconfig eth0 up
    sleep 3
    udhcpc -i eth0 -n -q -t 5 -T 3 > /dev/null 2>&1
    log "red lista: $(ifconfig eth0 | sed -n 's/.*inet addr:\([0-9.]*\).*/\1/p')"
}

# Receptor de programas del alumno (sin telnet): puerto 9100 recibe el ejecutable, 9101 lo aplica.
# Escucha en 0.0.0.0, asi que no hace falta esperar a que la red tenga IP.
receptor() {
    tcpsvd 0.0.0.0 9100 /opt/plc/rx_recibir.sh &
    tcpsvd 0.0.0.0 9101 /opt/plc/rx_aplicar.sh &
}

case "$1" in
    start)
        ( supervisar ) > /dev/null 2>&1 < /dev/null &      # no demorar el resto del arranque
        echo $! > "$PIDSUP"
        ;;
    stop)
        [ -f "$PIDSUP" ] && kill $(cat "$PIDSUP") 2>/dev/null
        killall tcpsvd 2>/dev/null
        ( echo 'quit()'; sleep 2 ) | timeout -t 4 nc 127.0.0.1 43628 > /dev/null 2>&1
        salidas_apagar
        ;;
    *)
        echo "uso: $0 {start|stop}"; exit 1 ;;
esac
exit 0
"""
RX1 = '#!/bin/sh\n# Lo ejecuta tcpsvd por cada conexion al 9100: guarda lo recibido (el ejecutable) en RAM.\ncat > /tmp/openplc.new\n'
RX2 = '#!/bin/sh\n# Lo ejecuta tcpsvd por cada conexion al 9101. Recibe una linea: "aplicar <md5>".\n# Verifica la suma, reemplaza el programa y detiene a OpenPLC con quit(): el supervisor lo relanza con el nuevo.\nread orden md5\nif [ "$orden" != "aplicar" ] || [ ! -s /tmp/openplc.new ]; then echo "ERROR: orden o programa ausente"; exit 0; fi\nreal=$(md5sum /tmp/openplc.new | cut -d\' \' -f1)\nif [ "$real" != "$md5" ]; then rm -f /tmp/openplc.new; echo "ERROR: md5 distinto ($real)"; exit 0; fi\nchmod +x /tmp/openplc.new\nmv -f /tmp/openplc.new /tmp/openplc_user\necho "OK"\n# parada ordenada por el puerto de control de OpenPLC (como el cargador por telnet); el supervisor lo relanza\n( echo "quit()"; sleep 2 ) | timeout -t 4 nc 127.0.0.1 43628 > /dev/null 2>&1\n'
openplc = open(OPENPLC, "rb").read()
nuevos = [
    C.nueva_entrada("opt/plc", b"", 0o040755),
    C.nueva_entrada("opt/plc/openplc", openplc, 0o100755),
    C.nueva_entrada("etc/plc", b"", 0o040755),
    C.nueva_entrada("etc/plc/mac", (MAC + "\n").encode(), 0o100644),
    C.nueva_entrada("opt/plc/rx_recibir.sh", RX1.encode(), 0o100755),
    C.nueva_entrada("opt/plc/rx_aplicar.sh", RX2.encode(), 0o100755),
    C.nueva_entrada("etc/init.d/plc.sh", PLC_SH.encode(), 0o100755),
    C.nueva_entrada("etc/rc5.d/S85plc.sh", b"../init.d/plc.sh", 0o120777),
    C.nueva_entrada("etc/rc6.d/K15plc.sh", b"../init.d/plc.sh", 0o120777),   # reboot: parada ordenada (quit()) antes del SIGTERM generico
    C.nueva_entrada("etc/rc0.d/K15plc.sh", b"../init.d/plc.sh", 0o120777),   # apagado
]
ents_nuevo = ents + nuevos
cpio_nuevo = C.escribir(ents_nuevo)

# ---------------------------------------------------------------- 3. recomprimir con los mismos parametros que uso Intel
lzma_nuevo = subprocess.run(["xz", "--format=lzma", "--lzma1=preset=6,dict=16MiB", "-c"], input=cpio_nuevo, capture_output=True, check=True).stdout
margen = len(lzma_orig) - len(lzma_nuevo)
print("initramfs original  : %9d bytes comprimidos (%d sin comprimir)" % (len(lzma_orig), len(cpio)))
print("initramfs modificado: %9d bytes comprimidos (%d sin comprimir)" % (len(lzma_nuevo), len(cpio_nuevo)))
print("quitados %d archivos de Bluetooth; agregados %d bytes de OpenPLC; margen libre: %d bytes" % (n_quitados, len(openplc), margen))
if margen < 4096:
    print("ERROR: no queda margen suficiente (hace falta quitar mas)"); sys.exit(1)

# relleno con ceros hasta el tamano original (el kernel ignora ceros tras el fin del flujo lzma)
cuerpo = lzma_nuevo + b"\x00" * margen
assert len(cuerpo) == len(lzma_orig)
activo_nuevo = firma.firmar(cuerpo, 7, clave)
assert len(activo_nuevo) == TAM_ACTIVO and firma.verificar(activo_nuevo)[0]

# ---------------------------------------------------------------- 4. reinsertar en la imagen y en la capsula
bin_nuevo = BIN_ORIG[:OFF_BIN] + activo_nuevo + BIN_ORIG[OFF_BIN + TAM_ACTIVO:]
cap_cuerpo = CAP_ORIG[1024:OFF_CAP] + activo_nuevo + CAP_ORIG[OFF_CAP + TAM_ACTIVO:]
hdr = firma.leer_encabezado(CAP_ORIG)
cap_nuevo = firma.firmar(cap_cuerpo, hdr["svn_index"], clave, svn=hdr["svn"])
assert len(bin_nuevo) == len(BIN_ORIG) and len(cap_nuevo) == len(CAP_ORIG)
ok_cap = firma.verificar(cap_nuevo)
assert ok_cap[0], ok_cap

open(os.path.join(SALIDA, "Flash-PLC.bin"), "wb").write(bin_nuevo)
open(os.path.join(SALIDA, "Flash-PLC.cap"), "wb").write(cap_nuevo)
open(os.path.join(SALIDA, "ramdisk_nuevo.lzma"), "wb").write(cuerpo)
open(os.path.join(SALIDA, "ramdisk_nuevo.cpio"), "wb").write(cpio_nuevo)
print("escritos: Flash-PLC.bin (%d) y Flash-PLC.cap (%d) en %s" % (len(bin_nuevo), len(cap_nuevo), SALIDA))
dif = [i for i in range(len(BIN_ORIG)) if BIN_ORIG[i] != bin_nuevo[i]]
print("bytes distintos respecto de la imagen de Intel: %d, todos dentro de 0x%x-0x%x" % (len(dif), dif[0], dif[-1]))
print("md5 .bin:", hashlib.md5(bin_nuevo).hexdigest(), "| md5 .cap:", hashlib.md5(cap_nuevo).hexdigest())
