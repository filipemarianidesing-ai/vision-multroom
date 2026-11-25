"""Testes de sanidade da biblioteca de cálculos (valores conferidos manualmente).
Rodar:  python3 -m pytest -q assessoria/ferramentas/testes
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "calc"))
import acustica as ac  # noqa: E402
import pytest  # noqa: E402


def aprox(a, b, tol=0.05):
    return abs(a - b) <= tol


def test_soma_db_nao_aritmetica():
    assert aprox(ac.soma_db([90, 90]), 93.01, 0.01)
    assert aprox(ac.soma_db([80, 70]), 80.41, 0.01)
    assert aprox(ac.soma_db([60] * 10), 70.0, 0.01)


def test_soma_coerente():
    assert aprox(ac.soma_coerente_db([90, 90]), 96.02, 0.01)
    assert ac.soma_coerente_db([90, 90], [0, 180]) < 0  # cancelamento (resíduo numérico)


def test_subtrai_db():
    assert aprox(ac.subtrai_db(70, 60), 69.54, 0.01)
    with pytest.raises(ValueError):
        ac.subtrai_db(62, 60)


def test_velocidade_e_atraso():
    assert aprox(ac.velocidade_som(20), 343.2, 0.2)
    assert aprox(ac.atraso_ms(10, 20), 29.14, 0.05)


def test_inverso_quadrado():
    assert aprox(ac.spl_inverso_quadrado(100, 1, 2), 93.98, 0.01)
    assert aprox(ac.spl_fonte_linha(100, 1, 2), 96.99, 0.01)


def test_sensibilidade():
    # 90 dB 1W/1m, 100 W, 10 m -> 90 + 20 - 20 = 90 dB
    assert aprox(ac.spl_por_sensibilidade(90, 100, 10), 90.0, 0.01)
    assert aprox(ac.spl_por_sensibilidade_tensao(90, 28.3, 1), 110.0, 0.01)
    assert aprox(ac.potencia_necessaria_w(90, 90, 10), 100, 0.5)


def test_sabine_eyring():
    v, s = 1000.0, 600.0
    a = 0.2 * s
    assert aprox(ac.rt_sabine(v, a), 1.342, 0.005)
    assert aprox(ac.rt_eyring(v, s, 0.2), 1.203, 0.005)
    assert ac.rt_eyring(v, s, 0.2) < ac.rt_sabine(v, a)


def test_rt_por_banda_e_faltantes():
    sup = [ac.Superficie("piso", 100, {500: 0.02, 1000: 0.03}, "teste"),
           ac.Superficie("forro", 100, {500: 0.6}, "teste")]
    r = ac.rt_por_banda(300, sup, bandas=(500, 1000))
    assert 1000 in r["bandas_sem_dado"]
    assert aprox(r["bandas"][500]["A_m2"], 62.0, 0.01)


def test_distancia_critica():
    r = ac.constante_sala(600, 0.2)          # 150 m²
    assert aprox(r, 150.0, 0.01)
    assert aprox(ac.distancia_critica(5, r), 0.141 * math.sqrt(750), 0.02)


def test_schroeder_e_modos():
    assert aprox(ac.frequencia_schroeder(0.5, 50), 200.0, 0.01)
    modos = ac.modos_sala(5, 4, 3, f_max=60)
    assert modos[0]["n"] == (1, 0, 0) and aprox(modos[0]["f_hz"], 34.3, 0.1)


def test_cobertura_teto():
    d = ac.diametro_cobertura(3.0, 1.2, 90)
    assert aprox(d, 3.6, 0.01)
    assert aprox(ac.espacamento_caixas_teto(3.0, 1.2, 90, "sobreposicao"), 2.546, 0.01)
    q = ac.quantidade_caixas_grade(8, 6, 2.546, otimizar=False)
    assert q["total"] == 4 * 3
    # caso apontado pela revisão independente: 8 x 6,5 m, forro 3,0, ouvido 1,2, 90° -> 3x3 basta
    q = ac.quantidade_caixas_grade(8, 6.5, 2.546)
    assert (q["nx"], q["ny"], q["total"]) == (3, 3, 9)
    ang = ac.angulo_pior_ponto(8 / 3, 6.5 / 3, 3.0, 1.2)
    assert aprox(ang, 43.66, 0.05) and ang <= 45


def test_linha_70v_e_cabo():
    c = ac.carga_linha_tensao_constante([6] * 10, 70.7)
    assert aprox(c["impedancia_equivalente_ohm"], 83.3, 0.1)
    assert c["amplificador_minimo_w"] == 75.0
    r = ac.resistencia_cabo_ohm(100, 1.5)
    assert aprox(r, 2.333, 0.01)
    p = ac.perda_cabo_db(r, 83.3)
    assert aprox(p["perda_db"], -0.24, 0.01)


def test_microfonia():
    pag = ac.pag_db(d0=15, d1=6, ds=0.3, d2=10)
    assert aprox(pag, 29.54, 0.02)
    nag = ac.nag_db(15, 1.5)
    assert aprox(nag, 20.0, 0.01)
    assert aprox(ac.margem_microfonia(pag, nag, 2), 29.54 - 20 - 3.01 - 6, 0.03)


def test_isolamento():
    assert aprox(ac.lei_massa_incidencia_campo(100, 500), 46.98, 0.01)
    # parede 10 m² R=50 com porta 2 m² R=25 -> domina a porta
    r = ac.isolamento_composto([(8, 50), (2, 25)])
    assert 31 < r < 33


def test_niveis_eletricos():
    assert aprox(ac.dbu_para_v(4), 1.228, 0.002)
    assert aprox(ac.v_para_dbu(0.7746), 0.0, 0.001)
