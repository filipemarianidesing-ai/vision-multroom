from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import exportar
from .auditoria import registrar
from .calculo import calcular_orcamento, hash_dados
from .expressoes import variaveis_usadas
from .forms import ItemOrcamentoForm, NovoOrcamentoForm, OrcamentoForm, VersaoForm, variaveis_para_texto
from .models import (AtualizacaoPrecos, BaseReferencia, ItemOrcamento, ModeloServico, Obra, Orcamento,
                     VersaoOrcamento)
from .permissoes import exige
from .referencias import snapshot_referencia
from .regras import criavel, ler_respostas, sugerir
from .views_cadastros import form_page


def _proxima_ordem(orc):
    return (orc.itens.aggregate(m=Max("ordem"))["m"] or 0) + 10


@exige("editar_orcamento")
def orcamento_novo(request, obra_pk):
    obra = get_object_or_404(Obra, pk=obra_pk)
    form = NovoOrcamentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        o = form.save(commit=False)
        o.obra, o.criado_por = obra, request.user
        o.save()
        registrar(request, "orcamento.criar", o, o.titulo)
        messages.success(request, "Orçamento criado. Defina BDI e arredondamento em 'Parâmetros'.")
        return redirect("orcamento", pk=o.pk)
    return form_page(request, form, f"Novo orçamento — {obra.nome}", "obras",
                     ajuda="A base fica fixa no orçamento. Trocar de base só pela ação 'Atualizar preços', que compara "
                           "valores e gera versão.")


@exige("ver")
def orcamento(request, pk):
    orc = get_object_or_404(Orcamento.objects.select_related("obra__cliente", "base"), pk=pk)
    dados = calcular_orcamento(orc)
    return render(request, "orc/orcamento.html", {"orc": orc, "dados": dados, "versoes": orc.versoes.all(),
                                                  "modelos": ModeloServico.objects.filter(ativo=True),
                                                  "rascunho": True})


@exige("editar_orcamento")
def orcamento_editar(request, pk):
    orc = get_object_or_404(Orcamento, pk=pk)
    form = OrcamentoForm(request.POST or None, instance=orc)
    if request.method == "POST" and form.is_valid():
        from .auditoria import diferencas
        mud = diferencas(form)
        form.save()
        registrar(request, "orcamento.parametros", orc, orc.titulo, alteracoes=mud)
        messages.success(request, "Parâmetros salvos.")
        return redirect("orcamento", pk=pk)
    return form_page(request, form, f"Parâmetros — {orc.titulo}", "obras",
                     ajuda="BDI por componentes: ((1+AC+S+R+G)(1+DF)(1+L)/(1−I)) − 1. Confira no edital/contrato e "
                           "registre a fonte na justificativa. Não inclua no BDI custos já orçados como itens "
                           "(ex.: mobilização, administração local, transporte).")


def _aplicar_form_no_item(item, form, orc):
    cd = form.cleaned_data
    item.etapa = cd["etapa"]
    item.ambiente = cd["ambiente"]
    item.status = cd["status"]
    item.complemento = cd["complemento"]
    item.formula = cd["formula"]
    item.variaveis = cd["variaveis"]
    item.bdi_tipo = cd["bdi_tipo"]
    item.observacao = cd["observacao"]


