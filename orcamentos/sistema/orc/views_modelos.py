from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .auditoria import diferencas, registrar
from .calculo import calcular_cp
from .forms import ComposicaoPropriaForm, ItemCPForm, ModeloServicoForm, PerguntaForm, RegraEtapaForm, UsuarioForm
from .models import BaseReferencia, ComposicaoPropria, ItemComposicaoPropria, ModeloServico, Pergunta, RegraEtapa
from .permissoes import exige
from .views_cadastros import form_page

# ---------------------------------------------------------------- Modelos de serviço


@exige("ver")
def modelos(request):
    return render(request, "orc/modelos.html", {"modelos": ModeloServico.objects.all()})


@exige("ver")
def modelo(request, pk):
    m = get_object_or_404(ModeloServico, pk=pk)
    return render(request, "orc/modelo.html", {"m": m, "perguntas": m.perguntas.all(), "regras": m.regras.all()})


@exige("gerir_modelos")
def modelo_form(request, pk=None):
    obj = get_object_or_404(ModeloServico, pk=pk) if pk else None
    form = ModeloServicoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        m = form.save()
        registrar(request, "modelo.salvar", m, m.nome, alteracoes=mud)
        return redirect("modelo", pk=m.pk)
    return form_page(request, form, "Modelo de serviço", "modelos")


@exige("gerir_modelos")
def pergunta_form(request, modelo_pk=None, pk=None):
    obj = get_object_or_404(Pergunta, pk=pk) if pk else None
    m = obj.modelo if obj else get_object_or_404(ModeloServico, pk=modelo_pk)
    form = PerguntaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        p = form.save(commit=False)
        p.modelo = m
        p.save()
        registrar(request, "pergunta.salvar", p, f"{m.nome}: {p.chave}", alteracoes=mud)
        return redirect("modelo", pk=m.pk)
    return form_page(request, form, f"Pergunta — {m.nome}", "modelos")


@exige("gerir_modelos")
def regra_form(request, modelo_pk=None, pk=None):
    obj = get_object_or_404(RegraEtapa, pk=pk) if pk else None
    m = obj.modelo if obj else get_object_or_404(ModeloServico, pk=modelo_pk)
    form = RegraEtapaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        r = form.save(commit=False)
        r.modelo = m
        r.save()
        registrar(request, "regra.salvar", r, f"{m.nome}: {r.chave}", alteracoes=mud)
        return redirect("modelo", pk=m.pk)
    chaves = ", ".join(m.perguntas.values_list("chave", flat=True))
    return form_page(request, form, f"Regra/etapa — {m.nome}", "modelos",
                     ajuda=f"Variáveis disponíveis (chaves das perguntas): {chaves}. Exemplos de condição: "
                           "area_massa > 0 · estado == 'ruim' · fundo and tipo == 'nova'.")


@exige("gerir_modelos")
@require_POST
def excluir_pergunta_regra(request, tipo, pk):
    Modelo = Pergunta if tipo == "pergunta" else RegraEtapa
    obj = get_object_or_404(Modelo, pk=pk)
    m_pk = obj.modelo_id
    registrar(request, f"{tipo}.excluir", obj, obj.chave)
    obj.delete()
    return redirect("modelo", pk=m_pk)


# ---------------------------------------------------------------- Composições próprias


@exige("ver")
def cps(request):
    return render(request, "orc/cps.html", {"cps": ComposicaoPropria.objects.all()})


@exige("ver")
def cp(request, pk):
    c = get_object_or_404(ComposicaoPropria, pk=pk)
    bases = BaseReferencia.objects.filter(status="confirmada")
    base = bases.filter(pk=request.GET.get("base")).first() or bases.first()
    return render(request, "orc/cp.html", {"cp": c, "calc": calcular_cp(c, base), "bases": bases, "base": base})


@exige("editar_cadastros")
def cp_form(request, pk=None):
    obj = get_object_or_404(ComposicaoPropria, pk=pk) if pk else None
    form = ComposicaoPropriaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        c = form.save()
        registrar(request, "cp.salvar", c, c.codigo, alteracoes=mud)
        return redirect("cp", pk=c.pk)
    return form_page(request, form, "Composição própria (não oficial)", "cps",
                     ajuda="Use somente quando não houver composição oficial adequada. O código CP-xxx é interno e nunca "
                           "deve ser apresentado como oficial.")


@exige("editar_cadastros")
def item_cp_form(request, cp_pk=None, pk=None):
    obj = get_object_or_404(ItemComposicaoPropria, pk=pk) if pk else None
    c = obj.cp if obj else get_object_or_404(ComposicaoPropria, pk=cp_pk)
    form = ItemCPForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        it = form.save(commit=False)
        it.cp = c
        try:
            it.full_clean()
        except Exception as exc:
            for msg in getattr(exc, "messages", [str(exc)]):
                form.add_error(None, msg)
            return form_page(request, form, f"Insumo/serviço — {c.codigo}", "cps")
        it.save()
        registrar(request, "cp.item.salvar", it, f"{c.codigo}: {it.descricao[:60]}", alteracoes=mud)
        return redirect("cp", pk=c.pk)
    return form_page(request, form, f"Insumo/serviço — {c.codigo}", "cps",
                     ajuda="Insumo/composição de base: o preço vem da base escolhida no orçamento. Mão de obra própria: "
                           "informe custo horário SEM encargos e o % de encargos (bases oficiais já incluem encargos; não "
                           "aplique de novo).")


@exige("editar_cadastros")
@require_POST
def item_cp_excluir(request, pk):
    it = get_object_or_404(ItemComposicaoPropria, pk=pk)
    c_pk = it.cp_id
    registrar(request, "cp.item.excluir", it, it.descricao[:60])
    it.delete()
    return redirect("cp", pk=c_pk)


# ---------------------------------------------------------------- Usuários


@exige("gerir_usuarios")
def usuarios(request):
    return render(request, "orc/usuarios.html", {"usuarios": User.objects.prefetch_related("groups").order_by("username")})


@exige("gerir_usuarios")
def usuario_form(request, pk=None):
    obj = get_object_or_404(User, pk=pk) if pk else None
    inicial = {"perfil": obj.groups.first().name if obj and obj.groups.exists() else "Orçamentista"}
    form = UsuarioForm(request.POST or None, instance=obj, initial=inicial)
    if request.method == "POST" and form.is_valid():
        u = form.save()
        registrar(request, "usuario.salvar", u, u.username, perfil=form.cleaned_data["perfil"],
                  ativo=u.is_active, senha_alterada=bool(form.cleaned_data.get("senha")))
        messages.success(request, "Usuário salvo.")
        return redirect("usuarios")
    return form_page(request, form, "Usuário", "usuarios")
