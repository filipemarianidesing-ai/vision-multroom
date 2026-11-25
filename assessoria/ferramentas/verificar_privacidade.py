#!/usr/bin/env python3
"""
Verificação de privacidade antes de commits (repositório PÚBLICO).

Bloqueia o commit se os arquivos preparados (staged) contiverem:
  - caminhos de dados privados (assessoria/projetos/<cliente>, apostilas/originais, apostilas/indice);
  - cabeçalho de licença, códigos de licença, CPF/CNPJ reais, e-mails pessoais;
  - trechos idênticos ao texto das apostilas indexadas (sequências de 10 palavras).
Nunca imprime o dado encontrado — só arquivo, linha e tipo.

Uso direto:  python3 assessoria/ferramentas/verificar_privacidade.py [--todos]
Como hook PreToolUse (Bash): lê o JSON da ferramenta no stdin; só age em 'git commit'/'git push';
sai com código 2 (bloqueio) e motivo no stderr.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]
INDICE = RAIZ_REPO / "assessoria" / "referencias" / "apostilas" / "indice"
CAMINHOS_PROIBIDOS = [re.compile(r"^assessoria/projetos/(?!_modelo/|README\.md$)"),
                      re.compile(r"^assessoria/referencias/apostilas/(originais|indice)/(?!\.gitkeep$)")]
PERMITIDOS = Path(__file__).with_name("privacidade_permitidos.txt")
_linhas = [l.strip() for l in PERMITIDOS.read_text(encoding="utf-8").splitlines()
           if l.strip() and not l.startswith("#")] if PERMITIDOS.exists() else []
FICTICIOS = {l.split(":", 1)[1] for l in _linhas if l.startswith("ficticio:")} | {"fulano@exemplo.com"}
FRASES_PUBLICAS = [l for l in _linhas if not l.startswith("ficticio:")]
PADROES = {
    "cabeçalho de licença": re.compile(r"licensed to\s+\w", re.I),
    "código de licença": re.compile(r"\b[A-Z]{2}\d{12,}\b"),
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "CNPJ": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "e-mail pessoal": re.compile(r"\b[\w.+-]+@(gmail|hotmail|outlook|yahoo|live|icloud|uol|bol|terra)\.com(\.br)?\b", re.I),
}
N_PALAVRAS = 10


def norm(s: str) -> list[str]:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", s)


def shingles(palavras: list[str]) -> set[tuple]:
    return {tuple(palavras[i:i + N_PALAVRAS]) for i in range(len(palavras) - N_PALAVRAS + 1)}


def base_apostilas() -> set[tuple]:
    sh: set[tuple] = set()
    for txt in INDICE.glob("*/paginas/p*.txt"):
        sh |= shingles(norm(txt.read_text(encoding="utf-8", errors="ignore")))
    for f in FRASES_PUBLICAS:          # títulos de normas/referências públicas não contam
        sh -= shingles(norm(f))
    return sh


def arquivos(todos: bool) -> list[str]:
    cmd = ["git", "ls-files"] if todos else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    return [l for l in subprocess.run(cmd, cwd=RAIZ_REPO, capture_output=True, text=True).stdout.splitlines() if l]


def verificar(todos: bool = False) -> list[str]:
    achados = []
    sh_ap = base_apostilas()
    for rel in arquivos(todos):
        if any(rx.search(rel) for rx in CAMINHOS_PROIBIDOS):
            achados.append(f"{rel}: caminho de dados privados (cliente/apostila)")
            continue
        p = RAIZ_REPO / rel
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, linha in enumerate(txt.splitlines(), 1):
            if "verificar_privacidade" in rel or "re.compile" in linha:
                continue
            for tipo, rx in PADROES.items():
                m = rx.search(linha)
                if m and not any(f in linha for f in FICTICIOS):
                    achados.append(f"{rel}:{n}: {tipo}")
        if sh_ap:
            comuns = shingles(norm(txt)) & sh_ap
            if comuns:
                achados.append(f"{rel}: {len(comuns)} trecho(s) de {N_PALAVRAS} palavras idênticos ao texto de apostila licenciada")
    return achados


def main() -> None:
    if "--todos" in sys.argv or sys.stdin.isatty():
        a = verificar(todos="--todos" in sys.argv)
        print("\n".join(a) if a else "OK: nenhum dado pessoal ou conteúdo licenciado encontrado.")
        sys.exit(1 if a else 0)
    try:
        cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except Exception:
        sys.exit(0)
    if not re.search(r"\bgit\b.*\b(commit|push)\b", cmd):
        sys.exit(0)
    a = verificar()
    if a:
        print("COMMIT BLOQUEADO pela verificação de privacidade (repositório público):\n- " + "\n- ".join(a[:20])
              + "\nRemova esses arquivos do stage (git restore --staged <arq>) ou o conteúdo sensível.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
