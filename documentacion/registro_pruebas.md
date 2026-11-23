> **Nota (23/11/2026):** esta es la bitácora cronológica completa. Los archivos mencionados en las primeras secciones (sketches de Arduino, `resultados_*.txt`, `openplc_galileo`, `hardware_layer_galileo.cpp`, `plc_cargar_telnet.py`, `prueba_fallas.py`…) se movieron a `archivo/`. El estado vigente está en `Informe final - PLC didactico Galileo.docx`, `mapa_pines_galileo_plc.md` y `guia_operacion.md`.

# Registro de pruebas con la Galileo Gen1 (2026-11-22)

**Hardware:** Galileo Gen1 (FAB-D), relé SRD-05VDC de 1 canal, Ethernet directo a la PC
(10.42.0.0/24, la PC comparte la conexión). Se programó desde la PC con el core "Revived Intel i586"
(compilador i586 de Intel recuperado, kernel 3.8.7 en la placa).

**Cableado del relé durante las pruebas:** SIG a D8, VCC al pin 5V de la placa, GND a GND, COM a GND.
Hasta las pruebas con A0 y A2 el NO iba a A2 y el NC a A0; después pasaron a D2 (NO) y D3 (NC).

| # | Prueba | Resultado | Estado |
|---|--------|-----------|--------|
| 1 | Análisis completo por telnet, 23 pasos de solo lectura | Kernel 3.8.7 con PREEMPT_VOLUNTARY y HZ=100, sin watchdog (no hay /dev/watchdog), `/dev/uio0` = sch_gpio, rootfs en RAM sin SD, 238 MB de RAM, CPU a 399 MHz. Sin sshd ni dropbear; sí telnetd y ftpd con root sin clave. | Hecha |
| 2 | Red de la placa | `eth0` arrancaba con MAC 00:00:00:00:00:00 y sin IP. Con la MAC de la etiqueta (98:4F:EE:00:FA:94) y DHCP queda en 10.42.0.151. La MAC no persiste al reiniciar. | Resuelta (hay que repetirla en cada arranque) |
| 3 | Polaridad del relé | Activo en nivel alto (observación visual con un bucle de 2 s activo y 3 s inactivo). | Hecha; falta confirmar con multímetro |
| 4 | Latencia Modbus TCP (coil 0 = relé en D8) | Lectura: mediana 1,14 ms, p99 1,26 ms. Escritura: mediana 3,4 a 3,5 ms, máximo 3,8 ms. 60 escrituras sin errores de eco. Excepciones correctas ante peticiones inválidas. | Hecha |
| 5 | Banco de jitter del ciclo de scan, v1 | **Fallida.** Los procesos de carga de CPU heredaron SCHED_FIFO y dejaron la placa sin CPU; hubo que reiniciarla. Sin resultados. | Descartada, rehecha en la 5b |
| 5b | Banco de jitter v2 (ciclo de 10 ms, 3000 ciclos por fase, sin tocar pines) | Atraso de cada despertar. A: SCHED_FIFO en reposo, 53 a 84 µs (prom. 63). B: SCHED_FIFO con dos procesos de carga de CPU, 48 a 215 µs (prom. 49, p99,9 = 69). C: SCHED_OTHER con la misma carga, 105 a 128 µs (prom. 106). Los 9000 ciclos quedaron por debajo de 250 µs. La carga se lanzó con prioridad normal y se mató sola. | Hecha; solo 30 s por fase, sin E/S ni tráfico de red concurrentes |
| 6 | Sonda analógica A0/A1/A2 con ADC | Las tres leen 0 con el relé en ambos estados (ningún terminal lleva tensión). Cada `analogRead` tarda ~400 µs. | Descartada para medir el contacto |
| 7 | Contacto con A0 y A2 como entradas digitales | Confirmó COM a GND, NC a A0 y NO a A2. Resolución de 4,4 ms (2,2 ms por lectura vía expansor I2C); no sirve para rebote. | Superada por la prueba 8 |
| 8 | Contacto con D2 (NO) y D3 (NC) en modo rápido, ~3,4 µs por muestra | Desde que vuelve `digitalWrite(D8)`: activar, NC abre a 1,36 ms y NO cierra a 3,22 ms; soltar, NO abre a 2,82 ms y NC cierra a 4,01 ms. Transferencia 1,9 ms al activar y 1,2 ms al soltar. Rebote del NO al activar ~20 transiciones en ~0,9 ms; en el NC al soltar ~37 en ~8,9 ms (dudoso: puede ser ruido del pull-up). Solo 41 de 60 soltados fueron válidos. `digitalWrite(D8)` tarda ~2,07 ms. | Hecha; rebote por confirmar con osciloscopio |
| 9 | Repetir la prueba 8 con VCC del relé directo a una fuente de 5 V | **No se logró el cableado.** El relé no conmutó (NO leyó 1000 de 1000 y NC 0 de 1000 en ambos estados). Probable falta de masa común o 5 V sin llegar a VCC. Sin resultados. | Descartada |
| 10 | Viabilidad de OpenPLC v3 en la placa | Se descargó OpenPLC v3 (commit b5d4135, 78 MB, trae matiec, libmodbus, dnp3 y snap7). matiec (`iec2c`) se compiló en el PC. El núcleo se compiló para i586 con el GCC 4.7.2 de Intel, sin DNP3 (stub oficial `dnp3_dummy.disabled`) y con stubs para snap7 y el maestro Modbus; solo hizo falta cambiar `thread_local` por `__thread` en la copia. El ejecutable (48 KB, dinámico) corre en la placa: arranca con SCHED_FIFO y mlockall, y con `start_modbus(502)` sirve Modbus TCP. Un programa ST de prueba (TON de 2 s que alterna `%QX0.0` y cuenta en `%MW0`) corrió: el contador sube cada ~2,0 s, leído por Modbus desde el PC. | Hecha; hito 1 (sin E/S real) |
| 11 | OpenPLC con E/S real en la Galileo (hito 2) | Capa de hardware propia: `%QX0.0` = relé en D8 (gpio26), `%IX0.0` = contacto NO en D2 (gpio14) y `%IX0.1` = contacto NC en D3 (gpio15), con sysfs y descriptores abiertos. D2 y D3 requieren enrutar al SoC (gpio31 y gpio30 en bajo) y activar su pull-up (gpio0 y gpio1 en alto); **en esta placa `echo low/high > direction` no fija el nivel: hay que poner `out` y escribir `value` aparte** (el primer intento leyó NO y NC siempre en 0 por eso). El programa ST de demostración arranca inerte y solo alterna el relé cada 2 s si se habilita el coil 1 por Modbus. Con el lazo cerrado: el relé commuta, el NO pasa a cerrado y el NC a abierto en cada paso, y el PLC ve la realimentación en el scan siguiente (scans_resp = 2, con scan de 20 ms). Al deshabilitar, el relé queda inactivo (NC cerrado). El arranque se automatiza con `arranque_openplc.ino`: red (MAC y DHCP), lanza OpenPLC desde `sketch.elf.old`, activa Modbus y abre un telnet que se apaga a los 30 min. | Hecha |
| 12 | Programa real en escalera: contactor supervisado | Diseñado como escalera de 7 peldaños y traducido a ST (`contactor_supervisado.st`): arranque/paro con enclavamiento (paro dominante, bloqueado por falla), salida al relé, supervisión de cierre, de contacto pegado y de coherencia NO/NC (tres TON de 100 ms con falla enclavada hasta RECONOCER), y contador de arranques. Pulsadores virtuales por Modbus (coils 1 a 3). Prueba por Modbus, 7 comprobaciones, todas OK: reposo, arranque enclavado que sigue tras soltar MARCHA, paro, segundo arranque, paro dominante con MARCHA pulsada, y contador = 2. matiec compiló a la primera. | Hecha |
| 13 | Supervisión de contactos con fallas reales (cables desconectados a propósito) | Tres fases con `prueba_fallas.py`, 18 de 18 comprobaciones OK (cinco fases). (1) NO desconectado de D2: al dar MARCHA el relé se activa, aparece FALLA_NO_CIERRA enclavada, el relé se suelta solo y no rearranca; RECONOCER la borra al desaparecer la causa; también salió incoherente, porque el NC abrió y el NO no cerró. (2) NC desconectado de D3: FALLA_CONTACTOS aparece en reposo sin mover nada y bloquea MARCHA; RECONOCER no la borra mientras persiste. (3) Todo reconectado: RECONOCER limpia, reposo coherente, MARCHA enclava, PARO suelta, arranque contado. (4) COM y NO puenteados a mano en el relé (contacto soldado simulado, sin orden): FALLA_PEGADO aparece, bloquea MARCHA y RECONOCER no la borra mientras persiste; también marca incoherente (NO y NC cerrados). (5) Puente quitado: vuelve a la normalidad. Límite: mi muestreo por Modbus fue lento (~0,7 s por foto), sin estados intermedios. | Hecha, las tres supervisiones probadas |
| 14 | Viabilidad de una imagen propia en la flash (estudio, sin grabar) | La placa trae `efi_capsule_update` y `start_spi_upgrade.sh`: graba una cápsula desde /tmp (RAM) y reinicia. El Linux de la flash es un initramfs de ~2,6 MB comprimidos (12 MB en RAM); OpenPLC pesa ~53 KB. Las fuentes del BSP v1.2.1 y el firmware 1.0.4 responden en archive.org (solo cabeceras); las páginas de Intel redirigen a 404, salvo la guía del BSP (cdrdv2-public.intel.com). No hay `/dev/mtd`: no se puede respaldar la flash. La MAC está en los datos de plataforma (pdat) de la flash. Conclusión: viable en principio, subproyecto de días con riesgo, y no guarda el programa de cada alumno sin reprogramar la flash. | Hecha (estudio) |
| 15 | STOP y RUN, carga por red y memoria retentiva | `quit()` detiene el programa y apaga las salidas; RUN tarda ~2 s hasta Modbus. Carga por red con `tcpsvd`: 53 KB en 1 s con md5 igual; secuencia completa de parada, carga y arranque ~10 s (`plc_cargar.py`). Retención con `start_pstorage`: sobrevive a STOP, RUN y cambio de programa (6 y 6), pero el archivo (14 336 bytes) está en RAM. OpenPLC lee una sola orden por mensaje; un primer intento falló por mandar dos juntas. El contador debe usar `%MW0` directamente, no un CTU interno. | Hecha |
| 16 | Costo de leer el expansor de E/S por I2C | Un byte: 2,18 ms; seis bytes: 5,38 ms (≈1,5 ms fijos + 0,65 ms por byte). Cada pin por sysfs también cuesta ~2,2 ms. Agrupar entradas y salidas por puerto baja el costo de ~26 ms (12 pines) a ~5 ms. Pendiente implementarlo en la capa de hardware. | Hecha (medición) |
| 17 | Modbus de OpenPLC: conexión persistente frente a nueva | Persistente: mediana 1,24 ms, p99 1,44 ms (130 s a 10 Hz, 1270 consultas, 0 errores). Conexión nueva: ~100 ms cada una (el servidor acepta con `sleepms(100)`). | Hecha |
| 18 | Herramienta de estación `plc.py` | Del `.st` a la placa en un comando: matiec 0,5 s, compilar el programa y enlazar 1,2 s (el núcleo se reutiliza), cargar y arrancar ~10 s. Probada con el programa del proyecto, con un ejemplo de alumno (intermitente) y con un programa con error de sintaxis (se informa en pocas líneas). Solo compilación probada con la placa ocupada; la carga con otro programa queda para después de la prueba de 1 h. | Parcial |
| 19 | Resistencia de 1 hora con E/S y red a la vez | Inició a las 01:35 (hora de la PC): un SCADA a 10 Hz por conexión persistente y un operador que arranca y para el relé cada 20 s. Mide el período real entre scans (instrumentación en la capa de hardware, línea `SCAN` cada 60 s). Una corrida corta de 130 s dio período medio 20,011 ms, mínimo 19,7 ms, máximo 96 ms (un ciclo > 25 ms) y E/S máx. 2,5 ms. **Resultado de 3600 s:** 179 992 scans, período medio 20,0 ms, máx. 93,6 ms, solo 1 ciclo > 25 ms, E/S máx. 2,5 ms, 109 ciclos de relé, sin cortes. Pero el canal Modbus tuvo 4859 errores en 21 699 consultas (22 %, ~36 000 esperadas), latencia p50 1,31 ms y un máximo de 1030 ms. Causa sin determinar (sospecha: reconexión del cliente de prueba o servidor Modbus de OpenPLC). | Completada con errores en Modbus |

