from .models import RegistroAuditoria


def registrar(request, acao, obj=None, descricao="", **detalhes):
    tipo = obj.__class__.__name__ if obj is not None else ""
    oid = str(getattr(obj, "pk", "") or "") if obj is not None else ""
    ip = None
    if request is not None:
        ip = request.META.get("REMOTE_ADDR")
    RegistroAuditoria.objects.create(
        usuario=request.user if request is not None and request.user.is_authenticated else None,
        acao=acao, objeto_tipo=tipo, objeto_id=oid, descricao=descricao[:2000], detalhes=detalhes, ip=ip)


def diferencas(form):
    """Campos alterados de um ModelForm (valor anterior → novo), para a trilha de auditoria."""
    out = {}
    for nome in form.changed_data:
        ini = form.initial.get(nome)
        novo = form.cleaned_data.get(nome)
        out[nome] = [str(ini) if ini is not None else None, str(novo) if novo is not None else None]
    return out
