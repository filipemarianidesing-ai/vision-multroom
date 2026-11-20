#!/usr/bin/env python3
"""
calc_auditorio.py — Ferramenta de cálculo do Agente Engenheiro de Auditórios (Mariani Áudio e Vídeo)

Lê o arquivo JSON de uma escola (modelo em template_escola.json) e gera um relatório
Markdown com:
  1. Linhas de visão (valor C por fileira) para o piso existente e para o perfil
     de arquibancada calculado (elevação do piso);
  2. Perfil de elevação mínimo (C-value) e verificação de rampa/degraus nos corredores;
  3. Lugares reservados (P.C.R., P.M.R./P.O.) — Decreto 5.296/2004 art. 23 e NBR 9050;
  4. Volume e tempo de reverberação (Sabine) por cenário de materiais, vazio/ocupado,
     com meta de referência DIN 18041:2016;
  5. Atenuação do som direto (fonte pontual x coluna) e tempo de delay de reforços;
  6. Dimensionamento preliminar de painel LED e de projeção.

Todos os resultados são de PRÉ-PROJETO. Valores marcados como hipótese no JSON
continuam hipótese no relatório. Uso:

    python3 calc_auditorio.py escola.json > calculos.md
"""
import json, math, sys

BANDAS = [125, 250, 500, 1000, 2000, 4000]

# Coeficientes de absorção sonora (Sabine) — valores típicos de literatura
# (Beranek, Long "Architectural Acoustics", catálogos). Substituir por dados de ensaio
# do produto especificado (ISO 354) quando o produto for definido.
MATERIAIS = {
    "alvenaria_rebocada_pintada": [0.01, 0.01, 0.02, 0.02, 0.02, 0.03],
    "concreto_aparente":          [0.01, 0.01, 0.02, 0.02, 0.02, 0.02],
    "piso_ceramico":              [0.01, 0.01, 0.01, 0.02, 0.02, 0.02],
    "piso_madeira_palco":         [0.15, 0.11, 0.10, 0.07, 0.06, 0.07],
    "carpete_6mm":                [0.02, 0.06, 0.14, 0.37, 0.60, 0.65],
    "forro_gesso_liso":           [0.29, 0.10, 0.05, 0.04, 0.07, 0.09],
    "forro_mineral_acustico":     [0.50, 0.70, 0.60, 0.70, 0.70, 0.50],
    "laje_telha_metalica":        [0.10, 0.08, 0.05, 0.05, 0.05, 0.05],
    "vidro_janela":               [0.35, 0.25, 0.18, 0.12, 0.07, 0.04],
    "porta_madeira":              [0.14, 0.10, 0.06, 0.08, 0.10, 0.10],
    "painel_la_mineral_50mm":     [0.25, 0.70, 0.95, 1.00, 0.95, 0.90],
    "painel_la_mineral_50mm_plenum100": [0.55, 0.95, 1.00, 1.00, 0.95, 0.90],
    "cortina_veludo_pregueada":   [0.14, 0.35, 0.55, 0.72, 0.70, 0.65],
    "difusor_madeira":            [0.20, 0.25, 0.25, 0.20, 0.20, 0.20],
    # plateia — por m2 de área de plateia (método de área, Beranek)
    "plateia_estofada_vazia":     [0.49, 0.66, 0.80, 0.88, 0.82, 0.70],
    "plateia_estofada_ocupada":   [0.60, 0.74, 0.88, 0.96, 0.93, 0.85],
    "plateia_rigida_vazia":       [0.10, 0.15, 0.20, 0.20, 0.25, 0.25],
    "plateia_rigida_ocupada":     [0.57, 0.61, 0.75, 0.86, 0.91, 0.86],
}
# absorção do ar 4m (1/m), 20 °C, 50 % UR (ISO 9613-1, aproximado)
AR_4M = [0.0, 0.0, 0.0, 0.003, 0.010, 0.024]


