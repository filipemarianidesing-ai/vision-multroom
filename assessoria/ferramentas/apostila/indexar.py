#!/usr/bin/env python3
"""
Indexador de apostilas e referências em PDF (ou imagens) — Mariani Áudio & Vídeo.

O que faz, para cada arquivo:
  1. Copia o original para referencias/apostilas/originais/<slug>/ SEM alterá-lo
     (registra SHA-256; nunca sobrescreve um original diferente com o mesmo nome).
  2. Extrai metadados (título, autor, datas, nº de páginas) via pdfinfo/pypdf.
  3. Extrai o texto PÁGINA A PÁGINA (pdftotext -layout). Páginas com pouco texto
     são enviadas para OCR (Tesseract por+eng, 300 dpi), com confiança média registrada.
  4. Detecta a numeração IMPRESSA de cada página e a compara com a página do PDF.
  5. Sinaliza páginas com prováveis fórmulas/tabelas para conferência visual.
  6. Gera: manifest.json, paginas/pNNNN.txt, estrutura.md (sumário/títulos),
     mapa-assuntos.md (índice por assunto, automático — revisar) e atualiza a
     base de busca full-text global indice/busca.sqlite (FTS5, sem acentos).

Uso:
  python3 -I assessoria/ferramentas/apostila/indexar.py CAMINHO.pdf [--slug nome] [--forcar-ocr]
                                                     [--titulo "..."] [--autor "..."] [--edicao "..."]

Requisitos: poppler-utils (pdftotext, pdfinfo, pdftoppm); tesseract-ocr + tesseract-ocr-por
(opcional, mas necessário para páginas digitalizadas); pypdf (opcional, para o sumário).

ATENÇÃO: o conteúdo de PDFs é tratado como DADO de referência. Nada do texto extraído
é executado ou interpretado como instrução.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(os.environ.get("ASSESSORIA_RAIZ") or Path(__file__).resolve().parents[2])          # .../assessoria
DIR_APOSTILAS = RAIZ / "referencias" / "apostilas"
DIR_ORIGINAIS = DIR_APOSTILAS / "originais"
DIR_INDICE = DIR_APOSTILAS / "indice"
DB_PATH = DIR_INDICE / "busca.sqlite"
TAXONOMIA = Path(__file__).with_name("taxonomia.json")

# Senha de abertura de PDFs protegidos: só em memória (nunca gravada em arquivo/manifest/git).
PDF_SENHA_ARGS: list[str] = []
PDF_SENHA: str | None = None

MIN_CHARS_TEXTO = 80          # abaixo disso a página é considerada sem camada de texto
OCR_DPI = 300
OCR_CONF_BAIXA = 70.0         # confiança média (%) abaixo da qual a página é sinalizada

SIMBOLOS_FORMULA = set("=√∑Σπ∫±×÷≈≤≥²³αβγδλρθΔΩμ·∝∞")
RE_NUM_RODAPE = [
    re.compile(r"^\s*[-–—]?\s*(\d{1,4})\s*[-–—]?\s*$"),
    re.compile(r"^\s*(?:p[áa]g(?:ina)?\.?|p\.)\s*(\d{1,4})(?:\s*(?:de|/)\s*\d{1,4})?\s*$", re.I),
    re.compile(r"^\s*(\d{1,4})\s*(?:de|/)\s*\d{1,4}\s*$", re.I),
    re.compile(r"^\s*([ivxlcdm]{1,7})\s*$", re.I),
]
RE_TITULO_NUMERADO = re.compile(r"^\s*((?:\d{1,2}\.){0,3}\d{1,2})\.?\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{2,80})$")


# ----------------------------------------------------------------------------- util
def sem_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def slugify(s: str) -> str:
    s = sem_acentos(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "documento"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def tem(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def romano_para_int(s: str) -> int | None:
    val = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    s = s.lower()
    if not s or any(c not in val for c in s):
        return None
    tot, prev = 0, 0
    for c in reversed(s):
        v = val[c]
        tot = tot - v if v < prev else tot + v
        prev = max(prev, v)
    return tot


# ----------------------------------------------------------------------------- extração
def configurar_senha(senha: str) -> None:
    """Define a senha de abertura (user password) para poppler e pypdf. Mantida só em memória."""
    global PDF_SENHA, PDF_SENHA_ARGS
    PDF_SENHA = senha
    PDF_SENHA_ARGS = ["-upw", senha]


def verificar_abertura(pdf: Path) -> None:
    """Falha com mensagem clara se o PDF exigir senha e ela estiver ausente ou incorreta."""
    r = run(["pdfinfo", *PDF_SENHA_ARGS, str(pdf)])
    if r.returncode != 0:
        msg = (r.stderr or "").lower()
        if "password" in msg or "incorrect" in msg or "encrypt" in msg:
            sys.exit("ERRO: o PDF é protegido por senha e a senha não foi informada ou está incorreta. "
                     "Defina APOSTILA_SENHA no ambiente (ou use --pedir-senha). A senha não é gravada.")
        sys.exit(f"ERRO ao abrir o PDF: {r.stderr.strip()}")


def metadados_pdf(pdf: Path) -> dict:
    meta: dict = {}
    if tem("pdfinfo"):
        r = run(["pdfinfo", *PDF_SENHA_ARGS, str(pdf)])
        for linha in r.stdout.splitlines():
            if ":" in linha:
                k, v = linha.split(":", 1)
                meta[k.strip()] = v.strip()
    out = {
        "titulo_pdf": meta.get("Title") or None,
        "autor_pdf": meta.get("Author") or None,
        "assunto_pdf": meta.get("Subject") or None,
        "criador_pdf": meta.get("Creator") or None,
        "produtor_pdf": meta.get("Producer") or None,
        "data_criacao_pdf": meta.get("CreationDate") or None,
        "data_modificacao_pdf": meta.get("ModDate") or None,
        "paginas": int(meta["Pages"]) if meta.get("Pages", "").isdigit() else None,
        "criptografado": meta.get("Encrypted", "no").lower().startswith("yes"),
    }
    return out


def sumario_pdf(pdf: Path) -> list[dict]:
    """Marcadores (bookmarks) do PDF, se existirem."""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return []
    try:
        rd = PdfReader(str(pdf))
        if rd.is_encrypted:
            rd.decrypt(PDF_SENHA or "")
        itens: list[dict] = []

        def walk(nodes, nivel=0):
            for n in nodes:
                if isinstance(n, list):
                    walk(n, nivel + 1)
                    continue
                try:
                    pg = rd.get_destination_page_number(n) + 1
                except Exception:
                    pg = None
                itens.append({"nivel": nivel, "titulo": str(n.title).strip(), "pagina_pdf": pg})

        walk(rd.outline)
        return itens
    except Exception:
        return []


def texto_pagina(pdf: Path, n: int) -> str:
    r = run(["pdftotext", *PDF_SENHA_ARGS, "-layout", "-enc", "UTF-8", "-f", str(n), "-l", str(n), str(pdf), "-"])
    return r.stdout.replace("\f", "")


def ocr_imagem(png: Path) -> tuple[str, float | None]:
    """OCR de uma imagem. Retorna (texto, confiança média em %)."""
    r = run(["tesseract", str(png), "stdout", "-l", "por+eng", "--psm", "3"])
    texto = r.stdout
    conf = None
    r2 = run(["tesseract", str(png), "stdout", "-l", "por+eng", "--psm", "3", "tsv"])
    vals = []
    for linha in r2.stdout.splitlines()[1:]:
        cols = linha.split("\t")
        if len(cols) >= 12 and cols[11].strip():
            try:
                c = float(cols[10])
                if c >= 0:
                    vals.append(c)
            except ValueError:
                pass
    if vals:
        conf = round(sum(vals) / len(vals), 1)
    return texto, conf


def ocr_pagina(pdf: Path, n: int) -> tuple[str, float | None]:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "pg"
        run(["pdftoppm", *PDF_SENHA_ARGS, "-r", str(OCR_DPI), "-f", str(n), "-l", str(n), "-png", "-singlefile", str(pdf), str(base)])
        png = base.with_suffix(".png")
        if not png.exists():
            return "", None
        return ocr_imagem(png)


def numero_impresso(texto: str) -> tuple[str | None, str | None]:
    """Procura número de página impresso nas 3 primeiras/últimas linhas não vazias."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    if not linhas:
        return None, None
    candidatos = [("rodape", l) for l in reversed(linhas[-3:])] + [("cabecalho", l) for l in linhas[:3]]
    for pos, linha in candidatos:
        # número isolado nas extremidades de uma linha de cabeçalho/rodapé
        partes = re.split(r"\s{3,}", linha.strip())
        for trecho in [linha.strip(), partes[0], partes[-1]]:
            for rx in RE_NUM_RODAPE:
                m = rx.match(trecho)
                if m:
                    val = m.group(1)
                    if val.isdigit() and 0 < int(val) < 3000:
                        return val, pos
                    if not val.isdigit() and romano_para_int(val) and len(linha.strip()) <= 8:
                        return val.lower(), pos
    return None, None


