"""Cálculos determinísticos do orçamento (Decimal, política de arredondamento explícita).

Política (registrada em cada versão):
- Quantidade: avaliada pela fórmula da memória e arredondada (meio para cima) em `casas_quantidade`.
- BDI (%): calculado a partir dos componentes e arredondado (meio para cima) em 2 casas.
- Preço unitário = custo unitário × (1 + BDI), arredondado ou truncado (modo do orçamento) em `casas_preco`.
- Custo total do item = quantidade × custo unitário, mesmo modo, 2 casas.
- Preço total do item = quantidade × preço unitário, mesmo modo, 2 casas.
- Totais = soma dos totais dos itens. Itens sem custo ou sem quantidade não entram e são listados como pendência.
- Composição própria: parcial de cada insumo = coeficiente × preço unitário truncado em 2 casas (mesma regra da
  coluna "Custo Total" do analítico do SINAPI, que usa TRUNC(coeficiente × custo; 2)); custo = soma das parciais.
"""
import hashlib
import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.utils import timezone

from .expressoes import ErroExpressao, avaliar, para_decimal

D = Decimal
CEM = D(100)


def q(valor, casas=2, modo=ROUND_HALF_UP):
    if valor is None:
        return None
    return valor.quantize(D(1).scaleb(-int(casas)), rounding=modo)


def modo_de(orc):
    return ROUND_DOWN if orc.modo_arredondamento == "ROUND_DOWN" else ROUND_HALF_UP


# --------------------------------------------------------------------------------------------
# BDI
# --------------------------------------------------------------------------------------------


def bdi_componentes(ac, s, r, g, df, l, i):
    """BDI (%) = ((1+AC+S+R+G)(1+DF)(1+L)/(1−I) − 1) × 100, componentes em %.

    Forma usual de cálculo por componentes adotada em referenciais públicos. A fonte normativa aplicável a cada
    contratação (edital, acórdão, regulamento local) deve ser registrada na justificativa do BDI.
    """
    ac, s, r, g, df, l, i = (x / CEM for x in (ac, s, r, g, df, l, i))
    if i >= 1:
        raise ValueError("Tributos (I) devem ser menores que 100%.")
    bdi = ((1 + ac + s + r + g) * (1 + df) * (1 + l) / (1 - i)) - 1
    return q(bdi * CEM, 2)


def bdi_servicos(orc):
    if orc.bdi_formula == "manual":
        if orc.bdi_manual is None:
            return None
        return q(orc.bdi_manual, 2)
    return bdi_componentes(orc.bdi_ac, orc.bdi_s, orc.bdi_r, orc.bdi_g, orc.bdi_df, orc.bdi_l, orc.bdi_i)


# --------------------------------------------------------------------------------------------
# Composição própria
# --------------------------------------------------------------------------------------------


def custo_item_cp(item, base):
    """Retorna (preco_unitario, fonte, alerta) de um item de composição própria. Preço None se indisponível."""
    from .models import Composicao, Insumo

    if item.tipo == "insumo_base":
        if base is None:
            return None, "", "Sem base selecionada para buscar o insumo."
        ins = Insumo.objects.filter(base=base, codigo=item.codigo_ref).first()
        if not ins:
            return None, "", f"Insumo {item.codigo_ref} não existe em {base.rotulo_curto}."
        if ins.preco is None:
            return None, f"{base.rotulo_curto} insumo {ins.codigo}", "Insumo sem preço na base."
        return ins.preco, f"{base.rotulo_curto} insumo {ins.codigo}", ""
    if item.tipo == "composicao_base":
        if base is None:
            return None, "", "Sem base selecionada para buscar a composição."
        comp = Composicao.objects.filter(base=base, codigo=item.codigo_ref).first()
        if not comp:
            return None, "", f"Composição {item.codigo_ref} não existe em {base.rotulo_curto}."
        if comp.custo is None:
            return None, f"{base.rotulo_curto} composição {comp.codigo}", "Composição sem custo na base."
        return comp.custo, f"{base.rotulo_curto} composição {comp.codigo}", ""
    if item.tipo == "cotacao":
        c = item.cotacao
        alerta = ""
        if c.validade and c.validade < timezone.localdate():
            alerta = f"Cotação vencida em {c.validade:%d/%m/%Y}."
        if c.descartada:
            alerta = "Cotação marcada como descartada."
        return c.preco_com_frete, f"Cotação {c.fornecedor} {c.data:%d/%m/%Y}", alerta
    if item.tipo == "mo_propria":
        if item.preco_informado is None or item.encargos_pct is None:
            return None, item.fonte, "Mão de obra sem custo ou encargos."
        return item.preco_informado * (1 + item.encargos_pct / CEM), f"{item.fonte} (+{item.encargos_pct}% encargos)", ""
    return item.preco_informado, item.fonte, "" if item.preco_informado is not None else "Sem preço."