def linhas_visao(D1, T, n, olho, piso, P):
    """C(n) = folga da linha de visão sobre o olho da fileira da frente (m).
    D1: distância horizontal do olho da 1ª fileira ao ponto focal; T: passo das fileiras;
    piso: lista de cotas relativas do piso por fileira (m); P: altura do ponto focal
    em relação ao piso da 1ª fileira (m)."""
    out = []
    for i in range(1, n):
        Dp = D1 + (i - 1) * T
        D = Dp + T
        hb = piso[i] + olho - P
        hf = piso[i - 1] + olho - P
        out.append(hb * Dp / D - hf)
    return out


def perfil_minimo(D1, T, n, olho, P, C, fileiras_planas=1):
    F = [0.0]
    for i in range(1, n):
        if i < fileiras_planas:
            F.append(0.0)
            continue
        Dp = D1 + (i - 1) * T
        D = Dp + T
        hf = F[i - 1] + olho - P
        hb = (hf + C) * D / Dp
        F.append(max(F[-1], hb - olho + P))
    return F


def arred_cima(v, passo):
    return math.ceil(round(v / passo, 6)) * passo


def lugares_reservados(lotacao):
    pcr = max(1, math.ceil(0.02 * lotacao))
    pmr = max(1, math.ceil(0.02 * lotacao))
    return pcr, pmr


def sabine(V, superficies, ocupado):
    res = []
    for b in range(6):
        A = 0.0
        for s in superficies:
            mat = s["material"]
            if mat.startswith("plateia_"):
                mat = mat.replace("_vazia", "_ocupada") if ocupado else mat.replace("_ocupada", "_vazia")
            A += s["area"] * MATERIAIS[mat][b]
        A += AR_4M[b] * V  # termo do ar: 4mV
        res.append(0.161 * V / A if A > 0 else float("inf"))
    return res


def meta_din18041(V):
    return {
        "A1 música": 0.45 * math.log10(V) + 0.07,
        "A2 fala/palestra": 0.37 * math.log10(V) - 0.14,
        "A3 aula/comunicação": 0.32 * math.log10(V) - 0.17,
    }


