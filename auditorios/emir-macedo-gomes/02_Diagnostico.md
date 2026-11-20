# 02 — Diagnóstico do auditório (pré-projeto)

**EEEM Emir de Macedo Gomes — Linhares/ES — SEDU proc. 2024-F7XLL**
Mariani Áudio e Vídeo · Rev. 0 · 20/11/2026 · Simulação de pré-projeto

Legenda das fontes: **[P]** = planta-base (`base/Planta_Auditorio_Emir_de_Macedo_Gomes.pdf`, recorte da prancha 02/08 do PSCIP, abr/2025) · **[C]** = cálculo deste pré-projeto (`dados/calculos_pre_projeto.md`) · **[H]** = hipótese a confirmar · **[V]** = depende de vistoria/medição.

---

## 1. Dados confirmados na planta

| Dado | Valor | Onde está na prancha (início → fim da medida) | Fonte |
|---|---|---|---|
| Área da plateia | 361,74 m² | rótulo "PLATÉIA AUDITÓRIO" | [P] |
| Lotação indicada | 270 lugares | rótulo "(270 lug)" | [P] |
| Área do palco | 89,59 m² | rótulo "PALCO" | [P] |
| Cotas de piso | plateia +0,20 · palco +1,20 → palco **1,00 m** acima da plateia | marcos de nível na plateia e no palco | [P] |
| Largura interna da plateia | **18,60 m** | cadeia na linha da boca de cena: 290+10+180+**900**+180+10+290 cm, da face interna da parede esquerda à da direita | [P] |
| Comprimento da plateia | ≈ 19,45 m (18,70 m até a borda do palco) | área ÷ largura; conferido graficamente da parede do fundo ao alinhamento das salas de apoio | [P]+[C] |
| Boca de cena | 9,00 m | cota "900" entre a plataforma elevatória e a escada | [P] |
| Palco entre salas de apoio | 12,60 m | cadeia inferior 330+600+330 cm | [P] |
| Profundidade do palco | ≈ 7,0 m da borda à parede do fundo (≈ 6,0 m a partir das salas de apoio) | cadeia vertical direita 10+125+10+100+10+120+10+215 cm | [P]+[C] |
| Corredores laterais | 3,04 m cada | cotas "304" da parede ao bloco de poltronas | [P] |
| Faixa livre no fundo | 1,99 m | cota "199" da parede do fundo à última fileira | [P] |
| Poltronas | 15 fileiras × 18 assentos, passo **1,00 m**; 1ª fileira com 14 poltronas + 2 espaços P.C.R. tracejados | contagem gráfica | [P]+[C] |
| Escada de acesso ao palco | 6 degraus, piso 30 cm, largura 145 cm (lado direito da planta) | numeração 01–06, cotas "30" e "145" | [P] |
| Plataforma elevatória | indicada ao lado esquerdo do palco | rótulo "PLATAFORMA ELEVATÓRIA" | [P] |
| Apoio | 2 salas de 6,81 m², 2 sanitários de 3,12 m², 2 depósitos de 2,58 m² | rótulos | [P] |
| Saídas | 2 portas no fundo (cantos) + 1 porta na frente à esquerda, junto ao palco | símbolos de porta PV2 | [P] |
| Incêndio | extintores (água 2A, pó BC 20BC), hidrante HP-13 2×15 m, iluminação de emergência, rotas de fuga sinalizadas | simbologia vermelha | [P] |
| Paredes superiores | linhas "PROJEÇÃO PAREDE SUP." em ziguezague nas duas laterais | linhas tracejadas | [P] — forma real [V] |

**Calibração do desenho:** 1 cm real = 0,2268 pt na prancha (escala ≈ 1:125). Obtida pela largura interna 18,60 m (421,8 pt entre as faces internas) e conferida na cadeia 330|600 (465 cm = 105,5 pt). Todas as pranchas derivadas usam essa calibração.

## 2. Divergências e alertas encontrados

1. **Lotação:** a contagem gráfica dá **266 poltronas + 2 espaços P.C.R.**; o rótulo indica 270 lugares. → Validar a lotação aprovada no PSCIP. [P]+[C]
2. **Lugares reservados insuficientes:** Decreto 5.296/2004, art. 23 exige pelo menos 2 % da lotação para P.C.R. (**6 espaços** para 270) e mais 2 % para P.M.R./deficiência visual/obesos (**6 assentos**). O desenho mostra **2 espaços P.C.R.**, todos na 1ª fileira. [C]
3. **18 assentos por fileira sem corredor central**, com acesso pelas duas pontas. → Conferir o limite de assentos entre corredores e a passagem livre entre fileiras na NT 10/2013 do CBMES. [V]
4. **Passagem entre fileiras:** passo de 1,00 m com poltronas desenhadas com ≈ 0,67 m de profundidade. A passagem livre real depende do rebatimento do assento. [V]

## 3. Problemas que o projeto resolve

### 3.1 Visibilidade — piso plano com palco alto
Com o palco 1,00 m acima e a plateia plana, o valor C (folga da linha de visão sobre o olho da fileira da frente) fica abaixo de 0,06 m da 4ª fileira em diante para um ponto focal 0,40 m acima do piso do palco [C]. Na prática, quem está do meio para trás vê o apresentador **só da cintura para cima**, e não vê quem está sentado ou no chão do palco (teatro, coral, formatura).