def calcular_cp(cp, base):
    linhas, total, alertas, completo = [], D(0), [], True
    for it in cp.itens.select_related("cotacao").all():
        preco, fonte, alerta = custo_item_cp(it, base)
        parcial = None
        if preco is not None:
            parcial = q(it.coeficiente * preco, 2, ROUND_DOWN)
            total += parcial
        else:
            completo = False
        if alerta:
            alertas.append(f"{it.descricao[:40]}: {alerta}")
        linhas.append({
            "tipo": it.get_tipo_display(), "codigo": it.codigo_ref, "descricao": it.descricao, "unidade": it.unidade,
            "coeficiente": it.coeficiente, "preco": preco, "parcial": parcial, "fonte": fonte, "alerta": alerta,
        })
    return {"linhas": linhas, "custo": total if completo and linhas else None, "alertas": alertas,
            "completo": completo and bool(linhas)}


# --------------------------------------------------------------------------------------------
# Itens e orçamento
# --------------------------------------------------------------------------------------------


def valores_variaveis(item):
    """Converte o JSON de variáveis em {nome: Decimal|str}. Inclui variáveis geométricas do ambiente."""
    vals = {}
    if item.ambiente_id:
        vals.update(item.ambiente.variaveis())
    for nome, info in (item.variaveis or {}).items():
        bruto = info.get("valor") if isinstance(info, dict) else info
        try:
            vals[nome] = para_decimal(bruto)
        except ErroExpressao:
            vals[nome] = str(bruto)
    return vals


def calcular_quantidade(item, casas):
    try:
        v = avaliar(item.formula, valores_variaveis(item))
    except ErroExpressao as exc:
        return None, str(exc)
    if not isinstance(v, D) or isinstance(v, bool):
        return None, "A fórmula da quantidade não resultou em número."
    if v < 0:
        return None, "Quantidade negativa."
    return q(v, casas, ROUND_HALF_UP), ""


def _s(v):
    return None if v is None else str(v)


def calcular_orcamento(orc):
    """Calcula todo o orçamento e devolve um dicionário serializável (base do snapshot de versão e das telas)."""
    from .models import Empresa

    modo = modo_de(orc)
    bdi_s = bdi_servicos(orc)
    bdi_e = q(orc.bdi_equip, 2) if orc.bdi_equip is not None else bdi_s
    itens_out, alertas = [], []
    tot = {"confirmado": {"custo": D(0), "preco": D(0)}, "condicional": {"custo": D(0), "preco": D(0)}}
    vistos = {}

    itens = list(orc.itens.select_related("ambiente").all())
    for n, it in enumerate(itens, start=1):
        numero = it.numero or str(n)
        qtd, erro_qtd = calcular_quantidade(it, orc.casas_quantidade)
        bdi = bdi_e if it.bdi_tipo == "equipamento" else bdi_s
        custo_u = it.custo_unitario
        preco_u = custo_t = preco_t = None
        pend = []
        if erro_qtd:
            pend.append(f"Quantidade: {erro_qtd}")
        if custo_u is None:
            pend.append("Sem custo unitário (não entra no total).")
        if bdi is None:
            pend.append("BDI não definido.")
        if custo_u is not None and bdi is not None:
            preco_u = q(custo_u * (1 + bdi / CEM), orc.casas_preco, modo)
        if qtd is not None and custo_u is not None:
            custo_t = q(qtd * custo_u, 2, modo)
        if qtd is not None and preco_u is not None:
            preco_t = q(qtd * preco_u, 2, modo)
        if qtd is not None and qtd == 0:
            pend.append("Quantidade igual a zero.")
        if orc.base_id and it.tipo_ref in ("composicao", "insumo") and it.ref_base_rotulo and \
                it.ref_base_rotulo != orc.base.rotulo_curto:
            pend.append(f"Referência de base diferente da base do orçamento ({it.ref_base_rotulo}).")
        pct_as = (it.ref_detalhe or {}).get("pct_as")
        if pct_as and D(str(pct_as)) > 0:
            pend.append(f"Custo com {D(str(pct_as)) * CEM:.2f}% de preços atribuídos de São Paulo (%AS) — ver nota SINAPI.")

        chave_dup = (it.tipo_ref, it.ref_codigo, it.ambiente_id) if it.ref_codigo else None
        if chave_dup:
            if chave_dup in vistos:
                pend.append(f"Possível duplicidade com o item {vistos[chave_dup]} (mesma referência e ambiente).")
            else:
                vistos[chave_dup] = numero

        if preco_t is not None and custo_t is not None and not pend_bloqueia(pend):
            tot[it.status]["custo"] += custo_t
            tot[it.status]["preco"] += preco_t

        for p in pend:
            alertas.append({"item": numero, "etapa": it.etapa, "mensagem": p})

        itens_out.append({
            "id": it.id, "numero": numero, "etapa": it.etapa, "ambiente": it.ambiente.nome if it.ambiente else "",
            "status": it.status, "tipo_ref": it.tipo_ref, "base": it.ref_base_rotulo, "codigo": it.ref_codigo,
            "descricao_oficial": it.ref_descricao, "complemento": it.complemento, "unidade": it.ref_unidade,
            "data_base": it.ref_data_base, "regime": it.ref_regime, "fonte": it.fonte,
            "formula": it.formula, "variaveis": it.variaveis, "variaveis_ambiente": variaveis_ambiente_usadas(it),
            "quantidade": _s(qtd), "custo_unitario": _s(custo_u), "bdi_tipo": it.bdi_tipo, "bdi": _s(bdi),
            "preco_unitario": _s(preco_u), "custo_total": _s(custo_t), "preco_total": _s(preco_t),
            "pendencias": pend, "observacao": it.observacao, "detalhe": it.ref_detalhe,
            "origem_modelo": it.origem_modelo, "chave_etapa": it.chave_etapa,
        })

    # Duplicidades por regra de modelo ("etapa X já inclui Y")
    alertas.extend(duplicidades_por_regra(orc, itens))

    empresa = Empresa.objects.first()
    base = orc.base
    dados = {
        "gerado_em": timezone.now().isoformat(timespec="seconds"),
        "orcamento": {"id": orc.id, "titulo": orc.titulo, "finalidade": orc.get_finalidade_display(),
                      "premissas": orc.premissas},
        "empresa": {"razao_social": empresa.razao_social, "cnpj": empresa.cnpj, "nome_comercial": empresa.nome_comercial,
                    "regime_tributario": empresa.regime_tributario} if empresa else {},
        "obra": {"nome": orc.obra.nome, "municipio": orc.obra.municipio, "uf": orc.obra.uf,
                 "endereco": orc.obra.endereco},
        "cliente": {"nome": orc.obra.cliente.nome, "tipo": orc.obra.cliente.get_tipo_display()},
        "base": {"rotulo": base.rotulo_curto, "descricao": str(base), "competencia": f"{base.competencia:%m/%Y}",
                 "regime": base.get_regime_display(), "arquivo": base.nome_arquivo, "sha256": base.sha256,
                 "leiaute": base.leiaute} if base else None,
        "politica": {"modo": orc.get_modo_arredondamento_display(), "modo_codigo": orc.modo_arredondamento,
                     "casas_preco": orc.casas_preco, "casas_quantidade": orc.casas_quantidade},
        "bdi": {"forma": orc.get_bdi_formula_display(), "formula": orc.bdi_formula,
                "ac": _s(orc.bdi_ac), "s": _s(orc.bdi_s), "r": _s(orc.bdi_r), "g": _s(orc.bdi_g),
                "df": _s(orc.bdi_df), "l": _s(orc.bdi_l), "i": _s(orc.bdi_i), "manual": _s(orc.bdi_manual),
                "servicos": _s(bdi_s), "equipamentos": _s(bdi_e), "equip_diferenciado": orc.bdi_equip is not None,
                "justificativa": orc.justificativa_bdi},
        "itens": itens_out,
        "totais": {k: {kk: str(vv) for kk, vv in v.items()} for k, v in tot.items()},
        "alertas": alertas,
    }
    return dados


