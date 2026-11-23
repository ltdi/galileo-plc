#!/bin/bash
# Instala el compilador cruzado de la Galileo (SDK de Intel, 2015) para el usuario actual, sin sudo.
#   instalar_compilador.sh [archivo.tar.bz2]
# Sin argumento descarga el SDK (56 MB) del espejo de archive.org y verifica su SHA-256.
# Deja el compilador en  ~/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0/i586
# (la ruta que esperan plc.py y construir.sh). El SDK trae rutas absolutas: hay que «reubicarlo» en la carpeta final;
# lo hacen install_script_py3.sh y relocate_sdk_py3.py (versiones de los scripts de Intel adaptadas a Python 3).
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
URL="https://web.archive.org/web/20191119130210if_/https://downloadmirror.intel.com/24806/eng/galileo-toolchain-linux64-1.6.2-1.0.tar.bz2"
SHA="935ccad3eaaec34f5de76eceb0f0ecd1372bdab0b7dc8f4241e8260c6f827b72"
DEST="$HOME/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0"
if [ -f "$DEST/i586/version-i586-poky-linux-uclibc" ] && [ -f "$DEST/i586/prev_install" ]; then echo "Ya instalado en $DEST"; exit 0; fi
ARCH="$1"
if [ -z "$ARCH" ]; then ARCH="$(mktemp -d)/galileo-toolchain.tar.bz2"; echo "Descargando el SDK..."; curl -L --fail -o "$ARCH" "$URL"; fi
echo "$SHA  $ARCH" | sha256sum -c -
mkdir -p "$DEST"; tar xjf "$ARCH" -C "$DEST"
cp "$AQUI/install_script_py3.sh" "$DEST/i586/install_script.sh"
cp "$AQUI/relocate_sdk_py3.py" "$DEST/i586/relocate_sdk.py"
chmod +x "$DEST/i586/install_script.sh" "$DEST/i586/relocate_sdk.py"
( cd "$DEST/i586" && bash ./install_script.sh -y -d "$DEST/i586" )
echo "Compilador instalado en $DEST/i586"
