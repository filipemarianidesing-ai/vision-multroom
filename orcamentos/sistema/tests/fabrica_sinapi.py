"""Gera uma planilha SINTÉTICA com o mesmo leiaute do SINAPI_Referência (para testes). Valores fictícios."""
from openpyxl import Workbook

UFS = ["AC", "AL", "ES", "SP"]


def gerar(caminho, competencia="10/2026", insumos=None, composicoes=None, analitico=None, quebrar_cabecalho=False):
    insumos = insumos if insumos is not None else [
        ("MATERIAL", 35692, "TINTA LATEX ACRILICA STANDARD, COR BRANCA", "L", "C", {"ES": 20.0}),
        ("MATERIAL", 11111, "INSUMO SEM PRECO NO ES", "UN", "CR", {"SP": 5.0}),
    ]
    composicoes = composicoes if composicoes is not None else [
        ("Pintura Interna", 104642, "PINTURA LÁTEX ACRÍLICA STANDARD, APLICAÇÃO MANUAL EM PAREDES, DUAS DEMÃOS. AF_04/2023", "M2", {"ES": (13.51, 0)}),
        ("Pintura Interna", 104641, "PINTURA LÁTEX ACRÍLICA ECONÔMICA, APLICAÇÃO MANUAL EM PAREDES, DUAS DEMÃOS. AF_04/2023", "M2", {"ES": (12.10, 0)}),
        ("Pintura Interna", 88489, "PINTURA LÁTEX ACRÍLICA PREMIUM, APLICAÇÃO MANUAL EM PAREDES, DUAS DEMÃOS. AF_04/2023", "M2", {"ES": (15.91, 0)}),
        ("Pintura Interna", 88495, "EMASSAMENTO COM MASSA LÁTEX, APLICAÇÃO EM PAREDE, UMA DEMÃO, LIXAMENTO MANUAL. AF_04/2023", "M2", {"ES": (16.27, 0)}),
        ("Pintura Interna", 88497, "EMASSAMENTO COM MASSA LÁTEX, APLICAÇÃO EM PAREDE, DUAS DEMÃOS, LIXAMENTO MANUAL. AF_04/2023", "M2", {"ES": (25.19, 0)}),
        ("Pintura Interna", 88485, "FUNDO SELADOR ACRÍLICO, APLICAÇÃO MANUAL EM PAREDE, UMA DEMÃO. AF_04/2023", "M2", {"ES": (5.47, 0)}),
        ("Pintura Interna", 104646, "EMASSAMENTO ... LIXAMENTO MECANIZADO", "M2", {"ES": (0, None)}),
        ("Limpeza de Obra", 99814, "LIMPEZA DE SUPERFÍCIE PISO OU PAREDE COM JATO DE ALTA PRESSÃO. AF_10/2025", "M2", {"ES": (2.11, 0)}),
    ]
    analitico = analitico if analitico is not None else {
        104642: ("COM CUSTO", [("INSUMO", 35692, "TINTA LATEX ACRILICA STANDARD, COR BRANCA", "L", 0.2367, "COM PREÇO")]),
        104646: ("SEM CUSTO", [("INSUMO", 11111, "INSUMO SEM PRECO NO ES", "UN", 1.0, "SEM PREÇO")]),
    }
    wb = Workbook()
    wb.remove(wb.active)
    for aba in ("ISD", "ICD", "ISE"):
        ws = wb.create_sheet(aba)
        ws["A1"] = "SINAPI - Sistema Nacional de Pesquisa de Custos e Índices"
        ws["A3"], ws["B3"] = "Mês de Referência:", competencia
        ws["A4"], ws["B4"] = "Data de emissão:", "12/11/2026"
        for j, uf in enumerate(UFS):
            ws.cell(4, 6 + j, uf)
            ws.cell(5, 6 + j, {"ES": "VITORIA"}.get(uf, uf))
            ws.cell(6, 6 + j, 1.183 if aba == "ISD" else 1.0222)
            ws.cell(7, 6 + j, 0.7385)
        cab = ["Classificação", "Código do\nInsumo", "Descrição do Insumo", "Unidade", "Origem de\nPreço"] + UFS
        if quebrar_cabecalho and aba == "ISD":
            cab[1] = "Codigo"
        for j, t in enumerate(cab, start=1):
            ws.cell(10, j, t)
        for i, (cl, cod, desc, un, orig, precos) in enumerate(insumos, start=11):
            for j, v in enumerate([cl, cod, desc, un, orig], start=1):
                ws.cell(i, j, v)
            for j, uf in enumerate(UFS):
                if uf in precos:
                    ws.cell(i, 6 + j, precos[uf])
    for aba in ("CSD", "CCD", "CSE"):
        ws = wb.create_sheet(aba)
        ws["A3"], ws["B3"] = "Mês de Referência:", competencia
        for j, uf in enumerate(UFS):
            ws.cell(9, 5 + 2 * j, uf)
        for j, t in enumerate(["Grupo", "Código da\nComposição", "Descrição", "Unidade"], start=1):
            ws.cell(10, j, t)
        for j, _ in enumerate(UFS):
            ws.cell(10, 5 + 2 * j, "Custo (R$)")
            ws.cell(10, 6 + 2 * j, "%AS")
        for i, (gr, cod, desc, un, custos) in enumerate(composicoes, start=11):
            ws.cell(i, 1, gr)
            ws.cell(i, 2, f'=HYPERLINK("#"&CELL("address",OFFSET(Analítico!$B$1,MATCH({cod},Analítico!$B:$B,0)-1,3)),{cod})')
            ws.cell(i, 3, desc)
            ws.cell(i, 4, un)
            for j, uf in enumerate(UFS):
                if uf in custos:
                    c, p = custos[uf]
                    ws.cell(i, 5 + 2 * j, c)
                    if p is not None:
                        ws.cell(i, 6 + 2 * j, p)
    ws = wb.create_sheet("Analítico")
    ws["A3"], ws["B3"] = "Mês de Referência:", competencia
    for j, t in enumerate(["Grupo", "Código da\nComposição", "Tipo Item", "Código do\nItem", "Descrição", "Unidade",
                           "Coeficiente", "Situação"], start=1):
        ws.cell(10, j, t)
    linha = 11
    for gr, cod, desc, un, _ in composicoes:
        sit, itens = analitico.get(cod, ("COM CUSTO", []))
        for j, v in enumerate([gr, cod, None, None, desc, un, None, sit], start=1):
            ws.cell(linha, j, v)
        linha += 1
        for tipo, ci, d, u, coef, s in itens:
            for j, v in enumerate([gr, cod, tipo, ci, d, u, coef, s], start=1):
                ws.cell(linha, j, v)
            linha += 1
    wb.save(caminho)
    return caminho