**Proposta (perfil B):** manter as fileiras 1–3 em +0,20 (zona acessível) e elevar progressivamente as fileiras 4–15 até +0,82, com patamar no fundo. Os corredores laterais viram **rampas com corrimão duplo** (inclinação variável ≤ 8 %, desnível total 0,62 m). Isso dá rota acessível a todos os níveis. O perfil A (C = 0,08 m) levaria o fundo a +1,28 e exigiria degraus; não é recomendado sem reprojeto das saídas. [C] — ver pranchas ARQ-01 e ARQ-02.

**Por que a elevação ajuda a acústica:** o som direto que passa rasante sobre as cabeças é atenuado pela plateia, sobretudo entre 100 e 400 Hz (efeito de incidência rasante). Elevar as fileiras reduz esse efeito, melhora a voz natural, o teatro e a música acústica, e encurta o caminho livre até o fundo. Com sistema de som, o ganho principal vem das colunas bem miradas, e a elevação complementa. O vazio sob os patamares vira caminho de cabos e recebe lã mineral para não ressoar.

**Condicionantes (afetam custo e viabilidade):**
- As **portas do fundo** estão em +0,20 e o patamar ficaria em +0,82. É preciso compatibilizar com degraus e rampa junto às portas, nova soleira com patamar externo ou relocação da saída. Isso exige **revisão do PSCIP no CBMES**. [V]
- **Pé-direito** sobre o patamar do fundo, com meta de ≥ 2,50 m livres. [V]
- **Estrutura do piso existente** e carga de uso da arquibancada (NBR 6120), validadas por engenheiro estrutural. [V]

### 3.2 Inteligibilidade da fala
- O volume estimado é de 2.000 a 2.900 m³ para pé-direito de 4,5 a 6,5 m. [H]
- Tempo de reverberação estimado hoje (Sabine, 500 Hz–1 kHz): **1,4–2,2 s** com poltronas estofadas. Com cadeiras rígidas e sala vazia, pode passar de **4 s**. [C]+[H]
- Meta do pré-projeto: **0,8–1,1 s** com sala ocupada (DIN 18041:2016, grupo A2 fala/palestra ≈ 1,1 s para esse volume; meta mais baixa favorece o sistema de som).
- Distância da caixa principal à 1ª fileira ≈ 7,6 m e à última ≈ 21 m. Com fonte pontual a queda é de ≈ 9 dB; com coluna direcional fica em ≈ 4–5 dB antes da mira. [C]
- Conclusão: **colunas direcionais + tratamento das paredes laterais e do fundo** são o núcleo do cenário essencial.

### 3.3 Conteúdo visível
- 1ª fileira a 5,4 m e última a 19,4 m da tela, com a tela 3,0 m atrás da borda do palco. A altura útil mínima pela regra 1/8 é 2,42 m. [C]
- Painel LED 5,00 × 2,81 m, P2,6 → ≈ 1920 × 1080 px nativos. Consumo médio ≈ 2,8 kW, pico 8,4 kW; peso ≈ 420 kg + estrutura. [C]+[H]
- Projeção laser ≈ 9.000 lm efetivos na mesma tela. Custa menos, mas depende de escurecer a sala: há janelas ou elementos na parede lateral esquerda [P], e o tipo deles precisa de vistoria [V].

### 3.4 Operação
Hoje não há informação sobre os equipamentos existentes [V]. O projeto prevê duas camadas de operação. A **escola** usa botões de cena (LIGAR · PALESTRA · FORMATURA · MÚSICA · VÍDEO · DESLIGAR) com volumes limitados. O **técnico** assume a mesa completa na posição de operação (FOH) em eventos grandes.

## 4. Hipóteses adotadas (até a vistoria)

| Hipótese | Valor adotado | Impacto se mudar |
|---|---|---|
| Pé-direito | 4,5 / 5,5 / 6,5 m (três cenários) | TR, altura das caixas, LED, varas de luz |
| Forro | gesso liso | TR (forro mineral reduziria a necessidade de nuvens) |
| Poltronas | estofadas (cenário E0) e rígidas (E0b) | TR com sala vazia; ensaios e formaturas |
| Piso da plateia | cerâmico/granilite sobre laje no solo | arquibancada, absorção |
| Altura do olho sentado | 1,12 m; cabeça +0,12 m | linhas de visão |
| Olho da 1ª fileira | 2,40 m da borda do palco | perfil da arquibancada |

## 5. Pendências que afetam custo ou dimensionamento

Ver aba **Pendências** da planilha `05_Quadro_Tecnico_e_Orcamento_Emir.xlsx` e o roteiro `07_Roteiro_Vistoria.md`. As prioritárias são:
1. Pé-direito e forro.
2. Nível real do piso e estrutura existente.
3. Lotação e situação do PSCIP.
4. Lado externo das portas do fundo.
5. Quadro elétrico.
6. Medição de TR e de ruído de fundo.
7. Estado das poltronas.
8. Equipamentos existentes.

## 6. Normas consultadas
Ver `../agente/normas_tecnicas.md`. Cada item está marcado como verificado na fonte oficial ou "conferir no texto vigente".
