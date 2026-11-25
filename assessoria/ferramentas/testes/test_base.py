"""Persistência da base: estado, empacotamento, restauração com verificação SHA-256 e adulteração.
Usa o PDF sintético do teste do indexador (conteúdo fictício) num ASSESSORIA_RAIZ temporário."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_indexador import gerar_pdf  # noqa: E402

FERR = Path(__file__).resolve().parents[1]
BASE = FERR / "base" / "base.py"
pytestmark = pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler ausente")


def run(args, raiz, ok=True):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       env={**os.environ, "ASSESSORIA_RAIZ": str(raiz)})
    if ok:
        assert r.returncode == 0, r.stdout + r.stderr
    return r


@pytest.fixture()
def ambiente(tmp_path):
    raiz = tmp_path / "assessoria"
    pdf = tmp_path / "doc-teste.pdf"
    gerar_pdf(pdf, tmp_path)
    run(["-I", str(FERR / "apostila" / "indexar.py"), str(pdf), "--slug", "doc"], raiz)
    ap = raiz / "referencias" / "apostilas"
    (ap / "curadoria").mkdir(parents=True, exist_ok=True)
    (ap / "curadoria" / "doc.json").write_text(json.dumps({"paginas_impressas": {"1": None, "3": "2"}}))
    (ap / "indice" / "doc" / "conferencia.json").write_text(json.dumps({"itens": [
        {"id": "eq-1", "posicao": 2, "pagina_impressa": "1", "tipo": "formula", "situacao": "conferida_sem_ressalva",
         "transcricao_fiel": "T = 0,161 V / A"}]}))
    h = hashlib.sha256(pdf.read_bytes()).hexdigest()
    (ap / "fontes.json").write_text(json.dumps({"_pasta_backup_drive": {"drive_folder_id": "x"},
        "doc": {"origem": {"titulo": pdf.name, "drive_file_id": "fake", "sha256": h, "bytes": pdf.stat().st_size},
                "backup": None}}))
    # reaplica a curadoria (indexação acima foi anterior à curadoria)
    run(["-I", str(FERR / "apostila" / "indexar.py"), str(pdf), "--slug", "doc"], raiz)
    return raiz, pdf, tmp_path


def test_estado_disponivel_e_hook(ambiente):
    raiz, _, _ = ambiente
    out = run([str(BASE), "estado", "--json"], raiz).stdout
    assert json.loads(out)["estado_geral"] == "DISPONIVEL"


def test_ciclo_backup_restauracao(ambiente):
    raiz, pdf, tmp = ambiente
    run([str(BASE), "status-conferencia", "doc"], raiz)
    pacote = tmp / "pacote.zip"
    info = json.loads(run([str(BASE), "empacotar", "doc", str(pacote)], raiz).stdout)
    run([str(BASE), "registrar-backup", "doc", str(pacote), "--drive-id", "fake2", "--titulo", "pacote.zip"], raiz)
    assert json.loads((raiz / "referencias/apostilas/fontes.json").read_text())["doc"]["backup"]["sha256"] == info["sha256"]

    # simula container novo: some tudo que não é versionado
    shutil.rmtree(raiz / "referencias/apostilas/indice")
    shutil.rmtree(raiz / "referencias/apostilas/originais")
    est = json.loads(run([str(BASE), "estado", "--json"], raiz).stdout)
    assert est["estado_geral"] == "PRECISA_RECONSTRUIR"
    hook = run([str(BASE), "estado", "--hook"], raiz).stdout
    assert "PRECISA SER RECONSTRUÍDA" in hook and "/restaurar-base" in hook and "INACESSÍVEL" in hook

    # restauração verificada
    out = run([str(BASE), "restaurar", "doc", "--origem", str(pdf), "--backup", str(pacote)], raiz).stdout
    assert "ESTADO FINAL: DISPONIVEL" in out
    man = json.loads((raiz / "referencias/apostilas/indice/doc/manifest.json").read_text())
    assert {p["pagina_pdf"]: p["pagina_impressa"] for p in man["paginas"]}[3] == "2"   # curadoria reaplicada
    assert (raiz / "referencias/apostilas/indice/doc/conferencia.json").exists()      # conferência recuperada
    res = json.loads(run(["-I", str(FERR / "apostila" / "buscar.py"), "sabine", "--json"], raiz).stdout)
    assert res and res[0]["pagina_pdf"] == 2


def test_recusa_origem_adulterada(ambiente):
    raiz, pdf, tmp = ambiente
    falsa = tmp / "falsa.pdf"
    falsa.write_bytes(pdf.read_bytes() + b"x")
    r = run([str(BASE), "restaurar", "doc", "--origem", str(falsa)], raiz, ok=False)
    assert r.returncode != 0 and "INTEGRIDADE" in (r.stdout + r.stderr)


def test_recusa_pacote_adulterado(ambiente):
    raiz, pdf, tmp = ambiente
    pacote = tmp / "pacote.zip"
    run([str(BASE), "empacotar", "doc", str(pacote)], raiz)
    run([str(BASE), "registrar-backup", "doc", str(pacote), "--drive-id", "f", "--titulo", "p.zip"], raiz)
    pacote.write_bytes(pacote.read_bytes()[:-10] + b"0123456789")
    r = run([str(BASE), "restaurar", "doc", "--origem", str(pdf), "--backup", str(pacote)], raiz, ok=False)
    assert r.returncode != 0 and "INTEGRIDADE" in (r.stdout + r.stderr)


def test_restauracao_sem_pacote_avisa_perda_da_conferencia(ambiente):
    raiz, pdf, tmp = ambiente
    shutil.rmtree(raiz / "referencias/apostilas/indice")
    r = run([str(BASE), "restaurar", "doc", "--origem", str(pdf)], raiz, ok=False)
    saida = r.stdout + r.stderr
    if not shutil.which("tesseract"):
        assert "tesseract ausente" in saida
        return
    assert "NÃO é recuperável sem o pacote" in saida
    assert "registro de conferência técnica ausente" in saida      # estado honesto: não DISPONIVEL
    man = json.loads((raiz / "referencias/apostilas/indice/doc/manifest.json").read_text())
    assert {p["pagina_pdf"]: p["pagina_impressa"] for p in man["paginas"]}[3] == "2"   # curadoria do repo reaplicada
