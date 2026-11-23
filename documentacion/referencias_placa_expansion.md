# Referencias para la placa de expansión (8 entradas aisladas, 4 relés)

Revisión de proyectos abiertos que sirven de base o de inspiración para diseñar la placa de expansión en KiCad (23/11/2026). Se **abrieron y leyeron** los archivos de cada repositorio; el circuito de `fastLOGIC` se leyó de su lista de materiales y esquema (no se simuló). Nada de esto se probó con la Galileo.

## 1. Lo que necesitamos
| Requisito | Detalle |
|---|---|
| Formato | shield con la huella del Arduino Uno R3 (la Galileo la respeta) |
| Entradas | 8, aisladas, de campo (5–24 V); el PLC las lee **activas a nivel bajo** (pin a masa = activo) |
| Salidas | 4 relés, uno por salida, **contactos independientes** (NA/NC/común por relé) |
| Lógica | 3,3 o 5 V según IOREF; sin integrados I2C (ver §4) |
| Seguridad | alimentación de las bobinas a través del contacto maestro; fusible de campo |
| Fabricación | KiCad, componentes con código de catálogo para pedirla ensamblada |

## 2. Comparación
| Proyecto | Licencia | Formato de diseño | Entradas | Salidas | Qué rescatamos |
|---|---|---|---|---|---|
| [Neumi/fastLOGIC](https://github.com/Neumi/fastLOGIC) (v001) | MIT | **KiCad** (`.kicad_sch/.kicad_pcb`) + BOM con códigos LCSC | 2 con optoacoplador EL817, disparo ≈9,5 V | 2 relés SRD (inversor), 10 A / 30 V | **Mejor base técnica** (ver §3). ATmega328P, se programa «como un Uno» |
| fastLOGIC v002 | MIT | KiCad | idem, con STM32F407 + Ethernet | 3 relés | solo como ejemplo de organización; no aplica el micro |
| [ElPercha/PLsi](https://github.com/ElPercha/PLsi) v0 | MIT | EasyEDA y Altium (KiCad importa Altium), PDF, Gerber, BOM | 8 con PC817, **un solo común**, 5–26 V | 6 relés SRD-05VDC con ULN2003 | arquitectura: **0 V del procesador aislado del campo**, fusibles externos, manual de 96 páginas |
| Shield de 8 entradas aisladas (OSHWA TH000007, PCBWay) | **CC BY-NC-SA** | PNG del esquema y BOM; no hay KiCad | 8 con EL357N, 3–32 V, diodo de polaridad | — | ideas: diodo contra polaridad inversa y divisor de resistencias; **no copiar archivos** (no comercial) |
| [Alarm-Siren/arduino-kicad-library](https://github.com/Alarm-Siren/arduino-kicad-library) | CC BY-SA 4.0 con excepción para las placas | KiCad 6+ | — | — | **huella del Uno R3**; el contorno no viene en `Edge.Cuts`, hay que trazarlo |
| CindyPotvin/OysterControl | **sin licencia** | KiCad (formato antiguo) | — | — | descartado: sin licencia no se puede reutilizar |
| dmogn/plc_controller_mega32l | MIT | KiCad 5 | — | — | descartado: alfa, otro micro y bus RS-485 |

## 3. Ideas que conservamos
| Idea | De dónde | Cómo la usamos |
|---|---|---|
| **Entrada con EL817/PC817, resistencia en serie, resistencia de 10 kΩ y LED indicador** | fastLOGIC, PLsi | las 8 entradas; el transistor del optoacoplador tira del pin a masa → **sale activo a nivel bajo sin invertir nada**, justo lo que lee nuestro PLC. En DIP (se cambia en el laboratorio) |
| **Un común de entradas** o común por grupo de 4 | PLsi | un común simplifica el cableado de un banco; se evalúa dejar dos grupos de 4 |
| **0 V del procesador aislado del campo** | PLsi | la placa no une la masa de campo con la de la Galileo |
| **Driver de relé**: `ULN2003` (TH, trae diodos de rebote) o `MMBT5551` + 2,2 kΩ + 10 kΩ a masa + diodo + LED | PLsi / fastLOGIC | con 4 relés el ULN2003 es más simple de reparar. **Falta verificar** en su hoja de datos que conduzca bien con la salida de 3,3 V de la Galileo |
| **Relé inversor con borne de 3 contactos (NA, común, NC) por relé** | fastLOGIC | cada relé con su propio común (PLsi comparte comunes de a 3 y limita la enseñanza) |
| **Bobinas desde el contacto maestro** | nuestra propuesta | la alimentación de las bobinas entra por el contacto maestro (ver `propuesta_contacto_maestro.md`) |
| **Fusibles externos**, 10 A en total | PLsi | indicados en la guía del alumno, no en la placa |
| **LED por cada entrada y salida** | los tres | didáctico: se ve el estado sin el panel |
| **Diodo de protección contra polaridad inversa en cada entrada** | shield OSHWA | en el LED de entrada |
| **Bornes atornillados de 3,5 mm y puntos de prueba** | fastLOGIC | cableado de banco y medición |
| **Lista de materiales con códigos LCSC y archivos para JLCPCB** | fastLOGIC | pedir la placa ya ensamblada |

## 4. Lo que **no** tomamos, y por qué
| Idea | Motivo |
|---|---|
| Expansor I2C PCF8574 (shield OSHWA) | el bus de la Galileo ya tiene el Cypress en la dirección `0x20`, y el PCF8574 usa `0x20`–`0x27`: chocarían. Nuestros 12 puntos de E/S son pines directos |
| Salida de relé con cuatro entradas analógicas, pantalla, Ethernet, tarjeta SD | no corresponden: lo resuelve la Galileo |
| Entradas con disparo de 9,5 V (fastLOGIC) | demasiado alto para 5 V; las nuestras deben activarse con 5 V |
| Archivos con licencia no comercial (CC BY-NC-SA) o sin licencia | se toma la idea, no el archivo |

## 5. Siguiente paso propuesto
1. Crear el proyecto KiCad con la huella del Uno (Alarm-Siren) y trazar el contorno en `Edge.Cuts`.
2. Copiar de fastLOGIC v001 el bloque de entrada (EL817) y adaptarlo para 5–24 V y activo a nivel bajo; calcular las resistencias (corriente del LED del optoacoplador).
3. Elegir el driver de relé tras revisar la hoja de datos con 3,3 V.
4. Dibujar el contacto maestro y su circuito de vigilancia.
5. Revisar los cálculos y pedir un prototipo.

Cálculos y elecciones de componentes **no están hechos**: esto es solo la selección de referencias.
