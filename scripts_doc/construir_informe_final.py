#!/usr/bin/env python3
"""Informe final: PLC didáctico con Intel Galileo Gen 1 (imagen propia en flash).
Uso: python3 construir_informe_final.py <dir_scripts_doc> <salida.docx>"""
import sys, os
sys.path.insert(0, sys.argv[1])
from docx_min import Doc

SALIDA = sys.argv[2]
ESTADO = {"Medido": "E2F0D9", "Probado": "E2F0D9", "Hecho": "E2F0D9", "Resuelto": "E2F0D9", "Documentado": "E2F0D9",
          "Parcial": "FFF2CC", "A verificar": "FFF2CC", "Sin verificar": "FFF2CC", "Abierto": "FBE4D5",
          "Pendiente": "EDEDED", "Inferencia": "EDEDED", "Alto": "FBE4D5", "Medio": "FFF2CC", "Bajo": "E2F0D9"}
d = Doc()

d.p("Laboratorio de Técnicas Digitales e Informática (LTDI)", base_rpr='<w:color w:val="595959"/><w:sz w:val="22"/>')
d.p("PLC didáctico con Intel Galileo Gen 1: estado final", "Title")
d.p("Imagen propia en la memoria flash, sin tarjeta microSD", "Subtitle")
d.p("**Versión del 23 de noviembre de 2026.** Reemplaza al «Reporte 2», al «Reporte: panorama actual y microSD» y al «Proyecto Galileo LTDI – actualizado», "
    "que quedaron en la carpeta {c}archivo/documentos_anteriores{/c}. Los datos de pines y registros están en {c}mapa_pines_galileo_plc.md{/c}; "
    "la bitácora de cada prueba, en {c}registro_pruebas.md{/c}; los procedimientos, en {c}guia_operacion.md{/c}.")

# ============================================================ 1
d.h1("1. Resumen ejecutivo")
d.vinetas([
    "**La placa ya se enciende y funciona como un PLC.** Con una imagen propia grabada en su flash arranca sola (unos 40 a 60 s desde que se enciende), levanta la red, "
    "ejecuta el programa de ejemplo (un ascensor de tres pisos) y atiende **Modbus TCP** en el puerto 502. No usa microSD ni telnet ni Arduino IDE.",
    "**Entradas y salidas:** 8 entradas (D2 a D7, D12, D13; activas a nivel bajo) y 4 salidas (D8 a D11), como pide el proyecto para la placa de expansión de 8 optoentradas y 4 relés. "
    "Las cuatro salidas y las ocho entradas se probaron en la placa (las entradas uniendo cada pin a GND).",
    "**Carga de programas por red** en unos 10 s, sin reprogramar la flash: un receptor dentro de la imagen recibe el ejecutable, verifica su suma de control y reinicia el PLC con el programa nuevo. "
    "Si el programa nuevo falla al arrancar, la placa vuelve sola al de fábrica. Los programas del alumno viven en RAM: al apagar vuelve el de fábrica.",
    "**Software para el alumno:** el editor oficial OpenPLC Editor 4.3.5, sin modificar. Elige su placa de una lista («Search») y sube con «Upload»; un servidor del laboratorio (Ubuntu) compila con matiec y carga en esa placa. "
    "Probado de punta a punta con el CLI del editor y la placa real; falta probar el descubrimiento con varias placas y la interfaz gráfica. Cualquier SCADA o cliente Modbus puede acceder al PLC; **CODESYS, TIA Portal y similares no pueden programarlo.**",
    "**Resistencia:** una hora con E/S y red a la vez, 35 945 consultas Modbus a 10 Hz sin un error, período de scan de 20,0 ms. "
    "Diez cargas seguidas de programas por red, sin fallas.",
    "**El costo fue una serie de cuelgues de la placa** hasta descubrir que cualquier señal a OpenPLC (SIGTERM, SIGSTOP) o un {c}reboot{/c} normal con el PLC corriendo la dejaba colgada. "
    "La causa de fondo no se conoce; la imagen lo evita deteniendo el PLC con la orden {c}quit(){/c} antes de apagar o reiniciar.",
])

