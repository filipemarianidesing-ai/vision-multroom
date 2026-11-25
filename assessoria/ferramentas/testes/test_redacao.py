"""Remoção de dados pessoais de cabeçalhos de licença (inclusive com OCR deformado). Dados fictícios."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "ix", Path(__file__).resolve().parents[1] / "apostila" / "indexar.py")
ix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ix)


def test_cabecalho_normal():
    t, n = ix.remover_dados_licenca("Licensed to Fulano - fulano@exemplo.com - 123.456.789-00 - AB123456789012\nTexto")
    assert "Fulano" not in t and "123.456" not in t and "Texto" in t and n >= 1


def test_cabecalho_ocr_deformado():
    linha = "Fulano de Tal - fulano O hotmail.com - 123.456.789-00 - HP123456789012345"
    t, n = ix.remover_dados_licenca(linha + "\nCapítulo 1 Fundamentos 3")
    assert "Fulano" not in t and "HP1234" not in t and "Capítulo 1" in t


def test_texto_tecnico_preservado():
    txt = "NPS = 10 log10(10^6 + 10^7) = 74,28 dB; ABNT NBR 16313 de 2014."
    assert ix.remover_dados_licenca(txt)[0] == txt