## Notas

- (Estado antiguo, ver abajo) Estado de la placa al terminar la prueba 10: el sketch cargado es `telnet_temporal` (que apaga el telnet a los 30 min),
  y OpenPLC corre aparte, lanzado a mano con `nohup` (puertos 43628 y 502). El relé está inactivo: la capa de E/S de OpenPLC
  todavía no maneja D8.
- D2 y D3 quedaron con el pull-up externo activado (gpio0 y gpio1 de Linux en alto). Es inofensivo.
- Pendiente: medir el rebote con osciloscopio, confirmar la polaridad con multímetro y decidir cómo persistir
  la MAC y el sketch tras un reinicio (la microSD solo como último recurso).

## OpenPLC en la Galileo: estado y pendientes (hitos 1 a 3 logrados)

- Archivos: `scripts_openplc/construir.sh` (construye todo desde las fuentes descargadas, sin modificarlas),
  `scripts_openplc/hardware_layer_galileo.cpp` (capa de E/S: D8, D2, D3), `arranque_openplc/arranque_openplc.ino` (arranque en la placa), `scripts_openplc/stubs_galileo.cpp`,
  `scripts_openplc/galileo_demo.st` (programa de prueba) y el ejecutable `openplc_galileo/openplc`.
- Pendiente: por qué OpenPLC no arranca solo si se sube como sketch (el cargador lo lanza y muere; queda un zombi). Se resuelve con `arranque_openplc`. Tras un reinicio hay que volver a subir ambos (todo en RAM).
- Pendiente: si OpenPLC muere sin salir limpio, el relé queda como estaba; hace falta el circuito de corte externo (etapa 8).
- Pendiente: reponer maestro Modbus (libmodbus) y evaluar snap7, ambos como stubs por ahora.

