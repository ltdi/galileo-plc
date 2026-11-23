# Mapa de pines de la Galileo Gen 1 (FAB-D) configurada como PLC

Documento de referencia: cómo está configurado cada pin del PLC didáctico (8 entradas, 4 salidas), con sus números de GPIO de Linux, puertos y máscaras del expansor Cypress, selectores (mux), registros I2C y direcciones del lado de OpenPLC/Modbus.

**Fuentes:** esquemático de la Galileo (`Galileo Schematic`, hoja del expansor U8 y de los conmutadores analógicos de D2/D3/D10–D13), datasheet del CY8C9540A (Doc. 38-12036 Rev. *A), `variant.cpp` de la FAB-D, y mediciones hechas en la placa el 23/11/2026. Actualizado el 23/11/2026 con la imagen v4 (flasheada). Cada dato dice de dónde sale: **[esq]** esquemático, **[ds]** datasheet, **[var]** `variant.cpp`, **[med]** medido en la placa.

## 1. Resumen: qué pin es qué

| Pin Arduino | Función en el PLC | Dirección IEC | GPIO Linux | Está en | PWM posible | Compartido con |
|---|---|---|---|---|---|---|
| D0, D1 | **No se usan** (consola serie) | – | – | Cypress + SoC | no | UART |
| D2 | Entrada 1 | `%IX0.0` | 14 | SoC (Quark) | no | Cypress P2.0 (mux) |
| D3 | Entrada 2 | `%IX0.1` | 15 | SoC (Quark) | sí (Cypress P0.2) | Cypress (mux) |
| D4 | Entrada 3 | `%IX0.2` | 28 | Cypress P1.4 | no | – |
| D5 | Entrada 4 | `%IX0.3` | 17 | Cypress P0.1 | sí (PWM5) | – |
| D6 | Entrada 5 | `%IX0.4` | 24 | Cypress P1.0 | sí (PWM6) | – |
| D7 | Entrada 6 | `%IX0.5` | 27 | Cypress P1.3 | no | – |
| D8 | Salida 1 (relé de pruebas) | `%QX0.0` | 26 | Cypress P1.2 | no | – |
| D9 | Salida 2 | `%QX0.1` | 19 | Cypress P0.3 | sí (PWM1) | – |
| D10 | Salida 3 | `%QX0.2` | 16 | Cypress P0.0 | sí (PWM7) | SPI SS (mux) |
| D11 | Salida 4 | `%QX0.3` | 25 | Cypress P1.1 | sí (PWM4) | SPI MOSI (mux) |
| D12 | Entrada 7 | `%IX0.6` | 38 | Cypress P3.2 | no | SPI MISO (mux) |
| D13 | Entrada 8 | `%IX0.7` | 39 | Cypress P3.3 | no | SPI SCK (mux) |
| A0–A5 | **No se usan** | – | – | Cypress P0.4–7, P3.0–1, P4 | – | entradas analógicas |

- Pines con PWM en la Galileo según el datasheet de la placa: **D3, D5, D6, D9, D10, D11**. En el PLC se usan D5 y D6 (entradas) y D9, D10 y D11 (salidas) **como GPIO**: el PWM está apagado (registro 0x1A = 0 [ds][med]).
- Ningún pin es "exclusivamente GPIO": D2/D3 y D10–D13 pasan por conmutadores analógicos que los conectan al Cypress o al SoC/SPI (sección 4). D4–D9 sí van directo a un único pin del Cypress (más una resistencia en serie de 33,2 Ω).
- Lógica: **entradas activas en nivel bajo** (contacto u optoacoplador a GND = `TRUE`); **salidas activas en nivel alto**.

## 2. Numeración de GPIO de Linux del expansor Cypress [esq][var]

El CY8C9540A (I2C, bus `/dev/i2c-0`, dirección **0x20**) tiene 6 puertos: 0, 1, 3 y 4 de 8 bits y 2 y 5 de 4 bits. Linux los numera consecutivos desde 16, sin huecos:

| Puerto | GPIO Linux | Bits |
|---|---|---|
| 0 | 16–23 | 8 |
| 1 | 24–31 | 8 |
| 2 | 32–35 | 4 |
| 3 | 36–43 | 8 |
| 4 | 44–51 | 8 |
| 5 | 52–55 | 4 |

Fórmula usada en la capa de hardware: con `g = gpio − 16`: si `g < 16`, `puerto = g/8`, `bit = g%8`; si `16 ≤ g < 20`, `puerto = 2`, `bit = g−16`; si `g ≥ 20`, `puerto = 3 + (g−20)/8`, `bit = (g−20)%8`. Máscara = `1 << bit`.

### Señales de cada puerto según el esquemático (U8)

