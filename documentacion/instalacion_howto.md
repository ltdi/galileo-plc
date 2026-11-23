# How-to: instalación del PLC didáctico con Galileo

> Todo el material externo (de dónde sale, versión y suma de verificación) está en [`FUENTES.md`](../FUENTES.md). `instalacion/obtener_dependencias.sh` lo descarga.

Guía para dejar listo un **PC de alumno (Ubuntu 22.04, x86-64)** y para **preparar una placa nueva**. Las órdenes están probadas donde se indica; lo no verificado está marcado como **[sin verificar]**.

```
 PC del alumno                                         Placa Galileo (imagen PLC en la flash)
 ┌──────────────────────────────────────────┐          ┌──────────────────────────┐
 │ OpenPLC Editor 4.3.5 (AppImage)          │          │ OpenPLC + supervisor     │
 │    ↕ HTTPS/UDP en 127.0.0.x (solo local) │   red    │ Modbus TCP   502         │
 │ Puente (puente_local.py)  ──────────────────────────→ │ receptor     9100/9101   │
 │   · busca placas  · compila (matiec +    │  local   └──────────────────────────┘
 │     compilador cruzado)  · carga         │
 │ Panel en vivo (Firefox) http://127.0.0.1:8088
 └──────────────────────────────────────────┘
```

No hay servidor aparte: todo corre en el PC del alumno. Se instalan en cada PC: el editor (~190 MB), el compilador cruzado (~190 MB), la estación de compilación (11 MB) y los scripts (<1 MB).

---

## A. Preparar un PC de alumno

### 1. Requisitos (sin sudo salvo el paso marcado)
| Qué | Cómo comprobarlo | Si falta |
|---|---|---|
| Ubuntu 22.04 x86-64 | `lsb_release -d`, `uname -m` | otras versiones: **[sin verificar]** |
| Python 3.8 o mayor | `python3 -V` | `sudo apt install python3` |
| `openssl` | `openssl version` | `sudo apt install openssl` |
| `libfuse2` (para el AppImage) | `ldconfig -p \| grep libfuse.so.2` | `sudo apt install libfuse2` |
| Firefox (ventana del panel; opcional) | `firefox --version` | el lanzador acepta `--sin-panel` |
| Red cableada o WiFi en la **misma red local** que las placas | `ip -4 addr` | el puente no cruza routers ni VLANs |

### 2. Copiar el proyecto
Copiar la carpeta del proyecto (la que contiene `lanzar_plc.py`, `scripts_openplc/`, `instalacion/`, `ejemplos_alumno/`, `openplc_galileo_8e4s/`) a `~/galileo-plc` (cualquier ruta sirve; los scripts calculan su ubicación).

### 3. OpenPLC Editor 4.3.5
Descargar el **AppImage de la versión 4.3.5** de la página de versiones (Releases) del repositorio `Autonomy-Logic/openplc-editor` y dejarlo en `~/Descargas` (el lanzador busca `OpenPLC*Editor*.AppImage` en `~/Descargas`, `~/Downloads`, `~/Escritorio`, `~/Applications`, `/opt`; con otra ruta: `--editor RUTA` o variable `OPENPLC_EDITOR`).
- SHA-256 del archivo probado: `cced27c878bdf992363cff4048a13a877c2f9adcb0676ca73ad54aabb357b4f4`.
- Usar **exactamente la 4.3.5**: el puente imita el protocolo de esa versión; otras versiones **[sin verificar]**.
- `chmod +x OpenPLC.Editor-4.3.5.AppImage`. El nombre de archivo exacto de la descarga **[sin verificar]** (el probado se llama así).

### 4. Compilador cruzado y comprobación (un solo comando)
```bash
cd ~/galileo-plc
bash instalacion/preparar_equipo.sh
```
Hace: revisa los requisitos; descarga el SDK de Intel (56 MB, del espejo de archive.org, y verifica su SHA-256 `935ccad3…827b72`) y lo instala **reubicado en tu HOME** (`~/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0/i586`, ~190 MB; sin sudo; ~1 minuto); compila el portón de ejemplo como prueba; y crea el acceso directo **«PLC Galileo (OpenPLC + puente)»** en el menú de aplicaciones.
- Sin Internet: `bash instalacion/preparar_equipo.sh /ruta/galileo-toolchain-20150316-linux64.tar.bz2` (el archivo se puede llevar en un USB).
- Probado: instalación desde cero con un `HOME` temporal y compilación posterior correcta. La descarga automática desde archive.org **[sin verificar]** en esta máquina (se usó el archivo ya descargado); la dirección viene del índice de paquetes de Intel.
- El SDK trae rutas absolutas: **no se puede copiar a otro usuario**, hay que reinstalarlo en cada HOME (por eso existe el script).

### 5. Estación de compilación (`openplc_galileo_8e4s/`)
Ya viene en el proyecto (11 MB). Contiene `iec2c` (matiec, compilado para el PC), `glue_generator`, la biblioteca IEC y el núcleo de OpenPLC ya compilado para la Galileo. Si hay que **reconstruirla** (se hace una vez, en un PC; luego se copia la carpeta):
```bash
bash instalacion/obtener_dependencias.sh --sin-editor      # deja descargas/openplc_v3 en el commit b5d41356 (abril de 2026), entre otras cosas
# matiec: construir utils/matiec_src/iec2c con las herramientas del propio OpenPLC (necesita gcc, g++, make, bison, flex, autoconf)
bash scripts_openplc/construir.sh "$PWD/descargas/openplc_v3" "$PWD/openplc_galileo_8e4s" "$PWD/ejemplos_alumno/programa_fabrica_seguro.st"   # rutas ABSOLUTAS; el último argumento es el programa de fábrica
```
Reconstruir desde cero (compilar matiec incluido) **[sin verificar]** en esta máquina: ya estaba compilado.

