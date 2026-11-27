"""Importador do SINAPI — pacote mensal "formato XLSX" (planilha SINAPI_Referência_AAAA_MM.xlsx).

Leiaute verificado no arquivo oficial de 10/2026 (SINAPI-2026-10-formato-xlsx.zip, emissão 12/11/2026):
- Abas de insumos ISD (sem desoneração), ICD (com desoneração), ISE (sem encargos):
  B3 = mês de referência "MM/AAAA"; B4 = data de emissão; linha 4/10 = siglas das UFs; linha 5 = localidade;
  linhas 6-7 = encargos horista/mensalista (ISD/ICD); linha 10 = cabeçalho; dados a partir da linha 11.
- Abas de composições CSD, CCD, CSE: linha 9 = UFs (colunas de custo); para cada UF, coluna "Custo (R$)" e, à
  direita, "%AS"; o código da composição está dentro de uma fórmula HYPERLINK(...; código).
- Aba "Analítico": linha de cabeçalho da composição (Tipo Item vazio) seguida dos itens INSUMO/COMPOSICAO com
  coeficiente e situação (COM CUSTO / SEM CUSTO / COM PREÇO / SEM PREÇO / EM ESTUDO).

Regras de qualidade:
- Célula de preço/custo vazia => sem preço (None), nunca zero.
- Custo 0 com %AS vazio, ou composição "SEM CUSTO" no analítico com custo 0 => sem custo (None).
- Estrutura diferente da esperada => erro de leiaute; o importador não tenta adivinhar colunas.
"""
import hashlib
import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import openpyxl

LEIAUTE = "SINAPI-Referencia-XLSX-2025"

ABAS = {"SD": ("ISD", "CSD"), "CD": ("ICD", "CCD"), "SE": ("ISE", "CSE")}
CAB_INSUMOS = ["Classificação", "Código do\nInsumo", "Descrição do Insumo", "Unidade", "Origem de\nPreço"]
CAB_COMPOSICOES = ["Grupo", "Código da\nComposição", "Descrição", "Unidade"]
CAB_ANALITICO = ["Grupo", "Código da\nComposição", "Tipo Item", "Código do\nItem", "Descrição", "Unidade",
                 "Coeficiente", "Situação"]
RE_CODIGO_HYPERLINK = re.compile(r",\s*(\d+)\s*\)\s*$")
RE_COMPETENCIA = re.compile(r"^(\d{2})/(\d{4})$")
UNIDADES_CONHECIDAS = {
    "UN", "M", "M2", "M3", "KG", "L", "H", "T", "CJ", "PAR", "MES", "DIA", "KM", "100M", "M3XKM", "TXKM",
    "CHP", "CHI", "GL", "G", "ML", "SC", "CENTO", "MIL", "JG", "RL", "PCT", "KIT", "KWH", "VB", "UNXKM", "HA",
    "M2XMES", "M3XMES", "UNXMES", "MXMES", "TXMES", "CX", "LATA", "BALDE", "GALAO", "FD", "PC", "MIL/UN", "MO",
    "310ML", "KGXKM", "LXKM", "M2XKM", "MXKM", "SC25KG",
}


class ErroLeiaute(Exception):
    pass


@dataclass
class Resultado:
    uf: str
    regime: str
    competencia: date | None = None
    emissao: str = ""
    localidade: str = ""
    encargos_horista: Decimal | None = None
    encargos_mensalista: Decimal | None = None
    insumos: list = field(default_factory=list)
    composicoes: list = field(default_factory=list)
    itens: dict = field(default_factory=dict)  # codigo_composicao -> [itens]
    erros: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    estatisticas: dict = field(default_factory=dict)
    nome_planilha: str = ""

    @property
    def valido(self):
        return not self.erros

    def aviso(self, msg, limite=300):
        if len(self.avisos) < limite:
            self.avisos.append(msg)
        self.estatisticas["avisos_total"] = self.estatisticas.get("avisos_total", 0) + 1


def sha256_arquivo(caminho_ou_bytes):
    h = hashlib.sha256()
    if isinstance(caminho_ou_bytes, (bytes, bytearray)):
        h.update(caminho_ou_bytes)
    else:
        with open(caminho_ou_bytes, "rb") as fh:
            for bloco in iter(lambda: fh.read(1 << 20), b""):
                h.update(bloco)
    return h.hexdigest()


