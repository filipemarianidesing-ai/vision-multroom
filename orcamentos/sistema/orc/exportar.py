"""Exportação do orçamento (a partir do dicionário calculado ou da versão congelada).

XLSX: valores de entrada (quantidade, custo unitário, componentes do BDI) como números; totais, BDI e preços como
FÓRMULAS editáveis que reproduzem a política de arredondamento do orçamento.
PDF: conferência visual, mesmo conteúdo.
"""
import io
from decimal import Decimal

from django.template.loader import render_to_string
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FMT_MOEDA = '#,##0.00'
FMT_QTD = '#,##0.00##'
NEGRITO = Font(bold=True)
CAB = PatternFill("solid", fgColor="DDE5F0")
FINO = Side(style="thin", color="999999")
BORDA = Border(left=FINO, right=FINO, top=FINO, bottom=FINO)


def _num(v):
    """openpyxl grava Decimal como número; mantemos Decimal para não perder precisão na escrita."""
    if v in (None, ""):
        return None
    return Decimal(str(v))


def _fn(modo):
    return "TRUNC" if modo == "ROUND_DOWN" else "ROUND"


def gerar_xlsx(dados, meta):
    wb = Workbook()
    ws = wb.active
    ws.title = "Orçamento"
    pol = dados["politica"]
    fn = _fn(pol["modo_codigo"])
    casas = pol["casas_preco"]

    # ---------------- BDI
    wb_bdi = wb.create_sheet("BDI")
    b = dados["bdi"]
    wb_bdi["A1"] = "Composição do BDI"
    wb_bdi["A1"].font = NEGRITO
    comp = [("Administração central (AC)", b["ac"]), ("Seguros (S)", b["s"]), ("Riscos (R)", b["r"]),
            ("Garantias (G)", b["g"]), ("Despesas financeiras (DF)", b["df"]), ("Lucro (L)", b["l"]),
            ("Tributos sobre o preço (I)", b["i"])]
    for i, (rot, val) in enumerate(comp, start=3):
        wb_bdi.cell(i, 1, rot)
        wb_bdi.cell(i, 2, "%")
        wb_bdi.cell(i, 3, _num(val))
    wb_bdi["A10"] = "BDI de serviços (%)"
    wb_bdi["A10"].font = NEGRITO
    if b["formula"] == "manual":
        wb_bdi["C10"] = _num(b["manual"])
        wb_bdi["D10"] = "percentual informado"
    else:
        wb_bdi["C10"] = "=ROUND(((1+(C3+C4+C5+C6)/100)*(1+C7/100)*(1+C8/100)/(1-C9/100)-1)*100,2)"
        wb_bdi["D10"] = "((1+AC+S+R+G)(1+DF)(1+L)/(1−I)) − 1"
    wb_bdi["A12"] = "BDI de fornecimento de equipamentos (%)"
    wb_bdi["C12"] = _num(b["equipamentos"]) if b["equip_diferenciado"] else "=C10"
    wb_bdi["A14"] = "Justificativa/fonte"
    wb_bdi["C14"] = b.get("justificativa") or "não informada"
    wb_bdi.column_dimensions["A"].width = 42
    wb_bdi.column_dimensions["C"].width = 14

    # ---------------- Cabeçalho
    emp = dados.get("empresa") or {}
    base = dados.get("base") or {}
    ws["A1"] = f"ORÇAMENTO — {dados['orcamento']['titulo']}"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = f"Empresa: {emp.get('razao_social', '')}  CNPJ {emp.get('cnpj', '')}"
    ws["A3"] = f"Cliente: {dados['cliente']['nome']}  ·  Obra/serviço: {dados['obra']['nome']} ({dados['obra']['municipio']}/{dados['obra']['uf']})"
    ws["A4"] = (f"Base: {base.get('descricao', 'não definida')}  ·  data-base {base.get('competencia', '')}  ·  "
                f"arquivo {base.get('arquivo', '')}")
    ws["A5"] = f"Versão: {meta.get('versao')}  {('SHA-256 ' + meta['sha256']) if meta.get('sha256') else ''}"
    ws["A6"] = "BDI serviços (%)"
    ws["C6"] = "='BDI'!C10"
    ws["A7"] = "BDI equipamentos (%)"
    ws["C7"] = "='BDI'!C12"
    ws["A8"] = (f"Arredondamento: {pol['modo']} — preço unitário {casas} casas; totais 2 casas; "
                f"quantidade {pol['casas_quantidade']} casas")
    for c in ("C6", "C7"):
        ws[c].number_format = FMT_MOEDA
        ws[c].font = NEGRITO

    cab = ["Item", "Etapa/ambiente", "Base", "Código", "Descrição oficial", "Complemento de escopo", "Unidade",
           "Quantidade", "Custo unitário", "Custo total", "BDI (%)", "Preço unitário final", "Preço total",
           "Data-base", "Status", "Fonte"]
    L0 = 10
    for j, t in enumerate(cab, start=1):
        c = ws.cell(L0, j, t)
        c.font, c.fill, c.border = NEGRITO, CAB, BORDA
        c.alignment = Alignment(wrap_text=True, vertical="center")

    linha = L0 + 1
    for it in dados["itens"]:
        r = linha
        etapa = it["etapa"] + (f" / {it['ambiente']}" if it["ambiente"] else "")
        valores = [it["numero"], etapa, it["base"], it["codigo"], it["descricao_oficial"], it["complemento"],
                   it["unidade"], _num(it["quantidade"]), _num(it["custo_unitario"])]
        for j, v in enumerate(valores, start=1):
            ws.cell(r, j, v)
        ref_bdi = "$C$7" if it["bdi_tipo"] == "equipamento" else "$C$6"
        ws.cell(r, 10, f'=IF(OR(H{r}="",I{r}=""),"",{fn}(H{r}*I{r},2))')
        ws.cell(r, 11, f"={ref_bdi}")
        ws.cell(r, 12, f'=IF(OR(I{r}="",K{r}=""),"",{fn}(I{r}*(1+K{r}/100),{casas}))')
        ws.cell(r, 13, f'=IF(OR(H{r}="",L{r}=""),"",{fn}(H{r}*L{r},2))')
        ws.cell(r, 14, it["data_base"])
        ws.cell(r, 15, "Confirmado" if it["status"] == "confirmado" else "Condicional")
        ws.cell(r, 16, it["fonte"])
        ws.cell(r, 8).number_format = FMT_QTD
        for col in (9, 10, 11, 12, 13):
            ws.cell(r, col).number_format = FMT_MOEDA
        for col in range(1, 17):
            ws.cell(r, col).border = BORDA
            ws.cell(r, col).alignment = Alignment(wrap_text=True, vertical="top")
        linha += 1
    ult = linha - 1
    linha += 1
    tot = [("Custo direto confirmado", f'=SUMIFS(J{L0+1}:J{ult},O{L0+1}:O{ult},"Confirmado")'),
           ("PREÇO TOTAL CONFIRMADO", f'=SUMIFS(M{L0+1}:M{ult},O{L0+1}:O{ult},"Confirmado")'),
           ("Itens condicionais — custo (fora do total)", f'=SUMIFS(J{L0+1}:J{ult},O{L0+1}:O{ult},"Condicional")'),
           ("Itens condicionais — preço (fora do total)", f'=SUMIFS(M{L0+1}:M{ult},O{L0+1}:O{ult},"Condicional")')]
    if ult < L0 + 1:
        tot = [(t, 0) for t, _ in tot]
    for rot, f in tot:
        ws.cell(linha, 12, rot).font = NEGRITO
        c = ws.cell(linha, 13, f)
        c.number_format, c.font = FMT_MOEDA, NEGRITO
        linha += 1
    linha += 1
    ws.cell(linha, 1, "Itens condicionais dependem de vistoria/confirmação e não compõem o total. Itens sem custo "
                      "ou sem quantidade aparecem em branco e constam na aba Pendências.")
    larguras = [6, 28, 16, 10, 50, 30, 8, 12, 13, 13, 9, 14, 14, 10, 12, 40]
    for j, w in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(L0 + 1, 1)

    # ---------------- Memória de cálculo
    wm = wb.create_sheet("Memória de cálculo")
    for j, t in enumerate(["Item", "Etapa", "Ambiente", "Fórmula", "Variáveis (valor | origem | obs.)",
                           "Variáveis do ambiente", "Quantidade", "Unidade"], start=1):
        c = wm.cell(1, j, t)
        c.font, c.fill = NEGRITO, CAB
    for i, it in enumerate(dados["itens"], start=2):
        vars_txt = "\n".join(
            f"{k} = {v.get('valor')} | {v.get('origem')} | {v.get('obs', '')}" if isinstance(v, dict) else f"{k} = {v}"
            for k, v in (it["variaveis"] or {}).items())
        amb_txt = "\n".join(f"{k} = {v}" for k, v in (it.get("variaveis_ambiente") or {}).items())
        for j, v in enumerate([it["numero"], it["etapa"], it["ambiente"], it["formula"], vars_txt, amb_txt,
                               _num(it["quantidade"]), it["unidade"]], start=1):
            c = wm.cell(i, j, v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
    wm.cell(len(dados["itens"]) + 3, 1, "Origem: F = fornecido · V = vistoria · E = estimativa/hipótese · C = calculado · M = medido")
    for j, w in enumerate([6, 30, 16, 30, 50, 25, 12, 8], start=1):
        wm.column_dimensions[get_column_letter(j)].width = w

    # ---------------- Composições (analítico copiado no momento da inclusão)
    wc = wb.create_sheet("Composições")
    r = 1
    for it in dados["itens"]:
        det = it.get("detalhe") or {}
        linhas = det.get("analitico") or det.get("linhas")
        if not linhas:
            continue
        wc.cell(r, 1, f"Item {it['numero']} — {it['codigo']} {it['descricao_oficial']}").font = NEGRITO
        r += 1
        if det.get("analitico"):
            for j, t in enumerate(["Tipo", "Código", "Descrição", "Unidade", "Coeficiente", "Situação"], start=1):
                wc.cell(r, j, t).font = NEGRITO
            r += 1
            for l in linhas:
                for j, v in enumerate([l["tipo"], l["codigo"], l["descricao"], l["unidade"], _num(l["coeficiente"]),
                                       l["situacao"]], start=1):
                    wc.cell(r, j, v)
                r += 1
        else:
            for j, t in enumerate(["Tipo", "Código", "Descrição", "Unidade", "Coeficiente", "Preço unit.", "Parcial",
                                   "Fonte"], start=1):
                wc.cell(r, j, t).font = NEGRITO
            r += 1
            for l in linhas:
                for j, v in enumerate([l["tipo"], l["codigo"], l["descricao"], l["unidade"], _num(l["coeficiente"]),
                                       _num(l["preco"]), _num(l["parcial"]), l["fonte"]], start=1):
                    wc.cell(r, j, v)
                r += 1
        r += 1
    wc.column_dimensions["C"].width = 60

    # ---------------- Pendências e referências
    wp = wb.create_sheet("Pendências")
    wp.append(["Item", "Etapa", "Pendência / alerta"])
    for c in wp[1]:
        c.font, c.fill = NEGRITO, CAB
    for a in dados["alertas"]:
        wp.append([a["item"], a["etapa"], a["mensagem"]])
    wp.column_dimensions["B"].width = 30
    wp.column_dimensions["C"].width = 90

    wr = wb.create_sheet("Referências")
    linhas_ref = [("Gerado em", dados["gerado_em"]), ("Versão", meta.get("versao")),
                  ("SHA-256 da versão", meta.get("sha256", "")), ("Descrição da revisão", meta.get("descricao", "")),
                  ("Revisado por", meta.get("revisado_por", "")), ("Finalidade", dados["orcamento"]["finalidade"]),
                  ("Premissas", dados["orcamento"]["premissas"])]
    if base:
        linhas_ref += [("Base", base["descricao"]), ("Competência", base["competencia"]), ("Regime", base["regime"]),
                       ("Arquivo oficial", base["arquivo"]), ("SHA-256 do arquivo", base["sha256"]),
                       ("Leiaute do importador", base["leiaute"])]
    for rot, v in linhas_ref:
        wr.append([rot, v])
        wr.cell(wr.max_row, 1).font = NEGRITO
    wr.column_dimensions["A"].width = 26
    wr.column_dimensions["B"].width = 90

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def gerar_pdf(dados, meta):
    from weasyprint import HTML

    html = render_to_string("orc/pdf_orcamento.html", {"dados": dados, "meta": meta})
    return HTML(string=html).write_pdf()
