"""Configuração do sistema de orçamentação da Mariani.

Todos os valores sensíveis vêm de variáveis de ambiente. Nenhum segredo é versionado.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Pasta de dados (arquivos oficiais importados, evidências, backups). Fora do git.
DADOS_DIR = Path(os.environ.get("ORC_DADOS", BASE_DIR / "dados"))

DEBUG = os.environ.get("ORC_DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("ORC_SECRET_KEY") or ("dev-inseguro-somente-local" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("Defina ORC_SECRET_KEY (ou ORC_DEBUG=1 para desenvolvimento local).")

ALLOWED_HOSTS = [h for h in os.environ.get("ORC_HOSTS", "localhost,127.0.0.1").split(",") if h]
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("ORC_CSRF_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "orc",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "orc.middleware.ExigeLoginMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "orc.permissoes.contexto_permissoes",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("ORC_DB_NAME", "orcamento"),
        "USER": os.environ.get("ORC_DB_USER", "postgres"),
        "PASSWORD": os.environ.get("ORC_DB_PASSWORD", ""),
        "HOST": os.environ.get("ORC_DB_HOST", "localhost"),
        "PORT": os.environ.get("ORC_DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

MEDIA_ROOT = DADOS_DIR / "arquivos"  # nunca servido diretamente: downloads passam por views com permissão
MEDIA_URL = "/nao-servido/"
BACKUP_DIR = Path(os.environ.get("ORC_BACKUP_DIR", DADOS_DIR / "backups"))

STATIC_URL = "static/"
STATIC_ROOT = DADOS_DIR / "static"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_AGE = 60 * 60 * 10  # 10 h
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
if not DEBUG:
    SESSION_COOKIE_SECURE = os.environ.get("ORC_HTTPS", "1") == "1"
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    if SESSION_COOKIE_SECURE:
        SECURE_HSTS_SECONDS = int(os.environ.get("ORC_HSTS", "3600"))
        SECURE_SSL_REDIRECT = os.environ.get("ORC_SSL_REDIRECT", "1") == "1"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
UPLOAD_MAX_BYTES = 200 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Recursos de IA: o núcleo não depende deles. Mantido desligado.
IA_HABILITADA = False
