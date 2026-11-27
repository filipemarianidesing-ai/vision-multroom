"""Backup completo: banco (pg_dump -Fc) + arquivos (originais de bases, evidências, documentos) + manifesto SHA-256.

Retenção padrão: 30 backups diários mais recentes + o último de cada mês dos 12 meses anteriores.
Uso: python manage.py backup [--destino DIR] [--sem-retencao]
"""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def env_pg():
    db = settings.DATABASES["default"]
    env = os.environ.copy()
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = db["PASSWORD"]
    args = ["-h", db.get("HOST") or "localhost", "-p", str(db.get("PORT") or 5432), "-U", db.get("USER") or "postgres"]
    return env, args, db["NAME"]


def aplicar_retencao(raiz, diarios=30, mensais=12):
    pastas = sorted([p for p in raiz.iterdir() if p.is_dir() and (p / "manifesto.json").exists()], reverse=True)
    manter = set(pastas[:diarios])
    meses = {}
    for p in pastas:
        mes = p.name[:6]
        meses.setdefault(mes, p)  # mais recente de cada mês (lista em ordem decrescente)
    for mes in sorted(meses, reverse=True)[:mensais + 1]:
        manter.add(meses[mes])
    removidos = []
    for p in pastas:
        if p not in manter:
            shutil.rmtree(p)
            removidos.append(p.name)
    return removidos


class Command(BaseCommand):
    help = "Gera backup do banco e dos arquivos com manifesto de hashes."

    def add_arguments(self, parser):
        parser.add_argument("--destino", default=str(settings.BACKUP_DIR))
        parser.add_argument("--sem-retencao", action="store_true")

    def handle(self, *args, **o):
        raiz = Path(o["destino"])
        pasta = raiz / datetime.now().strftime("%Y%m%d-%H%M%S")
        pasta.mkdir(parents=True, exist_ok=False)
        env, args_pg, nome = env_pg()
        dump = pasta / "banco.dump"
        r = subprocess.run(["pg_dump", "-Fc", "--no-owner", *args_pg, "-f", str(dump), nome], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            shutil.rmtree(pasta)
            raise CommandError(f"pg_dump falhou: {r.stderr}")
        arq = pasta / "arquivos.tar.gz"
        with tarfile.open(arq, "w:gz") as tar:
            if Path(settings.MEDIA_ROOT).exists():
                tar.add(settings.MEDIA_ROOT, arcname="arquivos")
        with connection.cursor() as c:
            c.execute("SELECT max(id) FROM django_migrations")
            migracao = c.fetchone()[0]
        from orc.models import BaseReferencia, Orcamento, VersaoOrcamento
        manifesto = {
            "criado_em": datetime.now().isoformat(timespec="seconds"), "banco": nome,
            "arquivos": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in (dump, arq)},
            "contagens": {"orcamentos": Orcamento.objects.count(), "versoes": VersaoOrcamento.objects.count(),
                          "bases": BaseReferencia.objects.count()},
            "ultima_migracao_id": migracao,
        }
        (pasta / "manifesto.json").write_text(json.dumps(manifesto, indent=2, ensure_ascii=False))
        removidos = [] if o["sem_retencao"] else aplicar_retencao(raiz)
        self.stdout.write(self.style.SUCCESS(f"Backup gerado em {pasta}"))
        if removidos:
            self.stdout.write(f"Retenção: removidos {len(removidos)} backups antigos.")
