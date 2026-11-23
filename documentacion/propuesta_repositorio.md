# Propuesta de repositorio para el PLC didáctico con Galileo

## Qué es el repositorio que ya existe (`utn/ltdi/galileo`)
- Clon de `https://github.com/ltdi/galileo` (rama `main`, dos commits), licencia **GPL-3.0**. Su README dice: «Proyectos para aprendizaje de la placa de desarrollo Galileo».
- Contiene `first_project/first_project.ino` (sketch de Arduino para probar el *ponchitoCIII*, la placa de pulsadores y LED del CIII) y, **sin versionar** (archivos sin seguimiento), los PDF de referencia: esquemático, hoja de datos de la Galileo y del Quark X1000, hoja del expansor CY8C9540A, libro 978-1-4302-6838-3 y la guía de Arduino. Pesa 26 MB, casi todo PDF.
- En `utn/ltdi/` hay además `RUST/` (presentaciones de un curso) y las imágenes `galileo_pinout.png`, `PLC_PLACA.png`.

Es un repositorio de **ejemplos de aprendizaje con el IDE de Arduino**. No tiene nada del sistema PLC.

## Por qué un repositorio nuevo
| | `ltdi/galileo` (existente) | Sistema PLC (nuevo) |
|---|---|---|
| Para qué | ejemplos de Arduino para alumnos | producto: imagen de flash, puente, panel, instalación |
| Quién lo usa | alumnos | administradores del laboratorio y alumnos |
| Ritmo de cambio | casi nulo | frecuente (versiones de imagen, scripts) |
| Contenido pesado | PDF de referencia | imágenes de flash, SDK, AppImage (**no deben ir a git**) |
| Dependencias de terceros | ninguna | OpenPLC v3, matiec, OpenPLC Editor, SDK de Intel (todas GPL o redistribuidas por Intel) |

Mezclarlos ensuciaría el repositorio de ejemplos y obligaría a los alumnos a clonar historial y binarios que no necesitan.

## Propuesta
- **Nombre:** `galileo-plc` (en GitHub: `ltdi/galileo-plc`).
- **Ubicación local:** `/home/dante/datos/utn/ltdi/galileo-plc/` (junto a `galileo/`).
- **Licencia:** GPL-3.0 (coherente con `ltdi/galileo` y con las piezas de terceros que se enlazan o modifican: OpenPLC v3 y matiec).
- **Rama principal:** `main`.

### Qué entra
```
galileo-plc/
├─ README.md                  índice y arranque rápido
├─ LICENSE                    GPL-3.0
├─ lanzar_plc.py              lanzador (puente + panel + editor)
├─ instalacion/               preparar_equipo.sh, instalar_compilador.sh, scripts de Intel adaptados a Python 3
├─ scripts_openplc/           puente_local.py, panel_vivo.py, servidor_runtime.py, plc.py, plc_cargar.py,
│                             capa de hardware, placa_virtual.py, monitor_plc.py, pruebas_placa/
├─ scripts_imagen/            construir_imagen.py, firma.py, cpio_newc.py
├─ telnet_elf/                fuentes (.c) del ELF de rescate
├─ ejemplos_alumno/           programas .st y plantillas del editor
├─ documentacion/             informe final (.docx), guía de operación, how-to, mapa de pines, registro de pruebas
└─ archivo/                   material histórico (opcional: ver abajo)
```

### Qué NO entra (`.gitignore`)
- `descargas/` (185 MB: firmware de Intel, repositorio `Galileo-Runtime`, OpenPLC v3): se obtiene con un script o se enlaza como submódulo.
- `imagen_trabajo/` (imágenes `.bin`/`.cap` generadas, 37 MB): van como **adjuntos de una versión (Releases)**, con su SHA-256.
- `openplc_galileo_8e4s/` (estación compilada, 11 MB): derivada de OpenPLC; se reconstruye con `construir.sh` o también va como adjunto de versión.
- `scripts_openplc/datos_servidor/` (certificado y **clave privada** del servidor central), `__pycache__/`, `*.openplc`, `*.elf`, `~/.config/galileo-plc/`.
- Imágenes y documentos ya pesados (`documentacion/*.docx` son 40–50 KB: sí entran).

### Pendiente antes de publicar
1. Un script `instalacion/obtener_dependencias.sh` que baje y verifique (SHA-256) OpenPLC v3 (`thiagoralves/OpenPLC_v3` @ `b5d41356`), `intel/Galileo-Runtime` y las imágenes 1.1.1 de Intel, y reconstruya la estación.
2. Anotar de dónde salieron exactamente `Flash-missingPDAT-Release-1.1.1.{bin,cap}` (no quedó registrado) y su SHA-256.
3. Decidir si `archivo/` (13 MB, prototipos y mediciones iniciales) se publica o queda local.
4. Revisar que ningún archivo lleve datos personales o claves.
5. Redistribuir la imagen firmada: la firma usa la clave por defecto **pública** de Intel (la misma de sus imágenes); confirmar que no hay problema de licencia al distribuir las imágenes de Intel modificadas.
