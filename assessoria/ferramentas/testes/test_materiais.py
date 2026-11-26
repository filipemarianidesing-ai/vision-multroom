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


def test_referencia_exige_aceite_e_converte_oitavas():
    with pytest.raises(mt.DadoInsuficiente):
        mt.superficie_referencia("vic-wavewood-ultra-lite", 10)
    s = mt.superficie_referencia("vic-wavewood-ultra-lite", 10, aceitar_declarado=True)
    assert set(s.alfa) == {125, 250, 500, 1000, 2000, 4000}
    assert s.fonte.startswith("[S-declarado]")
    c = mt.curva_referencia("vic-wavewood-ultra-lite")
    assert s.alfa[500] == round((c[400] + c[500] + c[630]) / 3, 2)


def test_espessura_aumenta_absorcao_em_baixa_frequencia():
    # Piano 60 mm < Forte < Fortissimo 120 mm a 125 Hz (conferido na imagem do catálogo, p. 27)
    p = mt.curva_referencia("vic-piano-forte-fortissimo-vmt", "Piano")[125]
    f = mt.curva_referencia("vic-piano-forte-fortissimo-vmt", "Forte")[125]
    ff = mt.curva_referencia("vic-piano-forte-fortissimo-vmt", "Fortissimo")[125]
    assert (p, f, ff) == (0.29, 0.38, 0.56)


def test_multiplas_curvas_exigem_modelo():
    with pytest.raises(ValueError):
        mt.curva_referencia("vic-flat-panel-vmt")
    assert mt.curva_referencia("vic-flat-panel-vmt", "40 mm")[500] == 0.74
