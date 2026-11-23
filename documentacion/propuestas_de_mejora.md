# Propuestas de mejora

Ideas para la siguiente etapa, con lo que se **comprobó** en la placa (23/11/2026) y lo que **no**. Ninguna está implementada salvo que se diga.

| # | Propuesta | Esfuerzo | Necesita hardware nuevo | Requiere reflashear |
|---|---|---|---|---|
| 1 | Contacto maestro de las salidas, con vigilancia | medio | sí (placa de expansión) | sí, para el latido |
| 2 | Entradas analógicas (A0–A5) | medio | acondicionamiento de señal | sí |
| 3 | Display alfanumérico | bajo a medio | sí (módulo I2C) | sí |
| 4 | Conexión Wi-Fi | bajo (puente) a alto (nativa) | sí | solo la nativa |
| 5 | Otras mejoras ya identificadas | varía | no | varía |

## 1. Contacto maestro con vigilancia
Un contacto (pulsador de emergencia y/o llave) en serie con la alimentación de las bobinas de los relés; con un relé de vigilancia gobernado por un latido del PLC para cubrir cuelgues y arranque. **No consume ninguna de las cuatro salidas:** el latido sale por A0–A3. Detalle en [`propuesta_contacto_maestro.md`](propuesta_contacto_maestro.md).

## 2. Aprovechar las entradas analógicas libres
- **Qué hay.** La placa trae un conversor **AD7298** (12 bits, 8 canales; la Galileo usa 6, A0–A5). El kernel ya lo gestiona: existe `/sys/bus/iio/devices/iio:device0` con `in_voltage0_raw` … `in_voltage5_raw`, `in_voltageN_scale` y un sensor de temperatura.
- **Comprobado:** el dispositivo responde y las seis lecturas con los pines al aire dan valores de 0 a 5 cuentas (≈0 V). Una lectura por `sysfs` cuesta del orden de 9 ms medido desde la consola (incluye lanzar `cat`; el costo real del conversor es menor, no medido).
- **Propuesta.** En la capa de hardware, leer los canales a un ritmo menor que el ciclo (por ejemplo cada 100 ms, para no cargar los 20 ms) y publicarlos como `%IW0.0`…`%IW0.5` (registros de entrada Modbus 0–5). El panel mostraría el valor y la tensión.
- **Usos en cátedra:** potenciómetro como consigna, sensores de temperatura o nivel, medición de corriente con sensor y acondicionamiento.
- **Cuidados / sin verificar:** el rango exacto de entrada (se asume 0–5 V según el jumper IOREF; **no medido**); cada pin A0–A5 es **o analógico o digital** (el conmutador lo decide), así que usar uno como analógico lo quita de la lista de GPIO extra; para 4–20 mA hace falta una resistencia de medición y protección; nunca señales de red.

## 3. Display alfanumérico
- **Qué mostraría:** dirección IP, estado (en marcha / sin programa), estado de las 4 salidas y las 8 entradas, falla del contacto maestro, hora de arranque.
- **Opción recomendada: LCD de 16×2 o 20×4 con módulo I2C (PCF8574)** en los pines SDA/SCL de la placa (A4/A5, que comparten el bus con el expansor de la Galileo; el expansor usa la dirección `0x20`, los módulos de LCD suelen usar `0x27`, sin choque). El kernel ya expone `/dev/i2c-0`. Haría falta un programa pequeño (unos pocos KB, caben en el margen de ~88 KB de la imagen) que escriba al HD44780 por I2C.
- **Opción alternativa:** display serie por D0/D1 (`ttyQRK0`); sin verificar.
- **Cuidados / sin verificar:** nivel lógico del módulo (5 V o 3,3 V según IOREF); usar A4/A5 para I2C los quita como analógicos; no se conectó ningún display todavía.

## 4. Conexión Wi-Fi
- **Qué hay en la imagen:** el kernel trae `cfg80211`, `mac80211`, `iwlwifi` e `iwldvm` (para tarjetas Wi-Fi de Intel en la ranura mini-PCIe de la placa). **No trae** `wpa_supplicant`, herramientas inalámbricas ni el archivo de firmware de ninguna tarjeta, ni controladores USB de Wi-Fi (no hay `rt2800usb`, `ath9k_htc`, etc.).
- **Espacio:** quedan ≈88 KB libres en el sistema de archivos en memoria de la imagen. Un firmware y un `wpa_supplicant` suman, a priori, bastante más (**tamaño no medido**): habría que liberar espacio quitando otros módulos.
- **Camino rápido, sin tocar la placa:** un **puente Wi-Fi a Ethernet** (cliente Wi-Fi con salida Ethernet, un mini-router en modo cliente) conectado al puerto de red de la Galileo. Se ve igual que un cable. Funciona hoy, **no probado**.
- **Camino nativo:** una tarjeta Wi-Fi Intel en la mini-PCIe + firmware + `wpa_supplicant` y configuración de la red (SSID y clave por placa, y el Modbus y el receptor no tienen autenticación). Más trabajo y más riesgo; solo si el puente no sirve.
- **Seguridad:** abrir la placa a Wi-Fi amplía quién puede cargar o forzar sus salidas; antes habría que añadir autenticación o aislar la red.

## 5. Otras mejoras ya identificadas
| Mejora | Qué resuelve | Estado |
|---|---|---|
| Usar el atributo `drive` de `sysfs` (`pullup`, `strong`, `hiz`) en vez de escribir al expansor por I2C | más limpio y sin acceso directo al chip; **comprobado** que el atributo existe y acepta escrituras | propuesta |
| A0–A3 como entradas/salidas digitales adicionales | más puntos de E/S si la placa de expansión los lleva al conector | propuesta (comprobado por software) |
| Autenticación o aislamiento: Modbus, receptor 9100/9101 y forzado (registros 2024–2027) sin autenticación | cualquiera en la red puede cargar o forzar | propuesta |
| Medir el estado de D8–D11 en los primeros ~15 s del arranque | confirmar el comportamiento seguro al encender | pendiente (medición) |
| Persistencia del programa del alumno (EEPROM o recarga automática desde el PC) | hoy se pierde al cortar la energía | propuesta |
| Depurador nativo del editor (reenviar el puerto 502, MD5 y numeración de variables) | ver variables dentro del editor | propuesta; hoy se usa el panel en vivo |
| Temporizador de vigilancia del Quark | reinicio automático ante un cuelgue | el kernel de Intel no trae el controlador |
| Causa de fondo de los cuelgues con señales a OpenPLC | hoy solo se evita | sin resolver |
| Generador de imágenes por MAC (un comando) | una imagen por placa | hoy es un argumento del script |
| Soporte de Windows para el paquete | laboratorios con Windows | descartado por ahora (el SDK de Intel trae versión para Windows) |
