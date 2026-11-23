#!/bin/bash
# Construye el nucleo de OpenPLC v3 para la Galileo Gen1 (i586, uClibc, GCC 4.7.2).
# Uso: construir.sh <dir_fuentes_openplc> <dir_salida> <programa.st>
# No modifica lo descargado: copia lo necesario a <dir_salida>.
#   - DNP3 desactivado (dnp3_dummy.disabled), maestro Modbus y snap7 como stubs.
set -e
SRC="$1"; OUT="$2"; ST="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
T=$HOME/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0/i586
GXX=$T/sysroots/x86_64-pokysdk-linux/usr/bin/i586-poky-linux-uclibc/i586-poky-linux-uclibc-g++
SR=$T/sysroots/i586-poky-linux-uclibc
FLAGS="--sysroot=$SR -march=i586 -std=gnu++11 -fpermissive -Os"

mkdir -p "$OUT/core" "$OUT/prog"
cp -r "$SRC/webserver/core/." "$OUT/core/"
cp "$SRC/utils/matiec_src/iec2c" "$OUT/iec2c"
mkdir -p "$OUT/lib" && cp -r "$SRC/utils/matiec_src/lib/." "$OUT/lib/"
cp "$ST" "$OUT/prog/programa.st"

echo "[1/6] matiec: ST -> C"
( cd "$OUT" && ./iec2c -f -l -p -r -R -a prog/programa.st )
( cd "$OUT" && mv POUS.c POUS.h LOCATED_VARIABLES.h VARIABLES.csv Config0.c Config0.h Res0.c core/ )

echo "[2/6] glue_generator (nativo en el PC)"
g++ -o "$OUT/glue_generator" "$SRC/utils/glue_generator_src/"*.cpp
( cd "$OUT/core" && ../glue_generator )

echo "[3/6] capa de hardware y stubs"
cp "$HERE/${HW:-hardware_layer_galileo_8e4s.cpp}" "$OUT/core/hardware_layer.cpp"
cp "$SRC/utils/snap7_src/wrapper/oplc_snap7.h" "$OUT/core/"
cp "$HERE/stubs_galileo.cpp" "$OUT/core/stubs_galileo.cpp"
cat "$SRC/webserver/core/dnp3_dummy.disabled" >> "$OUT/core/stubs_galileo.cpp"

echo "[4/6] compilar programa generado (como C++, igual que compile_program.sh)"
( cd "$OUT/core" && $GXX $FLAGS -I ./lib -c Config0.c Res0.c )

echo "[5/6] compilar el nucleo"
cd "$OUT/core"
rm -f dnp3.cpp modbus_master.cpp
# GCC 4.7 no soporta thread_local (llego en 4.8): usar la extension __thread (solo en la copia)
sed -i 's/thread_local/__thread/g' *.cpp
for f in *.cpp; do
  echo "   $f"
  $GXX $FLAGS -I ./lib -c "$f"
done

echo "[6/6] enlazar"
$GXX $FLAGS --sysroot=$SR *.o -o "$OUT/openplc" -pthread -lrt -ldl
ls -l "$OUT/openplc"
