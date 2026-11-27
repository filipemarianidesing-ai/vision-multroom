"""Configuração para testes automatizados (chave local, sem HTTPS)."""
import os

os.environ.setdefault("ORC_DEBUG", "1")

from .settings import *  # noqa: E402,F401,F403
