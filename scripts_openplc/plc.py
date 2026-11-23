#!/usr/bin/env python3
"""plc: del programa del alumno a la placa en marcha, en un solo comando.

    python3 plc.py programa.st                # compila y carga en la placa
    python3 plc.py programa.st --solo-compilar
    python3 plc.py programa.st --ip 10.42.0.151

Para el alumno NO hay que saber de toolchains: esta herramienta ya trae el traductor (matiec), el
compilador cruzado y el nucleo de OpenPLC ya compilado. Solo se recompila lo que depende del
programa (Config0, Res0 y glueVars), y se carga por red con verificacion.
La estacion (carpeta con iec2c, lib/, glue_generator y core/ con el nucleo compilado) la prepara el
laboratorio una sola vez con construir.sh."""
import os, sys, shutil, subprocess, tempfile, time

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTACION = os.environ.get("PLC_ESTACION", os.path.join(os.path.dirname(AQUI), "openplc_galileo_8e4s"))
T = os.path.expanduser("~/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0/i586")
GXX = T + "/sysroots/x86_64-pokysdk-linux/usr/bin/i586-poky-linux-uclibc/i586-poky-linux-uclibc-g++"
SR = T + "/sysroots/i586-poky-linux-uclibc"
FLAGS = ["--sysroot=" + SR, "-march=i586", "-std=gnu++11", "-fpermissive", "-Os"]

args = sys.argv[1:]
if not args or args[0].startswith("-"):
    print(__doc__); sys.exit(2)
st = os.path.abspath(args[0])
ip = args[args.index("--ip") + 1] if "--ip" in args else "10.42.0.151"
solo_compilar = "--solo-compilar" in args
t0 = time.time()

def paso(txt): print("[%5.1f s] %s" % (time.time() - t0, txt), flush=True)
def correr(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print((r.stdout + r.stderr)[-1500:]); paso("ERROR en: " + " ".join(cmd[:3])); sys.exit(1)
    return r

with tempfile.TemporaryDirectory(prefix="plc_") as tmp:
    nucleo = os.path.join(tmp, "core")
    shutil.copytree(os.path.join(ESTACION, "core"), nucleo)       # nucleo ya compilado (*.o)
    shutil.copytree(os.path.join(ESTACION, "lib"), os.path.join(tmp, "lib"))
    shutil.copy(os.path.join(ESTACION, "iec2c"), tmp)
    shutil.copy(os.path.join(ESTACION, "glue_generator"), tmp)
    shutil.copy(st, os.path.join(tmp, "programa.st"))
    paso("programa recibido: %s" % os.path.basename(st))

    r = subprocess.run(["./iec2c", "-f", "-l", "-p", "-r", "-R", "-a", "programa.st"], cwd=tmp, capture_output=True, text=True)
    if r.returncode != 0:
        print("El programa tiene errores de sintaxis:\n" + (r.stdout + r.stderr).strip()); sys.exit(1)
    for f in ("POUS.c", "POUS.h", "LOCATED_VARIABLES.h", "VARIABLES.csv", "Config0.c", "Config0.h", "Res0.c"):
        shutil.move(os.path.join(tmp, f), os.path.join(nucleo, f))
    paso("traducido de IEC 61131-3 a C (matiec)")

    correr(["../glue_generator"], nucleo)
    for src in ("Config0.c", "Res0.c", "glueVars.cpp"):
        correr([GXX] + FLAGS + ["-I", "./lib", "-c", src], nucleo)
    paso("compilado el programa (el nucleo de OpenPLC se reutiliza)")
    objs = sorted(f for f in os.listdir(nucleo) if f.endswith(".o"))
    exe = os.path.join(tmp, "openplc")
    correr([GXX] + FLAGS + objs + ["-o", exe, "-pthread", "-lrt", "-ldl"], nucleo)
    paso("enlazado: ejecutable de %d bytes" % os.path.getsize(exe))

    if solo_compilar:
        destino = os.path.splitext(st)[0] + ".openplc"
        shutil.copy(exe, destino)
        paso("listo (solo compilar): %s" % destino); sys.exit(0)
    r = subprocess.run([sys.executable, "-I", os.path.join(AQUI, "plc_cargar.py"), exe, "--ip", ip])
    sys.exit(r.returncode)
