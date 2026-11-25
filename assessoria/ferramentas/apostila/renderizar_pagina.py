#!/usr/bin/env python3
"""
Renderiza páginas de um original indexado em PNG para CONFERÊNCIA VISUAL de fórmulas,
tabelas, índices, expoentes e unidades (a extração de texto pode alterá-los).

Uso:
  python3 -I assessoria/ferramentas/apostila/renderizar_pagina.py SLUG PAG_PDF [PAG_PDF ...] [--dpi 150]

Saída: referencias/apostilas/indice/<slug>/imagens/pNNNN.png — abra com a ferramenta Read
(que exibe imagens) e compare com o texto extraído antes de citar valores.
PDF protegido: defina APOSTILA_SENHA no ambiente (a senha não é gravada).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(os.environ.get("ASSESSORIA_RAIZ") or Path(__file__).resolve().parents[2])
DIR_INDICE = RAIZ / "referencias" / "apostilas" / "indice"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("paginas", nargs="+", type=int)
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()
    man_path = DIR_INDICE / a.slug / "manifest.json"
    if not man_path.exists():
        sys.exit(f"Documento '{a.slug}' não indexado.")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    original = RAIZ / man["caminho_original"]
    out_dir = DIR_INDICE / a.slug / "imagens"
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in a.paginas:
        base = out_dir / f"p{p:04d}"
        senha = os.environ.get("APOSTILA_SENHA")
        pw = ["-upw", senha] if senha else []
        subprocess.run(["pdftoppm", *pw, "-r", str(a.dpi), "-f", str(p), "-l", str(p), "-png", "-singlefile",
                        str(original), str(base)], check=True)
        print(base.with_suffix(".png"))


if __name__ == "__main__":
    main()
