# Fuentes y dependencias externas

Todo lo que este repositorio **no** incluye, de dónde sale, cómo se verifica y si se comprobó que sigue disponible. Fecha de la comprobación: **23/11/2026** (respuesta HTTP/tamaño del servidor, o descarga completa donde se indica).

## 1. Se obtienen con `instalacion/obtener_dependencias.sh` y `instalar_compilador.sh`

| Qué | Dónde | Versión / verificación | Para qué | Disponibilidad |
|---|---|---|---|---|
| Imágenes de firmware de la Galileo **1.1.1** (`Flash-missingPDAT-Release-1.1.1.bin` y `.cap`) y `CapsuleApp-1.1.1.efi` | Espejo de archive.org del sitio de descargas de Intel: `https://archive.org/download/downloadcenter.intel.com/downloadmirror.intel.com_Sept20th2019.tar/downloadmirror.intel.com/26418/eng/<archivo>` (redirige a `ia800404.us.archive.org/view_archive.php?...`) | SHA-256 `.bin` `3da41d38…1378`, `.cap` `efdce2e5…8b8d`, `.efi` `0e372b8b…db6b51b` (completos en el script) | base de la imagen del PLC (solo se cambia el initramfs) | respuesta 200 comprobada; descarga completa probada con el script (ver registro). **Las páginas originales de Intel dan 404**; depende del espejo de archive.org |
| *Galileo Board User Guide* (330237-002) | mismo espejo, `…/23962/eng/Galileo_BoardUserGuide_330237_002.pdf` | SHA-256 `734de295…63e1`, 635 057 B | procedimiento de recuperación del firmware, pines | ídem |
| `intel/Galileo-Runtime` | `https://github.com/intel/Galileo-Runtime` | commit `ee66e9a3b21f5fc68068bbe3ab59d0d8ae03a232` | clave de firma por defecto (`sysimage/config/key.pem`), fuentes del BSP (parche de actualización por cápsula EFI, `spi-flash-tools`, `Quark_EDKII`) | repositorio público activo |
| **OpenPLC v3** | `https://github.com/thiagoralves/OpenPLC_v3` | commit `b5d41356dab4aeadca0dd7ca64ba542f870b595d` (abril de 2026); incluye matiec (`utils/matiec_src`) y el generador de enlace | núcleo del PLC y traductor ST → C | repositorio público activo |
| **SDK/compilador cruzado de Intel** (`galileo-toolchain-20150316-linux64.tar.bz2`) | `https://web.archive.org/web/20191119130210if_/https://downloadmirror.intel.com/24806/eng/galileo-toolchain-linux64-1.6.2-1.0.tar.bz2` (también hay versión Windows y macOS en el mismo índice) | SHA-256 `935ccad3eaaec34f5de76eceb0f0ecd1372bdab0b7dc8f4241e8260c6f827b72`, 56 227 185 B | compilar para el Quark (i586, uClibc, GCC 4.7) | respuesta 200 y tamaño exactos comprobados; instalación completa probada con el archivo ya descargado |
| **OpenPLC Editor 4.3.5** (AppImage) | `https://github.com/Autonomy-Logic/openplc-editor/releases/download/v4.3.5/OpenPLC.Editor-4.3.5.AppImage` | SHA-256 `cced27c878bdf992363cff4048a13a877c2f9adcb0676ca73ad54aabb357b4f4`, 188 322 226 B (el tamaño coincide con el de la ficha de la versión) | editor del alumno; GPL-3.0 | versión publicada el 14/11/2026 |

El índice de paquetes de Intel del que sale la dirección del SDK es el de Arduino para la Galileo (`package_i586_revive_local_index.json`, paquete `maxgerhardt`, herramienta `i586-poky-linux-uclibc` 1.6.3+1.0).

## 2. Documentación técnica consultada (no se descarga; las citas están en `documentacion/`)

| Documento | Número / origen | Dónde está hoy |
|---|---|---|
| *Intel Quark SoC X1000 Board Support Package (BSP): Build and Software User Guide* | 329687; `https://cdrdv2-public.intel.com/329687/quark-x1000-bsp-build-sw-rel-user-guide.pdf` | URL pública de Intel (leída completa) |
| *Intel Quark SoC X1000 Datasheet* | 329676 (copia usada: `quark-x1000-datasheet-557894.pdf`) | **copia local en `utn/ltdi/galileo` sin versionar** |
| *Intel Galileo Schematic* | 329682 | **copia local en `utn/ltdi/galileo` sin versionar** |
| *Galileo Datasheet* y *Arduino Galileo* (e000037) | Intel / Arduino | **copias locales en `utn/ltdi/galileo` sin versionar** |
| *Cypress CY8C9540A* | Doc. 38-12036 Rev. *A | **copia local en `utn/ltdi/galileo` sin versionar** |
| Capas Yocto `meta-intel-quark` y `meta-intel-galileo` | `https://git.yoctoproject.org/meta-intel-quark/about/` | abandonadas |
| OpenPLC Editor clásico (archivado) | `https://github.com/thiagoralves/OpenPLC_Editor` | archivado |
| Esquemas de la placa del proyecto (8 optoentradas y 4 relés) | documentos del proyecto del LTDI | **fuera de este repositorio** |

## 3. Lo que NO es alcanzable desde otro equipo (a resolver)

1. **Los PDF de referencia de la Galileo** están como archivos sin seguimiento en `utn/ltdi/galileo`. Habría que versionarlos allí (≈25 MB) o enlazarlos a sus fuentes oficiales.
2. **Dependencia de archive.org**: las imágenes de firmware y el SDK solo se consiguen en los espejos de archive.org (las páginas de Intel ya no existen). Convendría guardar una copia con las sumas de verificación en un almacenamiento propio del laboratorio.
3. **`archivo/`** (prototipos, mediciones iniciales, informes anteriores) queda solo en el equipo de origen.
4. **Las imágenes de flash generadas** (una por placa, con su MAC) y la **estación de compilación** compilada no se versionan: se regeneran con los scripts, o se publican como adjuntos de una versión.
5. El **Windows** del editor y del compilador existen en las mismas fuentes (el SDK trae versión `i686-mingw32`), pero **no se usaron ni probaron**.