def _abrir_planilha(caminho):
    """Aceita o ZIP oficial ou a planilha de referência já extraída. Retorna (workbook, nome)."""
    with open(caminho, "rb") as fh:
        inicio = fh.read(4)
    if inicio[:2] != b"PK":
        raise ErroLeiaute("Arquivo não é ZIP nem XLSX.")
    with zipfile.ZipFile(caminho) as z:
        nomes = z.namelist()
        if "[Content_Types].xml" in nomes:  # é a própria planilha xlsx
            return openpyxl.load_workbook(caminho, read_only=True, data_only=False), caminho.split("/")[-1]
        candidatos = [n for n in nomes if n.lower().endswith(".xlsx") and "refer" in n.lower()]
        if len(candidatos) != 1:
            raise ErroLeiaute(f"ZIP sem a planilha SINAPI_Referência (encontrados: {nomes}).")
        dados = z.read(candidatos[0])
    return openpyxl.load_workbook(io.BytesIO(dados), read_only=True, data_only=False), candidatos[0]


def _dec(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        raise ValueError("booleano")
    if isinstance(v, (int,)):
        return Decimal(v)
    if isinstance(v, float):
        return Decimal(repr(v))
    txt = str(v).strip()
    if not txt:
        return None
    return Decimal(txt.replace(",", "."))


def _codigo(v):
    if v is None:
        return None
    if isinstance(v, (int,)):
        return str(v)
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    txt = str(v).strip()
    m = RE_CODIGO_HYPERLINK.search(txt)
    if txt.startswith("=") and m:
        return m.group(1)
    if txt.isdigit():
        return txt
    return None


def _competencia(v, res, aba):
    m = RE_COMPETENCIA.match(str(v or "").strip())
    if not m:
        res.erros.append(f"{aba}: mês de referência ilegível em B3 ({v!r}).")
        return None
    return date(int(m.group(2)), int(m.group(1)), 1)


def _linhas(ws, inicio, fim=None):
    return ws.iter_rows(min_row=inicio, max_row=fim, values_only=True)


def analisar(caminho, uf="ES", regime="SD"):
    uf = uf.upper().strip()
    if regime not in ABAS:
        raise ValueError("Regime inválido.")
    res = Resultado(uf=uf, regime=regime)
    try:
        wb, nome = _abrir_planilha(caminho)
    except (ErroLeiaute, zipfile.BadZipFile) as exc:
        res.erros.append(f"Leiaute incompatível: {exc}")
        return res
    res.nome_planilha = nome
    aba_ins, aba_comp = ABAS[regime]
    faltando = [a for a in (aba_ins, aba_comp, "Analítico") if a not in wb.sheetnames]
    if faltando:
        res.erros.append(f"Leiaute incompatível: abas ausentes {faltando} (presentes: {wb.sheetnames}).")
        return res

    _ler_insumos(wb[aba_ins], res, aba_ins)
    if res.erros:
        return res
    situacoes = _ler_analitico(wb["Analítico"], res)
    if res.erros:
        return res
    _ler_composicoes(wb[aba_comp], res, aba_comp, situacoes)
    wb.close()

    # Coerência entre abas
    codigos_comp = {c["codigo"] for c in res.composicoes}
    sem_analitico = codigos_comp - set(res.itens)
    if sem_analitico:
        res.aviso(f"{len(sem_analitico)} composições sem itens no Analítico (ex.: {sorted(sem_analitico)[:5]}).")
    so_analitico = set(res.itens) - codigos_comp
    if so_analitico:
        res.aviso(f"{len(so_analitico)} composições do Analítico ausentes em {aba_comp} (ex.: {sorted(so_analitico)[:5]}).")

    conferir_analitico(res)
    unidades = {i["unidade"] for i in res.insumos} | {c["unidade"] for c in res.composicoes}
    desconhecidas = sorted(u for u in unidades if u.upper() not in UNIDADES_CONHECIDAS)
    if desconhecidas:
        res.aviso(f"Unidades não reconhecidas pela lista do sistema (conferir): {desconhecidas}")
    res.estatisticas["unidades"] = sorted(unidades)
    return res


def _cabecalho(ws, linha, esperado, res, aba):
    cab = next(_linhas(ws, linha, linha))
    obtido = [str(c).strip() if c is not None else "" for c in cab[:len(esperado)]]
    if obtido != esperado:
        res.erros.append(f"Leiaute incompatível em {aba}, linha {linha}: esperado {esperado}, encontrado {obtido}.")
        return None
    return cab


def _ler_insumos(ws, res, aba):
    topo = list(_linhas(ws, 1, 10))
    res.competencia = _competencia(topo[2][1], res, aba)
    res.emissao = str(topo[3][1] or "")
    cab = _cabecalho(ws, 10, CAB_INSUMOS, res, aba)
    if cab is None:
        return
    try:
        col = [str(c).strip() if c else "" for c in cab].index(res.uf)
    except ValueError:
        res.erros.append(f"{aba}: UF {res.uf} não encontrada no cabeçalho.")
        return
    if len(topo[4]) > col and topo[4][col]:
        res.localidade = str(topo[4][col])
    if aba in ("ISD", "ICD"):
        res.encargos_horista = _dec(topo[5][col]) if len(topo[5]) > col else None
        res.encargos_mensalista = _dec(topo[6][col]) if len(topo[6]) > col else None
    vistos, sem_preco = set(), 0
    for n, r in enumerate(_linhas(ws, 11), start=11):
        if not any(v is not None for v in r[:5]):
            continue
        codigo = _codigo(r[1])
        if not codigo:
            res.erros.append(f"{aba} linha {n}: código de insumo inválido ({r[1]!r}).")
            if len(res.erros) > 20:
                return
            continue
        if codigo in vistos:
            res.erros.append(f"{aba} linha {n}: código {codigo} repetido.")
            continue
        vistos.add(codigo)
        desc, un = (r[2] or "").strip() if isinstance(r[2], str) else r[2], (str(r[3]).strip() if r[3] else "")
        if not desc or not un:
            res.erros.append(f"{aba} linha {n}: insumo {codigo} sem descrição ou unidade.")
            continue
        try:
            preco = _dec(r[col] if len(r) > col else None)
        except Exception:
            res.erros.append(f"{aba} linha {n}: preço não numérico ({r[col]!r}).")
            continue
        if preco is None:
            sem_preco += 1
        elif preco < 0:
            res.erros.append(f"{aba} linha {n}: preço negativo.")
            continue
        res.insumos.append({"codigo": codigo, "descricao": desc, "unidade": un, "classificacao": r[0] or "",
                            "origem_preco": r[4] or "", "preco": preco, "linha": n})
    res.estatisticas["insumos"] = len(res.insumos)
    res.estatisticas["insumos_sem_preco"] = sem_preco


def _ler_analitico(ws, res):
    topo = list(_linhas(ws, 3, 3))[0]
    comp_an = _competencia(topo[1], res, "Analítico")
    if comp_an and res.competencia and comp_an != res.competencia:
        res.erros.append("Mês de referência do Analítico difere do das demais abas.")
    if _cabecalho(ws, 10, CAB_ANALITICO, res, "Analítico") is None:
        return {}
    situacoes, atual, ordem, n_itens = {}, None, 0, 0
    for n, r in enumerate(_linhas(ws, 11), start=11):
        if r[1] is None and r[2] is None:
            continue
        cod_comp = _codigo(r[1])
        if not cod_comp:
            res.erros.append(f"Analítico linha {n}: código de composição inválido ({r[1]!r}).")
            return situacoes
        if r[2] is None:  # cabeçalho da composição
            atual, ordem = cod_comp, 0
            situacoes[cod_comp] = (r[7] or "").strip()
            res.itens.setdefault(cod_comp, [])
            continue
        if cod_comp != atual:
            res.erros.append(f"Analítico linha {n}: item sem cabeçalho de composição ({cod_comp}).")
            return situacoes
        tipo = str(r[2]).strip().upper()
        if tipo not in ("INSUMO", "COMPOSICAO"):
            res.erros.append(f"Analítico linha {n}: tipo de item desconhecido {r[2]!r}.")
            return situacoes
        cod_item = _codigo(r[3])
        try:
            coef = _dec(r[6])
        except Exception:
            res.erros.append(f"Analítico linha {n}: coeficiente não numérico ({r[6]!r}).")
            return situacoes
        if coef is None:
            res.aviso(f"Analítico linha {n}: item {cod_item} da composição {cod_comp} sem coeficiente.")
        ordem += 1
        n_itens += 1
        res.itens[cod_comp].append({"tipo": tipo, "codigo": cod_item or "", "descricao": (r[4] or "").strip(),
                                    "unidade": (r[5] or "").strip(), "coeficiente": coef,
                                    "situacao": (r[7] or "").strip(), "ordem": ordem})
    res.estatisticas["itens_analitico"] = n_itens
    return situacoes


def _ler_composicoes(ws, res, aba, situacoes):
    topo = list(_linhas(ws, 1, 9))
    comp = _competencia(topo[2][1], res, aba)
    if comp and res.competencia and comp != res.competencia:
        res.erros.append(f"Mês de referência de {aba} difere do das abas de insumos.")
    cab = _cabecalho(ws, 10, CAB_COMPOSICOES, res, aba)
    if cab is None:
        return
    ufs = [str(c).strip() if c else "" for c in topo[8]]
    if res.uf not in ufs:
        res.erros.append(f"{aba}: UF {res.uf} não encontrada na linha 9.")
        return
    col = ufs.index(res.uf)
    if str(cab[col]).strip() != "Custo (R$)" or str(cab[col + 1]).strip() != "%AS":
        res.erros.append(f"Leiaute incompatível em {aba}: colunas da UF {res.uf} não são 'Custo (R$)' e '%AS'.")
        return
    vistos = set()
    st = {"composicoes": 0, "sem_custo": 0, "zero_tratado_sem_custo": 0, "zero_publicado": 0, "com_pct_as": 0}
    for n, r in enumerate(_linhas(ws, 11), start=11):
        if not any(v is not None for v in r[:4]):
            continue
        codigo = _codigo(r[1])
        if not codigo:
            res.erros.append(f"{aba} linha {n}: código de composição não reconhecido ({str(r[1])[:60]!r}).")
            if len(res.erros) > 20:
                return
            continue
        if codigo in vistos:
            res.erros.append(f"{aba} linha {n}: código {codigo} repetido.")
            continue
        vistos.add(codigo)
        desc, un = (r[2] or "").strip(), (str(r[3]).strip() if r[3] else "")
        if not desc or not un:
            res.erros.append(f"{aba} linha {n}: composição {codigo} sem descrição ou unidade.")
            continue
        try:
            custo, pct = _dec(r[col]), _dec(r[col + 1])
        except Exception:
            res.erros.append(f"{aba} linha {n}: custo não numérico.")
            continue
        situacao = situacoes.get(codigo, "")
        if custo is None:
            st["sem_custo"] += 1
        elif custo == 0 and (pct is None or situacao == "SEM CUSTO"):
            custo = None
            st["zero_tratado_sem_custo"] += 1
        elif custo == 0:
            st["zero_publicado"] += 1
            res.aviso(f"{aba} linha {n}: composição {codigo} com custo 0 publicado e %AS preenchido — conferir.")
        if pct and pct > 0:
            st["com_pct_as"] += 1
        res.composicoes.append({"codigo": codigo, "descricao": desc, "unidade": un, "grupo": r[0] or "",
                                "custo": custo, "pct_atribuido_sp": pct, "situacao": situacao, "linha": n})
    st["composicoes"] = len(res.composicoes)
    res.estatisticas.update(st)


def conferir_analitico(res):
    """Recalcula cada composição pelo Analítico: soma de TRUNC(coeficiente × preço; 2), como na planilha oficial.

    Registra quantas reproduzem o custo publicado, quantas divergem e quantas não podem ser recalculadas
    (algum item sem preço/custo na UF). Divergências viram aviso; não alteram o custo publicado.
    """
    from decimal import ROUND_DOWN

    ins = {i["codigo"]: i["preco"] for i in res.insumos}
    comp = {c["codigo"]: c["custo"] for c in res.composicoes}
    ok = dif = inc = 0
    for c in res.composicoes:
        if c["custo"] is None:
            continue
        total, falta = Decimal(0), False
        for it in res.itens.get(c["codigo"], []):
            preco = ins.get(it["codigo"]) if it["tipo"] == "INSUMO" else comp.get(it["codigo"])
            if preco is None or it["coeficiente"] is None:
                falta = True
                break
            total += (it["coeficiente"] * preco).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        if falta:
            inc += 1
        elif total == c["custo"]:
            ok += 1
        else:
            dif += 1
            res.aviso(f"Composição {c['codigo']}: custo publicado {c['custo']} ≠ recalculado {total}.")
    res.estatisticas.update({"conferencia_reproduzidas": ok, "conferencia_divergentes": dif,
                             "conferencia_nao_recalculaveis": inc})


def gravar(resultado, base):
    """Grava o resultado analisado nos modelos ligados à base (status 'previa')."""
    from ..models import Composicao, ComposicaoItem, Insumo

    Insumo.objects.bulk_create([Insumo(base=base, **i) for i in resultado.insumos], batch_size=5000)
    comps = Composicao.objects.bulk_create([Composicao(base=base, **c) for c in resultado.composicoes],
                                           batch_size=5000)
    por_codigo = {c.codigo: c for c in comps}
    itens = []
    for cod, lista in resultado.itens.items():
        comp = por_codigo.get(cod)
        if comp is None:
            continue
        itens.extend(ComposicaoItem(composicao=comp, **i) for i in lista)
    ComposicaoItem.objects.bulk_create(itens, batch_size=10000)