## Estado al 23 de noviembre (prueba de resistencia en curso)

- La placa corre el sketch `telnet_temporal` (telnet temporal) y OpenPLC desde `/tmp/openplc` con el programa «contactor supervisado» instrumentado (línea `SCAN` cada 60 s en el log).
- En la placa quedan receptores de prueba de `tcpsvd` en los puertos 9100 (carga de programa), 9101 (reenvío al puerto de control de OpenPLC), 9102 (lectura del log) y 9103 (pruebas). Son solo para el laboratorio y desaparecen al reiniciar.
- La prueba larga termina con `quit()`: al terminar OpenPLC queda detenido y el relé apagado.

## Imagen propia (23 de noviembre) — sin flashear

- `Flash-PLC.bin` y `Flash-PLC.cap` generados con `scripts_imagen/construir_imagen.py`: initramfs sin Bluetooth, con OpenPLC, MAC y `S85plc.sh`; margen de 90 KB.
- Firmas verificadas con `firma.py` (ramdisk en el .bin, ramdisk en el .cap y cápsula) y con `openssl` (RSA-PSS, el activo del ramdisk: Verified OK).
- qemu (`-cpu pentium2,+pae`): el kernel de Intel arranca hasta «turn off boot console» y después no muestra salida, ni siquiera con `rdinit=/bin/sh`. Pasa igual sin importar el initramfs, así que la consola real de la Galileo es `ttyQRK1` (UART PCI de Quark, que qemu no tiene), por eso no hay salida de init. Con `earlyprintk=serial,ttyS0,115200,keep` se ve que el initramfs nuevo se descomprime sin error (8304 KB liberados) y que el kernel se comporta igual que con el original de Intel, incluido el mensaje «Failed to execute /init» en ambos. Valida el formato del initramfs, no el arranque de los servicios.

## Errores Modbus de la prueba de 1 hora (diagnóstico)

- El servidor Modbus dejó de responder de forma permanente a ~2200 s (consultas fijas en 21 699 y errores acumulándose); el scan siguió normal toda la hora (179 992 ciclos).
- El log de la placa muestra que el descriptor de archivo de cada cliente nuevo sube de a uno por cada par de conexiones (7, 9, 10, 11, … 1023) y se clava en 1023: se agotó el límite de 1024 descriptores del proceso. Hay una pérdida de ~1 descriptor cada ~2,2 s. La causa exacta no está identificada: no está en `hardware_layer_galileo.cpp` ni en `persistent_storage.cpp` (revisados). Pendiente: mirar `/proc/<pid>/fd` en la placa. Hoy no hay telnet (puerto 23 cerrado), solo los receptores 9100-9103.

### Prueba del arranque en qemu con canal de depuración (23 de noviembre)

- Dato nuevo del datasheet Quark (carpeta `galileo/`): las UART de alta velocidad son PCI 8086:0936 (D20:F1 y D20:F5); el parche de Intel las trata como 8250 con `reg_shift=2` (o con el driver `intel_quark_uart` para `ttyQRK`). Qemu no las tiene, por eso no hay consola.
- Canal de depuración sin emular la UART: un script de prueba escribe al puerto E/S 0xE9 (`/dev/port`) y qemu lo guarda con `-debugcon`. Así se ve el arranque real de sysvinit con el initramfs nuevo.
- Resultado: init arranca (`/init` es un archivo vacío no ejecutable y el kernel cae a `/sbin/init`, igual que en la imagen de Intel); la MAC, `/opt/plc/openplc`, `S85plc.sh` están; `btusb` ya no está en `galileo.conf`.
- Fallo encontrado y corregido: sin `lo` configurada, OpenPLC moría con «Interactive Server: error binding socket». `plc.sh` ahora hace `ifconfig lo 127.0.0.1 up` y arranca el PLC antes de esperar la red. Con eso OpenPLC queda en marcha y Modbus escucha en el 502 (el gpio falla porque qemu no tiene sysfs de la Galileo, esperado).
- Imagen regenerada (md5 .bin b60b0cdc…, .cap 232dd863…); firmas verificadas. Sigue sin flashearse.

### Corrección sobre los errores Modbus de la prueba de 1 hora (23 de noviembre)

- La segunda corrida se congeló en el mismo punto que la primera: **21 699 ciclos**, no un tiempo. 21 699 × 3 consultas + 109 ciclos de relé × 4 = 65 533 peticiones, que es el límite del campo de 16 bits del identificador de transacción Modbus (65 535). `struct.pack('>H')` fallaba desde ahí y todas las peticiones contaban como error.
- Es un **defecto del script de prueba** (`prueba_larga.py`), no del servidor Modbus. Queda corregido (el id da la vuelta en 65 536). La hipótesis anterior de pérdida de descriptores de archivo en el servidor no está confirmada: el conteo se mantuvo en 12 durante 25 min con la carga completa. Los números de descriptor que subían en el log de la primera corrida son compatibles con el cliente abriendo y cerrando conexiones en bucle durante la fase de error.
- La fila 19 ('Completada con errores en Modbus') no vale como resultado de resistencia del servidor. Se repite la hora completa con el script corregido (resultado en `/tmp/claude-1000/resultado_larga_3.txt`).

- **Confirmado con la placa (04:20 de la placa):** el proceso `openplc` tenía 1023 descriptores abiertos, 1017 de ellos sockets sin cerrar, y `openplc.log` pesaba 1,46 MB (en tmpfs). El conteo estuvo en 12 de las 03:32 a las 04:05 y saltó a 1023 en unos minutos justo cuando el cliente de prueba empezó a abrir y cerrar conexiones en bucle por el error del identificador. Conclusión: el servidor Modbus de OpenPLC **pierde sockets si los clientes abren y cierran conexiones muy rápido** (llegó al límite de 1024 y quedó sin responder, aunque aceptaba TCP). En uso normal no ocurrió. Es una fragilidad del servidor para vigilar, no la causa del corte original.
- Se reinició OpenPLC y se lanzó la hora completa con el script corregido; el conteo de descriptores se registra cada 30 s en la placa (`/tmp/fdlog.txt`).

### Supervisor del PLC en `plc.sh` (23 de noviembre)

- `plc.sh` ahora corre un supervisor: relanza OpenPLC si muere, si supera 900 descriptores de archivo (el límite es 1024) o si Modbus deja de responder (consulta de 8 coils cada 5 s, 3 fallos seguidos), apaga las salidas al reiniciar y recorta el log de RAM a 256 KB. `stop` detiene el supervisor y el PLC.
- Prueba en qemu (canal de depuración): arranque normal con respuesta Modbus de 10 bytes; tras `kill -9` el proceso se relanza (pid 516 → 655); con el proceso congelado (`SIGSTOP`) el supervisor lo detecta y lo reemplaza (655 → 802); `stop` deja 0 procesos y 0 supervisores.
- No probado en la placa. Pendiente medir cuánto dura la interrupción de las salidas en un reinicio.
- La imagen quedó con el binario de 8 entradas / 4 salidas y el programa del ascensor (54 037 B); esa capa de hardware todavía no se probó en la placa. Margen libre del ramdisk: 89 324 B. Firmas verificadas con `firma.py`; md5 .bin e311e9f4…, .cap 0f198bbf….

