"""Constructor minimo de .docx (XML directo, sin dependencias).
Soporta: estilos, parrafos con negrita/cursiva/codigo/hipervinculos, listas, tablas, imagenes,
encabezado y pie con numeracion. Pensado para documentos de texto con tablas y figuras."""
import re, zipfile, struct
from xml.sax.saxutils import escape

EMU_CM = 360000
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')

def tamano_imagen(ruta):
    from PIL import Image
    with Image.open(ruta) as im:
        return im.size

class Doc:
    def __init__(self, fuente="Arial", color_h1="1F3864", color_h2="2F5496"):
        self.cuerpo = []
        self.rels = []        # (id, tipo, destino, externo)
        self.medios = []      # (nombre_en_zip, ruta_origen)
        self.nums = []        # instancias de numeracion decimal
        self._rid = 10
        self._img = 0
        self._bm = 0
        self.fuente = fuente
        self.c1, self.c2 = color_h1, color_h2
        # A4 con margenes de 2,2 cm
        self.ancho_pag, self.alto_pag, self.margen = 11906, 16838, 1247
        self.ancho = self.ancho_pag - 2 * self.margen

    # ------------------------------------------------------------ texto en linea
    def _rid_nuevo(self):
        self._rid += 1
        return "rId%d" % self._rid

    def runs(self, texto, base=""):
        """Marcas: **negrita**, {i}cursiva{/i}, {c}codigo{/c}, {u}url{/u}."""
        out = []
        patron = re.compile(r"(\*\*.+?\*\*|\{i\}.+?\{/i\}|\{c\}.+?\{/c\}|\{u\}.+?\{/u\})", re.S)
        for trozo in patron.split(texto):
            if not trozo:
                continue
            if trozo.startswith("**"):
                out.append(self._run(trozo[2:-2], base + "<w:b/>"))
            elif trozo.startswith("{i}"):
                out.append(self._run(trozo[3:-4], base + "<w:i/>"))
            elif trozo.startswith("{c}"):
                out.append(self._run(trozo[3:-4], base + '<w:rFonts w:ascii="Liberation Mono" w:hAnsi="Liberation Mono" w:cs="Liberation Mono"/><w:sz w:val="18"/>'))
            elif trozo.startswith("{u}"):
                url = trozo[3:-4]
                rid = self._rid_nuevo()
                self.rels.append((rid, "hyperlink", url, True))
                out.append('<w:hyperlink r:id="%s">%s</w:hyperlink>' % (
                    rid, self._run(url, base + '<w:color w:val="0563C1"/><w:u w:val="single"/>')))
            else:
                out.append(self._run(trozo, base))
        return "".join(out)

    def _run(self, txt, rpr):
        return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (
            ("<w:rPr>%s</w:rPr>" % rpr) if rpr else "", escape(txt))

    # ------------------------------------------------------------ bloques
    def p(self, texto, estilo=None, align=None, extra_ppr="", base_rpr="", unir=False):
        ppr = "<w:keepNext/>" if unir else ""
        if estilo: ppr += '<w:pStyle w:val="%s"/>' % estilo
        ppr += extra_ppr
        if align: ppr += '<w:jc w:val="%s"/>' % align
        self.cuerpo.append("<w:p>%s%s</w:p>" % (("<w:pPr>%s</w:pPr>" % ppr) if ppr else "", self.runs(texto, base_rpr)))

    def h1(self, t, salto=False): self.p(t, "Heading1", extra_ppr="<w:pageBreakBefore/>" if salto else "")
    def h2(self, t): self.p(t, "Heading2")
    def h3(self, t): self.p(t, "Heading3")

    def vinetas(self, items):
        for it in items:
            self.p(it, "ListParagraph", extra_ppr='<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')

    def numerada(self, items):
        self.nums.append(len(self.nums) + 2)      # numId 2, 3, ...
        nid = self.nums[-1]
        for it in items:
            self.p(it, "ListParagraph", extra_ppr='<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % nid)

    def salto(self):
        self.cuerpo.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    def imagen(self, ruta, ancho_cm, pie=None):
        w, h = tamano_imagen(ruta)
        cx = int(ancho_cm * EMU_CM)
        cy = int(cx * h / w)
        self._img += 1
        ext = ruta.rsplit(".", 1)[-1].lower()
        nombre = "image%d.%s" % (self._img, "jpeg" if ext in ("jpg", "jpeg") else "png")
        self.medios.append((nombre, ruta))
        rid = self._rid_nuevo()
        self.rels.append((rid, "image", "media/" + nombre, False))
        dib = ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
               '<wp:docPr id="%d" name="Imagen %d" descr="%s"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
               '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
               '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
               '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (
            cx, cy, self._img, self._img, escape(pie or nombre), self._img, nombre, rid, cx, cy)
        self.cuerpo.append('<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="60"/><w:jc w:val="center"/></w:pPr>%s</w:p>' % dib)
        if pie:
            self.p(pie, "Caption", align="center")

    def tabla(self, filas, anchos, encabezado=True, relleno_col=None, tam=18):
        """filas: lista de listas de str (admiten marcas). anchos en DXA (suma = ancho util).
        relleno_col: (indice_col, {texto_inicial: 'RRGGBB'}) para colorear segun el estado."""
        assert abs(sum(anchos) - self.ancho) < 40, (sum(anchos), self.ancho)
        borde = ''.join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' % l
                        for l in ("top", "left", "bottom", "right", "insideH", "insideV"))
        x = ['<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblBorders>%s</w:tblBorders>'
             '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="50" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
             '<w:bottom w:w="50" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr>' % (sum(anchos), borde)]
        x.append("<w:tblGrid>%s</w:tblGrid>" % "".join('<w:gridCol w:w="%d"/>' % a for a in anchos))
        for i, fila in enumerate(filas):
            enc = encabezado and i == 0
            x.append("<w:tr>%s" % ('<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if enc else '<w:trPr><w:cantSplit/></w:trPr>'))
            for j, celda in enumerate(fila):
                fill = None
                if enc: fill = "D9E2F3"
                elif relleno_col and j == relleno_col[0]:
                    for ini, col in relleno_col[1].items():
                        if celda.replace("*", "").startswith(ini): fill = col
                shd = '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill if fill else ""
                base = '<w:sz w:val="%d"/>' % tam + ("<w:b/>" if enc else "")
                parrafos = celda.split("\n")
                ps = "".join('<w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr>%s</w:p>' % self.runs(t, base) for t in parrafos)
                x.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>%s</w:tc>' % (anchos[j], shd, ps))
            x.append("</w:tr>")
        x.append("</w:tbl>")
        self.cuerpo.append("".join(x))
        self.cuerpo.append('<w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>')

    # ------------------------------------------------------------ piezas del paquete
    def _estilos(self):
        f = self.fuente
        def est(id_, nombre, base="Normal", ppr="", rpr="", sig=None, tipo="paragraph", q=True, extra=""):
            return ('<w:style w:type="%s" w:styleId="%s"><w:name w:val="%s"/>%s%s%s%s%s%s</w:style>' % (
                tipo, id_, nombre,
                '<w:basedOn w:val="%s"/>' % base if base else "",
                '<w:next w:val="%s"/>' % sig if sig else "",
                "<w:qFormat/>" if q else "",
                extra,
                "<w:pPr>%s</w:pPr>" % ppr if ppr else "",
                "<w:rPr>%s</w:rPr>" % rpr if rpr else ""))
        fn = '<w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s" w:eastAsia="%s"/>' % (f, f, f, f)
        s = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles %s>' % NS,
             '<w:docDefaults><w:rPrDefault><w:rPr>%s<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="es-AR" w:eastAsia="es-AR" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>'
             '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' % fn,
             '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>',
             est("Title", "Title", ppr='<w:spacing w:before="0" w:after="80"/>', rpr='%s<w:b/><w:color w:val="%s"/><w:sz w:val="52"/>' % (fn, self.c1), sig="Normal"),
             est("Subtitle", "Subtitle", ppr='<w:spacing w:after="160"/>', rpr='%s<w:color w:val="595959"/><w:sz w:val="28"/>' % fn, sig="Normal"),
             est("Heading1", "heading 1", ppr='<w:keepNext/><w:keepLines/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/>',
                 rpr='%s<w:b/><w:color w:val="%s"/><w:sz w:val="32"/>' % (fn, self.c1), sig="Normal"),
             est("Heading2", "heading 2", ppr='<w:keepNext/><w:keepLines/><w:spacing w:before="260" w:after="100"/><w:outlineLvl w:val="1"/>',
                 rpr='%s<w:b/><w:color w:val="%s"/><w:sz w:val="26"/>' % (fn, self.c2), sig="Normal"),
             est("Heading3", "heading 3", ppr='<w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="2"/>',
                 rpr='%s<w:b/><w:color w:val="404040"/><w:sz w:val="22"/>' % fn, sig="Normal"),
             est("ListParagraph", "List Paragraph", ppr='<w:spacing w:after="60"/><w:ind w:left="567" w:hanging="283"/>'),
             est("Caption", "caption", ppr='<w:spacing w:before="0" w:after="200"/>', rpr='<w:i/><w:color w:val="595959"/><w:sz w:val="18"/>'),
             est("TableText", "Table Text", ppr='<w:spacing w:after="0" w:line="252" w:lineRule="auto"/>', rpr='<w:sz w:val="18"/>', q=False),
             est("Header", "header", ppr='<w:spacing w:after="0"/>', rpr='<w:color w:val="7F7F7F"/><w:sz w:val="17"/>', q=False),
             est("Footer", "footer", ppr='<w:spacing w:after="0"/>', rpr='<w:color w:val="7F7F7F"/><w:sz w:val="17"/>', q=False),
             '</w:styles>']
        return "".join(s)

    def _numeracion(self):
        x = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering %s>' % NS,
             '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
             '<w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="567" w:hanging="283"/></w:pPr>'
             '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/></w:rPr></w:lvl></w:abstractNum>',
             '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
             '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="567" w:hanging="340"/></w:pPr></w:lvl></w:abstractNum>',
             '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>']
        for nid in self.nums:
            x.append('<w:num w:numId="%d"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>' % nid)
        x.append("</w:numbering>")
        return "".join(x)

    def guardar(self, ruta, titulo="Documento", autor="LTDI", encabezado="", pie_extra=""):
        sect = ('<w:sectPr><w:headerReference w:type="default" r:id="rId3"/><w:footerReference w:type="default" r:id="rId4"/>'
                '<w:pgSz w:w="%d" w:h="%d"/><w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>'
                % (self.ancho_pag, self.alto_pag, self.margen, self.margen, self.margen, self.margen))
        documento = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document %s><w:body>%s%s</w:body></w:document>' % (
            NS, "".join(self.cuerpo), sect)
        header = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr %s><w:p><w:pPr><w:pStyle w:val="Header"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="4" w:color="BFBFBF"/></w:pBdr></w:pPr>%s</w:p></w:hdr>'
                  % (NS, self._run(encabezado, "")))
        campo = lambda c: ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> %s </w:instrText></w:r>'
                           '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>' % c)
        footer = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr %s><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>%s%s%s%s</w:p></w:ftr>'
                  % (NS, self._run(pie_extra + "Página ", ""), campo("PAGE"), self._run(" de ", ""), campo("NUMPAGES")))
        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>',
                '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>',
                '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
                '<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>']
        for rid, tipo, dest, ext in self.rels:
            rels.append('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/%s" Target="%s"%s/>'
                        % (rid, tipo, escape(dest, {'"': "&quot;"}), ' TargetMode="External"' if ext else ""))
        rels.append("</Relationships>")
        tipos = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
                 '<Default Extension="jpeg" ContentType="image/jpeg"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                 '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                 '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
                 '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                 '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                 '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
        raiz = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
        core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                '<dc:title>%s</dc:title><dc:creator>%s</dc:creator><dc:language>es-AR</dc:language></cp:coreProperties>' % (escape(titulo), escape(autor)))
        app = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>python</Application></Properties>'
        ajustes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings %s><w:defaultTabStop w:val="708"/>'
                   '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>' % NS)
        with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", tipos)
            z.writestr("_rels/.rels", raiz)
            z.writestr("word/document.xml", documento)
            z.writestr("word/_rels/document.xml.rels", "".join(rels))
            z.writestr("word/styles.xml", self._estilos())
            z.writestr("word/numbering.xml", self._numeracion())
            z.writestr("word/settings.xml", ajustes)
            z.writestr("word/header1.xml", header)
            z.writestr("word/footer1.xml", footer)
            z.writestr("docProps/core.xml", core)
            z.writestr("docProps/app.xml", app)
            for nombre, origen in self.medios:
                z.write(origen, "word/media/" + nombre)
