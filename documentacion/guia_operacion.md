# Guía de operación del PLC didáctico (Galileo Gen 1)

Procedimientos verificados en la placa el 23/11/2026. Las rutas son relativas a la carpeta del proyecto. Pasos probados salvo donde se indica lo contrario.

## 1. Uso normal

1. Enchufar la fuente (5 V). La placa arranca sola; en 40 a 60 s tiene IP por DHCP y Modbus TCP en el puerto 502. Corre el programa de fábrica, que **deja las cuatro salidas apagadas** (`ejemplos_alumno/programa_fabrica_seguro.st`); se prueba con el panel en vivo (forzando entradas y salidas).
2. Ver el estado: cualquier cliente Modbus a `IP:502`. Entradas = discrete inputs 0–7, salidas = coils 0–3, `%MW` = holding registers desde 1024.
3. **No** enviar señales a OpenPLC (`kill`, `kill -STOP`, `reboot` sin parar antes): cuelgan la placa. Detenerlo siempre con `/etc/init.d/plc.sh stop` o con la orden `quit()` del puerto 43628.

## 2. Cargar un programa de alumno

### Con OpenPLC Editor (camino recomendado, un solo PC)

Todo ocurre entre el PC del alumno y la placa; no hay servidor aparte. Un **puente** (`scripts_openplc/puente_local.py`) corre en el mismo PC que el editor: busca las placas en la red, se las presenta al editor como si fueran runtimes de OpenPLC, compila el programa con matiec y lo carga en la placa. Todo queda en `127.0.0.x` (nada se abre hacia la red).

**Uso del alumno (Ubuntu):**
1. Ejecutar el lanzador: `python3 lanzar_plc.py` (arranca el puente, abre una **ventana pequeña de Firefox con el panel en vivo** y el editor; al cerrar el editor, el puente y la ventana del panel se detienen solos). `--sin-panel` si no se quiere la ventana. El panel usa un perfil propio de Firefox (en `~/snap/firefox/common/galileo-panel`), separado del Firefox de uso normal. Si el editor no está en `~/Descargas`, indicarlo con `--editor RUTA` o con la variable `OPENPLC_EDITOR`.
2. En el editor, abrir una plantilla de `ejemplos_alumno/plantilla_editor/` (copiada fuera de esa carpeta).
3. En la pantalla del dispositivo: **Search** → elegir la placa (aparece como `Galileo-XXXX`, con las 4 últimas cifras de su MAC) → **OK**. Usuario: cualquiera. Contraseña: `plc` (relleno que pide el editor; **no es una cuenta real**).
4. **Build options** (icono de descarga de la barra lateral) → **Build and upload**. En ~15 s el editor informa «PLC started».

**Cómo encuentra las placas:** el puente escanea las redes privadas del PC (hasta /22) buscando el puerto 9101 abierto y una respuesta propia del receptor de la imagen; sirve con DHCP, sin escribir IP en ningún archivo. Cada placa conserva su dirección local (`127.0.0.2`, `.3`, …) entre sesiones (`~/.config/galileo-plc/direcciones.json`). Solo atiende al editor del mismo PC. Registro: `~/.config/galileo-plc/puente.log`. Redes concretas: `--redes 10.0.5.0/24`.

Notas:
- El botón de subir no se llama «Upload»: es el icono de descarga («Build options») → **Build and upload**.
- El editor muestra siempre el PLC como «detenido» (el puente lo informa así para que no pida parar el PLC). No funciona la depuración en vivo del editor.
- Si hay varias placas, el nombre `Galileo-XXXX` se corresponde con la etiqueta de MAC de la placa.

### Alternativa: un servidor central del laboratorio

Mismo mecanismo pero en una PC aparte (`scripts_openplc/servidor_runtime.py`, `placas.json`, `configurar_alias.sh` para las IP virtuales); útil si no se quiere instalar el compilador en cada PC. Requiere IP virtuales en la red del laboratorio (ver sección 9). Probado con dos entradas de descubrimiento y una placa real.

### Sin el editor (línea de comandos)

Requisitos en el PC: Python 3, el compilador cruzado (`~/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc`) y la carpeta `openplc_galileo_8e4s` (estación ya compilada).

```bash
python3 scripts_openplc/plc.py ejemplos_alumno/porton.st --ip 10.42.0.151        # compila y carga
python3 scripts_openplc/plc.py ejemplos_alumno/porton.st --solo-compilar          # solo comprueba
```

- La carga usa los puertos 9100 (ejecutable) y 9101 (`aplicar <md5>`) de la placa; tarda ~10 s.
- Si el programa nuevo muere en menos de 10 s, la placa lo descarta y vuelve al de fábrica.
- El programa vive en RAM: al apagar la placa vuelve el de fábrica.
- Servidor web para el laboratorio (no probado en marcha): `python3 scripts_openplc/servidor_plc.py --puerto 8080 --placas 10.42.0.151`. Sin autenticación: solo en red aislada.