### Software en la PC: servidor de compilación y carga (23 de noviembre)

- Puestos del LTDI: Ubuntu y Windows 10. Decisión propuesta: **un servidor Ubuntu** con `scripts_openplc/servidor_plc.py` (solo biblioteca estándar) y una página web; el alumno usa el editor y el navegador, sin toolchain en su PC.
- Probado llamando a las funciones (sin abrir el puerto): portón compila en 1,0 s (52 978 B); el programa con error devuelve el mensaje de matiec con línea y columna; una IP fuera de la lista o pública se rechaza; programa vacío se rechaza. El servidor HTTP **no se probó en marcha** (el sistema bloqueó abrir un puerto de red desde la sesión).
- **Hueco encontrado:** la carga actual (`plc_cargar.py`) usa el telnet temporal y `tcpsvd` de la placa. La imagen final no los tiene. Hace falta un receptor de programas dentro de la imagen (escucha en un puerto, verifica md5 y le pide al supervisor que relance con el binario nuevo). Pendiente de implementar.

### Receptor de programas en la imagen (23 de noviembre)

- `plc.sh` lanza dos `tcpsvd` (BusyBox ya los trae): **9100** recibe el ejecutable en `/tmp/openplc.new`; **9101** recibe `aplicar <md5>`, verifica la suma, lo mueve a `/tmp/openplc_user` y mata a OpenPLC; el supervisor lo relanza eligiendo `/tmp/openplc_user` si existe, si no el de fábrica (`/opt/plc/openplc`, ejemplo del ascensor). Sin telnet ni sesión de shell.
- Si el programa del alumno muere en menos de 10 s se borra y vuelve el de fábrica (protege contra un binario corrupto o que no arranca).
- Prueba en qemu por loopback (canal de depuración): md5 incorrecto → «ERROR: md5 distinto»; programa válido → «OK», pid nuevo y `bin=/tmp/openplc_user`, Modbus responde 10 bytes; programa que sale de inmediato → «OK» pero a los pocos segundos el supervisor lo descarta y vuelve `/opt/plc/openplc`.
- `plc_cargar.py` usa ahora este protocolo (puertos 9100/9101); la versión por telnet quedó como `plc_cargar_telnet.py`. **No probado contra la placa real** (la que está en la mesa tiene el cargador de Arduino, no esta imagen).
- Límites: sin autenticación (cualquiera en la red puede cargar un programa y ejecutarlo como root: solo para red de laboratorio aislada); el programa del alumno vive en RAM y se pierde al apagar (vuelve el de fábrica).
- Imagen regenerada: margen del ramdisk 88 693 B; md5 .bin 6b58f5ff…, .cap eceb95ca…. Sigue sin flashearse.

### Pruebas previas a flashear, en la placa real (23 de noviembre)

- **Hora de resistencia #3 (script corregido):** 3600 s, 35 945 consultas Modbus a 10 Hz, **0 errores**, latencia p50 1,26 ms, p99 1,49 ms, máx. 1025 ms (un solo pico). Confirma que los errores de las corridas 1 y 2 eran del cliente de prueba.
- **Acceso:** la placa había perdido el telnet (se apaga a los 30 min). Recuperado subiendo por USB un ELF de 6 KB (`telnet_elf/telnet30.c`, compilado con el compilador cruzado y cargado con `clupload`, sin Arduino IDE).
- **Entradas (capa `hardware_layer_galileo_8e4s.cpp`):** hallazgo importante. Con nada conectado, D3..D7 leían «activo» (nivel bajo). Los GPIO del expansor Cypress (gpio16..55) quedan en modo **alta impedancia** (registro 0x23: bits 0, 3, 4 del puerto 1 y 1, 2 del puerto 0) y flotan. Corrección: la capa pone pull-up resistivo (reg 0x1D) y saca de alta impedancia (reg 0x23) por I2C a las entradas que están en el Cypress (`cy_pullup`). En reposo quedan [D2=0, D3=1, resto 0]; D3 está en 1 porque tiene el contacto NC del relé de las pruebas anteriores (cierra a GND), no es un error.
- **Salidas:** con `ejemplos_alumno/prueba_es.st` (salidas seguidas desde registros 1024..1027) las cuatro, D8 a D11, conmutan; D8 además cierra D2 (NO) y abre D3 (NC) del relé conectado.
- **Sin verificar:** las entradas D4..D7, D12 y D13 detectando un contacto real a GND (no hay nada cableado). Necesita un puente a mano.
- **Supervisor y receptor en la placa real** (scripts de la imagen copiados a la RAM, con el paso de red omitido para no cortar el acceso): `plc.sh start` arrancó OpenPLC, Modbus respondió y `tcpsvd` quedó en 9100/9101.
- **Falla:** al aplicar un programa nuevo por red (`plc_cargar.py`: envío al 9100 correcto, orden `aplicar` al 9101 sin respuesta) **la placa dejó de responder del todo**: sin ping, Modbus ni telnet, y el cargador USB tampoco la ve. Parece un cuelgue; causa sin identificar. En qemu la misma secuencia funcionó. Hace falta que el usuario reinicie la placa.

### Revisión del esquemático del Cypress y segundo cuelgue (23 de noviembre)

- Esquemático (U8, CY8C9540A): numeración de Linux = puerto 0 gpio16..23 (D10, D5, D3, D9, A5..A2), puerto 1 gpio24..31 (D6, D11, D8, D7, D4, I2C, D3_MUX, D2_MUX), puerto 2 (4 bits) gpio32..35, puerto 3 gpio36..43 (A1, A0, **D12**, **D13**, D0_MUX, D1_MUX, **D10_MUX**, **D11_MUX**), puerto 4 gpio44..51, puerto 5 (4 bits) gpio52..55 (reset, D12_MUX, D13_MUX). Los gpio y los mux que usa la capa coinciden con el esquemático.
- **Error encontrado y corregido:** `cy_pullup` calculaba el puerto como `(gpio-16)/8`, que para gpio ≥ 32 es incorrecto (los puertos 2 y 5 tienen 4 bits). D12 (gpio38) caía en puerto 2 bit 6 en lugar de puerto 3 bit 2. Ahora usa la tabla del esquemático.
- Pines con PWM según el esquemático/datasheet: D3, D5, D6, D9, D10, D11 (6). La capa usa D5, D6 como entradas y D9, D10, D11 como salidas; el PWM está desactivado por defecto (no se toca el registro 0x1A), así que funcionan como GPIO. No usan PWM: D2, D4, D7, D8, D12, D13.
- **Segundo cuelgue, reproducible:** con la imagen en la RAM de la placa (`empujar_ram.py`) y el supervisor corriendo, la placa dejó de responder **justo al abrir la conexión al puerto 9100** (monitor en vivo por telnet: uptime, carga, memoria libre 181 MB y descriptores estables hasta ese instante). El mismo envío con un `tcpsvd` lanzado a mano por telnet no colgó antes. Diferencias a aislar: supervisor, `salud` cada 5 s, `tcpsvd` lanzado por el supervisor con un script, sin consola.

