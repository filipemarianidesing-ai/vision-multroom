# Metodologia do Agente Engenheiro de Auditórios — Mariani Áudio e Vídeo

Fluxo padrão para transformar a **planta de qualquer escola** em um pré-projeto de auditório: arquibancada, acústica, som, LED, luz DMX e infraestrutura. Ele foi construído no caso EEEM Emir de Macedo Gomes e está pronto para receber as lições do projeto ABL (ver `licoes_ABL.md`).

## Etapa 1 — Ler a planta e calibrar
1. Abrir o PDF vetorial (PyMuPDF). Extrair os textos de cota (`get_text("words")`) e as linhas longas (`get_drawings()`) para achar as faces internas das paredes.
2. **Calibrar:** escolher uma cadeia de cotas impressa que cruze o ambiente de face a face. Calcular `pt_por_cm` e conferir em uma segunda cadeia, com diferença máxima de 0,5 %.
3. Registrar em `escola.json → calibracao`: as faces internas (x esquerda/direita, y fundo), a borda do palco e o alinhamento do palco.
4. Detectar as fileiras (perfil de pixels escuros no raster a 288 dpi) e o passo; contar poltronas por fileira. Comparar com a lotação do rótulo e **registrar divergências**.
5. Associar cada medida aos pontos de início e fim na prancha (tabela do diagnóstico).
6. **Nunca assumir paredes retas.** Varrer TODAS as linhas da base: tracejadas ("projeção parede sup.", forro, vigas), serrilhadas, chanfros e leques. Extrair os vértices (agrupar por cor/espessura) e desenhar essas linhas em todas as pranchas. Paredes em dente de serra, leque ou curvas mudam o tratamento acústico (faces refletoras × absorventes), a posição de caixas e varas, a altura livre sob faixas rebaixadas e a área de superfície. Símbolos não identificados (ex.: ⊗) vão para a vistoria.
7. **Se a planta for raster ou foto:** pedir PDF vetorial/DWG. Se não houver, calibrar pela maior cota legível e marcar tudo como [H].

## Etapa 2 — Diagnóstico
- Confirmado [P], calculado [C], hipótese [H], vistoria [V]. Nunca misturar.
- Verificar sempre: lotação × P.C.R. (Dec. 5.296: 2 % + 2 %), assentos por fileira × corredores (NT CBMES), saídas, plataforma e acesso ao palco.

## Etapa 3 — Arquibancada (elevação do piso)
Executar `calc_auditorio.py`. Para cada fileira n:

```
h(n+1) = (h(n) + C) · D(n+1) / D(n)      com h = olho − ponto focal
cota_piso(n) = h(n) + P − olho           (monotônica, ≥ 0)
```

- **Ponto focal P:** palco baixo (≤ 0,6 m) → borda do palco; palco alto (≈ 1,0 m) → 0,3–0,5 m acima do piso do palco.
- **C:** 0,06 m com poltronas alternadas; 0,08–0,12 m para visibilidade plena.
- Escolher o perfil pela regra de decisão:
  1. Desnível total ≤ 1,00 m e corredores em rampa (≤ 6,25 % médio, ≤ 8 % por segmento) → **rota acessível até o fundo** (preferido).
  2. Se exceder, corredores com degraus (2 por fileira quando o espelho > 0,18 m), guarda-corpos e P.C.R. nas zonas planas.
- **Sempre verificar:** saídas no nível original, pé-direito livre no fundo (≥ 2,50 m), estrutura existente e revisão do PSCIP.
- Benefício acústico a declarar: menos incidência rasante do som direto, melhor voz natural e caminho de cabos no vazio (com lã mineral).

## Etapa 4 — Acústica
- Volume com pé-direito medido ou em 3 hipóteses. TR de Sabine por banda, sala vazia e ocupada, com a biblioteca de materiais do script.
- Meta: 0,8–1,1 s (500–1 kHz, ocupado) para auditório escolar multiuso com som amplificado; conferir pela DIN 18041 (A2).
- Prioridades: (1) parede do fundo; (2) laterais nos 2/3 posteriores; (3) teto central/posterior; (4) cortinas de palco. O terço frontal e o teto frontal ficam refletores.
- Áreas finais só depois de medir TR e ruído de fundo.

## Etapa 5 — Sonorização
- Principal L/R nas faces laterais da boca de cena. Comparar fonte pontual e coluna direcional pela queda frente→fundo (script). Em sala reverberante, a coluna é o padrão.
- Front-fill se as fileiras 1–3 ficarem abaixo do eixo; delay se STI ou SPL do fundo não atingir a meta (atraso = d/343 + 10 ms).
- Subgraves em via independente, desligados no preset de fala.
- Mesa digital com cenas, DSP com presets bloqueados e interface de cenas para a escola (pode usar o app *Mariani Vision Control* deste repositório).

## Etapa 6 — Imagem e luz
- Altura útil ≥ distância da última fileira ÷ 8; pitch pela 1ª fileira; preferir resolução nativa 1920 × 1080.
- LED × projeção: luz ambiente, custo total, manutenção, estrutura e consumo.
- Luz: frontal a 40–50° com facas (protege a tela), preenchimento, contraluz, cruzada e cenário. DMX com 5 cenas para a escola e mesa completa para o técnico.

## Etapa 7 — Entregáveis (sempre os mesmos nomes)
```
<escola>/
  00_RESUMO.md                 índice, decisões em aberto
  01_Indice_Anexos.md
  02_Diagnostico.md
  03_Pranchas_Pre_Projeto_<escola>.pdf  (ARQ-01, SOM-01, VID-01, LUZ-01, ACU-01, INF-01, ARQ-02 corte, DIA-01..03)
  05_Quadro_Tecnico_e_Orcamento_<escola>.xlsx
  06_Cenarios_SEDU.md
  07_Roteiro_Vistoria.md
  08_Plano_Testes_Entrega.md
  09_Apresentacao_<escola>.html
  base/  (planta original)    dados/ (escola.json, layout.json, scripts, calculos_pre_projeto.md)
```

## Etapa 8 — Regras de apresentação ("projeto que o diretor quer executar")
1. Começar pelo **problema percebido** (não vê o palco, não entende a fala), com foto ou corte que comprove.
2. Cada intervenção responde: **qual problema resolve, por que nesse ponto, como será verificada na entrega.**
3. Mostrar o "antes e depois" com números simples (TR, fileiras que passam a ver o palco, tamanho da imagem).
4. Dois cenários (essencial e completo) e etapas que cabem no calendário escolar.
5. Ser transparente: o que é estimativa, o que depende de vistoria e o que exige o CBMES.
6. Identificar toda imagem como **"Simulação de pré-projeto"**.