def main(path):
    E = json.load(open(path, encoding="utf-8"))
    g = E["geometria"]
    p = E["plateia"]
    o = []
    w = o.append
    w(f"# Cálculos de pré-projeto — {E['escola']['nome']}\n")
    w(f"Gerado por `agente/calc_auditorio.py` a partir de `{path.split('/')[-1]}`. "
      "Resultados de pré-projeto; revisar após vistoria e medições.\n")

    # ---------------- 1. Linhas de visão
    n, T, D1, olho = p["fileiras"], p["passo_fileiras_m"], p["dist_olho_1a_fileira_ao_palco_m"], p["altura_olho_sentado_m"]
    hp = g["altura_palco_sobre_plateia_m"]
    w("## 1. Linhas de visão\n")
    w(f"- Fileiras: {n}; passo {T:.2f} m; olho da 1ª fileira a {D1:.2f} m da borda do palco; "
      f"última fileira a {D1 + (n-1)*T:.2f} m.")
    w(f"- Palco {hp:.2f} m acima da plateia. Altura do olho sentado {olho:.2f} m. "
      "C = folga da linha de visão sobre o olho da fileira da frente (0,12 m = vê por cima da cabeça; "
      "0,06 m = vê entre cabeças, exige poltronas alternadas).\n")
    focos = p["pontos_focais_acima_palco_m"]
    plano = [0.0] * n
    w("### 1.1 Piso existente (plano)\n")
    w("| Ponto focal | C mínimo (m) | Fileiras com C < 0,06 |")
    w("|---|---|---|")
    for f in focos:
        c = linhas_visao(D1, T, n, olho, plano, hp + f)
        ruins = [i + 2 for i, v in enumerate(c) if v < 0.06]
        w(f"| {f:.2f} m acima do piso do palco | {min(c):.3f} | {', '.join(map(str, ruins)) or '—'} |")
    w("")

    # ---------------- 2. Perfil de arquibancada
    w("## 2. Elevação do piso (arquibancada) — perfis mínimos\n")
    A = E["arquibancada"]
    w("| Cenário | Ponto focal | C alvo | Elevação por fileira (m, acumulada) | Topo (m) |")
    w("|---|---|---|---|---|")
    perfis = {}
    for cen in A["cenarios"]:
        F = perfil_minimo(D1, T, n, olho, hp + cen["foco_acima_palco_m"], cen["C_m"], A.get("fileiras_planas_frente", 1))
        Fq = [arred_cima(v, A.get("arredondamento_m", 0.01)) for v in F]
        perfis[cen["nome"]] = Fq
        w(f"| {cen['nome']} | +{cen['foco_acima_palco_m']:.2f} m | {cen['C_m']:.2f} | "
          + " / ".join(f"{v:.2f}" for v in Fq) + f" | {Fq[-1]:.2f} |")
    w("")
    for cen in A["cenarios"]:
        Fq = perfis[cen["nome"]]
        espelhos = [Fq[i] - Fq[i - 1] for i in range(1, n)]
        comp = (n - 1) * T
        i_media = Fq[-1] / comp * 100 if comp else 0
        w(f"**{cen['nome']}** — desnível total {Fq[-1]:.2f} m em {comp:.1f} m "
          f"(inclinação média {i_media:.1f} %); maior espelho por fileira {max(espelhos):.3f} m.")
        if Fq[-1] <= 1.00 and i_media <= 6.25:
            w("  - Corredores laterais podem ser **rampa contínua ≤ 6,25 %** (NBR 9050: até 1,00 m de desnível por segmento) → rota acessível até o fundo.")
        elif i_media <= 8.33:
            w("  - Corredores em rampa ≤ 8,33 % exigem patamar a cada 0,80 m de desnível (NBR 9050).")
        else:
            w("  - Corredores precisam de **degraus** (2 degraus por fileira quando o espelho por fileira > 0,18 m), "
              "corrimãos e guarda-corpo nas bordas livres (NBR 9050 / NBR 14718 / NT CBMES).")
        c = linhas_visao(D1, T, n, olho, Fq, hp + cen["foco_acima_palco_m"])
        w(f"  - Verificação: C mínimo obtido = {min(c):.3f} m.\n")
    w("> Elevar o fundo da plateia exige compatibilizar as **saídas no fundo** (portas no nível original), "
      "o **pé-direito livre** e a **estrutura**. Ver diagnóstico.\n")

    # ---------------- 3. Acessibilidade
    lot = p["lotacao_referencia"]
    pcr, pmr = lugares_reservados(lot)
    w("## 3. Lugares reservados\n")
    w(f"- Lotação de referência: {lot} lugares (validar lotação aprovada no PSCIP).")
    w(f"- Decreto 5.296/2004, art. 23: ≥ 2 % para P.C.R. → **{pcr} espaços**; ≥ 2 % para P.M.R./deficiência visual/obesos → **{pmr} assentos**.")
    w(f"- Indicados no desenho: {p.get('espacos_pcr_desenho', 'a levantar')} espaços P.C.R. → diferença: "
      f"{pcr - p.get('espacos_pcr_desenho', 0)} a prever. Distribuir em locais diversos com boa visibilidade (NBR 9050, seção de auditórios — conferir item na edição vigente).\n")

    # ---------------- 4. Acústica
    ac = E["acustica"]
    w("## 4. Volume e tempo de reverberação (Sabine) — hipóteses\n")
    w("Pé-direito não consta na planta: os cenários abaixo varrem alturas prováveis. "
      "Materiais existentes são hipótese até a vistoria. Meta de referência: DIN 18041:2016.\n")
    for H in ac["pe_direito_hipoteses_m"]:
        V = (g["area_plateia_m2"] + g["area_palco_m2"]) * H
        metas = meta_din18041(V)
        w(f"### Pé-direito {H:.1f} m → V ≈ {V:,.0f} m³".replace(",", "."))
        w("Metas DIN 18041 (500–1000 Hz, ocupado): " + "; ".join(f"{k} {v:.2f} s" for k, v in metas.items()) + "\n")
        w("| Cenário | Estado | " + " | ".join(f"{b} Hz" for b in BANDAS) + " | T médio 500–1k |")
        w("|---|---|" + "---|" * 6 + "---|")
        for cen in ac["cenarios"]:
            sup = []
            for s in cen["superficies"]:
                area = s["area"] if "area" in s else s["area_por_m_altura"] * H
                sup.append({"material": s["material"], "area": area})
            for ocup in (False, True):
                T60 = sabine(V, sup, ocup)
                w(f"| {cen['nome']} | {'ocupado' if ocup else 'vazio'} | " + " | ".join(f"{t:.2f}" for t in T60)
                  + f" | **{(T60[2]+T60[3])/2:.2f}** |")
        w("")

    # ---------------- 5. Som
    s = E["som"]
    w("## 5. Sonorização — cobertura e delays (estimativa geométrica)\n")
    xL, hL = s["main_x_m"], s["main_altura_m"]
    dmin = math.dist((0, D1, olho), (xL, 0, hL))
    dmax = math.dist((-p["largura_bloco_m"] / 2, D1 + (n - 1) * T, olho + max(perfis[A["recomendado"]])), (xL, 0, hL))
    w(f"- Caixa principal (L) em x = {xL:.1f} m, altura {hL:.1f} m. Distância à 1ª fileira (centro): {dmin:.1f} m; "
      f"à última fileira (canto oposto, já elevada): {dmax:.1f} m.")
    w(f"- Fonte pontual (−6 dB/dobro): variação ≈ {20*math.log10(dmax/dmin):.1f} dB frente→fundo.")
    w(f"- Coluna/line array em campo próximo (≈ −3 dB/dobro): ≈ {10*math.log10(dmax/dmin):.1f} dB, "
      "antes do ajuste de mira — justifica a avaliação de colunas direcionais.")
    if s.get("delay_y_m"):
        dd = math.dist((xL, 0, hL), (s["delay_x_m"], s["delay_y_m"], s["delay_altura_m"]))
        w(f"- Se houver reforço com delay em y = {s['delay_y_m']:.1f} m: atraso inicial = {dd:.1f} m / 343 m/s "
          f"+ 10 ms (precedência) ≈ **{dd/0.343 + 10:.0f} ms** (ajustar por medição de resposta ao impulso).")
    w("")

    # ---------------- 6. Imagem
    v = E["video"]
    w("## 6. Imagem — painel LED x projeção\n")
    Dlast = D1 + (n - 1) * T + v["recuo_tela_em_relacao_borda_palco_m"]
    Dfirst = D1 + v["recuo_tela_em_relacao_borda_palco_m"]
    for fator in (6, 8):
        h = Dlast / fator
        w(f"- Regra 1/{fator} da distância da última fileira ({Dlast:.1f} m): altura útil ≥ {h:.2f} m → 16:9 = {h*16/9:.2f} × {h:.2f} m.")
    L, Hh = v["led_largura_m"], v["led_altura_m"]
    for pitch in v["pitches_mm"]:
        px_w, px_h = L * 1000 / pitch, Hh * 1000 / pitch
        w(f"- LED {L:.2f} × {Hh:.2f} m, pitch {pitch} mm → {px_w:.0f} × {px_h:.0f} px; distância mínima confortável ≈ {pitch*1.0:.1f}–{pitch*1.5:.1f} m "
          f"(1ª fileira a {Dfirst:.1f} m).")
    area = L * Hh
    w(f"- Área {area:.1f} m²; consumo típico médio {area*v['consumo_medio_w_m2']/1000:.1f} kW, máximo {area*v['consumo_max_w_m2']/1000:.1f} kW; "
      f"peso ≈ {area*v['peso_kg_m2']:.0f} kg + estrutura (confirmar com fabricante).")
    lum = v["projecao_luminancia_alvo_cd_m2"] * math.pi * area / v["projecao_ganho_tela"]
    w(f"- Projeção na mesma área: para {v['projecao_luminancia_alvo_cd_m2']} cd/m² na tela (ganho {v['projecao_ganho_tela']}) "
      f"→ ≈ {lum:,.0f} lm efetivos (com controle de luz ambiente).".replace(",", "."))
    print("\n".join(o))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "template_escola.json")
