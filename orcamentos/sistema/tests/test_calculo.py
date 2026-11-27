from decimal import ROUND_DOWN, Decimal as D

from orc.calculo import bdi_componentes, q


def test_bdi_componentes_valor_conferido_a_mao():
    # (1+0,03+0,01+0,01+0)(1+0,01)(1+0,08)/(1−0,10) − 1 = 1,05 × 1,01 × 1,08 / 0,9 − 1 = 0,2726
    assert bdi_componentes(D(3), D(1), D(1), D(0), D(1), D(8), D(10)) == D("27.26")


def test_bdi_zero():
    assert bdi_componentes(*[D(0)] * 7) == D("0.00")


def test_arredondamento_e_truncamento():
    assert q(D("17.195"), 2) == D("17.20")
    assert q(D("17.195"), 2, ROUND_DOWN) == D("17.19")
    assert q(None) is None