### 6. Primer uso
```bash
python3 ~/galileo-plc/lanzar_plc.py          # o el acceso directo del menú
```
Abre (a) el puente, (b) una ventana pequeña de Firefox con el panel (`http://127.0.0.1:8088`) y (c) el editor. Al cerrar el editor, el puente y el panel se detienen solos.

En el editor:
1. Copiar una plantilla de `ejemplos_alumno/plantilla_editor/` fuera de esa carpeta y abrirla (*Abrir proyecto* → la carpeta entera, la que contiene `project.json`).
2. Pantalla del dispositivo → **Search** → elegir `Galileo-XXXX` (las 4 últimas cifras de la MAC de la placa) → **OK**. Usuario: cualquiera; **contraseña: `plc`** (relleno que pide el editor; no es autenticación real).
3. Barra lateral → icono de descarga (**Build options**) → **Build and upload**. En unos 15 s dice «PLC started».
4. Observar y forzar entradas y salidas en el panel.

### 7. Lista de comprobación
- [ ] `bash instalacion/preparar_equipo.sh` termina sin «FALTA» y compila el portón.
- [ ] Con la placa encendida y en la misma red, el lanzador la lista en Search y en el panel.
- [ ] Build and upload → «PLC started»; las salidas responden en el panel.
- [ ] Al cerrar el editor: `pgrep -fa puente_local` no muestra nada.

---

## B. Preparar una placa nueva (imagen del PLC en la flash)

Cada placa lleva su propia **MAC dentro de la imagen** (la de la etiqueta), por eso hay una imagen por placa. **Riesgo:** un corte de energía o una imagen defectuosa durante el flasheo puede inutilizar la placa; no se tiene aún el archivo `FVMAIN.fv` ni consola serie para recuperarla del firmware (ver la guía de operación).

1. **Material** (en el PC de preparación; no va a los PC de alumno): `bash instalacion/obtener_dependencias.sh --sin-editor` descarga y verifica las imágenes oficiales de Intel (firmware 1.1.1: `Flash-missingPDAT-Release-1.1.1.bin` y `.cap`), la guía de la placa, `intel/Galileo-Runtime` (clave de firma por defecto `sysimage/config/key.pem`, la misma de las imágenes originales) y OpenPLC v3, cada uno en la versión y con la suma de verificación de `FUENTES.md`.
2. **Construir la imagen** con la MAC de la etiqueta de *esa* placa:
```bash
python3 -I scripts_imagen/construir_imagen.py descargas/flash_1.1.1 descargas/galileo_runtime/sysimage/config/key.pem \
        openplc_galileo_8e4s/openplc 98:4F:EE:00:FA:94 imagen_trabajo/salida     # ← MAC de la placa
python3 -I scripts_imagen/firma.py verificar imagen_trabajo/salida/Flash-PLC.cap
```
3. **Flashear** (sin Arduino IDE): seguir `documentacion/guia_operacion.md`, sección 4 (ELF de rescate por USB → `modprobe efi_capsule_update` → enviar el `.cap` → **detener OpenPLC** → enviar la cápsula → `reboot`; **no cortar la alimentación en los ~150 s siguientes**).
4. Tras el reinicio la placa debe responder en la red con los puertos 502, 9100 y 9101 abiertos y aparecer en el panel.

---

## C. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| Search no encuentra la placa | La placa no responde (¿encendida, cable, misma red?). `ping IP_placa`. El puente escanea las redes privadas del PC cada 15 s: revisar `~/.config/galileo-plc/puente.log`. Si cuelga, desconectar y reconectar la alimentación (el botón Reboot puede no bastar). |
| Search encuentra una placa de más/de menos | Placas virtuales de prueba (`placas_virtuales`), u otro puente en marcha en el mismo PC (candado en `~/.config/galileo-plc/puente.lock`). |
| «Failed to stop PLC: not connected to the target» | El puente debe informar `STOPPED` (lo hace por defecto). Reiniciar con el lanzador. |
| «Compilation failed» al subir | El error de matiec con línea y columna sale en el registro del editor. |
| El panel dice «sin respuesta del puente» | El lanzador no está en marcha o el puente murió: relanzar. Registro: `~/.config/galileo-plc/puente.log`. |
| `libfuse.so.2 not found` al abrir el editor | `sudo apt install libfuse2`. |
| Una salida oscila | Realimentación de una salida hacia la entrada que la gobierna (p. ej., relé de pruebas en D9 con su contacto en D3). El relé de pruebas va en D8. |

## D. Actualizar y desinstalar
- **Actualizar scripts:** reemplazar la carpeta del proyecto (conserva `~/.config/galileo-plc/`).
- **Desinstalar:** borrar la carpeta del proyecto, `~/.config/galileo-plc`, `~/.local/share/applications/galileo-plc.desktop`, `~/.arduino15/packages/maxgerhardt` y `~/snap/firefox/common/galileo-panel`.
