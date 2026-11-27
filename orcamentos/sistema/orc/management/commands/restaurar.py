"""Restaura um backup em um banco (novo ou existente vazio) e em uma pasta de arquivos.

Uso: python manage.py restaurar PASTA_DO_BACKUP --banco NOME_DESTINO --arquivos DIR_DESTINO [--substituir]
Confere os hashes do manifesto antes de restaurar. Por segurança, não restaura sobre o banco em uso sem --substituir.
"""
import json
import subprocess
import tarfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from .backup import env_pg, sha256


class Command(BaseCommand):
    help = "Restaura banco e arquivos a partir de uma pasta de backup."

    def add_arguments(self, parser):
        parser.add_argument("pasta")
        parser.add_argument("--banco", required=True)
        parser.add_argument("--arquivos", required=True)
        parser.add_argument("--substituir", action="store_true")

    def handle(self, *args, **o):
        pasta = Path(o["pasta"])
        man = json.loads((pasta / "manifesto.json").read_text())
        for nome, info in man["arquivos"].items():
            if sha256(pasta / nome) != info["sha256"]:
                raise CommandError(f"Hash não confere para {nome}: backup corrompido.")
        env, args_pg, atual = env_pg()
        if o["banco"] == atual and not o["substituir"]:
            raise CommandError("Destino é o banco em uso. Use --substituir conscientemente (o conteúdo será trocado).")
        existe = subprocess.run(["psql", *args_pg, "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{o['banco']}'",
                                 "postgres"], env=env, capture_output=True, text=True).stdout.strip() == "1"
        if not existe:
            subprocess.run(["createdb", *args_pg, o["banco"]], env=env, check=True)
        r = subprocess.run(["pg_restore", "--no-owner", "--clean", "--if-exists", *args_pg, "-d", o["banco"],
                            str(pasta / "banco.dump")], env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise CommandError(f"pg_restore falhou: {r.stderr[-2000:]}")
        destino = Path(o["arquivos"])
        destino.mkdir(parents=True, exist_ok=True)
        with tarfile.open(pasta / "arquivos.tar.gz") as tar:
            tar.extractall(destino, filter="data")
        self.stdout.write(self.style.SUCCESS(f"Restaurado em banco '{o['banco']}' e arquivos em '{destino}'."))