@exige("editar_orcamento")
def item_form(request, orc_pk, pk=None):
    orc = get_object_or_404(Orcamento.objects.select_related("base", "obra"), pk=orc_pk)
    item = get_object_or_404(ItemOrcamento, pk=pk, orcamento=orc) if pk else None
    inicial = {"status": "confirmado", "bdi_tipo": "servico", "tipo_ref": "composicao",
               "codigo": request.GET.get("codigo", ""), "formula": "quantidade"}
    if request.GET.get("tipo"):
        inicial["tipo_ref"] = request.GET["tipo"]
    if item:
        inicial = {"etapa": item.etapa, "ambiente": item.ambiente_id, "status": item.status,
                   "tipo_ref": item.tipo_ref, "codigo": item.ref_codigo if item.tipo_ref != "cotacao" else "",
                   "cotacao": item.ref_codigo.replace("COT-", "") if item.tipo_ref == "cotacao" else None,
                   "complemento": item.complemento, "formula": item.formula,
                   "variaveis": variaveis_para_texto(item.variaveis), "bdi_tipo": item.bdi_tipo,
                   "observacao": item.observacao}
    form = ItemOrcamentoForm(request.POST or None, initial=inicial, obra=orc.obra)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        ref_mudou = (item is None or cd["tipo_ref"] != item.tipo_ref or
                     (cd["tipo_ref"] != "cotacao" and (cd["codigo"] or "").strip().upper() != item.ref_codigo.upper()) or
                     (cd["tipo_ref"] == "cotacao" and f"COT-{cd['cotacao'].pk}" != item.ref_codigo))
        snap = None
        if ref_mudou:
            snap, erro = snapshot_referencia(cd["tipo_ref"], cd["codigo"], orc.base,
                                             cd["cotacao"].pk if cd.get("cotacao") else None)
            if erro:
                form.add_error("codigo", erro)
                return form_page(request, form, "Item do orçamento", "obras")
        novo = item is None
        if novo:
            item = ItemOrcamento(orcamento=orc, ordem=_proxima_ordem(orc))
        _aplicar_form_no_item(item, form, orc)
        if snap:
            for k, v in snap.items():
                setattr(item, k, v)
        item.save()
        registrar(request, "item.criar" if novo else "item.editar", item, f"{orc.titulo}: {item.etapa}",
                  referencia=f"{item.tipo_ref} {item.ref_codigo}", custo=str(item.custo_unitario),
                  formula=item.formula, variaveis=item.variaveis)
        messages.success(request, "Item salvo." + ("" if not snap or snap["custo_unitario"] is not None
                                                     else " Atenção: referência sem custo — não entra no total."))
        return redirect("orcamento", pk=orc.pk)
    ajuda = ("Ao editar, o custo copiado da referência só muda se você trocar a referência. Atualização de preços é "
             "uma ação separada, com comparação e versão.")
    return form_page(request, form, "Item do orçamento", "obras", ajuda=ajuda)


@exige("editar_orcamento")
@require_POST
def item_excluir(request, pk):
    item = get_object_or_404(ItemOrcamento, pk=pk)
    orc_pk = item.orcamento_id
    registrar(request, "item.excluir", item, item.etapa, referencia=f"{item.tipo_ref} {item.ref_codigo}")
    item.delete()
    messages.success(request, "Item excluído.")
    return redirect("orcamento", pk=orc_pk)


@exige("editar_orcamento")
@require_POST
def item_mover(request, pk, direcao):
    item = get_object_or_404(ItemOrcamento, pk=pk)
    itens = list(item.orcamento.itens.all())
    i = itens.index(item)
    j = i - 1 if direcao == "cima" else i + 1
    if 0 <= j < len(itens):
        itens[i], itens[j] = itens[j], itens[i]
        for n, it in enumerate(itens):
            ItemOrcamento.objects.filter(pk=it.pk).update(ordem=(n + 1) * 10)
    return redirect("orcamento", pk=item.orcamento_id)


