# Inventario de placas Galileo Gen1

MAC leídas de las etiquetas en fotos del 27/11/2026. **Ninguna de las 8 placas nuevas se encendió ni se flasheó todavía.** No se sabe qué firmware traen.

| MAC | Nombre en Search | Imagen (`imagen_trabajo/placas/…`) | Estado |
|---|---|---|---|
| `98:4F:EE:00:FA:94` | `Galileo-FA94` | `imagen_trabajo/salida/` (v6) | flasheada y probada |
| `98:4F:EE:01:07:A4` | `Galileo-07A4` | `07A4/` | sin flashear |
| `98:4F:EE:01:08:B5` | `Galileo-08B5` | `08B5/` | sin flashear |
| `98:4F:EE:01:0C:A2` | `Galileo-0CA2` | `0CA2/` | sin flashear |
| `98:4F:EE:01:0C:A9` | `Galileo-0CA9` | `0CA9/` | sin flashear |
| `98:4F:EE:01:0D:2D` | `Galileo-0D2D` | `0D2D/` | sin flashear |
| `98:4F:EE:01:0E:95` | `Galileo-0E95` | `0E95/` | sin flashear |
| `98:4F:EE:01:0E:CE` | `Galileo-0ECE` | `0ECE/` | sin flashear |
| `98:4F:EE:01:0E:DE` | `Galileo-0EDE` | `0EDE/` | sin flashear |

**Puente J2:** en las fotos, las 8 placas nuevas dejan libre el pin marcado con el triángulo. Según la guía de la placa (sección 2.5.2), así el expansor de E/S queda en la dirección I2C `0x20`. No moverlo.

## Imágenes

Cada imagen lleva la MAC de su placa: **usar solo la de la carpeta que coincide con la etiqueta.** Cada carpeta tiene `Flash-PLC.cap` y `Flash-PLC.bin`; las sumas están en `imagen_trabajo/placas/MD5SUMS`. La carpeta `imagen_trabajo/` no se sube al repositorio.

Verificado en el PC (27/11/2026), en las 8 imágenes:

| Comprobación | Resultado |
|---|---|
| Firmas del `.cap` (cápsula y disco inicial) y del disco inicial del `.bin` | correctas |
| Resto de la imagen, fuera de lo modificado y firmado | igual a la de Intel 1.1.1 |
| Disco inicial comparado con el de la v6 | cambian solo `etc/plc/mac` y un comentario de `etc/init.d/plc.sh` |

Al reconstruir una imagen, su suma MD5 cambia aunque el contenido sea el mismo: la firma RSA-PSS usa un valor aleatorio. Para comparar dos compilaciones hay que comparar `ramdisk_nuevo.cpio`.

## Antes de flashear

1. El ELF de rescate (`telnet_elf/rescate.c`) tiene **fija la MAC de la placa `FA:94`**. Para otra placa hay que cambiarla en el fuente y recompilar; si no, la placa usa en red una MAC que no es la suya, y se repite si la `FA:94` está en la misma red.
2. Flashear **una sola placa** primero, siguiendo la [guía de operación](guia_operacion.md), sección 4. Comprobar que arranca, que aparece en Search con su nombre y que responden entradas y salidas antes de seguir con las demás.
3. No cortar la alimentación durante el flasheo. No hay todavía forma probada de recuperar una placa que no arranque.
