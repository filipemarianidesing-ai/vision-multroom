"""Perfis e permissões verificados no servidor (cada view chama `exige`)."""
from functools import wraps

from django.core.exceptions import PermissionDenied

PERFIS = {
    "Administrador": {"ver", "editar_cadastros", "editar_orcamento", "salvar_versao", "importar_base",
                      "gerir_modelos", "gerir_usuarios", "auditoria", "empresa"},
    "Orçamentista": {"ver", "editar_cadastros", "editar_orcamento", "salvar_versao", "importar_base",
                     "gerir_modelos"},
    "Revisor": {"ver", "salvar_versao"},
    "Leitura": {"ver"},
}


def acoes_do_usuario(user):
    if not user.is_authenticated or not user.is_active:
        return set()
    if user.is_superuser:
        return set().union(*PERFIS.values())
    acoes = set()
    for nome in user.groups.values_list("name", flat=True):
        acoes |= PERFIS.get(nome, set())
    return acoes


def pode(user, acao):
    return acao in acoes_do_usuario(user)


def exige(acao):
    def deco(view):
        @wraps(view)
        def inner(request, *args, **kwargs):
            if not pode(request.user, acao):
                raise PermissionDenied(f"Seu perfil não permite: {acao}.")
            return view(request, *args, **kwargs)
        return inner
    return deco


def contexto_permissoes(request):
    return {"perm": {a: True for a in acoes_do_usuario(getattr(request, "user", None))}
            if getattr(request, "user", None) else {}}