# ---------------------------------------------------------------- Modelos de serviço aplicados ao orçamento
@exige("editar_orcamento")
def aplicar_modelo(request, orc_pk):
    orc = get_object_or_404(Orcamento.objects.select_related("base", "obra"), pk=orc_pk)
    modelo = ModeloServico.objects.filter(pk=request.GET.get("modelo") or request.POST.get("modelo"), ativo=True).first()
    if not modelo:
        return render(request, "orc/modelo_escolher.html", {"orc": orc, "modelos": ModeloServico.objects.filter(ativo=True)})
    ambiente_id = request.POST.get("ambiente") or request.GET.get("ambiente") or ""
    ambiente = orc.obra.ambientes.filter(pk=ambiente_id).first() if ambiente_id else None
    ctx = {"orc": orc, "modelo": modelo, "perguntas": modelo.perguntas.all(), "ambientes": orc.obra.ambientes.all(),
           "ambiente": ambiente, "valores": request.POST}
    if request.method != "POST":
        return render(request, "orc/modelo_aplicar.html", ctx)
    respostas, erros = ler_respostas(modelo, request.POST)
    if erros:
        ctx["erros"] = erros
        return render(request, "orc/modelo_aplicar.html", ctx)
    sugestoes = sugerir(modelo, {k: v for k, v in respostas.items()}, orc.base)
    for s in sugestoes:
        s["criavel"] = criavel(s)
    if request.POST.get("acao") != "confirmar":
        ctx["sugestoes"] = sugestoes
        return render(request, "orc/modelo_aplicar.html", ctx)
    escolhidas = set(request.POST.getlist("etapa"))
    criados = 0
    variaveis = {p.chave: {"valor": str(respostas[p.chave]) if respostas[p.chave] is not None else "",
                           "origem": "F", "obs": p.texto} for p in modelo.perguntas.all()
                 if p.tipo == "numero" and respostas.get(p.chave) is not None}
    with transaction.atomic():
        for s in sugestoes:
            r = s["regra"]
            if r.chave not in escolhidas or not s["criavel"]:
                continue
            usadas = {k: v for k, v in variaveis.items() if k in variaveis_usadas(r.formula_quantidade)}
            item = ItemOrcamento(orcamento=orc, ordem=_proxima_ordem(orc), etapa=r.etapa, ambiente=ambiente,
                                 status=r.status_sugerido, complemento=r.complemento, formula=r.formula_quantidade,
                                 variaveis=usadas, observacao=r.observacao, origem_modelo=modelo.nome,
                                 chave_etapa=r.chave)
            snap = s["ref"] if s["ref"] else snapshot_referencia("sem_ref", "", orc.base)[0]
            if s["erro_ref"]:
                item.observacao = (item.observacao + "\n" if item.observacao else "") + f"Referência: {s['erro_ref']}"
            for k, v in snap.items():
                setattr(item, k, v)
            item.save()
            criados += 1
    registrar(request, "modelo.aplicar", orc, f"{modelo.nome} em {orc.titulo}",
              respostas={k: str(v) for k, v in respostas.items()}, etapas=sorted(escolhidas), criados=criados)
    messages.success(request, f"{criados} item(ns) incluído(s) a partir do modelo '{modelo.nome}'. Confira etapas, "
                              "referências e quantidades.")
    return redirect("orcamento", pk=orc.pk)


# ---------------------------------------------------------------- Atualização explícita de preços
def _comparar(orc, nova):
    linhas = []
    for it in orc.itens.all():
        lin = {"item": it, "antes": it.custo_unitario, "depois": it.custo_unitario, "situacao": "inalterado", "variacao": None,
               "snap": None}
        if it.tipo_ref in ("composicao", "insumo", "cp"):
            snap, erro = snapshot_referencia(it.tipo_ref, it.ref_codigo, nova)
            if erro:
                lin["situacao"] = f"não encontrado na nova base ({erro})"
            else:
                lin["snap"] = snap
                lin["depois"] = snap["custo_unitario"]
                if lin["depois"] is None:
                    lin["situacao"] = "sem custo na nova base"
                elif lin["antes"] is None:
                    lin["situacao"] = "passa a ter custo"
                elif lin["depois"] != lin["antes"]:
                    lin["situacao"] = "alterado"
                if lin["antes"] and lin["depois"] is not None:
                    lin["variacao"] = (lin["depois"] / lin["antes"] - 1) * 100
        linhas.append(lin)
    return linhas


def _criar_versao(request, orc, descricao, revisado_por=""):
    dados = calcular_orcamento(orc)
    ultimo = orc.versoes.aggregate(m=Max("numero"))["m"]
    numero = 0 if ultimo is None else ultimo + 1
    v = VersaoOrcamento(orcamento=orc, numero=numero, criado_por=request.user, descricao=descricao,
                        revisado_por=revisado_por, dados=dados,
                        total_confirmado=Decimal(dados["totais"]["confirmado"]["preco"]), sha256=hash_dados(dados))
    v.save()
    registrar(request, "versao.criar", v, f"{orc.titulo} {v.rotulo}: {descricao}", sha256=v.sha256)
    return v