# ============================================================ 2
d.h1("2. Qué contiene la placa")
d.tabla([
    ["Componente", "Qué hace", "Estado"],
    ["Imagen en flash (firmware 1.1.1 de Intel con el initramfs modificado)", "Se aplicó por cápsula EFI desde Linux. Solo cambia el initramfs: se quitó Bluetooth, se agregaron OpenPLC, la MAC de la etiqueta y los scripts de arranque. Firmada con la clave por defecto de Intel, la misma de las imágenes originales; el firmware la aceptó.", "Probado"],
    ["{c}plc.sh{/c} (nivel 5, S85)", "Supervisor: lanza OpenPLC, lo relanza si muere, si supera 900 descriptores de archivo, si Modbus no responde en 3 comprobaciones seguidas, y recorta el log de RAM a 256 KB. Lo detiene con la orden {c}quit(){/c}, sin señales (último recurso: {c}kill -9{/c} tras 8 s). Apaga las salidas en cada reinicio. Espera a que exista {c}/dev/i2c-0{/c} antes de lanzar.", "Probado"],
    ["Red", "Fija la MAC de la etiqueta (la placa arrancaba con 00:00:…) y pide IP por DHCP. Una placa por imagen: la MAC va dentro.", "Probado"],
    ["OpenPLC v3 (núcleo para i586/uClibc)", "Ejecutable de 54 KB con el programa del alumno incluido; capa de hardware propia de 8 entradas y 4 salidas; Modbus TCP; memoria retentiva (en RAM).", "Probado"],
    ["Receptor de programas", "Dos {c}tcpsvd{/c} de BusyBox: el 9100 recibe el ejecutable; el 9101 recibe {c}aplicar <md5>{/c}, verifica y reinicia el PLC con el programa nuevo. Sin autenticación.", "Probado"],
    ["Parada ordenada", "Enlaces {c}rc6.d/K15{/c} y {c}rc0.d/K15{/c}: antes de reiniciar o apagar se detiene OpenPLC con {c}quit(){/c}.", "Probado"],
], [2300, 5812, 1300], relleno_col=(2, ESTADO))
d.p("Recursos medidos: el initramfs conserva su tamaño original y quedan unos 88 KB libres; la RAM total es de 238 MB y con el PLC corriendo quedan unos 178 MB libres.")

# ============================================================ 3
d.h1("3. Pines y su configuración")
d.tabla([
    ["Pin", "Función", "Dirección IEC", "GPIO Linux", "Dónde está"],
    ["D2", "Entrada 1", "%IX0.0", "14", "SoC (mux a gpio31)"],
    ["D3", "Entrada 2", "%IX0.1", "15", "SoC (mux a gpio30)"],
    ["D4", "Entrada 3", "%IX0.2", "28", "Cypress puerto 1, bit 4"],
    ["D5", "Entrada 4", "%IX0.3", "17", "Cypress puerto 0, bit 1"],
    ["D6", "Entrada 5", "%IX0.4", "24", "Cypress puerto 1, bit 0"],
    ["D7", "Entrada 6", "%IX0.5", "27", "Cypress puerto 1, bit 3"],
    ["D12", "Entrada 7", "%IX0.6", "38", "Cypress puerto 3, bit 2 (mux gpio54)"],
    ["D13", "Entrada 8", "%IX0.7", "39", "Cypress puerto 3, bit 3 (mux gpio55)"],
    ["D8", "Salida 1 (relé de pruebas)", "%QX0.0", "26", "Cypress puerto 1, bit 2"],
    ["D9", "Salida 2", "%QX0.1", "19", "Cypress puerto 0, bit 3"],
    ["D10", "Salida 3", "%QX0.2", "16", "Cypress puerto 0, bit 0 (mux gpio42)"],
    ["D11", "Salida 4", "%QX0.3", "25", "Cypress puerto 1, bit 1 (mux gpio43)"],
], [800, 2200, 1500, 1100, 3812])
d.vinetas([
    "**No son GPIO exclusivos:** D2/D3 y D10 a D13 pasan por conmutadores analógicos que los conectan al SoC, al Cypress o al SPI (esquemático de la placa). D3, D5, D6, D9, D10 y D11 son los pines con PWM posible; el PLC los usa como GPIO y deja el PWM apagado.",
    "**Entradas del Cypress:** la Galileo las deja en alta impedancia (flotantes, leídas como «activas»). La capa de hardware les pone pull-up resistivo por I2C y **verifica leyendo de vuelta** (en el arranque las primeras transacciones se pierden).",
    "**Regla de la placa:** {c}echo low > direction{/c} no fija el nivel; hay que poner {c}direction=out{/c} y escribir {c}value{/c} por separado.",
    "Detalle de puertos, máscaras de bit, registros del Cypress y valores medidos: {c}mapa_pines_galileo_plc.md{/c}.",
])

