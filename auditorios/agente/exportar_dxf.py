#!/usr/bin/env python3
"""exportar_dxf.py — Exporta o pré-projeto para DXF (CADCraft, AutoCAD, BricsCAD, LibreCAD...).

Gera um DXF em METROS, escala 1:1, origem no centro da borda do palco
(x para a direita da planta, y para o fundo da plateia):
  - BASE-*      : todas as linhas vetoriais da planta oficial (PDF) convertidas para metros
  - ARQ/SOM/VID/LUZ/ACU/INF : elementos do layout.json, uma camada por disciplina
  - ARQ-PAREDE-SUPERIOR : dente de serra e leque do palco
  - ARQ-ARQUIBANCADA-3D : patamares com cota (3DFACE) para ver em 3D

Uso: python3 exportar_dxf.py escola.json layout.json base.pdf saida.dxf [perfil_json]
"""
import json, sys, math
import pymupdf, ezdxf

CORES_ACI = {"arq": 6, "som": 5, "video": 3, "luz": 30, "acu": 210, "infra": 8, "alerta": 1, "cinza": 9, "preto": 7}


def aci(c):
    if isinstance(c, str):
        return CORES_ACI.get(c, 7)
    r, g, b = c[:3]
    if r > 0.8 and g < 0.3 and b < 0.3: return 1
    if b > 0.6 and r < 0.3: return 5
    if g > 0.5 and r < 0.3: return 3
    if r > 0.5 and g > 0.3 and b < 0.2: return 30
    return 8 if max(r, g, b) > 0.3 else 7


