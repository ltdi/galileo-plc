#!/usr/bin/env python3
"""Convierte un proyecto de OpenPLC Editor 4.x (carpeta con project.json y pous/) en un unico archivo .st
que entiende matiec (el traductor que usa plc.py): POUs de texto + CONFIGURATION Config0/Res0 con las tareas.

    python3 proyecto_editor_a_st.py <carpeta_del_proyecto> [salida.st]

Solo se admiten POUs en texto estructurado (.st). Los POUs en escalera (.ld), FBD o SFC no se convierten:
el editor los pasa a texto estructurado dentro de su propia compilacion; hay que escribirlos en ST."""
import sys, os, json, glob

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    carpeta = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(carpeta, os.path.basename(os.path.abspath(carpeta)) + ".st")
    pj = os.path.join(carpeta, "project.json")
    if not os.path.exists(pj):
        print("No encuentro project.json en %s: no es un proyecto de OpenPLC Editor 4.x" % carpeta); return 3
    proy = json.load(open(pj))
    partes = []
    no_texto = []
    for sub in ("functions", "function-blocks", "programs"):          # funciones y bloques antes que los programas
        for f in sorted(glob.glob(os.path.join(carpeta, "pous", sub, "*"))):
            if f.endswith(".st"):
                partes.append(open(f).read().strip() + "\n")
            else:
                no_texto.append(os.path.relpath(f, carpeta))
    if no_texto:
        print("AVISO: estos POUs no estan en texto estructurado y se omiten: " + ", ".join(no_texto)); 
    if not any(p.lstrip().upper().startswith("PROGRAM") for p in partes):
        print("No hay ningun PROGRAM en texto estructurado en pous/programs/."); return 4
    cfg = proy["data"]["configuration"]["resource"]
    tareas = sorted(cfg.get("tasks", []), key=lambda t: t.get("priority", 0))
    lineas = ["CONFIGURATION Config0"]
    glob_vars = cfg.get("globalVariables", [])
    if glob_vars:
        lineas.append("  VAR_GLOBAL")
        for v in glob_vars:
            tipo = v.get("type", {}); tipo = tipo.get("value", tipo) if isinstance(tipo, dict) else tipo
            loc = (" AT %s" % v["location"]) if v.get("location") else ""
            ini = (" := %s" % v["initialValue"]) if v.get("initialValue") not in (None, "") else ""
            lineas.append("    %s%s : %s%s;" % (v["name"], loc, str(tipo).upper() if str(tipo).lower() in ("bool","int","dint","real","time","word","byte") else tipo, ini))
        lineas.append("  END_VAR")
    lineas.append("  RESOURCE Res0 ON PLC")
    for t in tareas:
        extra = "INTERVAL := %s," % t["interval"] if t.get("interval") else ""
        lineas.append("    TASK %s(%sPRIORITY := %s);" % (t["name"], extra, t.get("priority", 0)))
    for i in cfg.get("instances", []):
        lineas.append("    PROGRAM %s WITH %s : %s;" % (i["name"], i["task"], i["program"]))
    lineas += ["  END_RESOURCE", "END_CONFIGURATION"]
    open(salida, "w").write("\n".join(partes) + "\n" + "\n".join(lineas) + "\n")
    print("escrito %s (%d POUs, %d tareas)" % (salida, len(partes), len(tareas))); return 0

sys.exit(main())
