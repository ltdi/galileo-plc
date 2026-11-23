# Fuentes y dependencias externas

Todo lo que este repositorio **no** incluye, de dónde sale, cómo se verifica y si se comprobó que sigue disponible. Fecha de la comprobación: **23/11/2026** (respuesta HTTP/tamaño del servidor, o descarga completa donde se indica).

## 1. Se obtienen con `instalacion/obtener_dependencias.sh` y `instalar_compilador.sh`

| Qué | Dónde | Versión / verificación | Para qué | Disponibilidad |
|---|---|---|---|---|
| Imágenes de firmware de la Galileo **1.1.1** (`Flash-missingPDAT-Release-1.1.1.bin` y `.cap`) y `CapsuleApp-1.1.1.efi` | Espejo de archive.org del sitio de descargas de Intel: `https://archive.org/download/downloadcenter.intel.com/downloadmirror.intel.com_Sept20th2019.tar/downloadmirror.intel.com/26418/eng/<archivo>` (redirige a `ia800404.us.archive.org/view_archive.php?...`) | SHA-256 `.bin` `3da41d38…1378`, `.cap` `efdce2e5…8b8d`, `.efi` `0e372b8b…db6b51b` (completos en el script) | base de la imagen del PLC (solo se cambia el initramfs) | respuesta 200 comprobada; descarga completa probada con el script (ver registro). **Las páginas originales de Intel dan 404**; depende del espejo de archive.org |
| *Galileo Board User Guide* (330237-002) | `https://cdrdv2-public.intel.com/841680/galileo_boarduserguide_330237_002.pdf` (sitio oficial de Intel; sigue en línea) | SHA-256 `cb6af1bd6116ef1b93190d3eb16e6a3a1d74dea5312bbbc513201b1dc72961be`, 630 324 B | procedimiento de recuperación del firmware, pines | respuesta 200 y descarga completa comprobadas |
| `intel/Galileo-Runtime` | `https://github.com/intel/Galileo-Runtime` | commit `ee66e9a3b21f5fc68068bbe3ab59d0d8ae03a232` | clave de firma por defecto (`sysimage/config/key.pem`), fuentes del BSP (parche de actualización por cápsula EFI, `spi-flash-tools`, `Quark_EDKII`) | repositorio público activo |
| **OpenPLC v3** | `https://github.com/thiagoralves/OpenPLC_v3` | commit `b5d41356dab4aeadca0dd7ca64ba542f870b595d` (abril de 2026); incluye matiec (`utils/matiec_src`) y el generador de enlace | núcleo del PLC y traductor ST → C | repositorio público activo |
| **SDK/compilador cruzado de Intel** (`galileo-toolchain-20150316-linux64.tar.bz2`) | `https://web.archive.org/web/20191119130210if_/https://downloadmirror.intel.com/24806/eng/galileo-toolchain-linux64-1.6.2-1.0.tar.bz2` (también hay versión Windows y macOS en el mismo índice) | SHA-256 `935ccad3eaaec34f5de76eceb0f0ecd1372bdab0b7dc8f4241e8260c6f827b72`, 56 227 185 B | compilar para el Quark (i586, uClibc, GCC 4.7) | respuesta 200 y tamaño exactos comprobados; instalación completa probada con el archivo ya descargado |
| **OpenPLC Editor 4.3.5** (AppImage) | `https://github.com/Autonomy-Logic/openplc-editor/releases/download/v4.3.5/OpenPLC.Editor-4.3.5.AppImage` | SHA-256 `cced27c878bdf992363cff4048a13a877c2f9adcb0676ca73ad54aabb357b4f4`, 188 322 226 B (el tamaño coincide con el de la ficha de la versión) | editor del alumno; GPL-3.0 | versión publicada el 14/11/2026 |

El índice de paquetes de Intel del que sale la dirección del SDK es el de Arduino para la Galileo (`package_i586_revive_local_index.json`, paquete `maxgerhardt`, herramienta `i586-poky-linux-uclibc` 1.6.3+1.0).

## 2. Documentación técnica de referencia (PDF)

Enlaces aportados por el LTDI (sin los parámetros de seguimiento `utm_source=…`). «Copia local» = archivo en `utn/ltdi/galileo` (sin versionar); no se redistribuyen desde este repositorio. Comprobación del 23/11/2026.

