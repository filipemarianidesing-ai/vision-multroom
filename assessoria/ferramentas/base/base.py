#!/usr/bin/env python3
"""
Persistência da base de apostilas entre sessões — Mariani Áudio & Vídeo.

O repositório é PÚBLICO: aqui só ficam metadados, hashes, numeração curada e a SITUAÇÃO
da conferência. O conteúdo licenciado (ZIP/PDF original, texto extraído, transcrições de
fórmulas) fica em armazenamento PRIVADO autorizado (Google Drive do usuário) e é recuperado
com verificação de integridade (SHA-256).

Registro: assessoria/referencias/apostilas/fontes.json
  { "<slug>": { "origem": {titulo, drive_file_id, sha256, bytes},
                "backup": {titulo, drive_file_id, sha256, bytes, criado_em, conteudo} | null } }

Subcomandos
  estado [--hook] [--json]        Diagnóstico: DISPONIVEL | PRECISA_RECONSTRUIR | SEM_REGISTRO
  empacotar <slug> <saida.zip>    Gera o pacote de backup privado (índice + conferência), com hashes internos
  registrar-backup <slug> <zip> --drive-id ID --titulo T
                                  Grava hash/ID do pacote enviado ao Drive no fontes.json
  restaurar <slug> --origem ZIP_OU_PDF [--backup PACOTE.zip]
                                  Verifica SHA-256, preserva o original, restaura o índice do pacote
                                  (ou reindexa por OCR se não houver pacote), reaplica a curadoria,
                                  reconstrói a base de busca e valida o resultado.
  status-conferencia <slug>       Gera curadoria/<slug>-conferencia-status.json (sem transcrições)

Downloads do Drive são feitos pelo Claude com o conector Google Drive (ver skill /restaurar-base);
este script só trabalha com arquivos locais.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(os.environ.get("ASSESSORIA_RAIZ") or Path(__file__).resolve().parents[2])
APOST = RAIZ / "referencias" / "apostilas"
INDICE = APOST / "indice"
ORIGINAIS = APOST / "originais"
CURADORIA = APOST / "curadoria"
FONTES = APOST / "fontes.json"
DB = INDICE / "busca.sqlite"
FERR = Path(__file__).resolve().parents[1]

# Arquivos do índice que entram no pacote privado (as imagens não: são reextraídas do ZIP de origem)
ARQ_PACOTE = ["manifest.json", "estrutura.md", "mapa-assuntos.md", "mapa-curado.md",
              "conferencia.json", "conferencia.md", "curadoria.json"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ler_fontes(com_meta: bool = False) -> dict:
    d = json.loads(FONTES.read_text(encoding="utf-8")) if FONTES.exists() else {}
    return d if com_meta else {k: v for k, v in d.items() if not k.startswith("_")}


def gravar_fontes(d: dict) -> None:
    FONTES.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- estado
def estado_slug(slug: str, reg: dict) -> dict:
    """Verifica um documento. Rápido (não refaz hash de imagens; refaz o do original)."""
    r = {"slug": slug, "estado": "DISPONIVEL", "problemas": [], "detalhes": {}}
    dir_i = INDICE / slug
    man_p = dir_i / "manifest.json"
    orig = ORIGINAIS / slug / reg["origem"]["titulo"]
    if not orig.exists():
        r["problemas"].append("original ausente neste container")
    elif sha256(orig) != reg["origem"]["sha256"]:
        r["problemas"].append("original presente mas SHA-256 diferente do registrado")
    if not man_p.exists():
        r["problemas"].append("índice ausente")
    else:
        man = json.loads(man_p.read_text(encoding="utf-8"))
        n = len(man.get("paginas", []))
        faltam = [p["pagina_pdf"] for p in man["paginas"]
                  if not (dir_i / "paginas" / f"p{p['pagina_pdf']:04d}.txt").exists()]
        if faltam:
            r["problemas"].append(f"{len(faltam)} página(s) de texto ausentes")
        if man.get("sha256") != reg["origem"]["sha256"]:
            r["problemas"].append("índice gerado a partir de outro arquivo (hash não confere)")
        cur_p = CURADORIA / f"{slug}.json"
        if cur_p.exists():
            cur = json.loads(cur_p.read_text(encoding="utf-8"))
            esperadas = cur.get("paginas_impressas", {})
            pg = {str(p["pagina_pdf"]): p.get("pagina_impressa") for p in man["paginas"]}
            div = [k for k, v in esperadas.items() if pg.get(k) != v]
            if div:
                r["problemas"].append(f"curadoria não aplicada em {len(div)} página(s)")
        if not (dir_i / "conferencia.json").exists():
            r["problemas"].append("registro de conferência técnica ausente")
        r["detalhes"]["paginas"] = n
    if DB.exists():
        try:
            con = sqlite3.connect(DB)
            k = con.execute("SELECT count(*) FROM paginas WHERE doc=?", (slug,)).fetchone()[0]
            con.close()
            r["detalhes"]["paginas_na_busca"] = k
            if man_p.exists() and k != r["detalhes"].get("paginas"):
                r["problemas"].append("base de busca incompleta")
        except sqlite3.Error as e:
            r["problemas"].append(f"base de busca ilegível ({e})")
    else:
        r["problemas"].append("base de busca ausente")
    st = CURADORIA / f"{slug}-conferencia-status.json"
    if st.exists():
        s = json.loads(st.read_text(encoding="utf-8"))
        r["detalhes"]["conferencia"] = s.get("resumo")
    if r["problemas"]:
        r["estado"] = "PRECISA_RECONSTRUIR"
    r["backup_registrado"] = bool(reg.get("backup"))
    return r


def cmd_estado(a) -> None:
    fontes = ler_fontes()
    if not fontes:
        out = {"estado_geral": "SEM_REGISTRO", "documentos": []}
    else:
        docs = [estado_slug(s, reg) for s, reg in fontes.items()]
        geral = "DISPONIVEL" if all(d["estado"] == "DISPONIVEL" for d in docs) else "PRECISA_RECONSTRUIR"
        out = {"estado_geral": geral, "documentos": docs}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    linhas = []
    if out["estado_geral"] == "SEM_REGISTRO":
        linhas.append("BASE DE APOSTILAS: nenhuma apostila registrada (fontes.json ausente).")
    for d in out["documentos"]:
        det = d["detalhes"]
        conf = det.get("conferencia") or {}
        conf_txt = (", conferência: " + ", ".join(f"{k}={v}" for k, v in conf.items())) if conf else ""
        if d["estado"] == "DISPONIVEL":
            linhas.append(f"BASE DE APOSTILAS — {d['slug']}: DISPONÍVEL ({det.get('paginas')} páginas, "
                          f"integridade SHA-256 conferida, curadoria aplicada{conf_txt}).")
        else:
            linhas.append(f"BASE DE APOSTILAS — {d['slug']}: PRECISA SER RECONSTRUÍDA "
                          f"({'; '.join(d['problemas'])}). Backup privado registrado: "
                          f"{'sim' if d['backup_registrado'] else 'não (só reindexação por OCR)'}.")
    if a.hook and out["estado_geral"] == "PRECISA_RECONSTRUIR":
        linhas += [
            "",
            "INSTRUÇÃO PARA O ASSISTENTE: antes de responder qualquer demanda técnica que dependa da apostila,",
            "execute a skill /restaurar-base (baixa do Google Drive privado o ZIP de origem e o pacote de backup",
            "pelos IDs em assessoria/referencias/apostilas/fontes.json, verifica SHA-256 e restaura).",
            "Se o conector Google Drive não estiver disponível ou o download falhar, informe ao usuário que a",
            "base está INACESSÍVEL nesta sessão, explique o motivo e não cite a apostila sem a base.",
        ]
    print("\n".join(linhas))


# ----------------------------------------------------------------------------- conferência
def cmd_status_conferencia(a) -> None:
    src = INDICE / a.slug / "conferencia.json"
    reg = json.loads(src.read_text(encoding="utf-8"))
    itens = [{k: i.get(k) for k in ("id", "posicao", "pagina_impressa", "tipo", "situacao")}
             | {"tem_correcao_proposta": bool(i.get("correcao_proposta"))} for i in reg["itens"]]
    resumo: dict[str, int] = {}
    for i in itens:
        resumo[i["situacao"]] = resumo.get(i["situacao"], 0) + 1
    out = {"documento": a.slug, "gerado_em": dt.date.today().isoformat(),
           "aviso": "Somente a situação da conferência; transcrições e correções ficam no pacote privado.",
           "resumo": resumo, "itens": itens,
           "paginas_com_pendencia": sorted({i["posicao"] for i in itens if i["situacao"] in ("pendente", "ilegivel")})}
    dst = CURADORIA / f"{a.slug}-conferencia-status.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(dst, resumo)


# ----------------------------------------------------------------------------- backup
def cmd_empacotar(a) -> None:
    dir_i = INDICE / a.slug
    man = json.loads((dir_i / "manifest.json").read_text(encoding="utf-8"))
    arquivos = [n for n in ARQ_PACOTE if (dir_i / n).exists()]
    arquivos += [f"paginas/{p.name}" for p in sorted((dir_i / "paginas").glob("p*.txt"))]
    hashes = {n: sha256(dir_i / n) for n in arquivos}
    meta = {"slug": a.slug, "criado_em": dt.datetime.now().isoformat(timespec="seconds"),
            "sha256_origem": man["sha256"], "arquivos": hashes,
            "aviso": "Conteúdo licenciado para uso interno da Mariani. Não publicar."}
    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        for n in arquivos:
            z.write(dir_i / n, n)
        z.writestr("PACOTE.json", json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps({"pacote": str(saida), "sha256": sha256(saida), "bytes": saida.stat().st_size,
                      "arquivos": len(arquivos)}, ensure_ascii=False))


def cmd_registrar_backup(a) -> None:
    fontes = ler_fontes(com_meta=True)
    p = Path(a.pacote)
    with zipfile.ZipFile(p) as z:
        meta = json.loads(z.read("PACOTE.json"))
    if meta["sha256_origem"] != fontes[a.slug]["origem"]["sha256"]:
        sys.exit("ERRO: o pacote foi gerado a partir de outra origem.")
    fontes[a.slug]["backup"] = {"titulo": a.titulo, "drive_file_id": a.drive_id, "sha256": sha256(p),
                                "bytes": p.stat().st_size, "criado_em": meta["criado_em"],
                                "conteudo": "índice (texto por página, manifest, mapas) + conferência técnica"}
    gravar_fontes(fontes)
    print("registrado:", a.titulo)


# ----------------------------------------------------------------------------- restauração
def _rebuild_db(slug: str, man: dict) -> int:
    INDICE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS paginas USING fts5(doc UNINDEXED, arquivo UNINDEXED, "
                "pagina_pdf UNINDEXED, pagina_impressa UNINDEXED, metodo UNINDEXED, conf_ocr UNINDEXED, texto, "
                "tokenize='unicode61 remove_diacritics 2')")
    con.execute("CREATE TABLE IF NOT EXISTS documentos (doc TEXT PRIMARY KEY, manifest TEXT)")
    con.execute("DELETE FROM paginas WHERE doc=?", (slug,))
    dir_i = INDICE / slug
    rows = []
    for p in man["paginas"]:
        txt = (dir_i / "paginas" / f"p{p['pagina_pdf']:04d}.txt").read_text(encoding="utf-8")
        rows.append((slug, man["arquivo"], p["pagina_pdf"], p.get("pagina_impressa"), p["metodo"], p.get("conf_ocr"), txt))
    con.executemany("INSERT INTO paginas VALUES (?,?,?,?,?,?,?)", rows)
    con.execute("INSERT OR REPLACE INTO documentos VALUES (?,?)", (slug, json.dumps(man, ensure_ascii=False)))
    con.commit()
    con.close()
    return len(rows)


def _extrair_imagens(slug: str, origem: Path, man: dict) -> None:
    """Reextrai as imagens de página do ZIP de origem na mesma ordem usada na indexação."""
    nomes = man["metadados"].get("nomes_originais_ordenados") or []
    if not nomes or origem.suffix.lower() != ".zip":
        return
    d = INDICE / slug / "imagens-originais"
    d.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(origem) as z:
        for k, n in enumerate(nomes, 1):
            (d / f"p{k:04d}{Path(n).suffix.lower()}").write_bytes(z.read(n))


def _aplicar_curadoria(slug: str, man: dict) -> int:
    cur_p = CURADORIA / f"{slug}.json"
    if not cur_p.exists():
        return 0
    cur = json.loads(cur_p.read_text(encoding="utf-8"))
    n = 0
    for p in man["paginas"]:
        k = str(p["pagina_pdf"])
        if k in cur.get("paginas_impressas", {}) and p.get("pagina_impressa") != cur["paginas_impressas"][k]:
            p["pagina_impressa"] = cur["paginas_impressas"][k]
            p["numeracao"] = "curada"
            n += 1
    for k, v in cur.get("metadados", {}).items():
        man["metadados"].setdefault(k, v)
    return n


def cmd_restaurar(a) -> None:
    fontes = ler_fontes()
    if a.slug not in fontes:
        sys.exit(f"ERRO: '{a.slug}' não está em {FONTES}.")
    reg = fontes[a.slug]
    origem = Path(a.origem)
    h = sha256(origem)
    if h != reg["origem"]["sha256"]:
        sys.exit(f"ERRO DE INTEGRIDADE: SHA-256 da origem ({h[:12]}…) difere do registrado "
                 f"({reg['origem']['sha256'][:12]}…). Nada foi alterado.")
    print(f"[ok] origem íntegra (SHA-256 {h[:12]}…)")
    # preservar original com o nome registrado (somente leitura)
    dst_dir = ORIGINAIS / a.slug
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / reg["origem"]["titulo"]
    if not dst.exists() or sha256(dst) != h:
        if dst.exists():
            dst.chmod(0o644)
        shutil.copy2(origem, dst)
        dst.chmod(0o444)
    print(f"[ok] original preservado em {dst.relative_to(RAIZ)}")

    dir_i = INDICE / a.slug
    if a.backup:
        pac = Path(a.backup)
        hb = sha256(pac)
        if reg.get("backup") and hb != reg["backup"]["sha256"]:
            sys.exit(f"ERRO DE INTEGRIDADE: pacote de backup com SHA-256 diferente do registrado. Nada foi alterado.")
        with zipfile.ZipFile(pac) as z:
            meta = json.loads(z.read("PACOTE.json"))
            if meta["sha256_origem"] != h:
                sys.exit("ERRO: pacote de backup pertence a outra origem.")
            for n, hh in meta["arquivos"].items():
                if sha256_bytes(z.read(n)) != hh:
                    sys.exit(f"ERRO DE INTEGRIDADE no pacote: {n}")
            (dir_i / "paginas").mkdir(parents=True, exist_ok=True)
            for n in meta["arquivos"]:
                alvo = (dir_i / n).resolve()
                if dir_i.resolve() not in alvo.parents:
                    sys.exit(f"ERRO: caminho inválido no pacote: {n}")
                alvo.write_bytes(z.read(n))
        print(f"[ok] pacote de backup íntegro ({len(meta['arquivos'])} arquivos, criado em {meta['criado_em']})")
        man = json.loads((dir_i / "manifest.json").read_text(encoding="utf-8"))
    else:
        print("[!] sem pacote de backup: reindexando por OCR (exige tesseract; a conferência técnica "
              "privada NÃO é recuperável sem o pacote)")
        if not shutil.which("tesseract"):
            sys.exit("ERRO: tesseract ausente. Instale: apt-get install -y tesseract-ocr tesseract-ocr-por")
        subprocess.run([sys.executable, "-I", str(FERR / "apostila" / "indexar.py"), str(dst), "--slug", a.slug],
                       check=True, env={**os.environ, "ASSESSORIA_RAIZ": str(RAIZ)})
        man = json.loads((dir_i / "manifest.json").read_text(encoding="utf-8"))

    n_cur = _aplicar_curadoria(a.slug, man)
    (dir_i / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] curadoria reaplicada ({n_cur} ajuste(s) de numeração; demais já estavam aplicados)")
    _extrair_imagens(a.slug, dst, man)
    print("[ok] imagens de página reextraídas para conferência visual")
    k = _rebuild_db(a.slug, man)
    print(f"[ok] base de busca reconstruída ({k} páginas)")
    e = estado_slug(a.slug, reg)
    print(f"ESTADO FINAL: {e['estado']}" + (f" — {'; '.join(e['problemas'])}" if e["problemas"] else ""))
    if e["estado"] != "DISPONIVEL":
        sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("estado"); s.add_argument("--hook", action="store_true"); s.add_argument("--json", action="store_true")
    s.set_defaults(f=cmd_estado)
    s = sub.add_parser("empacotar"); s.add_argument("slug"); s.add_argument("saida"); s.set_defaults(f=cmd_empacotar)
    s = sub.add_parser("registrar-backup"); s.add_argument("slug"); s.add_argument("pacote")
    s.add_argument("--drive-id", required=True); s.add_argument("--titulo", required=True); s.set_defaults(f=cmd_registrar_backup)
    s = sub.add_parser("restaurar"); s.add_argument("slug"); s.add_argument("--origem", required=True)
    s.add_argument("--backup"); s.set_defaults(f=cmd_restaurar)
    s = sub.add_parser("status-conferencia"); s.add_argument("slug"); s.set_defaults(f=cmd_status_conferencia)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