# ============================================================ 4
d.h1("4. Cómo se programa y se accede")
d.h2("4.1 Flujo del alumno")
d.numerada([
    "Ejecuta el lanzador ({c}python3 lanzar_plc.py{/c}): abre OpenPLC Editor 4.3.5 y arranca en paralelo un puente a la Galileo; al cerrar el editor, el puente se detiene solo.",
    "Abre la plantilla del laboratorio (placa fijada en «OpenPLC Runtime v3») y programa en texto estructurado, escalera o bloques.",
    "En la pantalla del dispositivo pulsa «Search»: aparece cada Galileo encendida de la red (como {c}Galileo-XXXX{/c}, con las últimas cifras de su MAC); elige la suya y usa Build options → Build and upload. En unos 15 s el editor informa «PLC started».",
])
d.p("El puente ({c}scripts_openplc/puente_local.py{/c}, solo biblioteca estándar de Python) corre en el mismo PC que el editor: busca las placas escaneando la red local (puerto de carga abierto y respuesta propia de la imagen), las anuncia al editor como si fueran runtimes de OpenPLC con direcciones {c}127.0.0.N{/c}, compila el texto estructurado con matiec y lo carga en la placa elegida. "
    "No hace falta servidor aparte, ni IP virtuales, ni sudo, ni escribir las IP de las placas (sirve con DHCP). Solo se abre algo en el propio PC (loopback). "
    "**Probado en la placa real:** descubrimiento, y Build and upload con el CLI del editor oficial a través del puente (compilación y carga correctas), además de la interfaz gráfica con el servidor central (alternativa). El lanzador se probó con un editor simulado: arranca el puente y lo detiene al cerrar. **Sin probar:** el lanzador con el editor gráfico real, varias placas a la vez, una instalación limpia sin Internet y Windows (por ahora solo Ubuntu). El editor muestra el PLC siempre como «detenido» y no hay depuración en vivo.")
d.h2("4.2 Compatibilidad con software de PLC")
d.tabla([
    ["Herramienta", "¿Acceso?", "¿Programación?", "Comentario"],
    ["SCADA / HMI / Node-RED / Modbus Poll / pymodbus", "Sí", "–", "Modbus TCP, puerto 502: 8 entradas discretas, 4 bobinas, registros {c}%MW{/c} desde la dirección 1024."],
    ["CODESYS, TIA Portal, Studio 5000 como maestro Modbus", "Sí", "–", "Leen y escriben las E/S de esta placa."],
    ["OpenPLC Editor 4.x", "–", "Sí: texto, escalera y bloques", "Sube a un puente local que imita su runtime v3 (sección 4.1); el editor mismo traduce los lenguajes gráficos a texto. Un paquete de placa propio exigiría la firma de Autonomy Logic, por eso se usa este camino."],
    ["CODESYS, TIA Portal, Studio 5000, GX Works como entorno de programación", "–", "No", "Programan sus propios runtimes. Habría que instalar uno en la placa: licencia y Linux más nuevo que el 3.8.7."],
    ["LDmicro (escalera a C para Arduino)", "–", "No conectado", "Los documentos del proyecto lo usan en la Gen 2; no se integró con esta imagen."],
], [2800, 1100, 1700, 3812], relleno_col=None)