### Adaptador de proyectos del editor (alternativa sin servidor)

El editor guarda cada programa de texto estructurado como `pous/programs/*.st` dentro de la carpeta del proyecto. Para pasar un proyecto del editor a la placa:

```bash
python3 scripts_openplc/proyecto_editor_a_st.py ~/MiProyecto proyecto.st
python3 scripts_openplc/plc.py proyecto.st --ip 10.42.0.151
```

Solo POUs en texto estructurado: la escalera y los bloques gráficos del editor no se convierten (el editor los traduce internamente). Variables ubicadas con `AT %IX0.0` … `%IX0.7` y `%QX0.0` … `%QX0.3`. El editor no puede cargar directamente a esta placa (no hay paquete de placa firmado para la Galileo).

## 3. Reconstruir la imagen

```bash
# 1) núcleo de OpenPLC + programa de fábrica (rutas ABSOLUTAS)
bash scripts_openplc/construir.sh "$PWD/descargas/openplc_v3" "$PWD/openplc_galileo_8e4s" "$PWD/ejemplos_alumno/programa_fabrica_seguro.st"
# 2) imagen firmada (.bin y .cap) con la MAC de la etiqueta de la placa
python3 -I scripts_imagen/construir_imagen.py descargas/flash_1.1.1 descargas/galileo_runtime/sysimage/config/key.pem \
        openplc_galileo_8e4s/openplc 98:4F:EE:00:FA:94 imagen_trabajo/salida
# 3) comprobar firmas
python3 -I scripts_imagen/firma.py verificar imagen_trabajo/salida/Flash-PLC.cap
python3 -I scripts_imagen/firma.py verificar imagen_trabajo/salida/Flash-PLC.cap 224590
python3 -I scripts_imagen/firma.py verificar imagen_trabajo/salida/Flash-PLC.bin 260000
```

Última imagen flasheada (v6): `Flash-PLC.cap` md5 `913afc36b5c08e5737e5d0a90a6c8dac`, `Flash-PLC.bin` md5 `9079add31c60e37ab133fe7841661267`; incluye el forzado de entradas y salidas y el programa de fábrica seguro. La MAC va dentro de la imagen: **una imagen por placa**.

## 4. Flashear una placa (sin Arduino IDE)

La placa debe estar encendida, con red, y con un telnet temporal. Orden obligatorio: **detener OpenPLC antes de reiniciar**.

1. Si la placa tiene la imagen del PLC (sin telnet): subir el ELF de rescate por USB, que abre telnet 30 min y reconfigura la red:
   ```bash
   U=$(echo ~/.arduino15/packages/maxgerhardt/tools/sketchUploader/*)
   /bin/bash --noprofile $U/clupload/cluploadGalileo_linux.sh "$U/x86/bin" "$PWD/telnet_elf/rescate.elf" /dev/ttyACM0
   ```
   (Si dice «Dispositivo ocupado», esperar unos segundos y repetir: el puerto acaba de enumerarse.) El fuente es `telnet_elf/rescate.c`; la IP está fija en 10.42.0.151 y la MAC en el código.
2. En la placa (telnet, usuario `root` sin clave): `modprobe efi_capsule_update`. **Sin este paso no existe `/sys/firmware/efi_capsule`.**
3. Desde el PC, enviar el `.cap` al puerto 9100 de la placa (recibe en `/tmp/openplc.new`) y comprobar `md5sum /tmp/openplc.new`.
4. En la placa:
   ```sh
   /etc/init.d/plc.sh stop             # comprobar que ps ya no muestra openplc
   mkdir -p /lib/firmware && mv -f /tmp/openplc.new /lib/firmware/Flash-PLC.cap
   echo -n Flash-PLC.cap > /sys/firmware/efi_capsule/capsule_path
   echo 1 > /sys/firmware/efi_capsule/capsule_update     # dmesg: "submission success"
   sync; reboot
   ```
5. **No cortar la alimentación** durante los ~150 s siguientes: el firmware aplica la cápsula al reiniciar. La placa vuelve sola con la red y el PLC.
6. Si el paso 4 falla o `dmesg` no dice «submission success», **no reiniciar**.

Si una placa queda sin responder: cortar y restablecer la alimentación (el botón Reboot actúa sobre el procesador pero puede no alcanzar). Se pierde solo la RAM; la flash no cambia.

## 5. Recuperar el acceso a una placa en marcha

