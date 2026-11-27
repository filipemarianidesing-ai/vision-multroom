"""Teste de restauração: restaura o backup mais recente (ou o indicado) num banco temporário e compara contagens e
hashes das versões de orçamento com o manifesto/banco atual. Remove o banco temporário ao final.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from .backup import env_pg


class Command(BaseCommand):
    help = "Restaura o último backup em banco temporário e verifica a integridade."

    def add_arguments(self, parser):
        parser.add_argument("--pasta")

    def handle(self, *args, **o):
        raiz = Path(settings.BACKUP_DIR)
        pasta = Path(o["pasta"]) if o.get("pasta") else max((p for p in raiz.iterdir() if (p / "manifesto.json").exists()),
                                                             key=lambda p: p.name)
        man = json.loads((pasta / "manifesto.json").read_text())
        env, args_pg, _ = env_pg()
        temp_db = "orc_teste_restauracao"
        subprocess.run(["dropdb", "--if-exists", *args_pg, temp_db], env=env, check=True)
        with tempfile.TemporaryDirectory() as tmp:
            call_command("restaurar", str(pasta), banco=temp_db, arquivos=tmp)
            def q(sql):
                return subprocess.run(["psql", *args_pg, "-tAc", sql, temp_db], env=env, capture_output=True,
                                      text=True, check=True).stdout.strip()
            cont = {"orcamentos": int(q("SELECT count(*) FROM orc_orcamento")),
                    "versoes": int(q("SELECT count(*) FROM orc_versaoorcamento")),
                    "bases": int(q("SELECT count(*) FROM orc_basereferencia"))}
            from orc.calculo import hash_dados
            linhas = [l for l in q("SELECT sha256 || '\t' || dados::text FROM orc_versaoorcamento").splitlines() if l]
            hashes_ok = sum(1 for l in linhas if hash_dados(json.loads(l.split("\t", 1)[1])) == l.split("\t", 1)[0])
            if hashes_ok != len(linhas):
                raise CommandError(f"{len(linhas) - hashes_ok} versão(ões) restaurada(s) com conteúdo que não confere com o hash.")
            arquivos = sum(1 for _ in Path(tmp).rglob("*") if _.is_file())
        subprocess.run(["dropdb", *args_pg, temp_db], env=env, check=True)
        if cont != man["contagens"]:
            raise CommandError(f"Contagens divergentes: restaurado {cont} × manifesto {man['contagens']}")
        self.stdout.write(self.style.SUCCESS(
            f"Restauração OK a partir de {pasta.name}: {cont}, versões com hash conferido: {hashes_ok}, arquivos restaurados: {arquivos}."))