@exige("editar_orcamento")
def atualizar_precos(request, orc_pk):
    orc = get_object_or_404(Orcamento.objects.select_related("base"), pk=orc_pk)
    opcoes = BaseReferencia.objects.filter(status="confirmada").exclude(pk=orc.base_id)
    nova = opcoes.filter(pk=request.POST.get("base") or request.GET.get("base")).first()
    if not nova:
        return render(request, "orc/atualizar_precos.html", {"orc": orc, "opcoes": opcoes})
    linhas = _comparar(orc, nova)
    if request.method == "POST" and request.POST.get("acao") == "aplicar":
        with transaction.atomic():
            ultima = orc.versoes.first()
            atual = calcular_orcamento(orc)
            if not ultima or _sem_carimbo(ultima.dados) != _sem_carimbo(atual):
                _criar_versao(request, orc, f"Estado antes da atualização de preços para {nova.rotulo_curto}")
            comp = []
            for lin in linhas:
                it = lin["item"]
                comp.append({"item": it.etapa, "codigo": it.ref_codigo, "antes": str(lin["antes"]),
                             "depois": str(lin["depois"]), "situacao": lin["situacao"]})
                if lin["snap"]:
                    for k, v in lin["snap"].items():
                        setattr(it, k, v)
                    it.save()
            anterior = orc.base
            orc.base = nova
            orc.save()
            AtualizacaoPrecos.objects.create(orcamento=orc, base_anterior=anterior, base_nova=nova, comparacao=comp,
                                             aplicado_por=request.user)
            v = _criar_versao(request, orc, f"Atualização de preços: {anterior.rotulo_curto if anterior else '—'} → "
                                            f"{nova.rotulo_curto}")
        messages.success(request, f"Preços atualizados para {nova}. Versão {v.rotulo} gerada; versões anteriores "
                                  "preservam os valores antigos.")
        return redirect("orcamento", pk=orc.pk)
    return render(request, "orc/atualizar_precos.html", {"orc": orc, "opcoes": opcoes, "nova": nova, "linhas": linhas})


def _sem_carimbo(d):
    d = dict(d)
    d.pop("gerado_em", None)
    return hash_dados(d)


# ---------------------------------------------------------------- Versões e exportação
@exige("salvar_versao")
def versao_nova(request, orc_pk):
    orc = get_object_or_404(Orcamento, pk=orc_pk)
    form = VersaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        v = _criar_versao(request, orc, form.cleaned_data["descricao"], form.cleaned_data["revisado_por"])
        messages.success(request, f"Versão {v.rotulo} salva e congelada.")
        return redirect("versao", pk=v.pk)
    dados = calcular_orcamento(orc)
    bloqueios = [a for a in dados["alertas"]]
    return form_page(request, form, f"Salvar versão — {orc.titulo}", "obras",
                     ajuda=f"A versão congela itens, referências, quantidades, BDI e totais. Há {len(bloqueios)} "
                           "alerta(s)/pendência(s) que ficarão registrados na versão.")


@exige("ver")
def versao(request, pk):
    v = get_object_or_404(VersaoOrcamento.objects.select_related("orcamento"), pk=pk)
    integro = hash_dados(v.dados) == v.sha256
    return render(request, "orc/orcamento.html", {"orc": v.orcamento, "dados": v.dados, "versao": v,
                                                  "versoes": v.orcamento.versoes.all(), "integro": integro,
                                                  "rascunho": False})


@exige("ver")
def exportar_view(request, orc_pk, formato, versao_pk=None):
    orc = get_object_or_404(Orcamento, pk=orc_pk)
    if versao_pk:
        v = get_object_or_404(VersaoOrcamento, pk=versao_pk, orcamento=orc)
        dados, rotulo = v.dados, v.rotulo
        meta = {"versao": v.rotulo, "sha256": v.sha256, "descricao": v.descricao, "revisado_por": v.revisado_por,
                "data": timezone.localtime(v.criado_em).strftime("%d/%m/%Y %H:%M")}
    else:
        dados, rotulo, meta = calcular_orcamento(orc), "RASCUNHO", {"versao": "RASCUNHO (não versionado)"}
    nome = f"orcamento-{orc.pk}-{rotulo}"
    registrar(request, f"exportar.{formato}", orc, f"{orc.titulo} {rotulo}")
    if formato == "xlsx":
        conteudo = exportar.gerar_xlsx(dados, meta)
        resp = HttpResponse(conteudo, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = f'attachment; filename="{nome}.xlsx"'
        return resp
    conteudo = exportar.gerar_pdf(dados, meta)
    resp = HttpResponse(conteudo, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{nome}.pdf"'
    return resp
