"""Base de materiais: regras de uso em cálculo."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "calc"))
import materiais as mt  # noqa: E402


def test_base_carrega_e_tem_fontes():
    base = mt.carregar()
    assert {"lady-inovawall-28mm", "lady-ecoshapes-wood"} <= set(base)
    for m in base.values():
        assert m["fonte"]["arquivo"] and m["fonte"]["paginas"] and m["uso_em_calculo"]


def test_nrc_exige_opt_in_e_marca_estimativa():
    with pytest.raises(mt.DadoInsuficiente):
        mt.superficie("lady-inovawall-28mm", 10)
    s = mt.superficie("lady-inovawall-28mm", 10, aproximar_por_nrc=True)
    assert s.alfa == {500: 0.80, 1000: 0.80} and s.fonte.startswith("ESTIMATIVA [E]")


def test_nrc_nao_extrapola_bandas():
    with pytest.raises(mt.DadoInsuficiente):
        mt.superficie("lady-inovawall-28mm", 10, aproximar_por_nrc=True, bandas=(125, 500))


def test_material_sem_dado_acustico_recusado():
    with pytest.raises(mt.DadoInsuficiente):
        mt.superficie("lady-ecoshapes-wood", 10, aproximar_por_nrc=True)