| Puerto | Bit 0 | Bit 1 | Bit 2 | Bit 3 | Bit 4 | Bit 5 | Bit 6 | Bit 7 |
|---|---|---|---|---|---|---|---|---|
| P0 (gpio16–23) | **D10** (PWM7) | **D5** (PWM5) | D3 (PWM3) | **D9** (PWM1) | A5_MUX | A4_MUX | A3_MUX | A2_MUX |
| P1 (gpio24–31) | **D6** (PWM6) | **D11** (PWM4) | **D8** | **D7** | **D4** | I2C_MUX | IO3_MUX | IO2_MUX |
| P2 (gpio32–35) | IO2_INTC | – | WD (reserva) | – | | | | |
| P3 (gpio36–43) | A1_MUX | A0_MUX | **D12** | **D13** | IO0_MUX | IO1_MUX | **IO10_MUX** | **IO11_MUX** |
| P4 (gpio44–51) | A0_GPIO | A1_GPIO | A2_GPIO | A3_GPIO | A4_GPIO | A5_GPIO | IO0_GPIO | IO1_GPIO |
| P5 (gpio52–55) | RESET_SHLD | SW_RESET_SHLD | **IO12_MUX** | **IO13_MUX** | | | | |

Los pines en negrita son los que usa el PLC.

## 3. Pines del PLC en el Cypress: puerto, bit y máscara

| Pin | GPIO | Puerto.bit | Máscara | Modo de drive del PLC | Rol |
|---|---|---|---|---|---|
| D10 | 16 | P0.0 | `0x01` | fuerte (strong) | salida |
| D5 | 17 | P0.1 | `0x02` | **pull-up resistivo** | entrada |
| D9 | 19 | P0.3 | `0x08` | fuerte | salida |
| D6 | 24 | P1.0 | `0x01` | **pull-up resistivo** | entrada |
| D11 | 25 | P1.1 | `0x02` | fuerte | salida |
| D8 | 26 | P1.2 | `0x04` | fuerte | salida (relé) |
| D7 | 27 | P1.3 | `0x08` | **pull-up resistivo** | entrada |
| D4 | 28 | P1.4 | `0x10` | **pull-up resistivo** | entrada |
| D12 | 38 | P3.2 | `0x04` | **pull-up resistivo** | entrada |
| D13 | 39 | P3.3 | `0x08` | **pull-up resistivo** | entrada |

**Por qué hay que tocar el modo de drive.** En la Galileo las entradas del Cypress quedan en modo **alta impedancia** (registro 0x23). Sin nada conectado flotan y se leen como 0 (que en este PLC es "activo"). La capa de hardware (`cy_pullup`, en `scripts_openplc/hardware_layer_galileo_8e4s.cpp`) las pasa a pull-up resistivo, **lee de vuelta para verificar y reintenta hasta 12 veces** (en el arranque las primeras transacciones I2C se pierden: sin verificar, D4 y D5 quedaban flotando; medido tras el arranque: P0 pull-up `e4` / hi-Z `16` y P1 pull-up `29` / hi-Z `e4`), y avisa en `/tmp/openplc.log` si no lo logra. `plc.sh` espera además a que exista `/dev/i2c-0`. Los registros 0x1D–0x23 tienen "prioridad del último escrito" [ds]: poner un bit en 0x1D lo saca solo del modo que tuviera. Los datos medidos están en la sección 6.

## 4. Conmutadores analógicos (mux): pines que no son GPIO fijos [esq][var]

Cada conmutador (IN = línea de selección, NO = contacto "normalmente abierto", NC = "normalmente cerrado", COM = pin de la placa) conecta el pin del conector a una de dos fuentes. La selección la controla un bit del Cypress.

| Pin | Selección | GPIO de selección | Nivel para usarlo como GPIO del PLC | Origen con nivel alto | Origen con nivel bajo |
|---|---|---|---|---|---|
| D2 | IO2_MUX = P1.7 | gpio31 | **bajo** | Cypress P2.0 (IO2_INTC) | **SoC GPIO (gpio14)** |
| D3 | IO3_MUX = P1.6 | gpio30 | **bajo** | Cypress P0.2 (IO3_PWM) | **SoC GPIO (gpio15)** |
| D10 | IO10_MUX = P3.6 | gpio42 | **alto** | **Cypress P0.0 (gpio16)** | SPI SS (SoC) |
| D11 | IO11_MUX = P3.7 | gpio43 | **alto** | **Cypress P1.1 (gpio25)** | SPI MOSI (SoC) |
| D12 | IO12_MUX = P5.2 | gpio54 | **alto** | **Cypress P3.2 (gpio38)** | SPI MISO (SoC) |
| D13 | IO13_MUX = P5.3 | gpio55 | **alto** | **Cypress P3.3 (gpio39)** | SPI SCK (SoC) |