# ============================================================ 5
d.h1("5. Resultados de las pruebas")
d.tabla([
    ["Prueba", "Resultado", "Estado"],
    ["Una hora con E/S y red a la vez", "35 945 consultas Modbus a 10 Hz, 0 errores; latencia p50 1,26 ms, p99 1,49 ms, un solo pico de 1025 ms. Scan medio 20,0 ms (capa anterior de 1 relé: máximo 93,6 ms y 1 ciclo > 25 ms en una hora).", "Medido"],
    ["Diez cargas seguidas por red (placa real)", "10 de 10 aplicadas, Modbus respondiendo 12 s después de cada una. Con un programa que sale al instante: se descarta y vuelve el de fábrica.", "Probado"],
    ["Salidas D8 a D11", "Las cuatro conmutan al ordenarlas por Modbus; D8 cierra D2 (NO) y abre D3 (NC) del relé conectado.", "Probado"],
    ["Entradas en reposo", "Con el pull-up verificado quedan todas en reposo salvo D3 (por el contacto NC del relé).", "Probado"],
    ["Arranque desde la flash", "Tras cortar la alimentación o con {c}reboot{/c}: red y Modbus solos, sin intervención.", "Probado"],
    ["Entradas D4 a D7, D12 y D13 con un contacto a GND", "Cada pin se activa al unirlo a GND y se desactiva al soltarlo (D12 con un rebote del cable a mano). D2 y D3 ya se probaban con el relé.", "Probado"],
    ["Ascensor con entradas reales", "El programa corre; faltan las entradas físicas.", "Sin verificar"],
    ["Interrupción de las salidas en un reinicio del supervisor", "No se midió.", "Sin verificar"],
    ["Recuperación si una imagen no arranca", "Existe en el firmware, pero falta el archivo FVMAIN.fv y no hay consola serie probada.", "Pendiente"],
], [3000, 5412, 1000], relleno_col=(2, ESTADO))

# ============================================================ 6
d.h1("6. Problemas encontrados y cómo se resolvieron")
d.tabla([
    ["Problema", "Causa y solución", "Estado"],
    ["Cuelgues de la placa (cinco en total)", "Coincidieron con {c}kill{/c} (SIGTERM), {c}kill -STOP{/c}, un {c}reboot{/c} normal con OpenPLC corriendo y, tras la prueba con el editor, con el reinicio del supervisor por exceso de descriptores (el sondeo del estado abría una conexión Modbus por segundo). Con {c}quit(){/c} por el puerto de control todo funciona; el supervisor ya no usa señales. La causa de fondo no se conoce. Los cortes de alimentación hicieron perder RAM, no flash.", "Resuelto (evitado)"],
    ["Errores Modbus en las pruebas de una hora", "Eran del cliente de prueba: el identificador de transacción de 16 bits se desbordaba a las 65 535 peticiones. Corregido y repetida la hora completa.", "Resuelto"],
    ["Servidor Modbus de OpenPLC pierde sockets", "Si un cliente abre y cierra conexiones muy rápido se llega al límite de 1024 descriptores y deja de responder. El supervisor reinicia a los 900 (ahora con {c}quit(){/c}; ese reinicio por descriptores no se pudo probar). El servidor del laboratorio ya no sondea la placa por segundo. En uso normal con conexión persistente no ocurre.", "Parcial"],
    ["Entradas D4 y D5 leídas como activas tras el arranque", "Las primeras transacciones I2C del arranque se perdían y el pull-up no quedaba aplicado. Ahora se verifica leyendo de vuelta y se reintenta.", "Resuelto"],
    ["Pull-up mal calculado para D12 y D13", "El puerto del Cypress se calculaba con 8 bits por puerto; los puertos 2 y 5 tienen 4. Corregido con la tabla del esquemático.", "Resuelto"],
    ["OpenPLC termina con un error de segmentación después de {c}quit(){/c}", "Visible en {c}dmesg{/c} en cada recarga de programa; el supervisor igual lo relanza. No investigado.", "Abierto"],
    ["Programas de alumno solo en RAM", "Al apagar vuelve el de fábrica. Guardarlo exigiría reprogramar la flash entera (minutos y riesgo) o desarrollo propio.", "Abierto"],
], [2700, 5712, 1000], relleno_col=(2, ESTADO))