def sinais_formula_tabela(texto: str) -> dict:
    simb = sum(1 for c in texto if c in SIMBOLOS_FORMULA)
    linhas = [l for l in texto.splitlines() if l.strip()]
    tabulares = sum(1 for l in linhas if len(re.findall(r"\S+\s{3,}", l)) >= 3)
    numericas = sum(1 for l in linhas if len(re.findall(r"\d+[.,]?\d*", l)) >= 4)
    formula = simb >= 3 or bool(re.search(r"\b(log|ln|sqrt|10\s*log|20\s*log)\b", texto, re.I))
    tabela = tabulares >= 3 or numericas >= 4
    return {"formula_provavel": formula, "tabela_provavel": tabela, "simbolos": simb}


def titulos(texto: str) -> list[str]:
    out = []
    for l in texto.splitlines():
        s = l.strip()
        if not s or len(s) > 90:
            continue
        m = RE_TITULO_NUMERADO.match(s)
        letras = re.sub(r"[^A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç]", "", s)
        if m:
            out.append(s)
        elif len(letras) >= 6 and s.upper() == s and len(s.split()) <= 10 and not re.search(r"\d{3,}", s):
            out.append(s)
    return out[:8]


# ----------------------------------------------------------------------------- índice
def abrir_db() -> sqlite3.Connection:
    DIR_INDICE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS paginas USING fts5("
        "doc UNINDEXED, arquivo UNINDEXED, pagina_pdf UNINDEXED, pagina_impressa UNINDEXED, "
        "metodo UNINDEXED, conf_ocr UNINDEXED, texto, tokenize='unicode61 remove_diacritics 2')"
    )
    con.execute("CREATE TABLE IF NOT EXISTS documentos (doc TEXT PRIMARY KEY, manifest TEXT)")
    return con