def main(esc_p, lay_p, base_p, out_p, perfil_p=None):
    esc = json.load(open(esc_p, encoding="utf-8"))
    lay = json.load(open(lay_p, encoding="utf-8"))
    c = esc["calibracao"]
    K = c["pt_por_cm"] * 100
    XC = (c["x_face_interna_esquerda_pt"] + c["x_face_interna_direita_pt"]) / 2
    YB = c["y_borda_palco_pt"]
    m = lambda p: (round((p.x - XC) / K, 4), round((YB - p.y) / K, 4))

    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()

    def layer(name, color):
        if name not in doc.layers:
            doc.layers.add(name, color=color)
        return name

    # ---------- base vetorial
    page = pymupdf.open(base_p)[0]
    nb = 0
    vis = page.rect
    def dentro(*ps):
        return all(vis.x0 - 1 <= q.x <= vis.x1 + 1 and vis.y0 - 1 <= q.y <= vis.y1 + 1 for q in ps)
    for d in page.get_drawings():
        if not d["rect"].intersects(vis):
            continue
        col = d.get("color") or d.get("fill") or (0, 0, 0)
        red = col[0] > 0.8 and col[1] < 0.3
        lname = layer("BASE-INCENDIO", 1) if red else layer("BASE-ARQUITETURA", 8)
        for it in d["items"]:
            pts_it = [q for q in it[1:] if isinstance(q, pymupdf.Point)]
            if it[0] == "re":
                pts_it = [it[1].tl, it[1].br]
            elif it[0] == "qu":
                pts_it = [it[1].ul, it[1].lr]
            if not dentro(*pts_it):
                continue
            if it[0] == "l":
                msp.add_line(m(it[1]), m(it[2]), dxfattribs={"layer": lname}); nb += 1
            elif it[0] == "re":
                r = it[1]
                pts = [m(pymupdf.Point(r.x0, r.y0)), m(pymupdf.Point(r.x1, r.y0)), m(pymupdf.Point(r.x1, r.y1)), m(pymupdf.Point(r.x0, r.y1))]
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": lname}); nb += 1
            elif it[0] == "c":
                p0, p1, p2, p3 = it[1:5]
                pts = []
                for i in range(9):
                    t = i / 8
                    x = (1-t)**3*p0.x + 3*(1-t)**2*t*p1.x + 3*(1-t)*t**2*p2.x + t**3*p3.x
                    y = (1-t)**3*p0.y + 3*(1-t)**2*t*p1.y + 3*(1-t)*t**2*p2.y + t**3*p3.y
                    pts.append(m(pymupdf.Point(x, y)))
                msp.add_lwpolyline(pts, dxfattribs={"layer": lname}); nb += 1
            elif it[0] == "qu":
                q = it[1]
                msp.add_lwpolyline([m(q.ul), m(q.ur), m(q.lr), m(q.ll)], close=True, dxfattribs={"layer": lname}); nb += 1
    tl = layer("BASE-TEXTO", 8)
    for w in page.get_text("words"):
        x0, y0, x1, y1, t = w[:5]
        h = min(0.22, max(0.08, min(y1 - y0, x1 - x0) / K * 0.8))
        msp.add_text(t, height=h, dxfattribs={"layer": tl}).set_placement(m(pymupdf.Point(x0, y1)))

    # ---------- layout por disciplina
    disc_nome = {"ARQ-01": "ARQ", "SOM-01": "SOM", "VID-01": "VID", "LUZ-01": "LUZ", "ACU-01": "ACU", "INF-01": "INF"}
    for pr in lay["pranchas"]:
        pre = disc_nome.get(pr["codigo"], pr["codigo"])
        for it in pr["itens"]:
            cor = it.get("cor", "preto")
            is_wall = (isinstance(cor, list) and abs(cor[0] - 0.12) < 0.01) or (isinstance(cor, list) and abs(cor[0] - 0.35) < 0.01)
            if is_wall:
                if pre != "ARQ":
                    continue  # paredes desenhadas uma vez só
                lname = layer("ARQ-PAREDE-SUPERIOR", 7)
            else:
                lname = layer(f"{pre}", aci(cor))
            pts = [tuple(p) for p in it.get("pts", [])]
            t = it["tipo"]
            if t == "ret":
                (x0, y0), (x1, y1) = pts
                msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": lname})
            elif t in ("poli", "linha"):
                if len(pts) >= 2 and pts[0] != pts[-1] or t == "poli":
                    if len(pts) >= 2 and not (len(pts) == 2 and pts[0] == pts[1]):
                        msp.add_lwpolyline(pts, close=(t == "poli" and it.get("fechado", True)), dxfattribs={"layer": lname})
            elif t == "seta":
                msp.add_line(pts[0], pts[1], dxfattribs={"layer": lname})
            elif t == "circ":
                msp.add_circle(pts[0], it.get("raio_m", 0.25), dxfattribs={"layer": lname})
            elif t == "leque":
                cx, cy = pts[0]
                R = it["raio_m"]
                msp.add_arc((cx, cy), R, it["ang_ini"] - 90 + 90, it["ang_fim"], dxfattribs={"layer": lname})
            txt = it.get("tag") or it.get("texto")
            if txt:
                if pts:
                    px = sum(p[0] for p in pts) / len(pts); py = sum(p[1] for p in pts) / len(pts)
                else:
                    px, py = it["pos"]
                e = msp.add_text(txt, height=0.18, dxfattribs={"layer": layer(pre + "-TEXTO", aci(cor)), "rotation": it.get("rot", 0)})
                e.set_placement((px + 0.1, py + 0.1))

    # ---------- arquibancada 3D
    if perfil_p:
        P = json.load(open(perfil_p, encoding="utf-8"))
        l3 = layer("ARQ-ARQUIBANCADA-3D", 6)
        xb, rows, z0 = P["meia_largura_bloco_m"], P["frentes_fileiras_m"], P["cota_plateia_m"]
        prev = 0.0
        for i, yf in enumerate(rows):
            h = P["perfil_m"][i]
            ya, yb = yf - 0.33, yf + 0.67
            z = z0 + h
            msp.add_3dface([(-xb, ya, z), (xb, ya, z), (xb, yb, z), (-xb, yb, z)], dxfattribs={"layer": l3})
            if h > prev:
                msp.add_3dface([(-xb, ya, z0 + prev), (xb, ya, z0 + prev), (xb, ya, z), (-xb, ya, z)], dxfattribs={"layer": l3})
            msp.add_text(f"F{i+1} {z:+.2f}".replace(".", ","), height=0.15, dxfattribs={"layer": l3}).set_placement((-xb - 1.2, yf + 0.3, z))
            prev = h
        # patamar do fundo
        zt = z0 + P["perfil_m"][-1]
        msp.add_3dface([(-9.3, rows[-1] + 0.67, zt), (9.3, rows[-1] + 0.67, zt), (9.3, P["y_fundo_m"], zt), (-9.3, P["y_fundo_m"], zt)], dxfattribs={"layer": l3})
        # palco
        msp.add_3dface([(-6.3, -6.97, z0 + 1.0), (6.3, -6.97, z0 + 1.0), (6.3, 0, z0 + 1.0), (-6.3, 0, z0 + 1.0)], dxfattribs={"layer": l3})

    # carimbo
    lt = layer("CARIMBO", 7)
    for i, s in enumerate([f"MARIANI AUDIO E VIDEO - PRE-PROJETO - {esc['escola']['nome']}",
                           "SIMULACAO DE PRE-PROJETO - NAO E PROJETO EXECUTIVO",
                           "Unidade: metro. Origem (0,0) = centro da borda do palco. Cotas Z absolutas (plateia +0,20).",
                           "Base: " + esc["escola"]["fonte_base"]]):
        msp.add_text(s, height=0.3 if i == 0 else 0.2, dxfattribs={"layer": lt}).set_placement((-10.5, -10.5 - i * 0.45))
    doc.saveas(out_p)
    print("ok", out_p, "linhas da base:", nb)


if __name__ == "__main__":
    main(*sys.argv[1:6])
