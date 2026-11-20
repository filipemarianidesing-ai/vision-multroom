#!/usr/bin/env python3
"""
gerar_pranchas.py — Gera as pranchas de pré-projeto sobre a base vetorial da escola.

Entrada:
  escola.json  — dados calibrados (calibração pt/cm, geometria, plateia, arquibancada)
  layout.json  — elementos por disciplina, em METROS no sistema do auditório:
                 x = 0 no eixo do palco (positivo para a direita de quem olha o palco a partir da plateia...
                 ver nota), y = 0 na borda do palco (positivo para o fundo da plateia).
  base.pdf     — planta vetorial original (página 1)

Saída: PDF A3 paisagem, uma prancha por disciplina + corte da arquibancada + diagramas.

Uso:
  python3 gerar_pranchas.py escola.json layout.json base.pdf saida.pdf
"""
import json, sys, math, datetime
import pymupdf

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
A3 = pymupdf.paper_rect("a3-l")  # 1191 x 842

CORES = {
    "arq": (0.43, 0.16, 0.85), "som": (0.01, 0.52, 0.78), "video": (0.02, 0.59, 0.41),
    "luz": (0.92, 0.35, 0.05), "acu": (0.86, 0.15, 0.47), "infra": (0.28, 0.33, 0.41),
    "alerta": (0.80, 0.10, 0.10), "cinza": (0.45, 0.45, 0.45), "preto": (0.1, 0.1, 0.1),
}


def hexrgb(c):
    return CORES.get(c, c) if isinstance(c, str) else tuple(c)