### Aplicar con `quit()`, y tercer cuelgue (23 de noviembre)

- Con `rx_aplicar.sh` usando `quit()` (en vez de `kill`) la secuencia completa funcionó sobre la placa real: envío al 9100, `aplicar` al 9101 → «OK», OpenPLC relanzado con `/tmp/openplc_user` en ~9 s sin cuelgue; programa que sale al instante → el supervisor lo descarta y vuelve `/opt/plc/openplc`; segundo programa bueno cargado de nuevo. Conclusión: **`kill` (SIGTERM) a OpenPLC colgaba la placa** (tres veces). Causa de fondo sin identificar.
- Una consulta Modbus dio timeout justo después del tercer aplicar (el supervisor estaba relanzando); un minuto después Modbus respondía 10 bytes. No se repitió.
- **Tercer cuelgue**: `kill -STOP` a OpenPLC y lectura I2C del Cypress con `cyvolcado` (inicio repetido) → la placa dejó de responder. Dos señales distintas a OpenPLC colgaron la placa (SIGTERM y SIGSTOP). Hipótesis: el proceso OpenPLC (tiempo real, memoria bloqueada) ante señales deja al kernel 3.8.7 sin respuesta; no hay consola serie para verlo. No enviar señales a OpenPLC: parar solo por `quit()`.
- Documento nuevo: `mapa_pines_galileo_plc.md` (pines, GPIO, puertos y máscaras del Cypress, mux, registros, valores medidos, direcciones Modbus).

### Aplicar 10 veces seguidas, placa real (23 de noviembre)

- Supervisor + receptor de la imagen en la RAM de la placa, `quit()` en `rx_aplicar.sh`: 10 aplicaciones consecutivas por red alternando `prueba_es` y el ascensor, 10 de 10 aplicadas y con Modbus respondiendo 12 s después; la placa siguió contestando. Sin cuelgues.
- El reinicio espontáneo observado antes se debió a que se desenchufó la fuente para fotografiarla (la placa quedó solo con USB): no era un fallo. Retirada la hipótesis de alimentación.
- Los tres cuelgues anteriores coincidieron con señales a OpenPLC (SIGTERM, SIGSTOP). El camino por `quit()` no los reproduce. Causa de fondo sin identificar.

### Flasheo de Flash-PLC.cap (23 de noviembre)

- Autorizado por el usuario («si no queda ninguna prueba, procede con la imagen»). Antes: firmas verificadas (bin@0x260000, cap@0 y cap@0x224590), el módulo de la clave de firma es el mismo de las imágenes originales de Intel, openplc de la imagen = 7c1303bf…, md5 del `.cap` e3ba870d… verificado en la placa.
- Método: módulo `efi_capsule_update` (ya presente en el kernel de Intel), `.cap` copiado a `/lib/firmware`, `capsule_path` = `Flash-PLC.cap`, `capsule_update` = 1 → «submission success»; luego `reboot` (el firmware aplica la cápsula al reiniciar). Sysfs en `/sys/firmware/efi_capsule/`. `csh_jump` queda en 1 (salto de la cabecera de 1024 B).
- Observación aparte: cada vez que se aplica un programa, el proceso anterior de OpenPLC termina con «segfault at 68 … libpthread» después de `quit()` (visible en dmesg). No impide el relanzamiento; pendiente de investigar.

### Primer flasheo, segundo intento y hallazgos (23 de noviembre)

- **Primer flasheo (imagen v1) correcto:** tras el `reboot` con la cápsula, la placa volvió a la red a los ~145 s sola: OpenPLC en marcha (supervisor), puertos 502, 9100 y 9101 abiertos, sin telnet. Confirma que la imagen firmada por mí arranca en la placa real y que el firmware la aceptó.
- **Defecto de v1:** al arrancar, OpenPLC se lanzaba ~1 s antes de que existiera `/dev/i2c-0`, así que `cy_pullup` no se aplicaba y D4/D5 quedaban flotando en nivel bajo (leídas como activas). Reiniciando el programa con la placa ya arriba se corregía. Corregido en la imagen v2: `plc.sh` espera hasta 30 s a `/dev/i2c-0` antes de lanzar.
- **El módulo `efi_capsule_update` no se carga solo:** hay que hacer `modprobe efi_capsule_update`; el sysfs es `/sys/firmware/efi_capsule/` (no `/sys/firmware/efi/…`). Mi primer intento de la v2 falló por no cargarlo y reinicié igual (error mío): después de ese `reboot` la placa no volvió a la red.
- **Segundo `reboot` (con cápsula v2 enviada) tampoco volvió:** sin eventos de USB en el PC (el kernel no llegó a reiniciar) y sin red; hubo que cortar la alimentación. La cápsula, que vive en memoria, se perdió: la v2 **no** se flasheó. Hipótesis fuerte: el `reboot` de sysvinit envía SIGTERM a todos los procesos (`S20sendsigs`), incluido OpenPLC, y un SIGTERM a OpenPLC cuelga la placa (como con `kill`). El primer flasheo se salvó, no sé por qué.
- **Corrección en la imagen v3:** enlaces `etc/rc6.d/K15plc.sh` y `etc/rc0.d/K15plc.sh` → `plc.sh stop` (para el supervisor y ordena `quit()` a OpenPLC) antes de `sendsigs`. Procedimiento para flashear: `plc.sh stop` explícito, comprobar que `openplc` ya no existe, y recién entonces `reboot`.

### Imagen v4 flasheada y verificada (23 de noviembre)

- **Causa real de D4/D5 flotando al arrancar:** no era el orden con `/dev/i2c-0` (ya existía): las primeras transacciones I2C del arranque se pierden. Diagnóstico por registros: tras el arranque, P0 pull-up `e4` / hi-Z `16` (D5 sin pull-up) y P1 pull-up `29` / hi-Z `e4` (D4 sin pull-up); D6 y D7 sí habían quedado bien. Tras reiniciar OpenPLC con la placa ya estable quedaba todo bien. Corrección: `cy_pullup` ahora **verifica leyendo de vuelta** y reintenta hasta 12 veces (50 ms), y avisa en el log si no lo logra. `plc.sh` además espera a `/dev/i2c-0` (hasta 30 s).
- **Procedimiento de flasheo que funcionó** (sin Arduino IDE): subir `telnet_elf/rescate.elf` por USB con `clupload`; `modprobe efi_capsule_update`; enviar el `.cap` al puerto 9100 y verificar md5; `/etc/init.d/plc.sh stop` y comprobar que no queda `openplc`; copiar a `/lib/firmware/Flash-PLC.cap`; `echo -n Flash-PLC.cap > /sys/firmware/efi_capsule/capsule_path`; `echo 1 > /sys/firmware/efi_capsule/capsule_update` («submission success»); `sync; reboot`. La placa vuelve sola a los ~150 s (el firmware aplica la cápsula).
- **Imagen v4:** `.bin` md5 f566d1e3…, `.cap` md5 8821050c…; incluye supervisor, receptor 9100/9101, parada ordenada en reboot/apagado (`rc6.d`/`rc0.d`), espera de i2c, pull-up verificado, programa de fábrica = ascensor de 3 pisos.
- **Resultado en la placa:** arranque desde flash sin intervención, puertos 502/9100/9101 abiertos, sin telnet, entradas en reposo `01000000` (solo D3, por el contacto NC del relé de pruebas), `reboot` y corte de alimentación seguidos de arranque normal. Un `reboot` sin parar OpenPLC antes colgaba la placa; ya no pasa con el paso de parada de la imagen v4.
- **Sin verificar:** entradas D4–D7, D12, D13 con un contacto real; el ascensor con entradas reales; la interrupción de las salidas durante un reinicio del supervisor; el segfault de OpenPLC al terminar tras `quit()` (inocuo hasta ahora).

