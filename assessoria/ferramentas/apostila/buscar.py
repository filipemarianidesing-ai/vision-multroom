#!/usr/bin/env python3
"""
Busca na base de apostilas indexadas (FTS5, sem acentos, ranking BM25).

Exemplos:
  python3 -I assessoria/ferramentas/apostila/buscar.py "tempo de reverberação"
  python3 -I assessoria/ferramentas/apostila/buscar.py "sabine OR eyring" --limite 5
  python3 -I assessoria/ferramentas/apostila/buscar.py "distancia critica" --doc minha-apostila
  python3 -I assessoria/ferramentas/apostila/buscar.py --pagina minha-apostila 42     # texto integral da página 42 do PDF
  python3 -I assessoria/ferramentas/apostila/buscar.py --listar                        # documentos indexados

Sintaxe de consulta: palavras soltas (E lógico), "frase exata", OR, NOT, prefixo* .
Cada resultado traz: documento, arquivo, página do PDF, página impressa (quando detectada),
método de leitura (texto/ocr) e trecho. CITE SEMPRE arquivo + página. Confira a página
inteira (--pagina) — e a imagem da página, para fórmulas/tabelas — antes de usar um valor.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(os.environ.get("ASSESSORIA_RAIZ") or Path(__file__).resolve().parents[2])
DB_PATH = RAIZ / "referencias" / "apostilas" / "indice" / "busca.sqlite"


CURADORIA = RAIZ / "referencias" / "apostilas" / "curadoria"
ROTULO = {"conferida_sem_ressalva": "conferida", "conferida_com_ressalva": "conferida c/ ressalva",
          "correcao_proposta": "CORREÇÃO PROPOSTA — usar forma corrigida", "pendente": "PENDENTE — não usar em dimensionamento final",
          "ilegivel": "ILEGÍVEL — não usar"}


def situacao_pagina(doc: str, pagina_pdf: int) -> list[str]:
    """Situação da conferência técnica dos itens (fórmulas/tabelas) de uma página."""
    st = CURADORIA / f"{doc}-conferencia-status.json"
    if not st.exists():
        return ["conferência técnica: sem registro para este documento"]
    import json as _j
    itens = [i for i in _j.loads(st.read_text(encoding="utf-8"))["itens"] if i["posicao"] == int(pagina_pdf)]
    return [f"{i['id']}: {ROTULO.get(i['situacao'], i['situacao'])}" for i in itens]


def conectar() -> sqlite3.Connection:
    if not DB_PATH.exists():
        sys.exit("Nenhuma apostila indexada ainda. Rode indexar.py (veja assessoria/README.md).")
    return sqlite3.connect(DB_PATH)


def preparar(q: str) -> str:
    """Aceita linguagem natural: palavras sem operadores viram termos com E lógico."""
    if re.search(r'["*]|\b(OR|AND|NOT|NEAR)\b', q):
        return q
    termos = re.findall(r"[\wÀ-ÿ%'-]+", q)
    return " ".join(f'"{t}"' for t in termos)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("consulta", nargs="?")
    ap.add_argument("--doc", help="restringir a um documento (slug)")
    ap.add_argument("--limite", type=int, default=8)
    ap.add_argument("--pagina", nargs=2, metavar=("SLUG", "PAG_PDF"))
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    con = conectar()

    if a.listar:
        for doc, man in con.execute("SELECT doc, manifest FROM documentos ORDER BY doc"):
            m = json.loads(man)
            md = m["metadados"]
            print(f"- {doc}: {m['arquivo']} | {len(m['paginas'])} pp. | título: {md.get('titulo') or md.get('titulo_pdf') or '?'}"
                  f" | autor: {md.get('autor') or md.get('autor_pdf') or '?'} | avisos: {len(m['avisos'])}")
        return

    if a.pagina:
        slug, pg = a.pagina
        row = con.execute("SELECT arquivo, pagina_impressa, metodo, conf_ocr, texto FROM paginas WHERE doc=? AND pagina_pdf=?",
                          (slug, int(pg))).fetchone()
        if not row:
            sys.exit("Página não encontrada.")
        arq, imp, met, conf, txt = row
        print(f"=== {arq} — página PDF {pg} | impressa: {imp or 'não detectada'} | leitura: {met}"
              + (f" (OCR conf. {conf}%)" if conf is not None else "") + " ===")
        sit = situacao_pagina(slug, pg)
        if sit:
            print("--- conferência técnica desta página: " + " | ".join(sit))
            print("--- transcrições/correções: indice/" + slug + "/conferencia.json")
        print(txt)
        return

    if not a.consulta:
        ap.error("informe uma consulta, --pagina ou --listar")
    q = preparar(a.consulta)
    sql = ("SELECT doc, arquivo, pagina_pdf, pagina_impressa, metodo, conf_ocr, "
           "snippet(paginas, 6, '[[', ']]', ' … ', 28), bm25(paginas) FROM paginas WHERE paginas MATCH ?")
    params: list = [q]
    if a.doc:
        sql += " AND doc = ?"
        params.append(a.doc)
    sql += " ORDER BY bm25(paginas) LIMIT ?"
    params.append(a.limite)
    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        sys.exit(f"Consulta inválida para FTS5 ({e}). Use aspas para frases.")
    res = [{"doc": r[0], "arquivo": r[1], "pagina_pdf": r[2], "pagina_impressa": r[3],
            "leitura": r[4], "conf_ocr": r[5], "trecho": re.sub(r"\s+", " ", r[6]).strip()} for r in rows]
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    if not res:
        print(f"Sem resultados para: {a.consulta}  (consulta FTS: {q}). Tente sinônimos ou prefixo*.")
        return
    for i, r in enumerate(res, 1):
        imp = f", impressa {r['pagina_impressa']}" if r["pagina_impressa"] else ", impressa n/d"
        ocr = f" [OCR {r['conf_ocr']}%]" if r["leitura"] == "ocr" else ""
        sit = situacao_pagina(r["doc"], r["pagina_pdf"])
        sit_txt = ("\n   conferência: " + " | ".join(sit)) if sit else ""
        print(f"{i}. {r['arquivo']} — p. PDF {r['pagina_pdf']}{imp}{ocr}\n   {r['trecho']}{sit_txt}\n")


if __name__ == "__main__":
    main()