class Prancha:
    def __init__(self, doc, esc, base, titulo, codigo, num, total, disc_desc):
        self.doc, self.esc = doc, esc
        self.page = doc.new_page(width=A3.width, height=A3.height)
        pg = self.page
        pg.insert_font(fontname="dj", fontfile=FONT)
        pg.insert_font(fontname="djb", fontfile=FONTB)
        self.titulo, self.codigo = titulo, codigo
        # área do desenho
        self.area = pymupdf.Rect(20, 20, 860, 822)
        if base is not None:
            br = base[0].rect
            s = min(self.area.width / br.width, self.area.height / br.height)
            self.s = s
            self.ox = self.area.x0 + (self.area.width - br.width * s) / 2
            self.oy = self.area.y0 + (self.area.height - br.height * s) / 2
            tgt = pymupdf.Rect(self.ox, self.oy, self.ox + br.width * s, self.oy + br.height * s)
            pg.show_pdf_page(tgt, base, 0)
            # esmaece a base para destacar a disciplina
            sh = pg.new_shape()
            sh.draw_rect(tgt)
            sh.finish(fill=(1, 1, 1), color=None, fill_opacity=0.55)
            sh.commit()
        self.carimbo(num, total, disc_desc)

    # --- conversão metros -> página
    def P(self, x, y):
        c = self.esc["calibracao"]
        xc = (c["x_face_interna_esquerda_pt"] + c["x_face_interna_direita_pt"]) / 2
        k = c["pt_por_cm"] * 100  # pt por metro
        bx = xc + x * k
        by = c["y_borda_palco_pt"] - y * k
        return pymupdf.Point(self.ox + bx * self.s, self.oy + by * self.s)

    def k(self):
        return self.esc["calibracao"]["pt_por_cm"] * 100 * self.s

    def texto(self, p, t, size=7, cor="preto", bold=False, rot=0, align=0, width=None):
        cor = hexrgb(cor)
        if width:
            r = pymupdf.Rect(p.x, p.y, p.x + width, p.y + size * 6)
            self.page.insert_textbox(r, t, fontsize=size, fontname="djb" if bold else "dj", color=cor, align=align)
        else:
            self.page.insert_text(p, t, fontsize=size, fontname="djb" if bold else "dj", color=cor, rotate=rot)

    def item(self, it):
        pg = self.page
        cor = hexrgb(it.get("cor", "preto"))
        tipo = it["tipo"]
        sh = pg.new_shape()
        pts = [self.P(*q) for q in it.get("pts", [])]
        dash = it.get("tracejado")
        op = it.get("opacidade", 0.25)
        lw = it.get("espessura", 1.2)
        if tipo == "ret":
            r = pymupdf.Rect(pts[0], pts[1]).normalize()
            sh.draw_rect(r)
            sh.finish(color=cor, fill=cor if it.get("preenchido", True) else None, fill_opacity=op, width=lw,
                      dashes="[3 2] 0" if dash else None)
        elif tipo == "poli":
            sh.draw_polyline(pts + ([pts[0]] if it.get("fechado", True) else []))
            sh.finish(color=cor, fill=cor if it.get("preenchido", True) else None, fill_opacity=op, width=lw,
                      dashes="[3 2] 0" if dash else None, closePath=it.get("fechado", True))
        elif tipo == "linha":
            sh.draw_polyline(pts)
            sh.finish(color=cor, width=lw, dashes="[4 2] 0" if dash else None)
        elif tipo == "seta":
            a, b = pts[0], pts[1]
            sh.draw_line(a, b)
            ang = math.atan2(b.y - a.y, b.x - a.x)
            L = 6
            for d in (2.6, -2.6):
                sh.draw_line(b, pymupdf.Point(b.x - L * math.cos(ang + d / 6), b.y - L * math.sin(ang + d / 6)))
            sh.finish(color=cor, width=lw, dashes="[4 2] 0" if dash else None)
        elif tipo == "circ":
            r = it.get("raio_m", 0.25) * self.k()
            sh.draw_circle(pts[0], r)
            sh.finish(color=cor, fill=cor, fill_opacity=it.get("opacidade", 0.9), width=0.8)
        elif tipo == "leque":
            c = pts[0]
            R = it["raio_m"] * self.k()
            a0, a1 = math.radians(it["ang_ini"]), math.radians(it["ang_fim"])
            n = 24
            arc = [pymupdf.Point(c.x + R * math.cos(a0 + (a1 - a0) * i / n), c.y - R * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
            sh.draw_polyline([c] + arc + [c])
            sh.finish(color=cor, fill=cor, fill_opacity=it.get("opacidade", 0.10), width=0.6, closePath=True,
                      dashes="[3 2] 0" if dash else None)
        sh.commit()
        if it.get("tag"):
            q = pts[0] if tipo in ("circ", "leque") else pymupdf.Point(sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts))
            dx, dy = it.get("tag_desloc", [4, -4])
            self.etiqueta(pymupdf.Point(q.x + dx, q.y + dy), it["tag"], cor)
        if it.get("texto"):
            q = pts[0] if pts else self.P(*it["pos"])
            dx, dy = it.get("txt_desloc", [0, 0])
            self.texto(pymupdf.Point(q.x + dx, q.y + dy), it["texto"], size=it.get("tam", 6.5), cor=it.get("cor_txt", cor),
                       rot=it.get("rot", 0), bold=it.get("negrito", False))

    def etiqueta(self, p, t, cor):
        w = 4.4 * len(t) + 5
        r = pymupdf.Rect(p.x, p.y - 8, p.x + w, p.y + 2)
        sh = self.page.new_shape()
        sh.draw_rect(r)
        sh.finish(color=cor, fill=(1, 1, 1), width=0.8)
        sh.commit()
        self.texto(pymupdf.Point(p.x + 2.5, p.y - 0.6), t, size=6.5, cor=cor, bold=True)

    def escala(self):
        k = self.k()
        x0, y0 = 880, 655
        sh = self.page.new_shape()
        for i in range(5):
            r = pymupdf.Rect(x0 + i * k, y0 - 3, x0 + (i + 1) * k, y0)
            sh.draw_rect(r)
            sh.finish(color=(0, 0, 0), fill=(0, 0, 0) if i % 2 == 0 else (1, 1, 1), width=0.5)
        sh.commit()
        for i in (0, 1, 2, 5):
            self.texto(pymupdf.Point(x0 + i * k - 2, y0 + 8), str(i), size=6)
        self.texto(pymupdf.Point(x0 + 5 * k + 6, y0 + 1), "m — escala gráfica (calibrada pelas cotas impressas)", size=6)
        self.texto(pymupdf.Point(x0, y0 - 8), "Norte: não consta no recorte da base", size=5.5, cor="cinza")

    def carimbo(self, num, total, disc_desc):
        pg = self.page
        X0 = 872
        sh = pg.new_shape()
        sh.draw_rect(pymupdf.Rect(10, 10, A3.width - 10, A3.height - 10))
        sh.finish(color=(0, 0, 0), width=1.2)
        sh.draw_line(pymupdf.Point(X0 - 4, 10), pymupdf.Point(X0 - 4, A3.height - 10))
        sh.finish(color=(0, 0, 0), width=0.8)
        sh.draw_rect(pymupdf.Rect(X0, 668, A3.width - 18, A3.height - 18))
        sh.finish(color=(0, 0, 0), width=0.6)
        sh.draw_rect(pymupdf.Rect(X0, 20, A3.width - 18, 44))
        sh.finish(color=None, fill=(0.95, 0.85, 0.2), fill_opacity=1)
        sh.commit()
        self.texto(pymupdf.Point(X0 + 6, 36), "SIMULAÇÃO DE PRÉ-PROJETO — NÃO É PROJETO EXECUTIVO", size=8, bold=True)
        e = self.esc["escola"]
        y = 684
        self.texto(pymupdf.Point(X0 + 6, y), "MARIANI ÁUDIO E VÍDEO", size=11, bold=True); y += 14
        self.texto(pymupdf.Point(X0 + 6, y), "Pré-projeto de modernização de auditório", size=7.5); y += 12
        self.texto(pymupdf.Point(X0 + 6, y), e["nome"], size=8, bold=True); y += 11
        self.texto(pymupdf.Point(X0 + 6, y), f"{e['cidade']} — {e['rede']} — proc. {e['processo']}", size=6.5); y += 14
        self.texto(pymupdf.Point(X0 + 6, y), self.titulo, size=9.5, bold=True, cor="preto"); y += 4
        pg.insert_textbox(pymupdf.Rect(X0 + 6, y, A3.width - 24, y + 20), disc_desc, fontsize=6.3, fontname="dj", color=(0.1, 0.1, 0.1)); y += 26
        self.texto(pymupdf.Point(X0 + 6, y), f"Prancha {self.codigo}   |   {num}/{total}   |   Rev. 0   |   {datetime.date.today():%d/%m/%Y}", size=7, bold=True); y += 11
        pg.insert_textbox(pymupdf.Rect(X0 + 6, y - 6, A3.width - 24, y + 20), "Base: " + e["fonte_base"], fontsize=5.2, fontname="dj", color=(0.45, 0.45, 0.45))

    def legenda(self, itens, notas, y0=56):
        X0 = 876
        y = y0
        self.texto(pymupdf.Point(X0, y), "LEGENDA", size=8, bold=True); y += 12
        for cor, simb, txt in itens:
            c = hexrgb(cor)
            sh = self.page.new_shape()
            if simb == "circ":
                sh.draw_circle(pymupdf.Point(X0 + 6, y - 3), 3.2); sh.finish(color=c, fill=c, width=0.6)
            elif simb == "linha":
                sh.draw_line(pymupdf.Point(X0, y - 3), pymupdf.Point(X0 + 13, y - 3)); sh.finish(color=c, width=1.6)
            elif simb == "trac":
                sh.draw_line(pymupdf.Point(X0, y - 3), pymupdf.Point(X0 + 13, y - 3)); sh.finish(color=c, width=1.4, dashes="[3 2] 0")
            else:
                sh.draw_rect(pymupdf.Rect(X0, y - 7, X0 + 13, y)); sh.finish(color=c, fill=c, fill_opacity=0.35, width=0.8)
            sh.commit()
            r = pymupdf.Rect(X0 + 18, y - 8, A3.width - 22, y + 14)
            used = self.page.insert_textbox(r, txt, fontsize=6.3, fontname="dj", color=(0.1, 0.1, 0.1))
            lines = max(1, math.ceil(len(txt) / 62))
            y += 9 * lines + 3
        y += 6
        self.texto(pymupdf.Point(X0, y), "NOTAS", size=8, bold=True); y += 4
        for n in notas:
            r = pymupdf.Rect(X0, y, A3.width - 22, y + 60)
            self.page.insert_textbox(r, "• " + n, fontsize=6.2, fontname="dj", color=(0.15, 0.15, 0.15))
            y += 8.2 * max(1, math.ceil(len(n) / 66)) + 3
        return y


def caixa(pg, r, titulo, sub="", cor="som", fill=0.12):
    c = hexrgb(cor)
    sh = pg.new_shape()
    sh.draw_rect(r, radius=0.08)
    sh.finish(color=c, fill=c, fill_opacity=fill, width=1.1)
    sh.commit()
    pg.insert_textbox(pymupdf.Rect(r.x0 + 3, r.y0 + 3, r.x1 - 3, r.y0 + 16), titulo, fontsize=7.2, fontname="djb", color=c, align=1)
    if sub:
        pg.insert_textbox(pymupdf.Rect(r.x0 + 3, r.y0 + 14, r.x1 - 3, r.y1 - 2), sub, fontsize=5.8, fontname="dj", color=(0.15, 0.15, 0.15), align=1)


def seta(pg, a, b, cor="preto", txt=None, dash=False, lw=1.0):
    c = hexrgb(cor)
    a, b = pymupdf.Point(*a), pymupdf.Point(*b)
    sh = pg.new_shape()
    sh.draw_line(a, b)
    ang = math.atan2(b.y - a.y, b.x - a.x)
    for d in (0.45, -0.45):
        sh.draw_line(b, pymupdf.Point(b.x - 6 * math.cos(ang + d), b.y - 6 * math.sin(ang + d)))
    sh.finish(color=c, width=lw, dashes="[3 2] 0" if dash else None)
    sh.commit()
    if txt:
        m = pymupdf.Point((a.x + b.x) / 2 + 2, (a.y + b.y) / 2 - 2)
        pg.insert_text(m, txt, fontsize=5.6, fontname="dj", color=(0.25, 0.25, 0.25))


def main(esc_p, lay_p, base_p, out_p):
    esc = json.load(open(esc_p, encoding="utf-8"))
    lay = json.load(open(lay_p, encoding="utf-8"))
    base = pymupdf.open(base_p)
    doc = pymupdf.open()
    pranchas = lay["pranchas"]
    total = len(pranchas) + len(lay.get("extras", []))
    for i, pr in enumerate(pranchas, 1):
        p = Prancha(doc, esc, base, pr["titulo"], pr["codigo"], i, total, pr["descricao"])
        p.page.insert_font(fontname="dj", fontfile=FONT)
        for it in pr["itens"]:
            p.item(it)
        p.escala()
        p.legenda([tuple(x) for x in pr["legenda"]], pr["notas"])
    # extras são desenhados por funções do módulo específico da escola
    doc.save(out_p, garbage=3, deflate=True)
    return doc


if __name__ == "__main__":
    main(*sys.argv[1:5])
