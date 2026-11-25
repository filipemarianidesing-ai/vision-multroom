#!/usr/bin/env python3
"""
Cria a pasta de um novo projeto a partir de assessoria/projetos/_modelo.

Uso:
  python3 assessoria/ferramentas/novo_projeto.py "Nome do Cliente" "Nome do Projeto" [--cidade "Vitória/ES"]

Resultado: assessoria/projetos/<cliente>/<AAAA-MM-projeto>/ com ficha, pendências,
decisões, pastas de documentos recebidos (originais), cálculos, pesquisas, relatórios e medições.
Nunca sobrescreve um projeto existente.
"""
import argparse
import datetime as dt
import re
import shutil
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODELO = RAIZ / "projetos" / "_modelo"


def slug(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:50]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cliente")
    ap.add_argument("projeto")
    ap.add_argument("--cidade", default="")
    a = ap.parse_args()
    hoje = dt.date.today()
    destino = RAIZ / "projetos" / slug(a.cliente) / f"{hoje:%Y-%m}-{slug(a.projeto)}"
    if destino.exists():
        sys.exit(f"Já existe: {destino} — não sobrescrevo projetos.")
    shutil.copytree(MODELO, destino)
    for md in destino.rglob("*.md"):
        t = md.read_text(encoding="utf-8")
        t = (t.replace("{{CLIENTE}}", a.cliente).replace("{{PROJETO}}", a.projeto)
              .replace("{{CIDADE}}", a.cidade or "a informar").replace("{{DATA}}", hoje.isoformat()))
        md.write_text(t, encoding="utf-8")
    print(destino.relative_to(RAIZ.parent))


if __name__ == "__main__":
    main()