def mapa_assuntos(paginas: list[dict], slug: str, nome_arquivo: str) -> str:
    tax = json.loads(TAXONOMIA.read_text(encoding="utf-8"))
    linhas = [
        f"# Mapa de assuntos — {nome_arquivo}",
        "",
        "> Gerado automaticamente por busca de termos (taxonomia.json). É um ponto de partida:",
        "> confira as páginas antes de citar. Formato: página do PDF (página impressa).",
        "",
    ]
    for grupo, termos in tax.items():
        achados = []
        for termo in termos:
            t = sem_acentos(termo).lower()
            pgs = []
            for p in paginas:
                if t in sem_acentos(p["texto"]).lower():
                    imp = p.get("pagina_impressa")
                    pgs.append(f"{p['pagina_pdf']}" + (f" ({imp})" if imp and imp != str(p["pagina_pdf"]) else ""))
            if pgs:
                achados.append(f"- **{termo}** — pp. {', '.join(pgs[:25])}{' …' if len(pgs) > 25 else ''}")
        if achados:
            linhas.append(f"## {grupo}")
            linhas.extend(achados)
            linhas.append("")
    if len(linhas) == 5:
        linhas.append("_Nenhum termo da taxonomia encontrado (verifique a qualidade da extração/OCR)._")
    return "\n".join(linhas) + "\n"


# ----------------------------------------------------------------------------- principal
def preservar_original(origem: Path, slug: str) -> Path:
    destino_dir = DIR_ORIGINAIS / slug
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / origem.name
    if destino.exists():
        if sha256(destino) != sha256(origem):
            sys.exit(f"ERRO: já existe um original diferente em {destino}. Use outro --slug "
                     "(versões nunca sobrescrevem originais).")
        return destino
    if origem.resolve() != destino.resolve():
        shutil.copy2(origem, destino)
    destino.chmod(0o444)
    return destino


