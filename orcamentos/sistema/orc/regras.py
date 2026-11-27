"""Aplicação de modelos de serviço: perguntas -> etapas sugeridas, por regras cadastradas (sem IA)."""
from decimal import Decimal

from .expressoes import ErroExpressao, avaliar, para_decimal
from .models import RegraEtapa
from .referencias import snapshot_referencia


def ler_respostas(modelo, dados):
    """Converte o POST em {chave: valor}. Retorna (respostas, erros)."""
    respostas, erros = {}, []
    for p in modelo.perguntas.all():
        bruto = dados.get(f"p_{p.chave}", "")
        bruto = bruto.strip() if isinstance(bruto, str) else bruto
        if bruto in ("", None):
            if p.obrigatoria:
                erros.append(f"Responda: {p.texto}")
            respostas[p.chave] = None
            continue
        if p.tipo == "numero":
            try:
                v = para_decimal(bruto)
            except ErroExpressao:
                erros.append(f"Número inválido em: {p.texto}")
                continue
            if v is not None and v < 0:
                erros.append(f"Valor negativo em: {p.texto}")
            respostas[p.chave] = v
        elif p.tipo == "sim_nao":
            respostas[p.chave] = bruto in ("sim", "1", "true", "on")
        elif p.tipo == "escolha":
            validos = [v for v, _ in p.lista_opcoes()]
            if bruto not in validos:
                erros.append(f"Opção inválida em: {p.texto}")
            respostas[p.chave] = bruto
        else:
            respostas[p.chave] = str(bruto)
    return respostas, erros


def sugerir(modelo, respostas, base):
    regras = list(modelo.regras.all())
    sugestoes = []
    ativas = {}
    for r in regras:
        s = {"regra": r, "ativa": True, "erro": "", "quantidade": None, "ref": None, "erro_ref": "",
             "bloqueada_por": "", "deps_faltando": [], "nota": ""}
        if r.condicao.strip():
            try:
                s["ativa"] = bool(avaliar(r.condicao, respostas))
            except ErroExpressao as exc:
                s["ativa"] = False
                if str(exc).startswith("Variável"):
                    s["nota"] = f"Não avaliada: {exc} (pergunta opcional não respondida)."
                else:
                    s["erro"] = f"Condição: {exc}"
        if s["ativa"] and r.formula_quantidade.strip():
            try:
                v = avaliar(r.formula_quantidade, respostas)
                if not isinstance(v, Decimal):
                    raise ErroExpressao("fórmula não numérica")
                s["quantidade"] = v
            except ErroExpressao as exc:
                s["erro"] = f"Quantidade: {exc}"
        if s["ativa"] and r.tipo_ref != "nenhuma":
            s["ref"], s["erro_ref"] = snapshot_referencia(r.tipo_ref, r.codigo_ref, base)
        sugestoes.append(s)
        if s["ativa"]:
            ativas[r.chave] = s
    for s in sugestoes:
        r = s["regra"]
        if not s["ativa"]:
            continue
        if r.classificacao == "item":
            for chave in RegraEtapa.lista(r.inclui):
                if chave in ativas and ativas[chave]["regra"].classificacao == "item":
                    ativas[chave]["bloqueada_por"] = r.etapa
        s["deps_faltando"] = [d for d in RegraEtapa.lista(r.depende_de) if d not in ativas]
    return sugestoes


def criavel(s):
    r = s["regra"]
    return (s["ativa"] and r.classificacao == "item" and not s["bloqueada_por"] and not s["erro"]
            and r.formula_quantidade.strip() != "")
