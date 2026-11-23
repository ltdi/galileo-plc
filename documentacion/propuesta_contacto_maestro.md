# Propuesta: contacto maestro para las salidas de relé

**Estado:** propuesta de diseño para la placa de expansión (8 optoentradas y 4 relés). Nada de esto está construido ni medido salvo lo indicado como «observado».

## 1. Idea
Un contacto (interruptor con llave y/o pulsador de emergencia tipo hongo, normal cerrado) en serie con la **alimentación de las bobinas de los relés**. Con el contacto abierto, ningún relé puede cerrar, haga lo que haga el software. Es el equivalente del *relé de control maestro* de un tablero.

## 2. Por qué conviene
1. **El software no es una barrera de seguridad.** El PLC es un sistema Linux sin garantía de tiempo real.
2. **Cuelgues observados.** Durante las pruebas la placa se colgó varias veces (señales a OpenPLC, reinicios, etc.). Cuando el kernel se detiene, los pines de salida **conservan el último valor**: una salida activa quedaría activa. Un contacto maestro (y mejor aún, uno con vigilancia, ver 3.2) lo evita.
3. **Arranque.** Entre el encendido y el momento en que Linux inicia el PLC (~15 s) **no se midió** el estado de los pines D8–D11. El expansor de la placa (CY8C9540A) viene por defecto con salidas en alto y *pull-up* (hoja de datos, registros 0x08 y 0x1D), así que un módulo de relé activo en alto podría cerrarse un instante. Hay que medirlo; con un contacto maestro que se cierra recién cuando el PLC está en marcha, el problema desaparece.
4. **Mantenimiento y prácticas.** Permite cablear y tocar el banco con la certeza de que las salidas no se moverán.

## 3. Diseño sugerido

### 3.1 Etapa mínima (hardware simple)
- Pulsador de emergencia NC con enclavamiento + llave, **en serie con el positivo que alimenta las bobinas** (pin VCC o «JD-VCC» del módulo de relés).
- Corriente: una bobina SRD-05VDC consume del orden de 70–90 mA; cuatro, unos 0,3–0,4 A a 5 V. Un contacto de pulsador común alcanza.
- LED «salidas habilitadas» después del contacto.
- **Realimentación al PLC:** llevar el estado del contacto a una entrada (una de las 8 optoentradas o una novena) para que el programa y el panel en vivo lo vean (por ejemplo, para no «creer» que una salida actúa cuando está inhabilitada).

### 3.2 Etapa recomendada (con vigilancia)
- El contacto maestro lo gobierna un **relé de vigilancia**: se mantiene cerrado mientras llegue un **latido** (pulsos de ~2–5 Hz) que genera la capa de hardware del PLC *dentro del ciclo de programa*. Si el PLC se cuelga, se reinicia o aún está arrancando, no hay latido y el relé cae. Se puede construir con un monoestable reenganchable (por ejemplo, un 555) y un transistor.
- Cuesta una de las cuatro salidas (por ejemplo D11) o un pin libre del conector. El latido se generaría en `hardware_layer_galileo_8e4s.cpp`; el procedimiento y la frecuencia se definen al elegir los componentes.
- Cubre los cuelgues del sistema sin depender de que Linux funcione.

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
3. Elegir pulsador/llave, relé de vigilancia y qué salida se sacrifica para el latido (o ampliar el conector).
4. Dónde se coloca físicamente (frente del banco, accesible).
