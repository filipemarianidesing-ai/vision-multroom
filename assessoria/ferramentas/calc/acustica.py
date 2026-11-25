"""
Biblioteca de cálculos acústicos e eletroacústicos — Mariani Áudio & Vídeo.

PRINCÍPIOS
- Toda função documenta: fórmula, condições de validade e limitações.
- Unidades SI (m, m², m³, s, Pa, W, V, Ω), níveis em dB. Frequências em Hz.
- Nada aqui substitui medição, ensaio ou simulação validada. Os resultados são
  CALCULADOS/ESTIMADOS a partir das entradas; classifique-os assim nos relatórios.
- Nenhum dado de material, diretividade ou produto é embutido: tudo vem de entrada
  com fonte rastreável (ficha técnica, ensaio, apostila, literatura).

Uso típico em scripts de projeto:
    import sys; sys.path.insert(0, "assessoria/ferramentas/calc")
    import acustica as ac
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

P_REF = 20e-6        # Pa
W_REF = 1e-12        # W
BANDAS_OITAVA = (63, 125, 250, 500, 1000, 2000, 4000, 8000)


# =============================================================================
# Ar
# =============================================================================
def velocidade_som(temp_c: float = 20.0) -> float:
    """c ≈ 331,3·√(1 + T/273,15) m/s (ar seco). A 20 °C ≈ 343,2 m/s."""
    return 331.3 * math.sqrt(1 + temp_c / 273.15)


def comprimento_onda(freq_hz: float, temp_c: float = 20.0) -> float:
    """λ = c/f (m)."""
    return velocidade_som(temp_c) / freq_hz


def atraso_ms(distancia_m: float, temp_c: float = 20.0) -> float:
    """Tempo de propagação (ms) para alinhar fontes por atraso: t = d/c."""
    return 1000.0 * distancia_m / velocidade_som(temp_c)


# =============================================================================
# Decibéis — NUNCA somar níveis aritmeticamente
# =============================================================================
def soma_db(niveis: Iterable[float]) -> float:
    """Soma energética de fontes INCOERENTES: L = 10·log10(Σ 10^(Li/10)).
    Ex.: 90 dB + 90 dB = 93,0 dB (não 180 dB). Para fontes coerentes em fase
    (ex.: duas caixas idênticas em baixa frequência, muito próximas) o ganho pode
    chegar a +6 dB — use soma_coerente_db."""
    niveis = list(niveis)
    if not niveis:
        raise ValueError("lista vazia")
    return 10 * math.log10(sum(10 ** (l / 10) for l in niveis))


def soma_coerente_db(niveis: Sequence[float], fases_graus: Sequence[float] | None = None) -> float:
    """Soma de sinais COERENTES (mesma frequência) considerando fase: soma de pressões complexas.
    Válido para uma única frequência; em banda larga use soma_db."""
    fases = fases_graus or [0.0] * len(niveis)
    re_ = sum(10 ** (l / 20) * math.cos(math.radians(f)) for l, f in zip(niveis, fases))
    im_ = sum(10 ** (l / 20) * math.sin(math.radians(f)) for l, f in zip(niveis, fases))
    mag = math.hypot(re_, im_)
    return 20 * math.log10(mag) if mag > 0 else float("-inf")


def subtrai_db(total: float, fundo: float) -> float:
    """Nível da fonte isolada a partir do total medido e do ruído de fundo:
    Ls = 10·log10(10^(Lt/10) − 10^(Lf/10)). Se Lt − Lf < 3 dB a correção não é confiável
    (critérios normativos de medição costumam exigir diferença mínima — verificar a norma)."""
    if total <= fundo:
        raise ValueError("total deve ser maior que o ruído de fundo")
    if total - fundo < 3:
        raise ValueError("diferença < 3 dB: resultado não confiável")
    return 10 * math.log10(10 ** (total / 10) - 10 ** (fundo / 10))


def media_energetica_db(niveis: Iterable[float]) -> float:
    """Média energética (Leq de amostras de mesma duração): 10·log10(média de 10^(Li/10))."""
    niveis = list(niveis)
    return 10 * math.log10(sum(10 ** (l / 10) for l in niveis) / len(niveis))


def pa_para_db(p_pa: float) -> float:
    return 20 * math.log10(p_pa / P_REF)


def db_para_pa(lp_db: float) -> float:
    return P_REF * 10 ** (lp_db / 20)


# =============================================================================
# Propagação
# =============================================================================
def spl_inverso_quadrado(spl_ref: float, d_ref: float, d: float) -> float:
    """Fonte PONTUAL em CAMPO LIVRE: L(d) = Lref − 20·log10(d/dref) (−6 dB por dobro da distância).
    NÃO vale: no campo próximo da fonte, em line arrays no campo próximo (≈ −3 dB/dobro),
    nem em ambientes reverberantes além da distância crítica (use spl_campo_total)."""
    return spl_ref - 20 * math.log10(d / d_ref)


def spl_fonte_linha(spl_ref: float, d_ref: float, d: float) -> float:
    """Fonte em LINHA idealizada (infinita/coerente, campo próximo de um array): −10·log10(d/dref).
    Aplicação limitada à região onde o array se comporta como linha (depende do comprimento
    e da frequência). Use apenas com dados do fabricante para delimitar essa região."""
    return spl_ref - 10 * math.log10(d / d_ref)


def spl_por_sensibilidade(sens_db_1w1m: float, potencia_w: float, d_m: float) -> float:
    """SPL estimado no EIXO, campo livre: L = S + 10·log10(P) − 20·log10(d).
    Cuidados: (1) confirme se a sensibilidade é 1 W/1 m ou 2,83 V/1 m (para 4 Ω, 2,83 V ≈ 2 W);
    (2) espaço de medição (meio espaço vs. espaço pleno: até 6 dB de diferença);
    (3) compressão térmica e limites de excursão — o SPL máximo REAL pode ser menor que o calculado;
    (4) fora do eixo, aplique a atenuação do diagrama polar do fabricante (não invente)."""
    return sens_db_1w1m + 10 * math.log10(potencia_w) - 20 * math.log10(d_m)


def spl_por_sensibilidade_tensao(sens_db_2v83: float, tensao_v: float, d_m: float) -> float:
    """SPL no eixo, campo livre, a partir de sensibilidade em 2,83 V/1 m: L = S + 20·log10(V/2,83) − 20·log10(d)."""
    return sens_db_2v83 + 20 * math.log10(tensao_v / 2.83) - 20 * math.log10(d_m)


def potencia_necessaria_w(spl_alvo: float, sens_db_1w1m: float, d_m: float, headroom_db: float = 0.0) -> float:
    """Potência elétrica para SPL alvo no eixo (campo livre) + margem dinâmica:
    P = 10^((Lalvo + headroom − S + 20·log10 d)/10). Mesmas ressalvas de spl_por_sensibilidade."""
    return 10 ** ((spl_alvo + headroom_db - sens_db_1w1m + 20 * math.log10(d_m)) / 10)


# =============================================================================
# Acústica de salas
# =============================================================================
@dataclass
class Superficie:
    """Superfície com área (m²) e coeficientes de absorção por banda {Hz: α}.
    'fonte' é obrigatória: ficha de ensaio, apostila (arquivo+página) ou literatura."""
    nome: str
    area_m2: float
    alfa: Mapping[int, float]
    fonte: str = "NÃO INFORMADA"


@dataclass
class Absorvedor:
    """Absorção discreta (pessoas, cadeiras, objetos) em m² Sabine por unidade, por banda."""
    nome: str
    quantidade: float
    a_unit_m2: Mapping[int, float]
    fonte: str = "NÃO INFORMADA"


def area_absorcao(superficies: Sequence[Superficie], banda: int,
                  absorvedores: Sequence[Absorvedor] = ()) -> float:
    """A = Σ Si·αi + Σ Nj·Aj (m² Sabine) na banda indicada."""
    a = sum(s.area_m2 * s.alfa[banda] for s in superficies)
    a += sum(x.quantidade * x.a_unit_m2[banda] for x in absorvedores)
    return a


def rt_sabine(volume_m3: float, a_total_m2: float, m_ar: float = 0.0) -> float:
    """Sabine: T = 0,161·V / (A + 4mV).  (0,161 ≈ 24·ln10/c a ~20 °C)
    Validade: campo difuso, absorção média baixa/moderada (ᾱ ≲ 0,2–0,3) e distribuída;
    superestima T em salas muito absorventes. m_ar = coef. de atenuação do ar em potência (1/m) —
    só em altas frequências (≥ 2 kHz) e volumes grandes; informe a fonte do valor (ex.: ISO 9613-1)."""
    return 0.161 * volume_m3 / (a_total_m2 + 4 * m_ar * volume_m3)


def rt_eyring(volume_m3: float, s_total_m2: float, alfa_medio: float, m_ar: float = 0.0) -> float:
    """Eyring-Norris: T = 0,161·V / (−S·ln(1 − ᾱ) + 4mV).
    Melhor que Sabine quando ᾱ é alto e a absorção é uniformemente distribuída. Ambos falham
    com absorção concentrada (ex.: só no piso/forro), geometrias muito alongadas/achatadas
    (quadras, corredores) ou acoplamento entre volumes — nesses casos, considere Fitzroy,
    Arau-Puchades ou simulação e, sobretudo, MEÇA."""
    if not 0 < alfa_medio < 1:
        raise ValueError("alfa médio deve estar entre 0 e 1")
    return 0.161 * volume_m3 / (-s_total_m2 * math.log(1 - alfa_medio) + 4 * m_ar * volume_m3)


def rt_por_banda(volume_m3: float, superficies: Sequence[Superficie],
                 absorvedores: Sequence[Absorvedor] = (), bandas: Sequence[int] = BANDAS_OITAVA,
                 m_ar: Mapping[int, float] | None = None) -> dict:
    """Calcula Sabine e Eyring em cada banda e devolve também ᾱ e A — para memória de cálculo.
    Bandas sem dado de α em alguma superfície são ignoradas e listadas em 'bandas_sem_dado'."""
    s_total = sum(s.area_m2 for s in superficies)
    res, faltando = {}, []
    for b in bandas:
        if any(b not in s.alfa for s in superficies) or any(b not in x.a_unit_m2 for x in absorvedores):
            faltando.append(b)
            continue
        a = area_absorcao(superficies, b, absorvedores)
        alfa_m = a / s_total
        m = (m_ar or {}).get(b, 0.0)
        res[b] = {
            "A_m2": round(a, 2),
            "alfa_medio": round(alfa_m, 3),
            "T_sabine_s": round(rt_sabine(volume_m3, a, m), 2),
            "T_eyring_s": round(rt_eyring(volume_m3, s_total, min(alfa_m, 0.99), m), 2) if alfa_m < 1 else None,
        }
    return {"S_total_m2": round(s_total, 2), "V_m3": volume_m3, "bandas": res, "bandas_sem_dado": faltando}


def area_necessaria_para_rt(volume_m3: float, rt_alvo_s: float, a_existente_m2: float,
                            alfa_material: float, alfa_superficie_substituida: float = 0.0) -> float:
    """Área de material (m²) a aplicar para atingir T alvo (Sabine), considerando que o material
    cobre uma superfície que já tinha α_sub: ΔA = 0,161V/T − A_exist;  S = ΔA / (α_mat − α_sub).
    Estimativa de pré-dimensionamento por banda — verifique em todas as bandas relevantes."""
    delta = 0.161 * volume_m3 / rt_alvo_s - a_existente_m2
    if delta <= 0:
        return 0.0
    ganho = alfa_material - alfa_superficie_substituida
    if ganho <= 0:
        raise ValueError("material não aumenta a absorção da superfície substituída")
    return delta / ganho


def constante_sala(s_total_m2: float, alfa_medio: float) -> float:
    """R = S·ᾱ / (1 − ᾱ) (m²)."""
    return s_total_m2 * alfa_medio / (1 - alfa_medio)


def distancia_critica(q: float, r_sala_m2: float) -> float:
    """Dc = √(Q·R / 16π) ≈ 0,141·√(Q·R). Distância onde campo direto = campo reverberante.
    Modelo estatístico (campo difuso). Q é do fabricante, na banda considerada."""
    return math.sqrt(q * r_sala_m2 / (16 * math.pi))


def distancia_critica_sabine(q: float, volume_m3: float, rt_s: float) -> float:
    """Dc ≈ 0,057·√(Q·V/T) — forma equivalente via Sabine."""
    return 0.057 * math.sqrt(q * volume_m3 / rt_s)


def q_de_di(di_db: float) -> float:
    """Q = 10^(DI/10)."""
    return 10 ** (di_db / 10)


def spl_campo_total(lw_db: float, q: float, r_m: float, r_sala_m2: float) -> float:
    """Hopkins-Stryker: Lp = Lw + 10·log10(Q/(4πr²) + 4/R).
    Modelo de campo difuso — aproximação; não prevê modos, focalizações nem ecos."""
    return lw_db + 10 * math.log10(q / (4 * math.pi * r_m ** 2) + 4 / r_sala_m2)


def frequencia_schroeder(rt_s: float, volume_m3: float) -> float:
    """fS ≈ 2000·√(T/V). Abaixo dela o comportamento é MODAL e modelos estatísticos (Sabine/Eyring,
    Hopkins-Stryker) perdem validade."""
    return 2000 * math.sqrt(rt_s / volume_m3)


def modos_sala(lx: float, ly: float, lz: float, f_max: float = 300.0, temp_c: float = 20.0) -> list[dict]:
    """Modos de uma sala RETANGULAR de paredes rígidas (Rayleigh): f = c/2·√((nx/Lx)²+(ny/Ly)²+(nz/Lz)²).
    Não vale para geometrias irregulares ou paredes leves (drywall/forros) que alteram as condições de contorno."""
    c = velocidade_som(temp_c)
    out = []
    nmax = [int(2 * f_max * L / c) + 1 for L in (lx, ly, lz)]
    for nx in range(nmax[0] + 1):
        for ny in range(nmax[1] + 1):
            for nz in range(nmax[2] + 1):
                if nx == ny == nz == 0:
                    continue
                f = c / 2 * math.sqrt((nx / lx) ** 2 + (ny / ly) ** 2 + (nz / lz) ** 2)
                if f <= f_max:
                    tipo = {1: "axial", 2: "tangencial", 3: "oblíquo"}[sum(1 for n in (nx, ny, nz) if n)]
                    out.append({"f_hz": round(f, 1), "n": (nx, ny, nz), "tipo": tipo})
    return sorted(out, key=lambda m: m["f_hz"])


def alcons_peutz(r_m: float, rt_s: float, volume_m3: float, q: float, n_fontes_equiv: float = 1.0) -> float:
    """%ALcons (Peutz) = 200·r²·T²·(n+1) / (V·Q), para r ≤ 3,16·Dc; além disso ≈ 9·T.
    ESTIMATIVA GROSSEIRA: ignora ruído de fundo, ecos e distribuição real das reflexões.
    Não usar como prova de inteligibilidade — inteligibilidade se comprova MEDINDO (STI/STIPA)."""
    return 200 * r_m ** 2 * rt_s ** 2 * (n_fontes_equiv + 1) / (volume_m3 * q)


# =============================================================================
# Sonorização distribuída (forro) — cobertura geométrica
# =============================================================================
def diametro_cobertura(altura_forro_m: float, altura_ouvido_m: float, angulo_cobertura_graus: float) -> float:
    """Diâmetro coberto no plano de audição por uma caixa de teto apontada para baixo:
    D = 2·(h − h_ouvido)·tan(θ/2). θ = ângulo de cobertura (−6 dB) DO FABRICANTE na banda de
    interesse (tipicamente 2 kHz ou 4 kHz para fala). Ângulo sem banda definida = dado insuficiente."""
    h = altura_forro_m - altura_ouvido_m
    if h <= 0:
        raise ValueError("forro deve estar acima do plano de audição")
    return 2 * h * math.tan(math.radians(angulo_cobertura_graus / 2))


def espacamento_caixas_teto(altura_forro_m: float, altura_ouvido_m: float, angulo_graus: float,
                            criterio: str = "borda-a-borda") -> float:
    """Espaçamento em grade QUADRADA para caixas de teto.
    Critérios (D = diâmetro de cobertura):
      'borda-a-borda'   s = D            (economia; variação maior entre caixas)
      'sobreposicao'    s = D/√2 ≈ 0,71D (círculos cobrem a área do quadrado; uniformidade melhor)
      'centro-a-centro' s = D/2          (alta uniformidade/inteligibilidade, ex.: salas reverberantes)
    A uniformidade real (±dB) deve ser verificada com o diagrama polar e, idealmente, simulação/medição."""
    d = diametro_cobertura(altura_forro_m, altura_ouvido_m, angulo_graus)
    fator = {"borda-a-borda": 1.0, "sobreposicao": 1 / math.sqrt(2), "centro-a-centro": 0.5}
    if criterio not in fator:
        raise ValueError(f"critério deve ser um de {list(fator)}")
    return d * fator[criterio]


def quantidade_caixas_grade(comprimento_m: float, largura_m: float, espacamento_m: float,
                            otimizar: bool = True) -> dict:
    """Quantidade de caixas em grade retangular (caixas no centro de cada célula).

    espacamento_m = passo da grade QUADRADA equivalente ao critério (ver espacamento_caixas_teto).
    otimizar=True (padrão): aplica a condição geométrica real — a meia-diagonal da célula retangular
      não pode exceder a da célula quadrada do critério: √(px² + py²) ≤ s·√2 — e escolhe o menor
      nx·ny que a satisfaz (células retangulares podem economizar caixas).
    otimizar=False: critério eixo a eixo (px ≤ s e py ≤ s), mais conservador.
    Verifique sempre o ângulo no pior ponto com angulo_pior_ponto()."""
    s = espacamento_m
    if not otimizar:
        nx = max(1, math.ceil(comprimento_m / s))
        ny = max(1, math.ceil(largura_m / s))
    else:
        limite = s * math.sqrt(2)
        melhor = None
        for nx_ in range(1, math.ceil(comprimento_m / s) + 1):
            for ny_ in range(1, math.ceil(largura_m / s) + 1):
                if math.hypot(comprimento_m / nx_, largura_m / ny_) <= limite + 1e-9:
                    chave = (nx_ * ny_, abs(comprimento_m / nx_ - largura_m / ny_))
                    if melhor is None or chave < melhor[0]:
                        melhor = (chave, nx_, ny_)
        _, nx, ny = melhor
    return {"nx": nx, "ny": ny, "total": nx * ny,
            "passo_x_m": round(comprimento_m / nx, 2), "passo_y_m": round(largura_m / ny, 2),
            "criterio": "diagonal da célula" if otimizar else "eixo a eixo"}


def angulo_pior_ponto(passo_x_m: float, passo_y_m: float, altura_forro_m: float, altura_ouvido_m: float) -> float:
    """Ângulo fora do eixo (graus) no ponto mais desfavorável de uma célula (canto), em relação à caixa
    mais próxima: atan(meia-diagonal / (h − h_ouvido)). Compare com metade do ângulo de cobertura."""
    return math.degrees(math.atan(math.hypot(passo_x_m, passo_y_m) / 2 / (altura_forro_m - altura_ouvido_m)))


# =============================================================================
# Linhas de tensão constante (70 V / 100 V) e cabos
# =============================================================================
def carga_linha_tensao_constante(taps_w: Iterable[float], tensao_linha_v: float = 70.7,
                                 margem: float = 1.25) -> dict:
    """Soma das derivações (taps), impedância equivalente vista pelo amplificador e potência
    mínima recomendada do amplificador com margem (padrão 25%; perdas de transformadores e
    envelhecimento justificam margem — ajuste conforme o fabricante).
    Z = V²/P. Nunca ligar carga com Z abaixo do mínimo da saída do amplificador."""
    p = sum(taps_w)
    return {"potencia_taps_w": p,
            "impedancia_equivalente_ohm": round(tensao_linha_v ** 2 / p, 1) if p else None,
            "amplificador_minimo_w": round(p * margem, 1),
            "tensao_linha_v": tensao_linha_v}


def resistencia_cabo_ohm(comprimento_m: float, secao_mm2: float, ida_e_volta: bool = True,
                         resistividade_ohm_mm2_m: float = 0.0175) -> float:
    """R = ρ·L/S (cobre ≈ 0,0175 Ω·mm²/m a 20 °C). ida_e_volta=True considera os 2 condutores.
    Prefira a resistência por km da FICHA DO CABO quando disponível."""
    l = comprimento_m * (2 if ida_e_volta else 1)
    return resistividade_ohm_mm2_m * l / secao_mm2


def perda_cabo_db(r_cabo_ohm: float, z_carga_ohm: float) -> dict:
    """Perda por divisão de tensão (carga resistiva idealizada): perda = 20·log10(Z/(Z+Rc)).
    Para linha 70/100 V use z_carga = V²/P total. Critério usual de projeto: perda ≤ 0,5–1 dB
    (≈ 10–20% de potência) — confirme o critério adotado no projeto.
    Também devolve o fator de amortecimento limitado pelo cabo (Z/Rc) para baixa impedância."""
    perda = 20 * math.log10(z_carga_ohm / (z_carga_ohm + r_cabo_ohm))
    pot = 1 - (z_carga_ohm / (z_carga_ohm + r_cabo_ohm)) ** 2
    return {"perda_db": round(perda, 2), "perda_potencia_pct": round(100 * pot, 1),
            "fator_amortecimento_max_pelo_cabo": round(z_carga_ohm / r_cabo_ohm, 1) if r_cabo_ohm else None}


def impedancia_paralelo(*z_ohm: float) -> float:
    """Impedância nominal de caixas em paralelo (aproximação com impedâncias nominais — a impedância
    real varia com a frequência e pode cair abaixo da nominal)."""
    return 1 / sum(1 / z for z in z_ohm)


# =============================================================================
# Microfones — ganho antes da microfonia (modelo de Davis, campo livre)
# =============================================================================
def pag_db(d0: float, d1: float, ds: float, d2: float) -> float:
    """Ganho acústico potencial (PAG) — Davis, campo livre, fontes e microfone omnidirecionais:
    PAG = 20·log10( (D1·D0) / (Ds·D2) )
      D0 = orador→ouvinte mais distante; D1 = microfone→caixa; Ds = orador→microfone; D2 = caixa→ouvinte.
    Limitações: ignora diretividade (microfone/caixa melhoram), reverberação (piora) e
    quantidade de microfones abertos. Use para comparar arranjos, não como garantia."""
    return 20 * math.log10((d1 * d0) / (ds * d2))


def nag_db(d0: float, ead: float) -> float:
    """Ganho acústico necessário (NAG) = 20·log10(D0/EAD). EAD = distância equivalente de audição
    desejada (ex.: 0,6–1,5 m para fala confortável — critério de projeto, não norma)."""
    return 20 * math.log10(d0 / ead)


def margem_microfonia(pag: float, nag: float, n_mics_abertos: int = 1, margem_estabilidade_db: float = 6.0) -> float:
    """Margem = PAG − (NAG + 10·log10(NOM) + FSM). Positiva = viável no modelo. NOM = nº de microfones abertos;
    FSM = margem de estabilidade (usual 6 dB)."""
    return pag - (nag + 10 * math.log10(n_mics_abertos) + margem_estabilidade_db)


# =============================================================================
# Isolamento — APENAS ordem de grandeza
# =============================================================================
def lei_massa_incidencia_campo(massa_superficial_kg_m2: float, freq_hz: float) -> float:
    """Lei da massa (incidência de campo, parede simples, limitada pela massa):
    R ≈ 20·log10(m·f) − 47 dB.
    ESTIMATIVA TEÓRICA DE ORDEM DE GRANDEZA. Não considera: frequência de coincidência
    (queda acentuada), ressonâncias, frestas, portas/janelas, transmissão por flancos e
    estrutural, qualidade de execução. O desempenho em campo (DnT,w) costuma ser bem menor
    que o de laboratório (Rw). Isolamento se comprova com ENSAIO; nunca prometa com base nisto."""
    return 20 * math.log10(massa_superficial_kg_m2 * freq_hz) - 47


def isolamento_composto(elementos: Sequence[tuple[float, float]]) -> float:
    """Isolamento resultante de parede com elementos de áreas Si e índices Ri (dB):
    R = −10·log10( Σ Si·10^(−Ri/10) / Σ Si ). Mostra o efeito de portas, janelas e frestas
    (uma fresta pequena domina o resultado). Use Ri de ensaio, na mesma banda."""
    s_tot = sum(s for s, _ in elementos)
    tau = sum(s * 10 ** (-r / 10) for s, r in elementos) / s_tot
    return -10 * math.log10(tau)


# =============================================================================
# Áudio digital / níveis elétricos
# =============================================================================
def dbu_para_v(dbu: float) -> float:
    return 0.7746 * 10 ** (dbu / 20)


def v_para_dbu(v: float) -> float:
    return 20 * math.log10(v / 0.7746)


def dbv_para_v(dbv: float) -> float:
    return 10 ** (dbv / 20)