# ============================================================ 7
d.h1("7. Riesgos y límites")
d.vinetas([
    "**Sin red de seguridad si el kernel no arranca:** la modificación toca solo el initramfs, y se validó el arranque real; pero no hay {c}FVMAIN.fv{/c} ni consola serie comprobada para la recuperación del firmware. "
    "Si la placa queda con Linux funcionando, se puede volver a flashear por USB y red (el ELF de rescate de 6 KB lo demostró varias veces).",
    "**Un corte de energía durante la actualización de la cápsula** puede dejar la placa inutilizable; no se probó. Se recomienda no cortar la alimentación durante los ~150 s posteriores al reinicio.",
    "**Seguridad de red:** Modbus TCP y el receptor de programas no tienen autenticación; cualquiera en la red puede cargar un programa que corre como administrador. Solo para una red de laboratorio aislada.",
    "**Determinismo:** el kernel tiene un tick de 10 ms (HZ=100); el scan es de 20 ms con un máximo observado de 94 ms. Adecuado para ejercicios didácticos, no para control rápido.",
    "**Una imagen por placa:** la MAC está dentro de la imagen; cada placa necesita la suya.",
    "**Retención:** la memoria retentiva de OpenPLC se guarda en RAM y se pierde al apagar.",
])

# ============================================================ 8
d.h1("8. Próximos pasos recomendados")
d.numerada([
    "**Probar el ascensor completo con la placa de optoentradas del proyecto** (las entradas ya se probaron con puentes a GND) y confirmar la polaridad de la placa de relés.",
    "**Poner en marcha el servidor del laboratorio con las IP virtuales** y probar con la interfaz gráfica del editor, con Windows 10 y con varias placas; escribir una guía corta para alumnos.",
    "**Conseguir {c}FVMAIN.fv{/c} y una consola serie** antes de flashear más placas.",
    "**Decidir la persistencia de los programas de alumno** (EEPROM para programas diminutos, o recarga automática desde el servidor al arrancar).",
    "**Investigar el cuelgue con señales y el error de segmentación al cerrar OpenPLC**, o activar el watchdog del Quark (sección 21.14 del datasheet; el kernel de Intel no trae el controlador) para que la placa se reinicie sola.",
    "**Corregir el servidor Modbus** para que no pierda sockets, si se espera que lo usen varios clientes.",
])

# ============================================================ 9
d.h1("9. Fuentes y archivos")
d.vinetas([
    "Intel, Quark X1000 BSP Build and Software User Guide; Intel Galileo Board User Guide (330237); Quark SoC X1000 Datasheet (329676); Galileo Schematic (329682); Cypress CY8C9540A (38-12036).",
    "Repositorio {c}intel/Galileo-Runtime{/c} (herramientas y firmware 1.1.1) y las imágenes {c}Flash-missingPDAT-Release-1.1.1.{bin,cap}{/c}.",
    "OpenPLC v3 (núcleo) y matiec (traductor de IEC 61131-3 a C).",
    "Código del proyecto: {c}scripts_imagen/{/c} (construcción y firma de la imagen), {c}scripts_openplc/{/c} (capa de hardware, compilador del alumno, cargador, servidor), {c}telnet_elf/{/c} (ELF de rescate).",
    "Todo lo anterior a esta versión (prototipos de Arduino, mediciones iniciales, la estación de OpenPLC de un relé, informes previos) está en {c}archivo/{/c}.",
])
d.p("**Límites del informe:** las cifras de tiempos son de una sola placa y una sola fuente de alimentación; las pruebas de hardware se hicieron con un único relé conectado.",
    base_rpr='<w:i/><w:sz w:val="19"/>')

d.guardar(SALIDA, titulo="PLC didáctico con Intel Galileo Gen 1: estado final", autor="LTDI",
          encabezado="Proyecto Galileo LTDI — Informe final (23/11/2026)")
print("listo:", SALIDA)