### Entradas con contacto real (23 de noviembre)

- Con `scripts_openplc/pruebas_placa/probar_entradas.py` (Modbus persistente, 20 Hz) se unió cada pin a GND con un cable, uno por vez. Reposo: D2=0, D3=1 (contacto NC del relé), D4–D7=0, D12=0, D13=0. Resultado: **D4, D5, D6, D7, D12 y D13 pasan a ACTIVA al unirlos a GND y vuelven a inactiva al soltarlos** (63 a 109 s de la prueba). D12 mostró un rebote al contacto (activa, inactiva, activa en ~1 s), esperable en un cable a mano.
- Con esto las 8 entradas y las 4 salidas quedan comprobadas en la placa real. Quedan sin verificar el ascensor con una botonera completa y la polaridad de la placa de optoacopladores/relés del proyecto.

### OpenPLC Editor 4.3.5 (AppImage) y compatibilidad con la imagen (23 de noviembre)

- El editor nuevo (Autonomy Logic, Electron) **no usa matiec**: compila con **STruC++** (texto estructurado a C++) y arduino-cli. Su proyecto es una carpeta: `project.json` (tareas, instancias, globales), `pous/programs|functions|function-blocks/*.st` (ST como texto plano) y `pous/.../*.ld` (escalera: declaraciones + JSON de peldaños). Exporta PLCopen XML y PDF, no un `.st`. Trae el CLI headless `openplc-cli` (create, compile, upload, debug…).
- Su generador de la sección `CONFIGURATION` imita byte a byte el del editor antiguo (`Config0`/`Res0`, tareas, instancias), así que el texto es compatible con matiec.
- **Adaptador nuevo:** `scripts_openplc/proyecto_editor_a_st.py <carpeta_proyecto> [salida.st]` junta los POUs `.st` y arma la CONFIGURATION desde `project.json`. Probado con un proyecto creado por `openplc-cli create` (programa `luz := boton` con `AT %IX0.0` / `%QX0.0`): compila con `plc.py --solo-compilar` (52 506 B). No se cargó a la placa.
- **Limitación:** los POUs en escalera (`.ld`), FBD y SFC no se convierten (su paso a ST está dentro del compilador del editor); hay que escribirlos en ST.
- **Plugins/paquetes:** el editor admite paquetes de placa «VPP» (`openplc-cli packages install`) con firma Ed25519 obligatoria («falla cerrado»: clave desconocida = rechazo). Sin una firma de Autonomy Logic no se puede agregar la Galileo como destino. El destino «OpenPLC Runtime v3» del editor compila con STruC++ y sube a un runtime v3 por su servicio web: no sirve para esta imagen.

### Runtime virtual para OpenPLC Editor 4.x (23 de noviembre)

- **Decisión (usuario):** camino A: usar el editor oficial sin modificar, con un servidor del laboratorio que imita al runtime. Menos de 10 placas.
- **Protocolo sacado del código del editor** (4.3.5, GPL-3.0; los fuentes salen de los mapas de código del AppImage): descubrimiento por broadcast UDP 33333 con `OPENPLC_DISCOVER_V1` (el editor identifica cada runtime por la **IP de origen** de la respuesta: de ahí las IP virtuales por placa); API HTTPS 8443 (`/api/login`, `get-users-info`, `create-user`, `capabilities`, `version`, `upload-file` con el campo `file` = `program.st`, `compilation-status`, `start-plc`, `stop-plc`, `status`). Para el destino «OpenPLC Runtime v3» el editor sube el **texto estructurado ya completo** (`program.st`, con la sección CONFIGURATION), lo cual incluye lo que haya dibujado en escalera o FBD, y no hace la comprobación de versión del runtime v4.
- **`scripts_openplc/servidor_runtime.py`** (nuevo): implementa todo lo anterior; al recibir `program.st` ejecuta `plc.py --solo-compilar` y `plc_cargar.py --ip <placa>`; informa los pasos y los errores al editor. Configuración en `scripts_openplc/placas.json` (nombre, IP real, IP virtual). `configurar_alias.sh` agrega las IP virtuales (requiere sudo). Certificado TLS autofirmado generado la primera vez.
- **Prueba de extremo a extremo con la placa real**, usando el CLI del editor oficial (`openplc-cli upload <proyecto> --host 127.0.0.1 --target "OpenPLC Runtime v3"`) contra el servidor en loopback: el editor generó el texto, lo subió, el servidor compiló (52 606 B) y lo cargó en la Galileo; el editor mostró «Compilation completed successfully» y «PLC started». Con `%MW0`/`%MW1` por Modbus las salidas `%QX0.0`/`%QX0.1` respondieron como pedía el programa. Con un programa de sintaxis incorrecta, el servidor devuelve el error de matiec y el editor ve FAILED.
- **Sin probar:** el descubrimiento por broadcast real y las IP virtuales (necesitan sudo y la red del laboratorio; el formato de la respuesta sí se verificó contra el analizador del editor), el uso desde la interfaz gráfica del editor, Windows 10 como cliente, y varias placas a la vez. La escucha en 0.0.0.0 la debe iniciar el usuario.
- **Observación:** `stop-plc` responde «no soportado» (la imagen no tiene parada del PLC); la memoria retentiva guardó valores de pruebas anteriores (`coils antes [1, 0]`).

### Prueba con la interfaz gráfica de OpenPLC Editor 4.3.5 (23 de noviembre)

