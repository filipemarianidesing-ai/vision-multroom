import hashlib

from django.contrib import messages
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auditoria import diferencas, registrar
from .forms import AmbienteForm, ClienteForm, CotacaoForm, DocumentoEmpresaForm, EmpresaForm, ObraForm
from .models import (Ambiente, BaseReferencia, Cliente, Cotacao, DocumentoEmpresa, Empresa, Obra, Orcamento,
                     RegistroAuditoria)
from .permissoes import exige


def form_page(request, form, titulo, voltar, ajuda="", multipart=False):
    return render(request, "orc/form.html", {"form": form, "titulo": titulo, "voltar": voltar, "ajuda": ajuda,
                                             "multipart": multipart})


def _sha(arquivo):
    h = hashlib.sha256()
    for bloco in arquivo.chunks():
        h.update(bloco)
    arquivo.seek(0)
    return h.hexdigest()


def baixar(arquivo_field, nome=None):
    if not arquivo_field:
        raise Http404
    try:
        fh = arquivo_field.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    return FileResponse(fh, as_attachment=True, filename=nome or arquivo_field.name.split("/")[-1])


@exige("ver")
def inicio(request):
    empresa = Empresa.objects.first()
    hoje = timezone.localdate()
    docs_vencidos = DocumentoEmpresa.objects.filter(validade__lt=hoje) if empresa else []
    return render(request, "orc/inicio.html", {
        "empresa": empresa,
        "obras": Obra.objects.select_related("cliente").annotate(n=Count("orcamentos"))[:8],
        "orcamentos": Orcamento.objects.select_related("obra")[:8],
        "bases": BaseReferencia.objects.filter(status="confirmada")[:5],
        "docs_vencidos": docs_vencidos,
    })


# ---------------------------------------------------------------- Empresa
@exige("ver")
def empresa(request):
    emp = Empresa.objects.first()
    return render(request, "orc/empresa.html", {"empresa": emp, "documentos": emp.documentos.all() if emp else [],
                                                "hoje": timezone.localdate()})


@exige("empresa")
def empresa_editar(request):
    emp = Empresa.objects.first()
    form = EmpresaForm(request.POST or None, instance=emp)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        obj = form.save()
        registrar(request, "empresa.salvar", obj, "Cadastro da empresa", alteracoes=mud)
        messages.success(request, "Cadastro da empresa salvo.")
        return redirect("empresa")
    return form_page(request, form, "Cadastro da empresa", "empresa")


@exige("empresa")
def documento_novo(request, pk=None):
    emp = Empresa.objects.first()
    if not emp:
        messages.error(request, "Cadastre a empresa primeiro.")
        return redirect("empresa_editar")
    doc = get_object_or_404(DocumentoEmpresa, pk=pk) if pk else None
    form = DocumentoEmpresaForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == "POST" and form.is_valid():
        d = form.save(commit=False)
        d.empresa = emp
        if "arquivo" in request.FILES:
            d.sha256 = _sha(request.FILES["arquivo"])
        d.save()
        registrar(request, "documento.salvar", d, d.tipo, alteracoes=diferencas(form))
        messages.success(request, "Documento salvo.")
        return redirect("empresa")
    return form_page(request, form, "Documento da empresa", "empresa", multipart=True)


@exige("empresa")
def documento_arquivo(request, pk):
    d = get_object_or_404(DocumentoEmpresa, pk=pk)
    registrar(request, "documento.baixar", d, d.tipo)
    return baixar(d.arquivo)


# ---------------------------------------------------------------- Clientes
@exige("ver")
def clientes(request):
    return render(request, "orc/clientes.html", {"clientes": Cliente.objects.annotate(n=Count("obras"))})


@exige("editar_cadastros")
def cliente_form(request, pk=None):
    obj = get_object_or_404(Cliente, pk=pk) if pk else None
    form = ClienteForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        c = form.save()
        registrar(request, "cliente.salvar", c, c.nome, alteracoes=mud)
        messages.success(request, "Cliente salvo.")
        return redirect("clientes")
    return form_page(request, form, "Cliente / órgão", "clientes")


