#!/usr/bin/env python3
"""Lanza OpenPLC Editor junto con el puente a la Galileo, y detiene el puente al cerrar el editor.

    python3 lanzar_plc.py                    # busca el editor (AppImage) y lo abre
    python3 lanzar_plc.py --editor RUTA      # editor en otra ruta (o variable OPENPLC_EDITOR)
    python3 lanzar_plc.py --redes 10.0.5.0/24   # redes donde buscar placas (por defecto: las del PC)
    python3 lanzar_plc.py --sin-panel        # no abrir la ventana del panel en vivo (Firefox)

Dentro del editor: abrir el proyecto plantilla, Search -> elegir «Galileo-XXXX» -> Build options -> Build and upload.
Usuario: cualquiera. Contrasena: plc (relleno que pide el editor; no es autenticacion real)."""
import os, sys, glob, time, signal, shutil, subprocess, fcntl

AQUI = os.path.dirname(os.path.abspath(__file__))
PUENTE = os.path.join(AQUI, "scripts_openplc", "puente_local.py")
CACHE = os.path.join(os.path.expanduser("~"), ".config", "galileo-plc")
args = sys.argv[1:]
def opcion(nombre, defecto=None):
    return args[args.index(nombre) + 1] if nombre in args else defecto

def buscar_editor():
    p = opcion("--editor") or os.environ.get("OPENPLC_EDITOR")
    if p: return p
    for d in ("~/Descargas", "~/Downloads", "~/Escritorio", "~/Desktop", "~/Applications", "~/.local/bin", "/opt"):
        c = sorted(glob.glob(os.path.join(os.path.expanduser(d), "OpenPLC*Editor*.AppImage")))
        if c: return c[-1]
    return shutil.which("openplc-editor")

URL_PANEL = "http://127.0.0.1:8088"

def abrir_panel():
    """Ventana pequena de Firefox con el panel en vivo, en un perfil propio (instancia aparte: respeta el tamano y se
    puede cerrar sin tocar el Firefox del usuario). Devuelve el proceso, o None si no hay Firefox."""
    ff = shutil.which("firefox")
    if not ff: return None
    perfil = os.path.expanduser("~/snap/firefox/common/galileo-panel") if os.path.isdir(os.path.expanduser("~/snap/firefox")) \
        else os.path.join(CACHE, "perfil-firefox")
    os.makedirs(perfil, exist_ok=True)
    return subprocess.Popen([ff, "--no-remote", "--profile", perfil, "--new-window", URL_PANEL, "-width", "600", "-height", "760"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

def main():
    editor = buscar_editor()
    if not editor and "--sin-editor" not in args:
        print("No encuentro OpenPLC Editor. Indicalo con --editor RUTA o con la variable OPENPLC_EDITOR."); return 2
    os.makedirs(CACHE, exist_ok=True)
    cierre = open(os.path.join(CACHE, "puente.lock"), "w")
    try: fcntl.flock(cierre, fcntl.LOCK_EX | fcntl.LOCK_NB); puente_propio = True
    except OSError: puente_propio = False
    puente = None
    if puente_propio:
        cmd = [sys.executable, PUENTE] + (["--redes", opcion("--redes")] if opcion("--redes") else [])
        registro = open(os.path.join(CACHE, "puente.log"), "a")
        puente = subprocess.Popen(cmd, stdout=registro, stderr=registro, start_new_session=True)
        time.sleep(1.0)
        if puente.poll() is not None:
            print("El puente no pudo arrancar; mira %s" % os.path.join(CACHE, "puente.log")); return 3
        print("Puente a la Galileo en marcha (pid %d). Registro: %s" % (puente.pid, os.path.join(CACHE, "puente.log")))
        print("Panel en vivo (variables, entradas y salidas): http://127.0.0.1:8088")
    else:
        print("Ya hay un puente en marcha en este PC: se reutiliza.")
    panel = None
    if puente_propio and "--sin-panel" not in args:
        time.sleep(0.5)
        panel = abrir_panel()
    def detener(*_):
        if panel and panel.poll() is None:
            try: os.killpg(panel.pid, signal.SIGTERM)
            except ProcessLookupError: pass
        if puente and puente.poll() is None:
            try: os.killpg(puente.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: puente.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(puente.pid, signal.SIGKILL)
            print("Puente detenido.")
    signal.signal(signal.SIGTERM, lambda *a: (detener(), sys.exit(0)))
    try:
        if "--sin-editor" in args:
            print("(sin editor) Ctrl+C para detener."); signal.pause()
        else:
            if not os.access(editor, os.X_OK) and editor.endswith(".AppImage"): os.chmod(editor, 0o755)
            print("Abriendo %s ... el puente se detendra al cerrar el editor." % editor)
            subprocess.call(editor.split() if " " in editor and not os.path.exists(editor) else [editor])
    except KeyboardInterrupt:
        pass
    finally:
        detener()
    return 0

sys.exit(main())
