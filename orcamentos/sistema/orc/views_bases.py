import os
from decimal import ROUND_DOWN, Decimal

from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auditoria import registrar
from .forms import ImportarBaseForm
from .importadores import sinapi
from .models import BaseReferencia, Composicao, Insumo
from .permissoes import exige
from .views_cadastros import baixar, form_page


@exige("ver")
def bases(request):
    return render(request, "orc/bases.html", {"bases": BaseReferencia.objects.select_related("importado_por")})


@exige("importar_base")
def base_importar(request):
    form = ImportarBaseForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        up = request.FILES["arquivo"]
        if up.size > settings.UPLOAD_MAX_BYTES:
            messages.error(request, "Arquivo maior que o limite permitido.")
            return form_page(request, form, "Importar base oficial", "bases", multipart=True)
        uf, regime = form.cleaned_data["uf"].upper(), form.cleaned_data["regime"]
        sha = sinapi.sha256_arquivo(b"".join(up.chunks()))
        up.seek(0)
        dup = BaseReferencia.objects.filter(sha256=sha, uf=uf, regime=regime, status__in=["previa", "confirmada"]).first()
        if dup:
            messages.error(request, f"Este arquivo já foi importado para {uf}/{regime} ({dup}, situação: "
                                    f"{dup.get_status_display()}). Importação duplicada recusada.")
            return redirect("base", pk=dup.pk)
        base = BaseReferencia(fonte="SINAPI", uf=uf, regime=regime, nome_arquivo=up.name, sha256=sha,
                              leiaute=sinapi.LEIAUTE, competencia=timezone.localdate().replace(day=1),
                              importado_por=request.user)
        base.arquivo.save(f"{sha[:16]}_{os.path.basename(up.name)}", File(up), save=False)
        res = sinapi.analisar(base.arquivo.path, uf=uf, regime=regime)
        base.relatorio = {"erros": res.erros, "avisos": res.avisos, "estatisticas": res.estatisticas,
                          "planilha": res.nome_planilha}
        if not res.valido:
            base.status = "cancelada"
            base.save()
            registrar(request, "base.importacao_recusada", base, up.name, erros=res.erros[:20])
            messages.error(request, "Arquivo recusado: estrutura ou dados incompatíveis. Veja os erros.")
            return redirect("base", pk=base.pk)
        base.competencia = res.competencia
        base.data_emissao = res.emissao
        base.localidade = res.localidade
        base.encargos_horista = res.encargos_horista
        base.encargos_mensalista = res.encargos_mensalista
        with transaction.atomic():
            base.save()
            sinapi.gravar(res, base)
        conflito = BaseReferencia.objects.filter(fonte=base.fonte, uf=uf, regime=regime, competencia=base.competencia,
                                                 status="confirmada").exclude(pk=base.pk).first()
        if conflito:
            messages.warning(request, f"Já existe base confirmada para esta competência ({conflito}). "
                                      "A confirmação desta será recusada.")
        registrar(request, "base.previa", base, str(base), estatisticas=res.estatisticas)
        messages.success(request, "Arquivo analisado. Confira a prévia antes de confirmar.")
        return redirect("base", pk=base.pk)
    return form_page(request, form, "Importar base oficial (SINAPI)", "bases", multipart=True,
                     ajuda="O arquivo original é preservado com hash SHA-256. Nada é usado em orçamentos antes da "
                           "confirmação. Preços em branco ficam como 'sem preço', nunca zero.")


@exige("ver")
def base(request, pk):
    b = get_object_or_404(BaseReferencia, pk=pk)
    amostra_ins = b.insumos.order_by("linha")[:10]
    amostra_comp = b.composicoes.order_by("linha")[:10]
    return render(request, "orc/base_referencia.html", {"base": b, "rel": b.relatorio, "amostra_ins": amostra_ins,
                                             "amostra_comp": amostra_comp,
                                             "n_ins": b.insumos.count(), "n_comp": b.composicoes.count()})


@exige("importar_base")
@require_POST
def base_confirmar(request, pk):
    b = get_object_or_404(BaseReferencia, pk=pk, status="previa")
    if BaseReferencia.objects.filter(fonte=b.fonte, uf=b.uf, regime=b.regime, competencia=b.competencia,
                                     status="confirmada").exists():
        messages.error(request, "Já existe base confirmada para esta fonte/UF/competência/regime.")
        return redirect("base", pk=pk)
    b.status, b.confirmado_por, b.confirmado_em = "confirmada", request.user, timezone.now()
    b.save()
    registrar(request, "base.confirmar", b, str(b))
    messages.success(request, f"Base {b} confirmada e disponível para orçamentos.")
    return redirect("base", pk=pk)


@exige("importar_base")
@require_POST
def base_cancelar(request, pk):
    b = get_object_or_404(BaseReferencia, pk=pk, status="previa")
    with transaction.atomic():
        b.insumos.all().delete()
        b.composicoes.all().delete()
        b.status = "cancelada"
        b.save()
    registrar(request, "base.cancelar", b, str(b))
    messages.info(request, "Prévia cancelada. O arquivo original foi mantido para rastreabilidade.")
    return redirect("bases")


@exige("ver")
def base_arquivo(request, pk):
    b = get_object_or_404(BaseReferencia, pk=pk)
    return baixar(b.arquivo, b.nome_arquivo)


def _filtro_texto(qs, termos):
    for t in termos:
        qs = qs.filter(Q(descricao__unaccent__icontains=t) | Q(codigo=t))
    return qs


@exige("ver")
def consulta(request):
    confirmadas = BaseReferencia.objects.filter(status="confirmada")
    base_id = request.GET.get("base") or (confirmadas.first().pk if confirmadas.exists() else None)
    b = confirmadas.filter(pk=base_id).first() if base_id else None
    tipo = request.GET.get("tipo", "composicao")
    q = request.GET.get("q", "").strip()
    unidade = request.GET.get("unidade", "").strip().upper()
    resultados = None
    if b and (q or unidade):
        Modelo = Composicao if tipo == "composicao" else Insumo
        qs = Modelo.objects.filter(base=b)
        qs = _filtro_texto(qs, q.split())
        if unidade:
            qs = qs.filter(unidade__iexact=unidade)
        resultados = Paginator(qs.order_by("descricao"), 50).get_page(request.GET.get("pagina"))
    return render(request, "orc/consulta.html", {"bases": confirmadas, "base": b, "tipo": tipo, "q": q,
                                                 "unidade": unidade, "resultados": resultados,
                                                 "selecionar": request.GET.get("selecionar")})


@exige("ver")
def composicao(request, base_pk, codigo):
    b = get_object_or_404(BaseReferencia, pk=base_pk)
    c = get_object_or_404(Composicao, base=b, codigo=codigo)
    linhas, total, completo = [], Decimal(0), True
    for it in c.itens.all():
        if it.tipo == "INSUMO":
            ref = Insumo.objects.filter(base=b, codigo=it.codigo).first()
            preco = ref.preco if ref else None
        else:
            ref = Composicao.objects.filter(base=b, codigo=it.codigo).first()
            preco = ref.custo if ref else None
        parcial = None
        if preco is not None and it.coeficiente is not None:
            parcial = (it.coeficiente * preco).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            total += parcial
        else:
            completo = False
        linhas.append({"item": it, "preco": preco, "parcial": parcial})
    return render(request, "orc/composicao.html", {"base": b, "c": c, "linhas": linhas,
                                                   "total": total if completo else None, "completo": completo})
