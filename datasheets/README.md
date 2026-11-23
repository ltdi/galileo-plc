# Hojas de datos y documentos de referencia

Copias de consulta de los documentos técnicos de la Galileo Gen 1 que se usaron en este proyecto. Los derechos pertenecen a sus titulares (Intel, Cypress/Infineon); se incluyen **solo para que quien clone el repositorio no dependa de enlaces que cambian o bloquean las descargas automáticas**. Si un titular lo pide, se retiran. La fuente de cada uno, y la comprobación de su enlace, están en [`../FUENTES.md`](../FUENTES.md).

| Archivo | Documento | Págs. | Para qué se usó | SHA-256 |
|---|---|---|---|---|
| `galileo_esquematico_329682.pdf` | Esquemático de la Galileo (orden Intel 329682-001US) | 27 | numeración de GPIO, conmutadores (mux) de D2/D3/D10–D13, expansor, resistencias | `ab0925c3…c0681` |
| `galileo_gen1_feature_sheet.pdf` | *Galileo Feature Sheet* (hoja de datos de la placa) | 13 | pines, PWM, alimentación | `967161a9…93671c` |
| `galileo_board_user_guide_330237-002.pdf` | *Intel Galileo Board User Guide* 330237-002 | 20 | recuperación del firmware, conectores | `cb6af1bd…961be` |
| `quark_x1000_datasheet_329676.pdf` | *Intel Quark SoC X1000 Datasheet* 329676-005US | 935 | UART, GPIO, temporizador de vigilancia, reinicio | `9f3ddb32…728c` |
| `cy8c9540a_io_expander_38-12036.pdf` | Cypress *20-, 40-, and 60-Bit I/O Expander with EEPROM* (CY8C9540A), Doc. 38-12036 Rev. *A | 25 | registros del expansor: modo de salida, pull-up, PWM, puertos | `f2df476f…525cbc` |

No se incluye el libro de Apress (ISBN 978-1-4302-6838-3, 665 págs.) por tratarse de una obra comercial con derechos de autor; solo se cita en `FUENTES.md`. `Galileo Schematic.pdf` y `arduino_galileo_e000037_1.pdf` de `utn/ltdi/galileo` son el mismo archivo y aquí figura una sola vez.