- **Resultado: funcionó.** Con el servidor atado a `10.42.0.1:8443` (red de las placas), el editor (AppImage) encontró la placa con **Search** (entrada «Banco-1»), inició sesión, y «Build and upload» llegó hasta el final: el servidor compiló el programa de la plantilla (52 506 B), lo cargó en la Galileo y el editor mostró «Compilation completed successfully» y «PLC started». La opción de subir está en el botón **Build options** (icono de descarga) de la barra de actividades, y no se llama «Upload».
- **Problema 1 (mío):** `ECONNREFUSED` porque se subió mientras el servidor se reiniciaba.
- **Problema 2:** «Failed to stop PLC: not connected to the target». Causa: tras iniciar sesión el editor no logra describir el canal de depuración del destino «OpenPLC Runtime v3» («could NOT describe a debug channel… declares no channel the editor can connect through»), con lo que no abre su sesión de control y no puede parar el PLC que, según `/api/status`, estaba «RUNNING» (el editor exige parar antes de compilar en el dispositivo). La lectura estática del código (resolvedor de canales, capacidades, `hals.json`) indica que el canal Modbus TCP del v3 debería resolverse, así que **la causa exacta no se identificó**. No afecta a la subida (REST directo).
- **Solución aplicada:** `servidor_runtime.py` informa `STOPPED` en `/api/status` (por defecto, `"estado_editor"` en `placas.json`; admite `STOPPED`, `RUNNING` o `REAL`) y acepta `stop-plc`. Así el editor no pide parar el PLC. Efectos: el editor muestra «detenido» aunque la placa corra; **no hay depuración en vivo** (ver variables) porque ese canal iría a `10.42.0.1:502`, que no es la placa (se podría reenviar el puerto 502 a la placa).
- **Pendiente:** varias placas con IP virtuales, Windows 10, escalera/FBD desde el editor, depuración en vivo.

### Cuelgue tras la prueba con la GUI y causa probable (23 de noviembre)

- Un minuto después de la subida desde el editor, la placa dejó de responder (red y USB). Hipótesis fuerte: el editor consulta `/api/status` cada ~1 s y la primera versión del servidor sondeaba el puerto 502 de la placa en cada consulta (conexión que se abre y se cierra). Durante ~25 min fueron ~1 500 conexiones; el servidor Modbus de OpenPLC pierde ~1 descriptor cada 2 conexiones, así que se llegó a los 900 descriptores del umbral del supervisor justo en ese momento. El supervisor reiniciaba OpenPLC con `kill` (SIGTERM, y SIGKILL a los 1 s), que es la señal que cuelga la placa. Coincide con todos los cuelgues anteriores asociados a señales.
- **Correcciones:** (1) el servidor guarda 30 s el resultado del sondeo del puerto 502 y por defecto informa `STOPPED` sin tocar la placa; (2) en la imagen, el supervisor ya no usa señales para reiniciar OpenPLC: nueva función `parar_plc` (orden `quit()` por el puerto de control, espera hasta 8 s, y solo como último recurso `kill -9`). Imagen nueva: `.cap` md5 d42438b9…, firmas verificadas. **Pendiente de flashear** (la placa está colgada).

### Imagen v5 flasheada (23 de noviembre)

- Flasheada con el procedimiento de la guía (parada ordenada, cápsula, reinicio): volvió a la red a los ~160 s, puertos 502/9100/9101 abiertos, entradas en reposo `01000000`. `.cap` md5 d42438b9…, `.bin` md5 0fac999b….
- Cambio de la v5: el supervisor reinicia OpenPLC con `parar_plc` (orden `quit()`, espera hasta 8 s, `kill -9` solo como último recurso) en vez de `kill` + `kill -9`.
- **Prueba de tormenta de conexiones Modbus** (reproduce lo que hacía el sondeo del estado): ~1 850 conexiones abiertas y cerradas en ~340 s (≈1 100 atendidas; el servidor Modbus acepta unas 10 por segundo). La placa siguió respondiendo (ping y Modbus) al terminar. **No se pudo comprobar que se haya llegado al umbral de 900 descriptores**, así que el reinicio por descriptores con `parar_plc` sigue sin probarse en la placa.

### Escalera desde el editor (23 de noviembre)

- Programa en escalera (`main.ld`: un peldaño, contacto `entrada` → bobina `salida`, `%IX0.1` → `%QX0.1`) escrito a mano en el formato del editor (nodos `powerRail`, `contact`, `coil` y aristas) en una copia del proyecto `plantilla_escalera`, y subido con `openplc-cli upload` contra el servidor. El transpilador del editor generó texto estructurado limpio (`salida := entrada;` más la sección CONFIGURATION), el servidor lo compiló con matiec y lo cargó en la Galileo.
- **Comportamiento en la placa:** en reposo `IX0.1` = 1 (contacto NC del relé de pruebas cerrado a GND) y `QX0.1` = 1; al activar el relé por Modbus (D8) el NC abre y `IX0.1` = 0 y `QX0.1` = 0; al soltarlo vuelven a 1. La salida sigue a la entrada, como dice la escalera.
- **Sin probar:** dibujar el peldaño con el ratón en la interfaz gráfica. El archivo se escribió a mano (el CLI no necesita los metadatos de dibujo); falta confirmar que la interfaz permite dibujarlo y que lo generado es igual. El proyecto en blanco `plantilla_escalera` queda en Descargas para esa prueba.
- El servidor guarda copia del último programa recibido en `scripts_openplc/datos_servidor/ultimo_programa_<placa>.st` (diagnóstico).

### Escalera desde la interfaz gráfica (23 de noviembre)

- `plantilla_escalera` (peldaño `entrada` `%IX0.1` → `salida` `%QX0.1`) escrito por mí con la estructura que usa el editor (rieles `left-rail-…`/`right-rail-…`, manejadores `input`/`output`, aristas, tamaños), abierto en la interfaz: el peldaño se dibuja correctamente (rieles, contacto, bobina, comentario). La tabla de variables aparece vacía hasta cambiar a la vista de código y volver a la de tabla (particularidad del editor al abrir un POU de escalera; no se resolvió). Al guardar con Ctrl+S, el editor reescribió el archivo con la misma estructura (solo cambió el tamaño de vista del peldaño): se adoptó esa versión como plantilla.
- **Build and upload desde la interfaz** (16:08): el servidor recibió `program.st` con `salida := entrada;`, lo compiló y lo cargó. En la placa: reposo `IX0.1`=1 / `QX0.1`=1; con el relé activado por Modbus (abre el NC de D3) `IX0.1`=0 / `QX0.1`=0; al soltar, vuelven a 1. **La escalera dibujada en la interfaz funciona de punta a punta.**

### Puente local: todo entre el PC del alumno y la placa (23 de noviembre)

- **Requisito (usuario):** sin servidor aparte; solo Ubuntu por ahora; lo mínimo de trabajo para el alumno: un script que corra en paralelo al editor y se detenga al cerrarlo.
- **`scripts_openplc/puente_local.py` (nuevo):** reutiliza `servidor_runtime.py`. Escanea las redes privadas del PC (puerto 9101 + respuesta del receptor a la orden `quien`, que contesta «ERROR…»), nombra cada placa `Galileo-XXXX` con los 4 últimos dígitos de su MAC (ARP), le da una dirección local `127.0.0.N` (guardada en `~/.config/galileo-plc/direcciones.json`) y abre su API HTTPS en esa dirección (solo loopback). Responde al descubrimiento del editor únicamente si el pedido viene de una IP del propio PC, con la IP de origen de la placa (`127.0.0.N`). No requiere sudo ni IP virtuales.
- **`lanzar_plc.py` (nuevo, en la raíz):** arranca el puente (con candado para no duplicarlo), abre el editor (busca `OpenPLC*Editor*.AppImage` en Descargas y otras carpetas, o `--editor`/`OPENPLC_EDITOR`) y al salir el editor detiene el puente.
- **Pruebas:** (1) broadcast real desde la IP del PC: una respuesta desde `127.0.0.2` con `Galileo-FA94` (placa en 10.42.0.151, encontrada sola); (2) lanzador con un «editor» simulado de 70 s: puente arriba, puertos 8443 y 33333 ocupados mientras corría, **se detuvo solo y los puertos quedaron libres**; (3) durante esos 70 s, `openplc-cli upload --host 127.0.0.2` con el proyecto `plantilla_escalera`: «Compilation completed successfully», «PLC started», mismo programa que antes (md5 842bc5fd…).
- **No probado:** el lanzador con el editor gráfico real (solo con uno simulado y con el CLI), Search en la interfaz con el puente, varias placas, instalación limpia sin Internet, y la red real del laboratorio. Con DHCP: el puente vuelve a encontrar la placa por escaneo, pero un cambio de IP a mitad de una sesión no se probó.

