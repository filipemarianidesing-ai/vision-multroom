# 08 — Plano de testes e entrega

**EEEM Emir de Macedo Gomes — Auditório** · Mariani Áudio e Vídeo · Rev. 0

Coluna **Tipo**: **I** = exige instrumento e relatório de medição · **D** = verificado em demonstração com a equipe da escola.
As metas são de pré-projeto e são confirmadas no projeto executivo, depois da simulação.

## 1. Áudio

| # | Teste | Tipo | Método | Critério (meta) |
|---|---|---|---|---|
| A1 | Inteligibilidade (STI) | I | IEC 60268-16, sinal STIPA pelo sistema, 8+ posições cobrindo frente, centro, laterais e fundo, sala vazia (corrigir para ocupada) | STI ≥ 0,60 na média; nenhum ponto < 0,55 |
| A2 | Cobertura | I | Ruído rosa, SPL por banda (1/3 de oitava) nas mesmas posições | ±3 dB em 2 kHz em toda a área de plateia |
| A3 | Nível máximo | I | SPL contínuo no fundo, preset de música | ≥ 95 dB(A) sem distorção ou limitação audível |
| A4 | Margem antes da microfonia | I | Microfone de púlpito e sem fio em posições de uso, ganho até a realimentação | ≥ 6 dB acima do ganho de operação |
| A5 | Alinhamento do delay (se houver) | I | Resposta ao impulso na zona de sobreposição | Chegada do PA antes da caixa de delay (precedência) |
| A6 | Ruído do sistema | I | Sistema ligado e sem sinal, a 1 m das caixas | Inaudível no palco e na plateia |
| A7 | Todas as entradas e saídas | D | Teste canal a canal (mic, DI, notebook, player) | 100 % funcionais e identificadas |
| A8 | Microfones sem fio | D | Caminhar por toda a plateia e pelo palco | Sem perdas de sinal |
| A9 | Presets | D | A equipe chama PALESTRA, FORMATURA, MÚSICA e VÍDEO | Cada preset muda as vias corretas; subgrave desligado na palestra |

## 2. Acústica

| # | Teste | Tipo | Método | Critério |
|---|---|---|---|---|
| R1 | Tempo de reverberação | I | ISO 3382-2, antes e depois do tratamento | 0,8–1,1 s (500–1 kHz, ocupado, corrigido) |
| R2 | Ruído de fundo | I | NBR 10152:2017, climatização ligada | Dentro do valor de referência da norma para auditórios (conferir a tabela da edição vigente) |
| R3 | Eco de retorno | I/D | Impulso no palco; escuta e resposta ao impulso | Sem eco discreto vindo da parede do fundo |
| R4 | Fixações e reação ao fogo | D | Inspeção e certificados | Laudos do material conforme o CBMES |

## 3. Imagem

| # | Teste | Tipo | Método | Critério |
|---|---|---|---|---|
| V1 | Legibilidade | D | Slide-padrão com texto de 28/36/48 pt, lido da última fileira e das duas laterais extremas | Texto de 28 pt legível do fundo |
| V2 | Uniformidade e pixels | I/D | Telas de cor sólida; luminancímetro (se LED) | Sem pixels mortos; uniformidade conforme fabricante |
| V3 | Troca de fonte | D | Púlpito → FOH → auxiliar | < 3 s, com áudio acompanhando |
| V4 | Cintilação em câmera | D | Filmar o LED com celular | Sem faixas visíveis (refresh ≥ 3840 Hz) |
| V5 | Brilho por cena | D | Chamar cada cena | Brilho confortável sem ofuscar |

## 4. Iluminação

| # | Teste | Tipo | Método | Critério |
|---|---|---|---|---|
| L1 | Cenas | D | A equipe aciona as 5 cenas | Todas funcionam pela botoeira/tablet |
| L2 | Luz no rosto | I | Luxímetro vertical na altura do rosto, na área do púlpito e no centro do palco | ≥ 500 lx (meta de pré-projeto, ajustável) |
| L3 | Luz na tela | D | Cena de palestra com o LED/projeção ligado | Sem luz frontal atingindo a tela |
| L4 | Ofuscamento | D | Sentar nas fileiras 1, 8 e 15 | Nenhum refletor no campo de visão direto |
| L5 | Emergência | D | Desligar a energia normal | Iluminação de emergência independente do DMX |
| L6 | Segurança | D | Inspeção | Cabo de aço em cada refletor; ART das fixações |

## 5. Arquitetura (se o cenário completo for executado)

| # | Teste | Tipo | Critério |
|---|---|---|---|
| Q1 | Cotas dos patamares | I (nível a laser) | ±1 cm do perfil executivo |
| Q2 | Linhas de visão | D | Fotos na altura do olho sentado nas fileiras 4, 8, 12 e 15 mostram o apresentador a partir de 0,40 m acima do piso do palco |
| Q3 | Rampas e corrimãos | I | Inclinações por segmento e alturas de corrimão conforme NBR 9050 |
| Q4 | Saídas | D | Conforme PSCIP revisado e vistoria do CBMES |
| Q5 | P.C.R. | D | 6 espaços com visibilidade verificada |

## 6. Operação e entrega
- **Treinamento:** 2 sessões com a equipe da escola, mais um evento simulado operado pela escola sem ajuda (teste D).
- **Guia rápido** plastificado no rack e na FOH: 1 página por cena.
- **Documentação as built:** pranchas, diagrama de ligações, lista de cabos com identificação, senhas e backups dos presets (DSP, mesa, DMX), manuais e garantias.
- **Relatório de comissionamento** com todas as medições I, antes e depois.
- **Termo de recebimento** assinado pela direção.
