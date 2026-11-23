#!/bin/bash
# Prepara un PC Ubuntu (22.04, x86-64) para programar la Galileo PLC con OpenPLC Editor. Sin sudo.
#   bash instalacion/preparar_equipo.sh [archivo_sdk.tar.bz2]
# Hace: comprueba requisitos, instala el compilador cruzado, prueba una compilacion y crea el acceso directo del menú.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
falta=0
ok()  { echo "  [ok] $1"; }
mal() { echo "  [FALTA] $1"; falta=1; }
echo "1) Requisitos"
command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info<(3,8))' && ok "python3 $(python3 -V | cut -d' ' -f2)" || mal "python3 3.8 o mayor"
command -v openssl >/dev/null && ok "openssl" || mal "openssl (sudo apt install openssl)"
ldconfig -p 2>/dev/null | grep -q "libfuse.so.2" && ok "libfuse2 (para el AppImage del editor)" || mal "libfuse2 (sudo apt install libfuse2)"
command -v firefox >/dev/null && ok "firefox (ventana del panel)" || echo "  [aviso] sin firefox: el lanzador usará --sin-panel o abrirá la dirección a mano"
ed=$(ls ~/Descargas/OpenPLC*Editor*.AppImage ~/Downloads/OpenPLC*Editor*.AppImage ~/Applications/OpenPLC*Editor*.AppImage 2>/dev/null | tail -1)
[ -n "$ed" ] && ok "OpenPLC Editor: $ed" || mal "OpenPLC Editor 4.3.5 (AppImage) en ~/Descargas (ver documentacion/instalacion_howto.md)"
[ -x "$RAIZ/openplc_galileo_8e4s/openplc" ] && ok "estación de compilación (openplc_galileo_8e4s)" || mal "estación openplc_galileo_8e4s (ver howto, sección 4)"
[ $falta = 0 ] || { echo "Resuelva lo marcado como [FALTA] y repita."; exit 1; }
echo "2) Compilador cruzado"
bash "$RAIZ/instalacion/instalar_compilador.sh" "$@"
echo "3) Prueba de compilación (portón de ejemplo)"
python3 -I "$RAIZ/scripts_openplc/plc.py" "$RAIZ/ejemplos_alumno/porton.st" --solo-compilar | tail -2
echo "4) Acceso directo"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/galileo-plc.desktop <<D
[Desktop Entry]
Type=Application
Name=PLC Galileo (OpenPLC + puente)
Comment=Abre OpenPLC Editor con el puente a la Galileo y el panel en vivo
Exec=python3 $RAIZ/lanzar_plc.py
Terminal=false
Categories=Development;
D
echo "Listo. Abra «PLC Galileo» desde el menú de aplicaciones, o ejecute:  python3 $RAIZ/lanzar_plc.py"