### D9 oscilando: explicación (23 de noviembre)

- Con la señal del relé de pruebas en **D9** (cable movido temporalmente) y el programa de la plantilla de escalera (`salida` `%QX0.1` = D9 := `entrada` `%IX0.1` = D3), se forma un **oscilador por realimentación**: D9 activa el relé → el contacto NC del mismo relé abre D3 → `entrada`=0 → `salida`=0 → el relé suelta → el NC vuelve a cerrar D3 → … (vibrador). Las lecturas de ese momento mostraban `QX0.1` y `IX0.1` en oposición y cambiantes.
- Con el cable de nuevo en D8 no hay oscilación: 735 lecturas a 50 Hz durante 20 s con la escalera (un solo cambio, el inicial, de las entradas y las salidas por Modbus; D9 y D3 estables también leídos por sysfs en la placa) y 40 s con el ascensor (sin cambios).
- No es una falla de la placa. En la placa de expansión (optoentradas independientes de los relés) no habrá ese lazo salvo que el programa realimente a propósito una salida hacia la entrada que la gobierna. Nota para la plantilla: no conectar el relé a D9 si su contacto va a D3.

### Forzado de entradas y salidas desde el panel (23 de noviembre)

- **Problema:** en el panel, escribir `1` o `0` en una salida no se mantenía: el programa de la plantilla (`luz := pulsador`) la reescribe en cada ciclo de 20 ms. Modbus no permite escribir entradas.
- **Solución:** forzado en la capa de hardware (`hardware_layer_galileo_8e4s.cpp`): cuatro registros reservados (holding registers 2024–2027 = `%MW1000`–`%MW1003`) con máscara y valor de entradas y de salidas; la capa los aplica después de leer las entradas (el programa ve el valor forzado) y antes de escribir las salidas (el pin toma el valor forzado). Se limpian en los primeros 8 s tras arrancar. Panel: botones 1 / 0 / × por punto y «forzar 1 / forzar 0 / soltar» en la tabla, con marca naranja.
- **Pruebas en la placa** (programa `luz := pulsador` compilado con la capa nueva): forzar la entrada a 1 → `pulsador`=1 y `luz`=1; a 0 → ambas 0; forzar la salida a 1 → `luz`=1 aunque la entrada esté a 0; a 0 → 0; soltar → vuelve al comportamiento del programa. Vía API del panel: marcas `fe`/`fs` correctas.
- **Efecto del circuito de prueba:** con el relé de pruebas (`luz` en D8, contacto NO en D2 = `pulsador`), `luz`=1 cierra D2 y **mantiene** `pulsador`=1 aunque se suelte el forzado (auto-retención por el cableado, no un fallo).
- La imagen de la flash no lleva aún el forzado (compilada antes); los programas subidos desde el editor sí.

### Ventana del panel en el lanzador (23 de noviembre)

- `lanzar_plc.py` abre, tras arrancar el puente, una ventana de Firefox de ~600×760 con `http://127.0.0.1:8088`, como instancia aparte (`--no-remote --profile ~/snap/firefox/common/galileo-panel`, para que se respete el tamaño y no se toque el Firefox del usuario). Al detener el lanzador se cierra esa ventana junto con el puente. Opción `--sin-panel`. Probado con un «editor» ausente (`--sin-editor`): se abrió una ventana de 652×812 (con bordes), y al enviar SIGTERM al lanzador se cerraron la ventana y el puente y quedaron libres los puertos. No se probó con el editor real.

### Placas virtuales y fallo de los botones del panel (23 de noviembre)

- **`scripts_openplc/placa_virtual.py` (nuevo):** placas simuladas en loopback (receptor 9100/9101 como el de la imagen, Modbus en 1502, que el receptor anuncia con `puerto=1502`; el puente y el panel usan ese puerto). Probado con dos: el puente las encontró (`Galileo-000B`, `Galileo-000C`), el CLI del editor subió `plantilla_galileo` a una (compilación real) y el panel mostró las variables.
- **Fallo encontrado con el navegador:** el panel reconstruía los botones cada 400 ms y un clic se perdía si la página se redibujaba entre pulsar y soltar (la referencia al botón quedaba obsoleta). Posible causa de «no me deja escribir 1 o 0». **Corregido:** la página construye los botones una vez y solo actualiza valores y marcas (y no sobreescribe el campo de `%MW` mientras se escribe). Comprobado en el navegador: clic en «forzar 0» → `%IX0.0 (forzada)` con borde naranja, `pulsador`=0, `fe`=1.

### Fuentes y descarga de dependencias (23 de noviembre)

- `FUENTES.md` (nuevo) lista cada dependencia externa con origen, versión/commit, SHA-256 y comprobación de disponibilidad. `instalacion/obtener_dependencias.sh` (nuevo) las descarga y verifica.
- **Prueba desde cero** en una carpeta vacía: las cuatro descargas del espejo de archive.org (`.bin`, `.cap`, `CapsuleApp-1.1.1.efi` y la guía de la placa) coincidieron con las sumas de verificación; `intel/Galileo-Runtime` se obtuvo en el commit `ee66e9a3` y `thiagoralves/OpenPLC_v3` en `b5d41356`. El SDK (56 227 185 B) y el editor 4.3.5 (188 322 226 B) responden en sus URL con el tamaño exacto; el editor no se volvió a descargar.
- **Lo que sigue sin ser alcanzable desde otro equipo:** los PDF de referencia de la Galileo (sin versionar en `utn/ltdi/galileo`), `archivo/`, y todo depende de que archive.org mantenga los espejos de Intel.

### Verificación de los enlaces de referencia (23 de noviembre)

- Enlaces aportados por el LTDI contrastados con las copias locales (SHA-256): el esquemático de `dl.btc.pl` y la hoja de la Galileo de `intel.com` son **idénticos** a los archivos de `utn/ltdi/galileo`; `Galileo Schematic.pdf` y `arduino_galileo_e000037_1.pdf` son el mismo archivo (el enlace se repite en la lista). La guía de la placa del sitio oficial de Intel (630 324 B) **no es idéntica** a la del espejo de archive.org (635 057 B): el script usa ahora la oficial. Hoja del CY8C9540A (Arrow), capítulo del libro (Springer) y datasheet del Quark (Mouser): **no verificables desde aquí** (bloqueo anti-robots o corte de conexión). Detalle en `FUENTES.md`.
