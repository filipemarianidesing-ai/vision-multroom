from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

LIVRES = ("/entrar/", "/static/")


class ExigeLoginMiddleware:
    """Toda página exige login, exceto a tela de entrada e arquivos estáticos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(LIVRES):
            return redirect(f"{reverse(settings.LOGIN_URL)}?next={request.path}")
        return self.get_response(request)
