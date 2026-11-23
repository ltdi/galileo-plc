# galileo-plc: PLC didáctico con Intel Galileo Gen 1 (LTDI – UTN)

Una Galileo Gen 1 (FAB-D) que arranca sola como un PLC: imagen propia en la flash, OpenPLC, 8 entradas / 4 salidas, Modbus TCP y carga de programas por red. Sin microSD. Estado al **23/11/2026**.

## Documentación vigente (`documentacion/`)

| Archivo | Contenido |
|---|---|
| `Informe final - PLC didactico Galileo.docx` | qué se construyó, pines, flujo del alumno, pruebas, problemas, riesgos y pasos siguientes |
| `guia_profesores.md` (y `Guia para profesores - PLC Galileo.docx`) | **para docentes** de máquinas e instalaciones eléctricas: qué hace el PLC, límites, prácticos y seguridad |
| `propuestas_de_mejora.md` | **propuestas de mejora**: contacto maestro, entradas analógicas, display, Wi-Fi y otras |
| `propuesta_contacto_maestro.md` | propuesta de hardware: contacto maestro (con vigilancia) que deshabilita las bobinas de los relés |
| `instalacion_howto.md` | **cómo instalar**: PC de alumno (Ubuntu) y placa nueva |
| `propuesta_repositorio.md` | qué es `ltdi/galileo` y propuesta de repositorio `galileo-plc` |
| `guia_operacion.md` | cómo usar, cargar programas, reconstruir y flashear la imagen, rescatar una placa |
| `mapa_pines_galileo_plc.md` | pines, GPIO de Linux, puertos y máscaras del Cypress, mux, registros, direcciones Modbus |
| `registro_pruebas.md` | bitácora cronológica de todas las pruebas |

## Carpetas

| Carpeta | Contenido |
|---|---|
| `instalacion/` | `preparar_equipo.sh` (un solo comando para un PC de alumno) e `instalar_compilador.sh` |
| `datasheets/` | copias de consulta de los PDF de Intel y Cypress usados (esquemático, hojas de datos, guía de la placa) |
| `scripts_imagen/` | construcción y firma de la imagen (`construir_imagen.py`, `firma.py`, `cpio_newc.py`) |
| `lanzar_plc.py` | lanzador: abre el puente local, una ventana pequeña de Firefox con el panel en vivo y el editor; todo se detiene al cerrar el editor |
| `scripts_openplc/` | puente local (`puente_local.py`), panel en vivo (`panel_vivo.py`), placas virtuales de prueba (`placa_virtual.py`) y servidor central alternativo (`servidor_runtime.py`, `placas.json`, `configurar_alias.sh`), adaptador de proyectos de OpenPLC Editor (`proyecto_editor_a_st.py`), capa de hardware (`hardware_layer_galileo_8e4s.cpp`), compilador del alumno (`plc.py`), cargador (`plc_cargar.py`), servidor web (`servidor_plc.py`), pruebas (`pruebas_placa/`, `prueba_larga.py`) |
| `openplc_galileo_8e4s/` | estación de compilación ya construida (núcleo de OpenPLC, matiec, glue) |
| `imagen_trabajo/salida/` | `Flash-PLC.bin` y `Flash-PLC.cap` (imagen v4, la flasheada) |
| `ejemplos_alumno/` | programas de ejemplo en texto estructurado (`programa_fabrica_seguro`, `motor_marcha_paro`, `inversion_giro`, `estrella_triangulo`, `ascensor3`, `porton`, `intermitente`, `prueba_es`, `con_error`) |
| `telnet_elf/` | ELF de rescate de 6 KB (red + telnet 30 min) que se sube por USB |
| `scripts_doc/` | generador del informe Word |
| `descargas/` | firmware 1.1.1 de Intel, BSP, guías, fuentes de OpenPLC (185 MB) |
| `archivo/` | todo lo anterior a esta versión: informes previos, prototipos de Arduino, mediciones iniciales, estación de un relé, código obsoleto |

## Lo esencial

- **Entradas:** D2 D3 D4 D5 D6 D7 D12 D13 → `%IX0.0…0.7` (activas a nivel bajo). **Salidas:** D8 D9 D10 D11 → `%QX0.0…0.3` (activas a nivel alto).
- **Cargar un programa:** con `python3 lanzar_plc.py` (abre OpenPLC Editor 4.3.5 y un puente local; Search + Build and upload), o por línea de comandos: `python3 scripts_openplc/plc.py programa.st --ip <IP de la placa>`.
- **Nunca** enviar señales a OpenPLC ni reiniciar la placa sin detenerlo antes (ver `guia_operacion.md`).
- Entradas y salidas probadas en la placa. Sin verificar: ascensor con botonera física y polaridad de la placa de relés; servicio HTTP del servidor web; recuperación si el firmware no arranca (falta `FVMAIN.fv`).

## Qué no trae este repositorio

Para mantenerlo liviano (≈600 KB) **no incluye** material de terceros ni archivos generados, que se obtienen aparte:

| Carpeta (ignorada) | Qué es | Cómo se consigue |
|---|---|---|
| `descargas/` | firmware de Intel (imágenes 1.1.1, `intel/Galileo-Runtime`), fuentes de OpenPLC v3 (`thiagoralves/OpenPLC_v3`, probado con el commit `b5d41356`) | ver `documentacion/instalacion_howto.md` y `documentacion/propuesta_repositorio.md` |
| `openplc_galileo_8e4s/` | estación de compilación (núcleo de OpenPLC para la Galileo, matiec) | se reconstruye con `scripts_openplc/construir.sh`, o se copia de un PC ya preparado |
| `imagen_trabajo/` | imágenes `Flash-PLC.bin/.cap` generadas (una por placa, con su MAC) | `scripts_imagen/construir_imagen.py` |
| `archivo/` | material histórico (prototipos, mediciones iniciales, informes anteriores) | queda en el equipo de origen |

`scripts_openplc/placas.json` (servidor central, opcional) se crea copiando `placas.ejemplo.json`.
Todo lo anterior, con su origen, versión y suma de verificación, está en [`FUENTES.md`](FUENTES.md); `instalacion/obtener_dependencias.sh` lo descarga y verifica.