# ---------------------------------------------------------------- Obras e ambientes
@exige("ver")
def obras(request):
    return render(request, "orc/obras.html", {"obras": Obra.objects.select_related("cliente").annotate(n=Count("orcamentos"))})


@exige("editar_cadastros")
def obra_form(request, pk=None):
    obj = get_object_or_404(Obra, pk=pk) if pk else None
    form = ObraForm(request.POST or None, instance=obj, initial={"cliente": request.GET.get("cliente")})
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        o = form.save(commit=False)
        if not o.pk:
            o.criado_por = request.user
        o.save()
        registrar(request, "obra.salvar", o, o.nome, alteracoes=mud)
        messages.success(request, "Obra salva.")
        return redirect("obra", pk=o.pk)
    if not Cliente.objects.exists():
        messages.info(request, "Cadastre primeiro o cliente (escola/órgão).")
    return form_page(request, form, "Obra / serviço", "obras")


@exige("ver")
def obra(request, pk):
    o = get_object_or_404(Obra.objects.select_related("cliente"), pk=pk)
    return render(request, "orc/obra.html", {"obra": o, "ambientes": o.ambientes.all(),
                                             "orcamentos": o.orcamentos.all()})


@exige("editar_cadastros")
def ambiente_form(request, obra_pk=None, pk=None):
    amb = get_object_or_404(Ambiente, pk=pk) if pk else None
    o = amb.obra if amb else get_object_or_404(Obra, pk=obra_pk)
    form = AmbienteForm(request.POST or None, instance=amb)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        a = form.save(commit=False)
        a.obra = o
        a.save()
        registrar(request, "ambiente.salvar", a, f"{o.nome} / {a.nome}", alteracoes=mud)
        messages.success(request, "Ambiente salvo.")
        return redirect("obra", pk=o.pk)
    return form_page(request, form, f"Ambiente — {o.nome}", "obras",
                     ajuda="Dimensões ficam disponíveis na memória de cálculo como comprimento, largura, pe_direito, "
                           "area_piso e perimetro. Informe só o que foi medido.")


@exige("editar_cadastros")
@require_POST
def ambiente_excluir(request, pk):
    a = get_object_or_404(Ambiente, pk=pk)
    obra_pk = a.obra_id
    registrar(request, "ambiente.excluir", a, a.nome)
    a.delete()
    messages.success(request, "Ambiente excluído (itens vinculados ficaram sem ambiente).")
    return redirect("obra", pk=obra_pk)


# ---------------------------------------------------------------- Cotações
@exige("ver")
def cotacoes(request):
    return render(request, "orc/cotacoes.html", {"cotacoes": Cotacao.objects.all(), "hoje": timezone.localdate()})


@exige("editar_cadastros")
def cotacao_form(request, pk=None):
    obj = get_object_or_404(Cotacao, pk=pk) if pk else None
    form = CotacaoForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        mud = diferencas(form)
        c = form.save(commit=False)
        if "arquivo" in request.FILES:
            c.sha256 = _sha(request.FILES["arquivo"])
        c.save()
        registrar(request, "cotacao.salvar", c, str(c), alteracoes=mud)
        messages.success(request, "Cotação salva.")
        return redirect("cotacoes")
    return form_page(request, form, "Cotação de fornecedor", "cotacoes", multipart=True,
                     ajuda="Registre a evidência (PDF/e-mail). Preços promocionais, antigos, de usados ou de produto "
                           "tecnicamente diferente devem ser justificados ou descartados.")


@exige("ver")
def cotacao_arquivo(request, pk):
    c = get_object_or_404(Cotacao, pk=pk)
    return baixar(c.arquivo)


@exige("auditoria")
def auditoria(request):
    return render(request, "orc/auditoria.html", {"registros": RegistroAuditoria.objects.select_related("usuario")[:500]})