El ELF de rescate (paso 1 de la sección 4) abre telnet y deja la red lista. Con telnet: `python3 scripts_openplc/tel.py "comando"`; monitor en vivo: `python3 scripts_openplc/pruebas_placa/flujo.py "comando" 60`.

## 6. Herramientas de diagnóstico (`scripts_openplc/pruebas_placa/`)

| Archivo | Para qué |
|---|---|
| `empujar_ram.py` | copia a la RAM de la placa los archivos de la imagen para probarlos antes de flashear |
| `repetir_aplicar.py` | aplica N veces programas alternados y comprueba Modbus |
| `flujo.py` | corre un comando por telnet mostrando la salida en vivo y avisa si se corta |
| `cysimple.c`, `cyvolcado.c` | vuelcan registros del Cypress (compilar con el compilador cruzado, enviar por 9100). `cyvolcado` usa inicio repetido de I2C y coincidió con un cuelgue: preferir `cysimple`. No congelar OpenPLC con señales |
| `probar_entradas.py` | vigila las 8 entradas por Modbus e imprime cada cambio con el nombre del pin (unir cada pin a GND para probar) |
| `iotest.c` | mide el costo de leer el Cypress por I2C |
| `scripts_openplc/prueba_larga.py` | resistencia con E/S y red a la vez (usar el id de transacción Modbus de 16 bits con vuelta) |

## 7. Problemas conocidos

- Cuelgue con señales a OpenPLC o `reboot` con el PLC corriendo (evitado en la imagen; causa de fondo desconocida).
- El servidor Modbus de OpenPLC pierde sockets si un cliente abre y cierra conexiones muy rápido; el supervisor reinicia a los 900 descriptores.
- OpenPLC termina con un error de segmentación después de `quit()` (inocuo hasta ahora).

## 8. Plantillas del editor (`ejemplos_alumno/plantilla_editor/`)

- `plantilla_galileo`: programa en texto estructurado (`luz := pulsador`).
- `plantilla_escalera`: un peldaño en escalera (`entrada` `%IX0.1` → `salida` `%QX0.1`), guardado por el propio editor.
- Ambas traen la placa «OpenPLC Runtime v3»; la IP del runtime (`10.42.0.1`, la del servidor del laboratorio) la completa **Search**. Copiarlas fuera de la carpeta del proyecto antes de abrirlas (el editor las modifica al guardar).
- Particularidad observada: en un programa de escalera recién abierto la tabla de variables puede verse vacía hasta cambiar a la vista de código y volver a la de tabla.

## 9. Puesta en marcha en el laboratorio (Ubuntu)

Cada PC de alumno necesita lo mismo (se puede copiar una carpeta ya preparada):
1. **OpenPLC Editor 4.3.5** (AppImage) en `~/Descargas` o con `OPENPLC_EDITOR`.
2. El **paquete del proyecto**: `lanzar_plc.py`, `scripts_openplc/`, `openplc_galileo_8e4s/` (estación ya construida), `ejemplos_alumno/plantilla_editor/`.
3. El **compilador cruzado de la Galileo** en `~/.arduino15/packages/maxgerhardt/tools/i586-poky-linux-uclibc/1.6.3+1.0/` (~190 MB; binario x86-64 de Linux; se puede copiar de un PC ya preparado).
4. **Python 3** y **`openssl`** (vienen con Ubuntu).
5. Las placas en la **misma red local** que el PC (el puente no cruza routers ni VLANs) y con la imagen del PLC.

Sin verificar: una instalación limpia de Ubuntu sin Internet (el editor en su primer arranque instala componentes de Arduino); el tamaño de la red real del laboratorio; el lanzador con el editor real (se probó con un editor simulado y con el CLI del editor); varias placas a la vez; Windows (descartado por ahora).

## 10. Ver y forzar variables en vivo