def _fmt_dec(v):
    txt = format(v.normalize(), "f") if isinstance(v, D) else str(v)
    return txt


def variaveis_ambiente_usadas(item):
    """Só as dimensões do ambiente efetivamente usadas na fórmula (e não sobrescritas por variável do item)."""
    if not item.ambiente_id:
        return {}
    from .expressoes import variaveis_usadas
    try:
        usadas = variaveis_usadas(item.formula)
    except ErroExpressao:
        return {}
    proprias = set((item.variaveis or {}).keys())
    return {k: _fmt_dec(v) for k, v in item.ambiente.variaveis().items() if k in usadas and k not in proprias}


def pend_bloqueia(pend):
    """Pendências que impedem o item de entrar no total (as demais são avisos)."""
    return any(p.startswith(("Quantidade:", "Sem custo", "BDI não")) for p in pend)


def duplicidades_por_regra(orc, itens):
    from .models import RegraEtapa

    alertas = []
    por_modelo = {}
    for it in itens:
        if it.origem_modelo and it.chave_etapa:
            por_modelo.setdefault((it.origem_modelo, it.ambiente_id), {})[it.chave_etapa] = it
    for (modelo_nome, _amb), etapas in por_modelo.items():
        regras = {r.chave: r for r in RegraEtapa.objects.filter(modelo__nome=modelo_nome)}
        for chave, it in etapas.items():
            regra = regras.get(chave)
            if not regra:
                continue
            for incluida in RegraEtapa.lista(regra.inclui):
                if incluida in etapas:
                    alertas.append({"item": it.numero or "", "etapa": it.etapa,
                                    "mensagem": f"Duplicidade: '{regra.etapa}' já inclui '{etapas[incluida].etapa}'."})
            for dep in RegraEtapa.lista(regra.depende_de):
                if dep not in etapas:
                    alertas.append({"item": it.numero or "", "etapa": it.etapa,
                                    "mensagem": f"Dependência ausente: etapa '{dep}' não está no orçamento."})
    return alertas


def hash_dados(dados):
    bruto = json.dumps(dados, sort_keys=True, ensure_ascii=False, default=str).encode()
    return hashlib.sha256(bruto).hexdigest()
