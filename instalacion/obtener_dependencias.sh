#!/bin/bash
# Descarga y verifica el material de terceros que NO está en este repositorio (ver FUENTES.md).
#   bash instalacion/obtener_dependencias.sh [--sin-editor]
# Deja en la raíz del proyecto:  descargas/openplc_v3, descargas/galileo_runtime, descargas/flash_1.1.1, descargas/guia_placa
# y (salvo --sin-editor) el AppImage del editor en ~/Descargas. El compilador cruzado lo baja instalar_compilador.sh.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; D="$RAIZ/descargas"; mkdir -p "$D"
ESPEJO="https://archive.org/download/downloadcenter.intel.com/downloadmirror.intel.com_Sept20th2019.tar/downloadmirror.intel.com"
bajar() {   # destino url sha256
  if [ -f "$1" ] && echo "$3  $1" | sha256sum -c --quiet - 2>/dev/null; then echo "  [ya está] $1"; return; fi
  mkdir -p "$(dirname "$1")"; curl -L --fail -s -o "$1" "$2"; echo "$3  $1" | sha256sum -c -
}
fijar() {   # directorio url commit : clona exactamente ese commit
  if [ -d "$1/.git" ] && [ "$(git -C "$1" rev-parse HEAD 2>/dev/null)" = "$3" ]; then echo "  [ya está] $1 @ ${3:0:8}"; return; fi
  rm -rf "$1" 2>/dev/null || true; mkdir -p "$1"; git -C "$1" init -q; git -C "$1" remote add origin "$2"
  git -C "$1" fetch -q --depth 1 origin "$3"; git -C "$1" checkout -q FETCH_HEAD; echo "  [ok] $1 @ ${3:0:8}"
}
echo "1) Imágenes y guía de Intel (espejo de archive.org del sitio downloadmirror.intel.com)"
bajar "$D/flash_1.1.1/Flash-missingPDAT-Release-1.1.1.bin" "$ESPEJO/26418/eng/Flash-missingPDAT-Release-1.1.1.bin" 3da41d38766d891fdb09dbb0d707e3c9ea0ce733e5c4e17a12c305f380491378
bajar "$D/flash_1.1.1/Flash-missingPDAT-Release-1.1.1.cap" "$ESPEJO/26418/eng/Flash-missingPDAT-Release-1.1.1.cap" efdce2e553a7071c9f1a9e3c20ab193c394ba70218b3988de102d052dbbe8b8d
bajar "$D/flash_1.1.1/CapsuleApp-1.1.1.efi"                "$ESPEJO/26418/eng/CapsuleApp-1.1.1.efi"                0e372b8bd2ed76856f1a264064cc1db6547673b8adebff4a55a1f3f80db6b51b
bajar "$D/guia_placa/Galileo_BoardUserGuide_330237_002.pdf" "$ESPEJO/23962/eng/Galileo_BoardUserGuide_330237_002.pdf" 734de295581b06d55105553d22e9306d023805093ba019798a816380393163e1
echo "2) Repositorios de GitHub, en el commit probado"
fijar "$D/galileo_runtime" https://github.com/intel/Galileo-Runtime   ee66e9a3b21f5fc68068bbe3ab59d0d8ae03a232
fijar "$D/openplc_v3"      https://github.com/thiagoralves/OpenPLC_v3 b5d41356dab4aeadca0dd7ca64ba542f870b595d
if [ "$1" != "--sin-editor" ]; then
  echo "3) OpenPLC Editor 4.3.5 (AppImage, ~188 MB)"
  bajar "$HOME/Descargas/OpenPLC.Editor-4.3.5.AppImage" "https://github.com/Autonomy-Logic/openplc-editor/releases/download/v4.3.5/OpenPLC.Editor-4.3.5.AppImage" cced27c878bdf992363cff4048a13a877c2f9adcb0676ca73ad54aabb357b4f4
  chmod +x "$HOME/Descargas/OpenPLC.Editor-4.3.5.AppImage"
fi
echo "Listo. Siguiente: bash instalacion/preparar_equipo.sh"
