# Guía para profesores: el PLC didáctico con Galileo

Para cátedras de **máquinas eléctricas** e **instalaciones eléctricas**. Estado al 23/11/2026; todo lo que aquí se afirma como «probado» se probó en la placa real del laboratorio.

## 1. En una frase

Un autómata programable pequeño y económico (placa Intel Galileo) que los alumnos programan en **escalera** (o en texto estructurado) desde un PC, y que **arranca solo al enchufarlo**, como un PLC comercial. El programa se carga por red en unos 15 segundos, sin cables especiales ni tarjetas de memoria.

## 2. Qué puede hacer

| Capacidad | Detalle |
|---|---|
| **Entradas y salidas** | 8 entradas digitales y 4 salidas digitales. Las entradas se activan al cerrar un contacto a masa (GND). |
| **Lenguajes** | Escalera (LD) y texto estructurado (ST), probados. Bloques de función (FBD) los ofrece el editor, no se probaron. |
| **Funciones habituales** | Autorretención, temporizadores (TON probado), contadores y flancos de la biblioteca estándar IEC 61131-3 (disponibles; solo el temporizador se probó). |
| **Ciclo de programa** | 20 ms. |
| **Ver y forzar en vivo** | Un panel en el navegador muestra entradas, salidas y las variables del programa, y permite **forzar** una entrada o una salida. Sirve para **simular pulsadores, finales de carrera o térmicos sin cablear nada**. |
| **Comunicación** | Modbus TCP: se puede conectar a un SCADA, un panel HMI o Node-RED (tema de supervisión y telecontrol). |
| **Errores de programación** | El compilador indica la línea y la columna del error. |

## 3. Qué NO puede (todavía)

- **No tiene entradas ni salidas analógicas** en este sistema: todavía no sirve para variadores con señal de 0–10 V ni para sensores de 4–20 mA.
- **Los pines trabajan a nivel lógico de la placa (3,3–5 V)**. No soportan 24 V ni 220 V. La **placa de expansión con 8 optoentradas y 4 relés** del proyecto está en desarrollo; hasta que exista se usan pulsadores a masa y un módulo de relé comercial (un relé de ese tipo conmuta una carga pequeña o la bobina de un contactor, nunca el motor directamente).
- **No es un PLC de seguridad ni de tiempo real estricto.** El ciclo es de 20 ms, con picos medidos de hasta ~94 ms. **El paro de emergencia y las protecciones se cablean aparte, independientes del PLC.**
- **El programa vive en la memoria RAM:** si se corta la energía, la placa vuelve a su **programa de fábrica** (un ascensor de 3 pisos) y hay que cargar el programa otra vez.

## 4. Cómo usarlo en la cátedra

**Qué necesita cada banco:** un PC (Ubuntu) con el paquete instalado (ver `instalacion_howto.md`; lo prepara el administrador del laboratorio una sola vez), una placa en la misma red, y una fuente de 5 V.

**Qué hace el alumno (5 pasos):**

1. Abre el acceso directo «PLC Galileo»: se abre el editor y una ventana pequeña con el panel en vivo.
2. Abre una **plantilla** de proyecto (escalera o texto).
3. Programa la lógica.
4. En el editor: *Search* → elige su placa → icono de descarga (*Build options*) → **Build and upload**.
5. Observa y fuerza entradas en el panel, o prueba con sus pulsadores y lámparas.

**Tres formas de aprovecharlo:**

- **Solo con el PC** (sin cablear): se fuerzan las entradas desde el panel y se ven las salidas. Ideal para explicar enclavamientos y secuencias en el aula, y para que el alumno compruebe su lógica antes de cablear.
- **Con pulsadores, lámparas y relés** en el banco: la lógica de comando de un tablero, con los elementos reales.
- **Con contactores y motor** de un banco de ensayo: solo con módulo de relé, protecciones adecuadas y el docente a cargo.

## 5. Prácticos propuestos

Los programas de ejemplo están en `ejemplos_alumno/`. «Probado» significa cargado en la placa y verificado forzando las entradas desde el panel.

| # | Práctico | Qué enseña | Entradas / salidas | Estado |
|---|---|---|---|---|
| 1 | **Marcha-paro con enclavamiento y térmico** (`motor_marcha_paro.st`) | autorretención, contactos NC, lógica de falla segura | 3 / 2 | probado |
| 2 | **Inversión de giro** (`inversion_giro.st`) | enclavamiento cruzado, parar antes de invertir | 4 / 2 | probado |
| 3 | **Estrella-triángulo** (`estrella_triangulo.st`) | temporización (5 s), secuencia, tiempo muerto de 100 ms, KM2 y KM3 nunca a la vez | 3 / 3 | probado |
| 4 | Luz intermitente (`intermitente.st`) | dos temporizadores (1 s encendida, 3 s apagada); se habilita forzando una salida desde el panel | 0 / 2 | incluido, compila |
| 5 | Portón automático (`porton.st`) | máquina de estados, finales de carrera, fotocélula | 4 / 3 | incluido, compila; lógica sin verificar |
| 6 | Ascensor de 3 pisos (`ascensor3.st`) | secuencias, memoria de llamadas | 8 / 4 | programa de fábrica; carga y corre; sin verificar con botonera real |
| 7 | Detección de errores (`con_error.st`) | leer los mensajes del compilador | — | incluido |
| 8 | Arranque secuencial de cintas o bombas, control de nivel con boyas | temporización, histéresis | — | **propuesto, no incluido** |

Los programas 1 a 3 están pensados para el cableado típico de un tablero: pulsador de **paro** y contacto del **térmico** en **normal cerrado**, de modo que si un cable se corta el motor se detiene.

## 6. Seguridad

1. **Nunca conectar la tensión de red ni 24 V directamente** a los pines de la placa.
2. El **paro de emergencia** y las protecciones (guardamotor, térmico, fusibles) van cableados, **sin depender del PLC**.
3. Las salidas manejan un módulo de relé; la potencia la conmutan contactores con sus protecciones.
4. **Al encender**, la placa ejecuta el programa de fábrica (el ascensor) hasta que se cargue otro. **No conectar cargas peligrosas durante el arranque.** Está pendiente reemplazar ese programa por uno que deje todas las salidas apagadas.
5. Las entradas se leen **activas al cerrar a masa** (lógica negativa): una entrada sin conectar vale «inactiva».

## 7. Lo que falta

- La **placa de expansión** (8 optoentradas, 4 relés) y la verificación de su polaridad.
- Entradas analógicas.
- Un programa de fábrica «seguro» (todo apagado) y una guía para el alumno.
- Pruebas en el laboratorio con varios bancos a la vez, y en Windows.
- Si necesitan un práctico que no está en la lista, indíquenlo: los de estas características se pueden agregar al repositorio.

*Repositorio: https://github.com/ltdi/galileo-plc · Instalación: `documentacion/instalacion_howto.md` · Operación: `documentacion/guia_operacion.md`.*
