# Cálculos de pré-projeto — EEEM Emir de Macedo Gomes — Auditório

Gerado por `agente/calc_auditorio.py` a partir de `escola.json`. Resultados de pré-projeto; revisar após vistoria e medições.

## 1. Linhas de visão

- Fileiras: 15; passo 1.00 m; olho da 1ª fileira a 2.40 m da borda do palco; última fileira a 16.40 m.
- Palco 1.00 m acima da plateia. Altura do olho sentado 1.12 m. C = folga da linha de visão sobre o olho da fileira da frente (0,12 m = vê por cima da cabeça; 0,06 m = vê entre cabeças, exige poltronas alternadas).

### 1.1 Piso existente (plano)

| Ponto focal | C mínimo (m) | Fileiras com C < 0,06 |
|---|---|---|
| 0.00 m acima do piso do palco | -0.035 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 |
| 0.20 m acima do piso do palco | 0.005 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 |
| 0.40 m acima do piso do palco | 0.017 | 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 |
| 0.60 m acima do piso do palco | 0.029 | 7, 8, 9, 10, 11, 12, 13, 14, 15 |

## 2. Elevação do piso (arquibancada) — perfis mínimos

| Cenário | Ponto focal | C alvo | Elevação por fileira (m, acumulada) | Topo (m) |
|---|---|---|---|---|
| A — visibilidade plena | +0.40 m | 0.08 | 0.00 / 0.00 / 0.00 / 0.04 / 0.09 / 0.15 / 0.22 / 0.31 / 0.40 / 0.49 / 0.60 / 0.71 / 0.83 / 0.95 / 1.08 | 1.08 |
| B — rampa acessível | +0.40 m | 0.06 | 0.00 / 0.00 / 0.00 / 0.01 / 0.04 / 0.07 / 0.11 / 0.15 / 0.20 / 0.26 / 0.32 / 0.39 / 0.46 / 0.54 / 0.62 | 0.62 |
| C — mínimo | +0.50 m | 0.06 | 0.00 / 0.00 / 0.00 / 0.00 / 0.01 / 0.02 / 0.03 / 0.06 / 0.09 / 0.13 / 0.17 / 0.22 / 0.27 / 0.33 / 0.39 | 0.39 |

**A — visibilidade plena** — desnível total 1.08 m em 14.0 m (inclinação média 7.7 %); maior espelho por fileira 0.130 m.
  - Corredores em rampa ≤ 8,33 % exigem patamar a cada 0,80 m de desnível (NBR 9050).
  - Verificação: C mínimo obtido = 0.064 m.

**B — rampa acessível** — desnível total 0.62 m em 14.0 m (inclinação média 4.4 %); maior espelho por fileira 0.080 m.
  - Corredores laterais podem ser **rampa contínua ≤ 6,25 %** (NBR 9050: até 1,00 m de desnível por segmento) → rota acessível até o fundo.
  - Verificação: C mínimo obtido = 0.054 m.

**C — mínimo** — desnível total 0.39 m em 14.0 m (inclinação média 2.8 %); maior espelho por fileira 0.060 m.
  - Corredores laterais podem ser **rampa contínua ≤ 6,25 %** (NBR 9050: até 1,00 m de desnível por segmento) → rota acessível até o fundo.
  - Verificação: C mínimo obtido = 0.052 m.

> Elevar o fundo da plateia exige compatibilizar as **saídas no fundo** (portas no nível original), o **pé-direito livre** e a **estrutura**. Ver diagnóstico.

## 3. Lugares reservados

- Lotação de referência: 270 lugares (validar lotação aprovada no PSCIP).
- Decreto 5.296/2004, art. 23: ≥ 2 % para P.C.R. → **6 espaços**; ≥ 2 % para P.M.R./deficiência visual/obesos → **6 assentos**.
- Indicados no desenho: 2 espaços P.C.R. → diferença: 4 a prever. Distribuir em locais diversos com boa visibilidade (NBR 9050, seção de auditórios — conferir item na edição vigente).

## 4. Volume e tempo de reverberação (Sabine) — hipóteses

Pé-direito não consta na planta: os cenários abaixo varrem alturas prováveis. Materiais existentes são hipótese até a vistoria. Meta de referência: DIN 18041:2016.

### Pé-direito 4.5 m → V ≈ 2.031 m³
Metas DIN 18041 (500–1000 Hz, ocupado): A1 música 1.56 s; A2 fala/palestra 1.08 s; A3 aula/comunicação 0.89 s

| Cenário | Estado | 125 Hz | 250 Hz | 500 Hz | 1000 Hz | 2000 Hz | 4000 Hz | T médio 500–1k |
|---|---|---|---|---|---|---|---|---|
| E0 existente (hip.: forro liso, poltronas estofadas) | vazio | 1.29 | 1.66 | 1.60 | 1.48 | 1.39 | 1.30 | **1.54** |
| E0 existente (hip.: forro liso, poltronas estofadas) | ocupado | 1.19 | 1.53 | 1.48 | 1.38 | 1.27 | 1.16 | **1.43** |
| E0b existente (hip.: cadeiras rígidas) | vazio | 1.87 | 3.47 | 3.93 | 3.93 | 2.73 | 2.03 | **3.93** |
| E0b existente (hip.: cadeiras rígidas) | ocupado | 1.21 | 1.75 | 1.69 | 1.51 | 1.29 | 1.15 | **1.60** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | vazio | 1.13 | 1.09 | 0.94 | 0.86 | 0.84 | 0.83 | **0.90** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | ocupado | 1.05 | 1.03 | 0.90 | 0.83 | 0.80 | 0.77 | **0.86** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | vazio | 0.98 | 0.76 | 0.66 | 0.62 | 0.63 | 0.63 | **0.64** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | ocupado | 0.92 | 0.73 | 0.64 | 0.60 | 0.60 | 0.60 | **0.62** |