Los niveles están confirmados por el funcionamiento de las salidas y entradas en la placa [med] (D10, D11 y D12/D13 con mux en alto; D2/D3 con mux en bajo). El conexionado "alto = Cypress" de D10–D13 es consistente con `variant.cpp` y el esquemático (el contacto NO de cada conmutador va a la señal `*_GPIO`).

### Pull-ups externos de D2 y D3 (SoC)

D2 y D3 tienen una habilitación de pull-up propia, controlada por el SoC (esquemático: `CLN_IO2_PU_EN` = SoC GPIO<8>, `CLN_IO3_PU_EN` = SoC GPIO<9>). En Linux son **gpio0 (D2)** y **gpio1 (D3)** [var]; hay que ponerlos en alto como salida. Quedan en alto en el PLC [med].

D4–D13 no tienen resistencias de pull-up/pull-down en la placa: solo una resistencia serie de 33,2 Ω hacia el conector [esq]. Por eso el pull-up del Cypress es necesario.

## 5. Acceso por sysfs desde OpenPLC

Orden que sigue la capa de hardware (`initializeHardware`), todo por `/sys/class/gpio`:

1. **Salidas** (D8, D9, D10, D11): si tiene mux (D10, D11), `export` del mux, `direction=out`, `value=1`; luego `export` del gpio, `direction=out`, `value=0` y se abre `value` para escritura.
2. **Entradas** (D2…D13): si tiene mux, ponerlo (D2: gpio31=0, D3: gpio30=0, D12: gpio54=1, D13: gpio55=1); si tiene pull-up de SoC, `gpio0=1` / `gpio1=1`; `direction=in`; después `cy_pullup()` por I2C si es un gpio del Cypress (16–55); se abre `value` para lectura.

**Importante en esta placa:** `echo low > direction` o `echo high > direction` **no fijan el nivel**. Hay que escribir `direction=out` y después `value` por separado.

Si el pin no está exportado todavía, la capa hace `echo N > /sys/class/gpio/export`.

## 6. Registros del Cypress: significado y valores medidos

Acceso: `/dev/i2c-0`, dirección esclava **0x20** (`I2C_SLAVE_FORCE`). El registro es autoincremental [ds]: se escribe la dirección y se lee N bytes seguidos. Para los registros 0x19–0x23 hay que escribir antes el **selector de puerto 0x18** (valor 0–7).

| Registro | Nombre | Significado | Valor por defecto [ds] |
|---|---|---|---|
| 0x00–0x07 | Input Port 0..7 | niveles reales de los pines (solo lectura) | – |
| 0x08–0x0F | Output Port 0..7 | niveles de salida. Para poder usar un pin como entrada su bit debe ser 1 | FFh |
| 0x10–0x17 | Interrupt Status Port | cambios detectados desde la última lectura | 00h |
| 0x18 | Port Select | puerto a configurar con 0x19–0x23 | 00h |
| 0x19 | Interrupt Mask | 1 = interrupción desactivada | FFh |
| 0x1A | Select PWM | 1 = el pin va al PWM | 00h |
| 0x1B | Inversion | 1 = invierte la lectura de la entrada | 00h |
| 0x1C | Pin Direction | **1 = entrada, 0 = salida** | 00h |
| 0x1D | Drive: Pull Up | resistivo arriba, fuerte abajo | FFh |
| 0x1E | Drive: Pull Down | fuerte arriba, resistivo abajo | 00h |
| 0x1F | Drive: Open Drain High | | 00h |
| 0x20 | Drive: Open Drain Low | | 00h |
| 0x21 | Drive: Strong | fuerte arriba y abajo (rápido) | 00h |
| 0x22 | Drive: Slow Strong | fuerte, lento | 00h |
| 0x23 | Drive: High-Z | alta impedancia | 00h |
| 0x28–0x2B | PWM (select, config, period, width) | | 00/00/FF/80 |
| 0x2D | Enable WDE/EEE/EERO | EEPROM y watchdog del chip (desactivados) | 00h |
| 0x2E | Device ID / Status | | 20h/40h/60h |
| 0x30 | Command | guardar/leer configuración en EEPROM | 00h |

### Valores medidos en la placa (PLC en marcha, 23/11/2026) [med]

Lectura de los puertos de entrada y salida (0x00–0x05 y 0x08–0x0D):

```
INPUT  0x00..05: ee 39 ff cf ff ff
OUTPUT 0x08..0D: fe 39 ff cf ff ff    (P0 = fe con D10 en 0; varía con las salidas)
DEVICE ID/STATUS 0x2E: 40
```

Registros de configuración, puertos 0 a 2 (lectura estable):