def indexar(arquivo: Path, slug: str | None, forcar_ocr: bool, extra: dict) -> dict:
    if not arquivo.exists():
        sys.exit(f"ERRO: arquivo não encontrado: {arquivo}")
    for cmd in ("pdftotext", "pdfinfo", "pdftoppm"):
        if not tem(cmd):
            sys.exit(f"ERRO: '{cmd}' não instalado (pacote poppler-utils).")
    ocr_ok = tem("tesseract")
    slug = slug or slugify(arquivo.stem)
    original = preservar_original(arquivo, slug)

    eh_imagem = original.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    saida = DIR_INDICE / slug
    (saida / "paginas").mkdir(parents=True, exist_ok=True)

    avisos: list[str] = []
    paginas: list[dict] = []
    if eh_imagem:
        meta = {"paginas": 1}
        if not ocr_ok:
            sys.exit("ERRO: imagem exige OCR e o tesseract não está instalado.")
        texto, conf = ocr_imagem(original)
        paginas.append({"pagina_pdf": 1, "texto": texto, "metodo": "ocr", "conf_ocr": conf})
    else:
        verificar_abertura(original)
        meta = metadados_pdf(original)
        meta["protegido_por_senha"] = bool(PDF_SENHA)
        if meta.get("criptografado"):
            avisos.append("PDF criptografado: original preservado como recebido (protegido). "
                          "Renderização/consulta das imagens exige a mesma senha (APOSTILA_SENHA).")
        n = meta.get("paginas") or 0
        if n == 0:
            sys.exit("ERRO: não foi possível determinar o número de páginas (PDF danificado?).")
        for i in range(1, n + 1):
            txt = texto_pagina(original, i)
            metodo, conf = "texto", None
            if forcar_ocr or len(txt.strip()) < MIN_CHARS_TEXTO:
                if ocr_ok:
                    t2, conf = ocr_pagina(original, i)
                    if len(t2.strip()) > len(txt.strip()):
                        txt, metodo = t2, "ocr"
                    else:
                        conf = None
                else:
                    metodo = "sem_texto_ocr_indisponivel"
            paginas.append({"pagina_pdf": i, "texto": txt, "metodo": metodo, "conf_ocr": conf})
            print(f"  página {i}/{n}: {metodo}" + (f" (conf {conf}%)" if conf is not None else ""), file=sys.stderr)

    # numeração impressa e consistência
    offsets = []
    for p in paginas:
        imp, pos = numero_impresso(p["texto"])
        p["pagina_impressa"], p["pos_numero"] = imp, pos
        if imp and imp.isdigit():
            offsets.append(p["pagina_pdf"] - int(imp))
    offset_tipico = Counter(offsets).most_common(1)[0][0] if offsets else None

    for p in paginas:
        p.update(sinais_formula_tabela(p["texto"]))
        p["titulos"] = titulos(p["texto"])
        p["chars"] = len(p["texto"].strip())
        flags = []
        if p["chars"] < MIN_CHARS_TEXTO:
            flags.append("pouco_ou_nenhum_texto")
        if p["metodo"] == "ocr":
            flags.append("ocr")
            if p["conf_ocr"] is None or p["conf_ocr"] < OCR_CONF_BAIXA:
                flags.append("ocr_baixa_confianca")
        if p["metodo"] == "sem_texto_ocr_indisponivel":
            flags.append("NAO_LIDA")
        if p["formula_provavel"] or p["tabela_provavel"]:
            flags.append("conferir_visualmente")
        imp = p["pagina_impressa"]
        if imp and imp.isdigit() and offset_tipico is not None and p["pagina_pdf"] - int(imp) != offset_tipico:
            flags.append("numeracao_impressa_irregular")
        p["flags"] = flags
        (saida / "paginas" / f"p{p['pagina_pdf']:04d}.txt").write_text(p["texto"], encoding="utf-8")

    nao_lidas = [p["pagina_pdf"] for p in paginas if "NAO_LIDA" in p["flags"]]
    if nao_lidas:
        avisos.append(f"Páginas NÃO lidas (sem texto e sem OCR): {nao_lidas}")
    baixa = [p["pagina_pdf"] for p in paginas if "ocr_baixa_confianca" in p["flags"]]
    if baixa:
        avisos.append(f"OCR com baixa confiança (<{OCR_CONF_BAIXA}%) nas páginas: {baixa}")

    sumario = [] if eh_imagem else sumario_pdf(original)
    manifest = {
        "slug": slug,
        "arquivo": original.name,
        "caminho_original": str(original.relative_to(RAIZ)),
        "sha256": sha256(original),
        "tamanho_bytes": original.stat().st_size,
        "indexado_em": dt.datetime.now().isoformat(timespec="seconds"),
        "metadados": {**meta, **{k: v for k, v in extra.items() if v}},
        "ocr_disponivel": ocr_ok,
        "offset_tipico_pdf_menos_impressa": offset_tipico,
        "avisos": avisos,
        "sumario_pdf": sumario,
        "paginas": [{k: v for k, v in p.items() if k != "texto"} for p in paginas],
    }
    (saida / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # estrutura.md
    est = [f"# Estrutura — {original.name}", "",
           f"- Título (metadado): {meta.get('titulo_pdf') or extra.get('titulo') or 'não informado'}",
           f"- Autor (metadado): {meta.get('autor_pdf') or extra.get('autor') or 'não informado'}",
           f"- Edição: {extra.get('edicao') or 'não informada (confirmar na capa/ficha catalográfica)'}",
           f"- Data de criação (metadado do PDF, não é a edição): {meta.get('data_criacao_pdf') or 'n/d'}",
           f"- Páginas do PDF: {len(paginas)}",
           f"- Diferença típica (página PDF − página impressa): {offset_tipico if offset_tipico is not None else 'não detectada'}",
           ""]
    if sumario:
        est += ["## Marcadores do PDF", ""]
        est += [f"{'  ' * s['nivel']}- {s['titulo']} — p. PDF {s['pagina_pdf']}" for s in sumario]
        est.append("")
    est += ["## Títulos detectados por página (heurística)", ""]
    for p in paginas:
        if p["titulos"]:
            imp = f" (impr. {p['pagina_impressa']})" if p["pagina_impressa"] else ""
            est.append(f"- p. {p['pagina_pdf']}{imp}: " + " | ".join(p["titulos"]))
    est += ["", "## Páginas sinalizadas", ""]
    for p in paginas:
        if p["flags"]:
            est.append(f"- p. {p['pagina_pdf']}: {', '.join(p['flags'])}")
    (saida / "estrutura.md").write_text("\n".join(est) + "\n", encoding="utf-8")
    (saida / "mapa-assuntos.md").write_text(mapa_assuntos(paginas, slug, original.name), encoding="utf-8")

    # base de busca
    con = abrir_db()
    con.execute("DELETE FROM paginas WHERE doc = ?", (slug,))
    con.executemany(
        "INSERT INTO paginas (doc, arquivo, pagina_pdf, pagina_impressa, metodo, conf_ocr, texto) VALUES (?,?,?,?,?,?,?)",
        [(slug, original.name, p["pagina_pdf"], p["pagina_impressa"], p["metodo"], p["conf_ocr"], p["texto"]) for p in paginas],
    )
    con.execute("INSERT OR REPLACE INTO documentos VALUES (?, ?)", (slug, json.dumps(manifest, ensure_ascii=False)))
    con.commit()
    con.close()
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", type=Path)
    ap.add_argument("--slug")
    ap.add_argument("--forcar-ocr", action="store_true", help="OCR em todas as páginas (compara com a camada de texto)")
    ap.add_argument("--titulo")
    ap.add_argument("--autor")
    ap.add_argument("--edicao")
    ap.add_argument("--pedir-senha", action="store_true",
                    help="PDF protegido: pede a senha no terminal (não aparece na tela nem no histórico)")
    a = ap.parse_args()
    # Senha: variável de ambiente APOSTILA_SENHA ou --pedir-senha. Nunca por argumento de linha de comando.
    senha = os.environ.get("APOSTILA_SENHA") or (getpass.getpass("Senha do PDF: ") if a.pedir_senha else None)
    if senha:
        configurar_senha(senha)
    if a.slug and len(a.arquivos) > 1:
        sys.exit("--slug só pode ser usado com um arquivo por vez.")
    for arq in a.arquivos:
        print(f"Indexando {arq} ...", file=sys.stderr)
        m = indexar(arq, a.slug, a.forcar_ocr, {"titulo": a.titulo, "autor": a.autor, "edicao": a.edicao})
        metodos = Counter(p["metodo"] for p in m["paginas"])
        print(json.dumps({
            "slug": m["slug"], "arquivo": m["arquivo"], "paginas": len(m["paginas"]),
            "metodos": metodos, "offset_pdf_menos_impressa": m["offset_tipico_pdf_menos_impressa"],
            "conferir_visualmente": [p["pagina_pdf"] for p in m["paginas"] if "conferir_visualmente" in p["flags"]],
            "avisos": m["avisos"],
            "saida": str((DIR_INDICE / m["slug"]).relative_to(RAIZ.parent)),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
