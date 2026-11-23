#!/usr/bin/env python3
"""Figuras del documento actualizado: arquitectura y diagrama de escalera.
Uso: python3 -I figuras.py <directorio_salida>"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
def fuente(t, b=False): return ImageFont.truetype(FB if b else FR, t)

AZUL, AZUL_B = (221, 235, 247), (91, 140, 196)      # ya disponible
VERDE, VERDE_B = (214, 234, 190), (112, 166, 70)    # se desarrolla en el proyecto
GRIS, GRIS_B = (240, 240, 240), (150, 150, 150)
NEGRO = (30, 30, 30)

def texto_centrado(d, caja, txt, f, color=NEGRO, interlinea=6):
    x0, y0, x1, y1 = caja
    lineas = txt.split("\n")
    alt = [d.textbbox((0, 0), l, font=f)[3] for l in lineas]
    total = sum(alt) + interlinea * (len(lineas) - 1)
    y = y0 + (y1 - y0 - total) / 2
    for l, a in zip(lineas, alt):
        w = d.textlength(l, font=f)
        d.text((x0 + (x1 - x0 - w) / 2, y), l, font=f, fill=color)
        y += a + interlinea

def caja(d, x0, y0, x1, y1, txt, relleno, borde, f):
    d.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=relleno, outline=borde, width=3)
    texto_centrado(d, (x0, y0, x1, y1), txt, f)

def flecha(d, p0, p1, doble=False, color=NEGRO, w=4):
    d.line([p0, p1], fill=color, width=w)
    def punta(a, b):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        l = 18
        d.polygon([b, (b[0] - l * math.cos(ang - 0.4), b[1] - l * math.sin(ang - 0.4)),
                   (b[0] - l * math.cos(ang + 0.4), b[1] - l * math.sin(ang + 0.4))], fill=color)
    punta(p0, p1)
    if doble: punta(p1, p0)

# ---------------------------------------------------------------- arquitectura
def arquitectura():
    W, H = 1920, 950
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    ft, fm, fs = fuente(30, True), fuente(25), fuente(22)

    # panel PC
    d.rounded_rectangle((20, 20, 700, 850), radius=24, fill=GRIS, outline=GRIS_B, width=3)
    d.text((50, 36), "PC de desarrollo (Linux)", font=ft, fill=NEGRO)
    caja(d, 60, 100, 660, 215, "Programa en escalera (ladder)\no en texto estructurado (ST)", AZUL, AZUL_B, fm)
    caja(d, 60, 275, 660, 390, "matiec (iec2c)\ntraduce el programa IEC 61131-3 a C", AZUL, AZUL_B, fm)
    caja(d, 60, 450, 660, 620, "Compilador cruzado i586 (GCC 4.7.2)\n+ núcleo de OpenPLC v3\n+ capa de hardware de la Galileo", VERDE, VERDE_B, fm)
    caja(d, 60, 680, 660, 795, "Arduino IDE\n(carga del ejecutable por USB)", AZUL, AZUL_B, fm)
    flecha(d, (360, 215), (360, 275)); flecha(d, (360, 390), (360, 450)); flecha(d, (360, 620), (360, 680))

    # panel placa
    d.rounded_rectangle((780, 20, 1460, 850), radius=24, fill=GRIS, outline=GRIS_B, width=3)
    d.text((810, 36), "Placa Intel Galileo (Linux embebido)", font=ft, fill=NEGRO)
    caja(d, 820, 100, 1420, 215, "Núcleo OpenPLC: ciclo de scan\n(20 ms en las pruebas)", VERDE, VERDE_B, fm)
    caja(d, 820, 290, 1110, 420, "Capa de hardware\n(GPIO por sysfs)", VERDE, VERDE_B, fm)
    caja(d, 1130, 290, 1420, 420, "Servidor Modbus TCP\n(puerto 502)", VERDE, VERDE_B, fm)
    caja(d, 820, 520, 1420, 700, "Placa de entradas y salidas\nSalidas: relés · Entradas: optoacopladores\n(se diseña y construye en el proyecto)", VERDE, VERDE_B, fm)
    flecha(d, (965, 215), (965, 290), doble=True)
    flecha(d, (1275, 215), (1275, 290), doble=True)
    flecha(d, (965, 420), (965, 520), doble=True)

    # carga por USB (PC -> placa)
    flecha(d, (660, 737), (780, 737))
    d.text((540, 800), "USB", font=fs, fill=NEGRO)

    # panel red
    d.rounded_rectangle((1520, 20, 1900, 850), radius=24, fill=GRIS, outline=GRIS_B, width=3)
    d.text((1550, 36), "Red del laboratorio", font=ft, fill=NEGRO)
    caja(d, 1550, 290, 1870, 420, "SCADA, HMI o\ncliente Modbus TCP", AZUL, AZUL_B, fm)
    flecha(d, (1420, 355), (1550, 355), doble=True)
    d.text((1428, 318), "Ethernet", font=fs, fill=NEGRO)

    # leyenda
    d.rectangle((60, 892, 90, 915), fill=AZUL, outline=AZUL_B, width=2)
    d.text((100, 891), "ya disponible", font=fs, fill=NEGRO)
    d.rectangle((320, 892, 350, 915), fill=VERDE, outline=VERDE_B, width=2)
    d.text((360, 891), "se desarrolla o adapta en el proyecto", font=fs, fill=NEGRO)
    im.save(os.path.join(OUT, "arquitectura.png"))

# ---------------------------------------------------------------- escalera
def escalera():
    W, H = 1600, 1080
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    fl, ft, fp = fuente(24), fuente(30, True), fuente(22)
    RI, RD = 70, 1530
    d.line((RI, 90, RI, 940), fill=NEGRO, width=6)
    d.line((RD, 90, RD, 940), fill=NEGRO, width=6)

    def hl(x0, x1, y): d.line((x0, y, x1, y), fill=NEGRO, width=4)
    def vl(x, y0, y1): d.line((x, y0, x, y1), fill=NEGRO, width=4)
    def etiqueta(x, y, txt, arriba=True):
        w = d.textlength(txt, font=fl)
        d.text((x - w / 2, y - 62 if arriba else y + 34), txt, font=fl, fill=NEGRO)
    def contacto(x, y, nom, nc=False, arriba=True):
        vl(x - 14, y - 26, y + 26); vl(x + 14, y - 26, y + 26)
        if nc: d.line((x - 22, y + 30, x + 22, y - 30), fill=NEGRO, width=4)
        if nom: etiqueta(x, y, nom, arriba)
    def bobina(x, y, nom):
        d.ellipse((x - 24, y - 24, x + 24, y + 24), outline=NEGRO, width=4)
        etiqueta(x, y, nom)

    d.text((90, 24), "Programa «contactor supervisado»: peldaños 1 a 3", font=ft, fill=NEGRO)

    # Peldaño 1: enclavamiento con paro dominante
    y1, y1b = 170, 270
    d.text((92, y1 - 78), "1", font=ft, fill=(120, 120, 120))
    hl(RI, 190, y1); vl(190, y1, y1b); hl(190, 330, y1b); hl(190, 330, y1)
    contacto(260, y1, "MARCHA"); contacto(260, y1b, "MOTOR", arriba=False)
    hl(330, 420, y1); hl(330, 420, y1b); vl(420, y1, y1b)
    hl(420, 760, y1); contacto(600, y1, "PARO", nc=True)
    hl(760, 1000, y1); contacto(900, y1, "FALLA_GENERAL", nc=True)
    hl(1000, 1330 - 24, y1)
    bobina(1330, y1, "MOTOR")
    hl(1330 + 24, RD, y1)

    # Peldaño 2: salida física
    y2 = 470
    d.text((92, y2 - 78), "2", font=ft, fill=(120, 120, 120))
    hl(RI, 400, y2); contacto(260, y2, "MOTOR")
    hl(400, 1330 - 24, y2)
    bobina(1330, y2, "RELE (salida D8)")
    hl(1330 + 24, RD, y2)

    # Peldaño 3: supervisión de cierre
    y3, y3b = 690, 790
    d.text((92, y3 - 78), "3", font=ft, fill=(120, 120, 120))
    hl(RI, 400, y3); contacto(200, y3, "RELE")
    hl(400, 600, y3); contacto(420, y3, "NO_CERRADO", nc=True)
    d.rectangle((600, y3 - 55, 770, y3 + 55), outline=NEGRO, width=4, fill=(245, 245, 245))
    d.text((630, y3 - 42), "TON", font=ft, fill=NEGRO)
    d.text((610, y3 + 4), "PT=100 ms", font=fp, fill=NEGRO)
    hl(770, 840, y3)
    vl(840, y3, y3b); hl(840, 1080, y3); hl(840, 1080, y3b); vl(1080, y3, y3b)
    contacto(960, y3, "T_CIERRE.Q"); contacto(960, y3b, "FALLA_NO_CIERRA", arriba=False)
    hl(1080, 1170 - 14, y3); contacto(1170, y3, "RECONOCER", nc=True)
    hl(1170 + 14, 1390 - 24, y3)
    bobina(1390, y3, "FALLA_NO_CIERRA")
    hl(1390 + 24, RD, y3)

    # leyenda
    y = 880
    contacto(150, y + 40, "")
    d.text((190, y + 22), "contacto normalmente abierto", font=fp, fill=NEGRO)
    contacto(620, y + 40, "", nc=True)
    d.text((660, y + 22), "contacto normalmente cerrado", font=fp, fill=NEGRO)
    d.ellipse((1100, y + 16, 1148, y + 64), outline=NEGRO, width=4)
    d.text((1162, y + 22), "bobina (salida)", font=fp, fill=NEGRO)
    d.text((90, 985), "Los peldaños 4 a 7 siguen el mismo esquema: contacto pegado, coherencia NO/NC, falla general y contador de arranques.",
           font=fp, fill=(90, 90, 90))
    d.text((90, 1020), "Nombres tomados del programa en ST (Anexo A). NO_CERRADO es el contacto NO del relé leído por la placa.",
           font=fp, fill=(90, 90, 90))
    im.save(os.path.join(OUT, "escalera.png"))

arquitectura()
escalera()
print("figuras listas en", OUT)