### Pé-direito 5.5 m → V ≈ 2.482 m³
Metas DIN 18041 (500–1000 Hz, ocupado): A1 música 1.60 s; A2 fala/palestra 1.12 s; A3 aula/comunicação 0.92 s

| Cenário | Estado | 125 Hz | 250 Hz | 500 Hz | 1000 Hz | 2000 Hz | 4000 Hz | T médio 500–1k |
|---|---|---|---|---|---|---|---|---|
| E0 existente (hip.: forro liso, poltronas estofadas) | vazio | 1.57 | 2.02 | 1.94 | 1.79 | 1.66 | 1.51 | **1.87** |
| E0 existente (hip.: forro liso, poltronas estofadas) | ocupado | 1.44 | 1.87 | 1.80 | 1.67 | 1.52 | 1.35 | **1.74** |
| E0b existente (hip.: cadeiras rígidas) | vazio | 2.27 | 4.20 | 4.71 | 4.64 | 3.17 | 2.29 | **4.67** |
| E0b existente (hip.: cadeiras rígidas) | ocupado | 1.48 | 2.13 | 2.04 | 1.82 | 1.54 | 1.34 | **1.93** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | vazio | 1.37 | 1.33 | 1.14 | 1.04 | 1.02 | 0.98 | **1.09** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | ocupado | 1.28 | 1.26 | 1.09 | 1.00 | 0.96 | 0.91 | **1.05** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | vazio | 1.20 | 0.92 | 0.81 | 0.75 | 0.76 | 0.75 | **0.78** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | ocupado | 1.12 | 0.89 | 0.78 | 0.73 | 0.73 | 0.71 | **0.76** |

### Pé-direito 6.5 m → V ≈ 2.934 m³
Metas DIN 18041 (500–1000 Hz, ocupado): A1 música 1.63 s; A2 fala/palestra 1.14 s; A3 aula/comunicação 0.94 s

| Cenário | Estado | 125 Hz | 250 Hz | 500 Hz | 1000 Hz | 2000 Hz | 4000 Hz | T médio 500–1k |
|---|---|---|---|---|---|---|---|---|
| E0 existente (hip.: forro liso, poltronas estofadas) | vazio | 1.85 | 2.38 | 2.28 | 2.09 | 1.91 | 1.70 | **2.18** |
| E0 existente (hip.: forro liso, poltronas estofadas) | ocupado | 1.70 | 2.20 | 2.11 | 1.95 | 1.76 | 1.53 | **2.03** |
| E0b existente (hip.: cadeiras rígidas) | vazio | 2.67 | 4.92 | 5.46 | 5.29 | 3.58 | 2.51 | **5.38** |
| E0b existente (hip.: cadeiras rígidas) | ocupado | 1.74 | 2.50 | 2.39 | 2.13 | 1.78 | 1.52 | **2.26** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | vazio | 1.62 | 1.56 | 1.35 | 1.22 | 1.18 | 1.12 | **1.29** |
| T1 essencial (painéis 120 m² + cortinas 60 m²) | ocupado | 1.50 | 1.48 | 1.29 | 1.18 | 1.12 | 1.05 | **1.23** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | vazio | 1.41 | 1.09 | 0.95 | 0.89 | 0.88 | 0.87 | **0.92** |
| T2 completo (T1 + nuvens 150 m² + difusor 20 m²) | ocupado | 1.32 | 1.05 | 0.92 | 0.86 | 0.85 | 0.82 | **0.89** |

## 5. Sonorização — cobertura e delays (estimativa geométrica)

- Caixa principal (L) em x = 7.0 m, altura 3.0 m. Distância à 1ª fileira (centro): 7.6 m; à última fileira (canto oposto, já elevada): 21.1 m.
- Fonte pontual (−6 dB/dobro): variação ≈ 8.8 dB frente→fundo.
- Coluna/line array em campo próximo (≈ −3 dB/dobro): ≈ 4.4 dB, antes do ajuste de mira — justifica a avaliação de colunas direcionais.
- Se houver reforço com delay em y = 11.4 m: atraso inicial = 11.6 m / 343 m/s + 10 ms (precedência) ≈ **44 ms** (ajustar por medição de resposta ao impulso).

## 6. Imagem — painel LED x projeção

- Regra 1/6 da distância da última fileira (19.4 m): altura útil ≥ 3.23 m → 16:9 = 5.75 × 3.23 m.
- Regra 1/8 da distância da última fileira (19.4 m): altura útil ≥ 2.42 m → 16:9 = 4.31 × 2.42 m.
- LED 5.00 × 2.81 m, pitch 2.6 mm → 1923 × 1081 px; distância mínima confortável ≈ 2.6–3.9 m (1ª fileira a 5.4 m).
- LED 5.00 × 2.81 m, pitch 2.9 mm → 1724 × 969 px; distância mínima confortável ≈ 2.9–4.3 m (1ª fileira a 5.4 m).
- LED 5.00 × 2.81 m, pitch 3.9 mm → 1282 × 721 px; distância mínima confortável ≈ 3.9–5.8 m (1ª fileira a 5.4 m).
- Área 14.1 m²; consumo típico médio 2.8 kW, máximo 8.4 kW; peso ≈ 422 kg + estrutura (confirmar com fabricante).
- Projeção na mesma área: para 200 cd/m² na tela (ganho 1.0) → ≈ 8.828 lm efetivos (com controle de luz ambiente).
