"""Busca de referências e montagem do snapshot copiado para o item de orçamento."""
from .calculo import calcular_cp
from .models import Composicao, ComposicaoPropria, Cotacao, Insumo


def _s(v):
    return None if v is None else str(v)


def snapshot_referencia(tipo, codigo, base, cotacao_id=None):
    """Retorna (dados_snapshot, erro). `dados_snapshot` tem os campos ref_* do ItemOrcamento."""
    codigo = (codigo or "").strip()
    if tipo in ("composicao", "insumo"):
        if base is None:
            return None, "Selecione a base de referência do orçamento antes de incluir itens da base."
        if tipo == "composicao":
            obj = Composicao.objects.filter(base=base, codigo=codigo).first()
            if not obj:
                return None, f"Composição {codigo} não encontrada em {base.rotulo_curto}."
            detalhe = {
                "grupo": obj.grupo, "situacao": obj.situacao, "pct_as": _s(obj.pct_atribuido_sp),
                "linha_arquivo": obj.linha, "arquivo": base.nome_arquivo, "sha256_arquivo": base.sha256,
                "analitico": [{"tipo": i.tipo, "codigo": i.codigo, "descricao": i.descricao, "unidade": i.unidade,
                               "coeficiente": _s(i.coeficiente), "situacao": i.situacao} for i in obj.itens.all()],
            }
            custo = obj.custo
        else:
            obj = Insumo.objects.filter(base=base, codigo=codigo).first()
            if not obj:
                return None, f"Insumo {codigo} não encontrado em {base.rotulo_curto}."
            detalhe = {"classificacao": obj.classificacao, "origem_preco": obj.origem_preco,
                       "linha_arquivo": obj.linha, "arquivo": base.nome_arquivo, "sha256_arquivo": base.sha256}
            custo = obj.preco
        return {
            "tipo_ref": tipo, "ref_base_rotulo": base.rotulo_curto, "ref_codigo": obj.codigo,
            "ref_descricao": obj.descricao, "ref_unidade": obj.unidade,
            "ref_data_base": f"{base.competencia:%m/%Y}", "ref_regime": base.regime, "ref_detalhe": detalhe,
            "custo_unitario": custo,
            "fonte": f"{base} — arquivo {base.nome_arquivo}, linha {obj.linha}",
        }, None
    if tipo == "cp":
        cp = ComposicaoPropria.objects.filter(codigo=codigo.upper()).first()
        if not cp:
            return None, f"Composição própria {codigo} não encontrada."
        calc = calcular_cp(cp, base)
        return {
            "tipo_ref": "cp", "ref_base_rotulo": "Composição própria", "ref_codigo": cp.codigo,
            "ref_descricao": cp.descricao, "ref_unidade": cp.unidade,
            "ref_data_base": f"{base.competencia:%m/%Y}" if base else "", "ref_regime": base.regime if base else "",
            "ref_detalhe": {"linhas": [{k: _s(v) if k in ("coeficiente", "preco", "parcial") else v
                                        for k, v in l.items()} for l in calc["linhas"]],
                            "alertas": calc["alertas"], "premissas": cp.premissas,
                            "justificativa": cp.justificativa, "memoria": cp.memoria},
            "custo_unitario": calc["custo"],
            "fonte": f"Composição própria {cp.codigo} (não é código oficial)",
        }, None
    if tipo == "cotacao":
        c = Cotacao.objects.filter(pk=cotacao_id).first()
        if not c:
            return None, "Cotação não encontrada."
        return {
            "tipo_ref": "cotacao", "ref_base_rotulo": "Cotação", "ref_codigo": f"COT-{c.pk}",
            "ref_descricao": c.especificacao, "ref_unidade": c.unidade,
            "ref_data_base": f"{c.data:%m/%Y}", "ref_regime": "",
            "ref_detalhe": {"fornecedor": c.fornecedor, "data": f"{c.data:%d/%m/%Y}",
                            "validade": f"{c.validade:%d/%m/%Y}" if c.validade else "",
                            "preco_unitario": _s(c.preco_unitario), "frete": _s(c.frete),
                            "quantidade_cotada": _s(c.quantidade), "inclui_instalacao": c.inclui_instalacao,
                            "condicoes": c.condicoes, "prazo": c.prazo},
            "custo_unitario": c.preco_com_frete,
            "fonte": f"Cotação {c.fornecedor} de {c.data:%d/%m/%Y}",
        }, None
    if tipo == "sem_ref":
        return {"tipo_ref": "sem_ref", "ref_base_rotulo": "", "ref_codigo": "", "ref_descricao": "",
                "ref_unidade": "", "ref_data_base": "", "ref_regime": "", "ref_detalhe": {},
                "custo_unitario": None, "fonte": "Pendente de referência"}, None
    return None, "Tipo de referência inválido."
