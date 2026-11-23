# Propuesta: contacto maestro para las salidas de relé

**Estado:** propuesta de diseño para la placa de expansión (8 optoentradas y 4 relés). Nada de esto está construido ni medido salvo lo indicado como «observado».

## 1. Idea
Un **interruptor maestro con autoenclavamiento** en la **alimentación de las bobinas de los relés** (solo ahí: la Galileo se alimenta aparte y sigue viva, ver `referencias_placa_expansion.md` §5). Con el interruptor desarmado, ningún relé puede cerrar, haga lo que haga el software. Es el equivalente del *relé de control maestro* de un tablero, con marcha (ARMAR) y paro (PARO). Es un **paro didáctico de comando, no un circuito de seguridad**.

## 2. Por qué conviene
1. **El software no es una barrera de seguridad.** El PLC es un sistema Linux sin garantía de tiempo real.
2. **Cuelgues observados.** Durante las pruebas la placa se colgó varias veces (señales a OpenPLC, reinicios, etc.). Cuando el kernel se detiene, los pines de salida **conservan el último valor**: una salida activa quedaría activa. Un contacto maestro (y mejor aún, uno con vigilancia, ver 3.2) lo evita.
3. **Arranque.** Entre el encendido y el momento en que Linux inicia el PLC (~15 s) **no se midió** el estado de los pines D8–D11. El expansor de la placa (CY8C9540A) viene por defecto con salidas en alto y *pull-up* (hoja de datos, registros 0x08 y 0x1D), así que un módulo de relé activo en alto podría cerrarse un instante. Hay que medirlo; con un contacto maestro que se cierra recién cuando el PLC está en marcha, el problema desaparece.
4. **Mantenimiento y prácticas.** Permite cablear y tocar el banco con la certeza de que las salidas no se moverán.

## 3. Diseño sugerido

### 3.1 Enclavamiento con MOSFET (decidido; **no simulado ni construido**)
| Parte | Función |
|---|---|
| Q1: MOSFET canal P en la línea de 5 V hacia las bobinas | conmuta la alimentación de las bobinas; debe conducir plenamente con 5 V de compuerta |
| R entre compuerta y fuente (≈10 kΩ) | lo mantiene apagado por defecto |
| Q2: NPN pequeño | baja la compuerta de Q1 |
| Pulsador **ARMAR** (normal abierto) | da un impulso a la base de Q2 |
| Realimentación desde la salida de Q1 a la base de Q2, **a través del pulsador PARO (normal cerrado)** | mantiene el enclavamiento; al abrir PARO se apaga todo y no vuelve solo |
| LED en la línea de las bobinas | indica «armado» |

Consecuencias del diseño:
- **Tras un corte de energía o un reinicio las bobinas quedan apagadas** hasta pulsar ARMAR. Una llave que quede en ON no da esa garantía.
- **El pulsador PARO solo lleva unos miliamperios:** sirve cualquier pulsador NC grande y cómodo (no hace falta una seta de emergencia para circuito impreso), incluso cableado a distancia; si se corta el cable, desarma.
- Corriente a conmutar: una bobina SRD-05VDC consume del orden de 70–90 mA; cuatro, unos 0,3–0,4 A a 5 V. Un MOSFET pequeño de bajo umbral alcanza (**verificar la hoja de datos**).
- El MOSFET en cortocircuito dejaría de cortar: por eso se presenta como paro didáctico, no de seguridad. El paro de emergencia de potencia se cablea aparte, sobre los contactores. No corta lo que ya está energizado en el lado de potencia de los contactos.

### 3.2 Desarme por el PLC (opcional)
- Un segundo NPN en paralelo, gobernado por un **latido**, puede desarmar el enclavamiento. El PLC **no puede armar**, solo desarmar.
- Un monoestable reenganchable (por ejemplo, un 555) detecta que faltan pulsos de ~2–5 Hz, generados por la capa de hardware dentro del ciclo de programa. Si el PLC se cuelga, se reinicia o está arrancando, no hay latido y el enclavamiento cae. Se puede exigir latido presente para que ARMAR sea efectivo, así que no se arma durante los ~15 s de arranque.
- **No cuesta ninguna salida de relé.** El latido sale por un pin analógico libre de la Galileo, usado como GPIO: **A0 a A3** (A4 y A5 comparten pines con el bus I2C: evitarlos). Cada uno tiene un conmutador que hay que poner en «GPIO»:

  | Pin | GPIO de Linux | Conmutador (poner en alto) |
  |---|---|---|
  | A0 | 44 | gpio37 |
  | A1 | 45 | gpio36 |
  | A2 | 46 | gpio23 |
  | A3 | 47 | gpio22 |

  Comprobado en la placa el 23/11/2026 (solo por software, sin medir el pin): con `gpio37`=1, `gpio44` se exporta, se comporta como salida (1 y 0 leídos de vuelta), y como entrada con *pull-up* lee 1. No se midió el nivel eléctrico en el conector.
- El latido se generaría en `hardware_layer_galileo_8e4s.cpp`, dentro del ciclo de programa; aún **no está implementado**.
- **Estado hacia el PLC:** un divisor de resistencias desde la línea de bobinas puede llevar el estado «armado» a otro pin A0–A3 (o a una entrada), para que el panel lo muestre. Sin implementar.
- **De paso:** A0–A3 (y, con cuidado, A4/A5) quedan disponibles como entradas o salidas digitales adicionales si la placa de expansión las llevara a su conector.

### 3.3 Complementos
- **Resistencias de bajada** (≈10 kΩ) en la señal de entrada de cada driver de relé, para que un pin en alta impedancia o con *pull-up* en el arranque no active nada.
- Confirmar la **polaridad** del módulo de relés (activo en alto o en bajo).
- El contacto maestro **no reemplaza** el paro de emergencia de potencia: ese actúa sobre los contactores y se cablea aparte, sin pasar por el PLC.

## 4. Impacto en el software
- Ninguno obligatorio para la etapa mínima.
- Opcional: una entrada «MAESTRO» en el panel en vivo y en las plantillas; latido en la capa de hardware (etapa 3.2).

## 5. Pendiente de medir o decidir
1. Estado real de D8–D11 durante los primeros segundos del arranque (multímetro/osciloscopio o un LED).
2. Polaridad del módulo de relés de la placa del proyecto.
3. Dimensionar y simular el enclavamiento (MOSFET P de bajo umbral, NPN, resistencias), elegir los pulsadores ARMAR y PARO, y llevar el pin A0 (o A1–A3) al desarme por latido si se hace la etapa 3.2.
4. Dónde se coloca físicamente (frente del banco, accesible).
