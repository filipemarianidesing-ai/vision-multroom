from decimal import Decimal as D

import pytest

from orc.expressoes import ErroExpressao, avaliar, para_decimal, variaveis_usadas


def test_virgula_decimal_e_funcoes():
    assert avaliar("10,5 * 2") == D("21.0")
    assert avaliar("max(a; 2,5)", {"a": D("1")}) == D("2.5")
    assert avaliar("arred(1 / 3; 4)") == D("0.3333")
    assert avaliar("comprimento * pe_direito - vaos", {"comprimento": D("10"), "pe_direito": D("3"), "vaos": D("2.4")}) == D("27.6")


def test_numeros_exatos_sem_float():
    assert avaliar("0.1 + 0.2") == D("0.3")


def test_condicoes():
    v = {"estado": "ruim", "area": D("5"), "fundo": True}
    assert avaliar("estado == 'ruim' and area > 0", v) is True
    assert avaliar("fundo and not estado == 'bom'", v) is True
    assert avaliar("area >= 6", v) is False


@pytest.mark.parametrize("expr", ["__import__('os')", "a.b", "a[0]", "open('x')", "lambda: 1", "2 ** 10"])
def test_bloqueia_elementos_perigosos(expr):
    with pytest.raises(ErroExpressao):
        avaliar(expr, {"a": D(1)})


def test_erros_claros():
    with pytest.raises(ErroExpressao, match="não informada"):
        avaliar("x + 1")
    with pytest.raises(ErroExpressao, match="Divisão por zero"):
        avaliar("1 / 0")
    with pytest.raises(ErroExpressao, match="sem valor"):
        avaliar("x", {"x": None})


def test_para_decimal():
    assert para_decimal("1.234,56") == D("1234.56")
    assert para_decimal("12.5") == D("12.5")
    assert para_decimal("") is None
    assert para_decimal(2.1) == D("2.1")


def test_variaveis_usadas():
    assert variaveis_usadas("max(a; b) * c") == {"a", "b", "c"}