| Puerto | 0x1C Dirección | 0x1D Pull-up | 0x21 Strong | 0x23 High-Z | Lectura |
|---|---|---|---|---|---|
| P0 | `e2` | `e2` | `09` | `14` | bits 0 y 3 = salidas fuertes (D10, D9); bit 1 (D5) entrada con pull-up; bits 2 (D3) y 4 (A5) en alta impedancia |
| P1 | `39` | `39` | `c6` | `00` | bits 0, 3, 4 (D6, D7, D4) entradas con pull-up; bits 1, 2 (D11, D8) salidas fuertes; bits 6, 7 (mux de D3 y D2) salidas fuertes |
| P2 | `ff` | `ff` | `00` | `00` | sin uso |

Los valores `0x1A` (PWM) = `00` y `0x1B` (inversión) = `00` en estos puertos [med]. La máscara de interrupciones (0x19) está en `ff` (desactivadas).

**Antes de aplicar `cy_pullup`** (medido con el primer volcado): P0 `hiz = 06` (bits 1 y 2: D5 y D3 en alta impedancia), P1 `pullup = 00`, `hiz = 19` (D6, D7, D4 en alta impedancia: bits 0, 3, 4). Con ese estado D4–D7 se leían siempre en 0.

**Pendiente de verificar (lecturas inestables en puertos 3 a 5; la lectura del registro de pull-up de P3 repitió el valor de P0 en un volcado):** los puertos 3, 4 y 5 (D12, D13 y los mux de D10–D13). Las lecturas de configuración de esos puertos no fueron estables en los dos volcados que hice; hay que repetirlos con OpenPLC detenido por `quit()` (no por señales) y con `cysimple`. Con la capa actual D12 y D13 no dieron aviso de pull-up sin verificar y leen en reposo. Los niveles que sí se conocen: `INPUT` P3 = `cf` (bits 2 y 3 = D12 y D13 en alto en reposo, bits 6 y 7 = mux de D10 y D11 en alto) y P5 = `ff` (bits 2 y 3 = mux de D12 y D13 en alto).

### Estado de los GPIO de Linux (sysfs) en marcha [med]

| gpio | Dirección | Valor | Función |
|---|---|---|---|
| 0, 1 | out | 1 | pull-up de D2 y D3 |
| 14, 15 | in | 1, 0 | D2 y D3 (D3 en 0 por el contacto NC del relé de pruebas) |
| 16, 19, 25, 26 | out | 0/1/0/0 | D10, D9, D11, D8 (según lo que ordene el programa) |
| 17, 24, 27, 28 | in | 1 | D5, D6, D7, D4 (en reposo, con pull-up) |
| 30, 31 | out | 0 | selectores de D3 y D2 (hacia el SoC) |
| 38, 39 | in | 1 | D12, D13 |
| 42, 43, 54, 55 | out | 1 | selectores de D10, D11, D12, D13 (hacia el Cypress) |

## 7. Direcciones del lado de OpenPLC / Modbus TCP (puerto 502, unidad 1)

| Variable IEC | Pin | Modbus |
|---|---|---|
| `%IX0.0` … `%IX0.7` | D2 D3 D4 D5 D6 D7 D12 D13 | Discrete Inputs (función 2), direcciones 0–7 |
| `%QX0.0` … `%QX0.3` | D8 D9 D10 D11 | Coils (función 1/5/15), direcciones 0–3 |
| `%MW0` … | – | Holding Registers (función 3/6/16) desde la dirección **1024** |

Los bits de memoria `%MX` no están expuestos por Modbus en esta versión de OpenPLC: usar `%MW` si hace falta escribir desde el cliente.

## 8. Tiempos medidos [med]

- Lectura I2C del Cypress: 2,18 ms por byte suelto, 5,38 ms para 6 bytes seguidos; por sysfs ~2,2 ms por pin.
- Ciclo del PLC: 20 ms (HZ = 100 del kernel; usar múltiplos de 10 ms).
- Con la capa de 1 relé + 2 contactos: período medio 20,0 ms, máximo 93,6 ms en una hora, 1 ciclo > 25 ms.

## 9. Lo que todavía no está verificado

(Estado al 23/11/2026, imagen v4.)

- **Comprobado:** D4, D5, D6, D7, D12 y D13 pasan a activa al unirlos a GND y vuelven al soltarlos (prueba manual con `probar_entradas.py`); D2 y D3 con el contacto del relé; D8 a D11 conmutan.
- Los registros de configuración de los puertos 3, 4 y 5 del Cypress (ver sección 6).
- Polaridad de la placa de relés/optos del proyecto (si el módulo activa con nivel alto o bajo).
- Los números de GPIO del SoC de los pull-ups (gpio0, gpio1) y de las entradas D2/D3 (gpio14, gpio15) vienen de `variant.cpp`; el esquemático da los nombres de señal (`GPIO<6>`…`GPIO<9>`) y la correspondencia se comprobó por el funcionamiento, no leyendo registros del SoC.