- **Desde el editor (depurador): no funciona todavía.** El depurador de OpenPLC Editor para el destino «Runtime v3» abre una conexión Modbus TCP al puerto 502 de la dirección del runtime (aquí `127.0.0.N`, donde el puente no escucha ese puerto), y además compara el MD5 del programa y usa su propia numeración de variables (no verificadas contra matiec). El núcleo de la placa sí trae las funciones de depuración de OpenPLC v3 (códigos 0x41 a 0x45).
- **Desde el teclado: `python3 monitor_plc.py`** (en la raíz del proyecto). Muestra en una línea las 8 entradas, las 4 salidas y `%MW0..3`, refrescando 4 veces por segundo. Órdenes: `q0 1` / `q1 0` (forzar una salida, si el programa no la escribe), `mw 0 123` (escribir `%MW0`), `salir`. Busca la placa solo, o `--ip`.
- **Con cualquier cliente Modbus TCP** (QModMaster, Modbus Poll, Node-RED, pymodbus) a la IP de la placa, puerto 502: entradas = discrete inputs 0–7, salidas = coils 0–3, `%MW` = holding registers desde 1024.
- **Panel en vivo del puente (nuevo):** con el lanzador en marcha, abrir **http://127.0.0.1:8088** en el navegador. Muestra las 8 entradas y 4 salidas con sus pines, y una tabla con las **variables con nombre del programa que se subió** (las declaradas con `AT %IX…`, `%QX…`, `%MW…`, `%IW…`, `%QW…`), con su valor y, para las salidas y los `%MW`, botones para escribir. Usa una sola conexión Modbus persistente. Las variables internas (sin `AT`) y los `%MX` no se pueden leer por Modbus con este núcleo.

  **Cómo se arma la tabla «variables del programa»** (`panel_vivo.py`):

  | Paso | Qué ocurre |
  |---|---|
  | 1. Nombres | Al hacer *Build and upload*, el puente guarda el texto del programa en la memoria de la placa correspondiente (`placa.st`). `variables_de()` busca con una expresión regular las declaraciones `nombre AT %<I/Q/M><X/W/D>n[.bit] : TIPO`. |
  | 2. Valores | El panel pide `/api/estado` unas 2,5 veces por segundo; el puente lee cada variable por Modbus TCP: `%IX` bobinas de entrada (índice = byte×8+bit), `%QX` bobinas, `%IW` registros de entrada n, `%QW` registros de retención n, `%MW` registros de retención 1024+n. `INT` se lee con signo; los demás tipos, sin signo. |
  | 3. Dibujo | La página actualiza las celdas en su lugar (no reconstruye la tabla), para no perder clics. |

  Limitaciones: solo aparecen las variables con dirección `AT`; `%MX`, `DWORD` y `REAL` se muestran sin valor; los nombres existen **solo si el programa se subió con este puente en esta sesión** (al reiniciar el puente, o con el programa de fábrica, la tabla queda vacía; el estado de las entradas y salidas sí se ve). Los programas en escalera aparecen igual, porque el editor los convierte a texto estructurado antes de subirlos.
- **Forzado (nuevo):** en el panel, cada entrada y cada salida tiene botones **1**, **0** y **×** (soltar); y en la tabla, las variables `%IX0.n` y `%QX0.n` tienen «forzar 1 / forzar 0 / soltar». Forzar impone el valor al punto aunque el programa diga otra cosa (el programa ve la entrada forzada; la salida física toma el valor forzado). Un punto forzado se marca en naranja. Se usa la capa de hardware: cuatro registros reservados `%MW1000` a `%MW1003` (holding registers 2024 a 2027: máscara y valor de las entradas, máscara y valor de las salidas); **no usar `%MW1000`–`%MW1003` en los programas**. Los forzados se borran solos en los primeros 8 s tras arrancar el PLC (para que la memoria retentiva no restaure uno viejo). Requiere que el programa se haya compilado con la capa nueva (los que se suben desde el editor ya la llevan; el programa de fábrica de la flash, no, hasta que se reflashee).
- Sin forzar, escribir una salida desde el panel (o por Modbus) no sirve si el programa la escribe en cada ciclo (`luz := pulsador` la reescribe a los 20 ms).

**Cuidado con la realimentación en las pruebas:** en la plantilla de escalera `salida` es D9 y `entrada` es D3. El relé de pruebas debe ir en **D8** (sus contactos a D2 y D3). Si la señal del relé se conecta a D9, el contacto NC del propio relé alimenta la entrada que gobierna esa salida y la salida oscila (vibrador).

## 11. Placas virtuales (para probar el panel sin la placa real)

`python3 scripts_openplc/placa_virtual.py --n 2` crea dos placas simuladas en loopback (`127.1.0.11`, `127.1.0.12`; Modbus en el puerto 1502, carga en 9100/9101). El puente las encuentra solo (siempre escanea también `127.1.0.0/28`, además de las redes del PC): basta arrancar `placa_virtual.py` y luego el lanzador de siempre. Aparecen en Search y en el panel junto a las placas reales. Si se usa `--redes`, hay que incluir esa red a mano (`--redes 10.42.0.0/24,127.1.0.0/28`). Aparecen como `Galileo-000B` y `Galileo-000C` en Search y en el panel. Cada una simula un PLC sencillo: `%QX0.0..3` siguen a `%IX0.0..3`, `%IX0.0` parpadea sola cada 3 s en la primera, `%MW0` cuenta segundos, `%MW1` las cargas recibidas, y admiten el forzado. **No ejecutan el programa que se les sube** (sirve para revisar la interfaz, el descubrimiento y la carga: sí se compila de verdad).