| Documento | Enlace | Comprobación | Copia local (SHA-256, tamaño) |
|---|---|---|---|
| Cypress CY8C9540A, *20-, 40-, and 60-Bit I/O Expander with EEPROM* (Doc. 38-12036 Rev. *A, 25 págs.) | https://static6.arrow.com/aropdfconversion/4ff63fde2cf55e2187d4576526e7e941d8943b00/cy8c9540_8.pdf | **no verificado**: el servidor cortó la conexión (curl error 92, también con HTTP/1.1) | `cy8c9540_8.pdf` · `f2df476f…525cbc` · 396 193 B |
| Libro *Intel Galileo…* (Apress, ISBN 978-1-4302-6838-3), capítulo 4: identificación del expansor | https://link.springer.com/chapter/10.1007/978-1-4302-6838-3_4 | **no verificado**: la editorial devuelve una página de desafío anti-robots (no es un PDF; el acceso al capítulo puede requerir suscripción) | `978-1-4302-6838-3.pdf` · `1646f950…e1573` · 16 822 950 B · 665 págs. (**libro con derechos de autor: no redistribuir**) |
| Esquemático de la Galileo (27 págs.; orden de Intel 329682-001US): secciones del expansor, SPI, ADC y flash | https://dl.btc.pl/kamami_wa/arduino_galileo_e000037_1.pdf (copia de Kamami) | **verificado**: PDF de 1 019 484 B, **idéntico** a las copias locales | `arduino_galileo_e000037_1.pdf` y `Galileo Schematic.pdf` · `ab0925c3…c0681` (el mismo archivo con dos nombres) |
| Intel Galileo Gen 1 *Feature Sheet* / datasheet (13 págs.) | https://www.intel.com/content/dam/www/public/us/en/documents/datasheets/galileo-g1-datasheet.pdf | **verificado con otra herramienta** (`curl` recibe «Access Denied» 403; la descarga normal funciona): **idéntico** a la copia local | `galileo-g1-datasheet.pdf` · `967161a9…93671c` · 607 296 B |
| *Intel Galileo Board User Guide* 330237-002 (20 págs.) | https://cdrdv2-public.intel.com/841680/galileo_boarduserguide_330237_002.pdf | **verificado**: PDF de 630 324 B, SHA-256 `cb6af1bd…961be`. Mismo título y páginas que la copia del espejo de archive.org (635 057 B), pero **no son idénticos byte a byte** (dos versiones del PDF) | la guía de `descargas/guia_placa/` (espejo de archive.org) · `734de295…63e1` |
| *Intel Quark SoC X1000 Datasheet* (doc. 329676, 935 págs.) | https://www.mouser.com/datasheet/2/612/quark-x1000-datasheet-557894.pdf | **no verificado**: Mouser bloquea la descarga automática («Access Denied»/tiempo agotado) | `quark-x1000-datasheet-557894.pdf` · `9f3ddb32…728c` · 6 220 962 B |

Otras fuentes citadas en la documentación:

| Documento | Dónde |
|---|---|
| *Intel Quark SoC X1000 BSP: Build and Software User Guide* (329687) | `https://cdrdv2-public.intel.com/329687/quark-x1000-bsp-build-sw-rel-user-guide.pdf` (leída completa) |
| Capas Yocto `meta-intel-quark` y `meta-intel-galileo` | `https://git.yoctoproject.org/meta-intel-quark/about/` (abandonadas) |
| OpenPLC Editor clásico (archivado) | `https://github.com/thiagoralves/OpenPLC_Editor` |
| Esquemas de la placa del proyecto (8 optoentradas y 4 relés) | documentos del proyecto del LTDI: **fuera de este repositorio** |

## 3. Lo que NO es alcanzable desde otro equipo (a resolver)

1. **Los PDF de referencia de la Galileo** están como archivos sin seguimiento en `utn/ltdi/galileo`. De los enlaces recibidos están comprobados el esquemático y la hoja de la Galileo (idénticos a las copias locales) y la guía de la placa; **la hoja del CY8C9540A, el capítulo del libro y el datasheet del Quark no se pudieron verificar en línea** (bloqueo anti-robots o corte de conexión), de modo que hoy solo existe su copia local. Habría que versionarlos en un lugar propio del laboratorio.
2. **Dependencia de archive.org**: las imágenes de firmware y el SDK solo se consiguen en los espejos de archive.org (las páginas de Intel ya no existen). Convendría guardar una copia con las sumas de verificación en un almacenamiento propio del laboratorio.
3. **`archivo/`** (prototipos, mediciones iniciales, informes anteriores) queda solo en el equipo de origen.
4. **Las imágenes de flash generadas** (una por placa, con su MAC) y la **estación de compilación** compilada no se versionan: se regeneran con los scripts, o se publican como adjuntos de una versión.
5. El **Windows** del editor y del compilador existen en las mismas fuentes (el SDK trae versión `i686-mingw32`), pero **no se usaron ni probaron**.
