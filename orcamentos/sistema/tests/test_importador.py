import os
from decimal import Decimal as D

import pytest

from orc.importadores import sinapi

from .fabrica_sinapi import gerar


def test_analisa_planilha_sintetica(tmp_path):
    r = sinapi.analisar(str(gerar(tmp_path / "s.xlsx")), "ES", "SD")
    assert r.valido, r.erros
    assert str(r.competencia) == "2026-10-01"
    assert r.localidade == "VITORIA"
    ins = {i["codigo"]: i for i in r.insumos}
    assert ins["35692"]["preco"] == D("20.0")
    assert ins["11111"]["preco"] is None  # vazio no ES => sem preço, nunca zero
    comp = {c["codigo"]: c for c in r.composicoes}
    assert comp["104642"]["custo"] == D("13.51")
    assert comp["104646"]["custo"] is None  # 0 com %AS vazio => sem custo
    assert r.estatisticas["zero_tratado_sem_custo"] == 1
    assert r.itens["104642"][0]["coeficiente"] == D("0.2367")


def test_recusa_leiaute_diferente(tmp_path):
    r = sinapi.analisar(str(gerar(tmp_path / "s.xlsx", quebrar_cabecalho=True)), "ES", "SD")
    assert not r.valido
    assert "Leiaute incompatível" in r.erros[0]


def test_recusa_codigo_repetido(tmp_path):
    ins = [("MATERIAL", 1, "A", "UN", "C", {"ES": 1.0}), ("MATERIAL", 1, "B", "UN", "C", {"ES": 2.0})]
    r = sinapi.analisar(str(gerar(tmp_path / "s.xlsx", insumos=ins)), "ES", "SD")
    assert any("repetido" in e for e in r.erros)


def test_recusa_arquivo_que_nao_e_planilha(tmp_path):
    p = tmp_path / "x.zip"
    p.write_bytes(b"isto nao e zip")
    r = sinapi.analisar(str(p), "ES", "SD")
    assert not r.valido


def test_uf_inexistente(tmp_path):
    r = sinapi.analisar(str(gerar(tmp_path / "s.xlsx")), "RJ", "SD")
    assert not r.valido


@pytest.mark.skipif(not os.environ.get("SINAPI_ARQUIVO"), reason="defina SINAPI_ARQUIVO com o pacote oficial")
def test_arquivo_oficial():
    r = sinapi.analisar(os.environ["SINAPI_ARQUIVO"], "ES", "SD")
    assert r.valido, r.erros
    assert r.estatisticas["insumos"] > 4000
    assert r.estatisticas["composicoes"] > 10000
    assert r.estatisticas["conferencia_divergentes"] == 0
    assert r.estatisticas["conferencia_reproduzidas"] > 7000
