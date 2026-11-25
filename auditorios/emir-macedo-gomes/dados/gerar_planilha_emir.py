#!/usr/bin/env python3
"""Quadro técnico item a item + orçamento preliminar (2 cenários) — EEEM Emir de Macedo Gomes.
Saída: ../05_Quadro_Tecnico_e_Orcamento_Emir.xlsx
Preços ficam EM ABERTO até haver cotação (registrar fonte e data em cada linha)."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "05_Quadro_Tecnico_e_Orcamento_Emir.xlsx")
AL = "a levantar"

# cod, disc, item, especificação mínima, problema que resolve, local/prancha, por que nesse ponto,
# un, qtd_ess, qtd_comp, critério, dependências, teste de aceitação, obra civil, categoria orçamento
I = [
 # ARQUITETURA
 ("ARQ-01","Arquitetura","Arquibancada (elevação do piso) — perfil B","Estrutura metálica leve ou alvenaria + laje; 12 patamares de 1,00 m (F4–F15) + patamar de fundo; acabamento antiderrapante; lã mineral no vazio","Plateia não vê o apresentador da cintura para baixo a partir da 4ª fileira; som direto rasante sobre cabeças","ARQ-01/ARQ-02 — bloco central F4–F15 e fundo","Elevação calculada fileira a fileira (C ≈ 0,06 m, foco 0,40 m acima do palco)","m²",0,170,"2 blocos de 6,26 m × 12 m (F4–F15) + corredor central de 1,50 m em rampa + rampas laterais de 2,29 m; corredor do fundo permanece no piso existente — confirmar após levantamento a laser","Vistoria do piso/laje existente; estrutural; revisão PSCIP (layout)","Conferência de cotas (±1 cm); verificação de C com perfil real; prova de carga/inspeção estrutural","Sim","Infraestrutura"),
 ("ARQ-02","Arquitetura","Rampas laterais (2,29 m) e corredor central (1,50 m)","Rampas laterais de 2,29 m com corrimão duplo; corredor central de 1,50 m em rampa com passadeira e LED nas bordas (entrada da formatura); largura, inclinação ≤ 8 %, piso antiderrapante, corrimão duplo 0,70/0,92 m nos dois lados, sinalização tátil","Rota acessível até todos os níveis e saídas; entrada dos formandos pelo corredor central","ARQ-01 — corredores laterais","Mantém os corredores existentes como rota de fuga e acesso","m",0,39,"2 × 12 m (laterais) + 15 m (central)","NBR 9050 (rampas/corrimãos); NT 10 CBMES","Medição de inclinação por segmento; teste de corrimão","Sim","Infraestrutura"),
 ("ARQ-03","Arquitetura","Guarda-corpos e bordas de patamar","Guarda-corpo onde houver desnível livre; altura e carga conforme NBR 14718","Proteção contra queda na borda da fileira 15 e no topo das rampas","ARQ-01 — borda F15 (vidro 1,10 m) e topo das rampas","Desnível de 0,62 m entre a F15 e o corredor do fundo","m",0,AL,"Definir no executivo","Estrutural; PSCIP","Inspeção visual e ensaio de carga amostral","Sim","Infraestrutura"),
 ("ARQ-04","Arquitetura","Escadas do topo ao corredor do fundo (3 × 4 degraus)","2 escadas laterais de 1,60 m + 1 escada central de 1,50 m (entrada da formatura), 4 degraus com espelho 15,5 cm e piso 30 cm, corrimão inox, perfil antiderrapante e LED; corredor do fundo (1,98 m) mantido em +0,20 ligando as 2 portas existentes","Mantém o acesso e a rota de fuga pelas duas portas do fundo","ARQ-01 — fim dos corredores laterais, junto às portas dos cantos do fundo","As portas ficam no nível atual; a escada liga a fileira 15 (+0,82) ao corredor","un",0,3,"Desnível 0,62 m; Blondel 2e + p = 0,61 m","Revisão do PSCIP (layout); NT 10 CBMES (escadas)","Conferência de espelhos/pisos; corrimão; rota de fuga desobstruída","Sim","Infraestrutura"),
 ("ARQ-05","Arquitetura","Espaços P.C.R. + assentos P.M.R./P.O.","6 espaços P.C.R. 0,80 × 1,20 m com assento de acompanhante; 6 assentos reservados sinalizados","Desenho indica 2 espaços; Dec. 5.296/2004 art. 23 pede 2 % + 2 %","ARQ-01 — frente, meio (F11) e patamar","Distribuídos em locais diversos com boa visibilidade","un",6,6,"2 % de 270 = 5,4 → 6 (cada grupo)","Lotação aprovada no PSCIP; layout final de poltronas","Verificação dimensional e de visibilidade a partir de cada espaço","Parcial","Materiais"),
 ("ARQ-06","Arquitetura","Poltronas atuais — retirada, revisão e reinstalação nos patamares","Retirar as poltronas existentes, revisar fixação e estofado e reinstalar nos novos patamares (2 blocos de 9 por fileira), com nova numeração","Reaproveita o que a escola já tem; obrigatório se não houver troca, pois a arquibancada exige retirar as poltronas","ARQ-01 — plateia","Mantém a capacidade com o menor custo","un",257,257,"257 poltronas no layout com corredor central; conferir estado e modelo na vistoria","Vistoria (modelo, fixação, estado); arquibancada","Inspeção de fixação e numeração; passagem livre entre fileiras conforme NT CBMES","Não","Instalação"),
 ("ARQ-06B","Arquitetura","OPCIONAL — troca por poltronas estofadas com assento rebatível","Poltrona estofada, encosto alto, assento rebatível (fecha sozinho), braço compartilhado; cor e tecido a escolher pela escola","Mais passagem entre fileiras, conforto e acústica estável com a sala vazia; depende de orçamento (pedido da direção)","ARQ-01 — plateia","Substitui ARQ-06 se aprovada; pode ficar para uma etapa posterior","un",0,257,"257 poltronas; 3 cotações com fonte e data","Decisão da direção / verba SEDU","Amostra aprovada pela direção; inspeção de fixação e rebatimento","Não","Equipamentos"),
 # SOM
 ("SOM-01","Som","Sistema principal Line Bonsai — 2 colunas suspensas","2 colunas de 8 caixas mini line array Line Bonsai, com bumper, cabos de aço e segurança; inclinações de pré-ajuste 10°–32° (10/11/13/15/18/21/26/32°)","Fala clara da 1ª à última fileira, com cobertura por faixas e menos reflexão nas paredes","SOM-01 — suspensas sobre as laterais da boca de cena, x = ±5,2 m, topo ≈ 5,0 m, viradas 18° para o centro","Posição L/R mantém a imagem no palco; altura cobre as fileiras por cima das cabeças","cx",16,16,"8 caixas por coluna; ângulos finais no software do fabricante com a ficha da Line Bonsai","Pé-direito; pontos de fixação validados pelo estrutural; ficha técnica e peso do conjunto","Cobertura ±3 dB (2 kHz); STI ≥ 0,60 (meta); inspeção da suspensão","Não","Equipamentos"),
 ("SOM-02","Som","Subwoofers 18\" (SUB-1/SUB-2)","2 subwoofers de 18\" no chão; via independente no DSP","Extensão de graves para música, vídeo e formaturas","SOM-01 — chão da plateia junto à frente do palco, x = ±3,6 m","Perto do palco, fora das rotas; acoplamento com o piso","un",2,2,"Desligáveis no preset de palestra","Rota de circulação da 1ª fileira","Resposta 40–100 Hz no centro da plateia; preset de fala com sub desligado","Não","Equipamentos"),
 ("SOM-03","Som","Front-fills","Caixas compactas de baixa altura na borda do palco","Cobrir F1–F3 se ficarem fora do alcance do PA","SOM-01 — borda do palco","Fileiras 1–3 ficam a 2–4 m e abaixo do eixo das colunas","un",0,AL,"Só se a simulação mostrar queda > 6 dB nas F1–F3","Simulação","Medição de SPL nas F1–F3","Não","Equipamentos"),
 ("SOM-04","Som","Reforços com delay (DLY-1/DLY-2)","Caixas compactas na face reta da parede superior (junto ao ⊗), ≈ 11 m da borda; atraso inicial ≈ 44 ms","Fundo com pouco nível ou baixa inteligibilidade","SOM-01 — face reta do dente de serra, x = ±7,4 m","Ponto alto fora da faixa rebaixada; 2/3 da plateia","un",0,AL,"Só se STI no fundo < meta com o PA","Simulação; medição pós-instalação","Medição de alinhamento (resposta ao impulso) e STI no fundo","Não","Equipamentos"),
 ("SOM-05","Som","Monitores de palco","Retornos de chão coaxiais 10\"–12\"","Apresentadores e músicos se escutam","SOM-01 — boca de cena","Ângulo para o palco, fora do eixo dos microfones","un",2,4,"Ess.: 2 (falas/coral); Comp.: 4 (música)","Mesa com vias auxiliares","Margem antes da microfonia ≥ 6 dB com retorno ligado","Não","Equipamentos"),
 ("SOM-06","Som","Mesa de som digital","≥ 16 entradas mic + estéreo, cenas, controle por tablet, gravação USB; reserva ≥ 25 %","Mistura e distribuição de microfones, instrumentos e computador","SOM-01 — FOH","Operação com escuta representativa da plateia","un",1,1,"Ess.: 16 entradas; Comp.: 24–32 entradas com stagebox","Roteiro de eventos da escola","Teste de todas as entradas/saídas; recall de cenas","Não","Equipamentos"),
 ("SOM-07","Som","Stagebox digital","16 entradas / 8 saídas, link por cabo de rede","Elimina multicabo analógico e ruído","SOM-01 — CP1/CP2 ou rack","Um cabo de rede pelo duto da arquibancada","un",0,1,"Comp.: obrigatório; Ess.: entradas no rack","Duto FOH-palco","Teste de canais e latência","Não","Equipamentos"),
 ("SOM-08","Som","DSP / matriz","Processador com EQ, delay, limitador por via, presets e controle por GPIO/rede","Ajustes separados por via + presets simples para a escola","SOM-01 — rack","Protege as caixas e fixa o ajuste do comissionamento","un",1,1,"Vias: PA, sub, FF, delay, monitores, gravação","Equipamentos definidos","Verificação de presets e bloqueio de parâmetros","Não","Equipamentos"),
 ("SOM-09","Som","Amplificação","Multicanal classe D com folga ≥ 3 dB sobre potência programa das caixas (se passivas)","Alimenta as caixas passivas","SOM-01 — rack","Rack ventilado, perto do palco","un",1,AL,"Pela impedância/potência das caixas escolhidas","Escolha das caixas","Medição de tensão de saída e temperatura em uso","Não","Equipamentos"),
 ("SOM-10","Som","Microfone de púlpito","Gooseneck cardioide/supercardioide com base e chave","Falas institucionais","SOM-01 — púlpito","Ponto fixo de discurso","un",1,1,"1 por púlpito","Púlpito com passagem de cabo","Inteligibilidade e margem antes da microfonia","Não","Equipamentos"),
 ("SOM-11","Som","Microfones sem fio","UHF digital, faixa legal Anatel, 2 bastão + 2 headset (ess.)","Apresentadores e perguntas do público","SOM-01 — antenas na boca de cena","Antenas com linha de visada para palco e plateia","canal",2,4,"Ess.: 2 canais; Comp.: 4 canais","Coordenação de frequências","Teste de alcance em toda a plateia sem dropout","Não","Equipamentos"),
 ("SOM-12","Som","Microfones com fio + pedestais","Dinâmicos de voz/instrumento","Contingência e palco","SOM-01 — CP1/CP2","Reserva em caso de falha do sem fio","un",4,6,"","—","Teste de todos os canais","Não","Equipamentos"),
 ("SOM-13","Som","DIs","DI passivo/ativo","Instrumentos e fontes de linha","SOM-01 — palco","—","un",2,4,"","—","Teste de ruído e nível","Não","Equipamentos"),
 ("SOM-14","Som","Rack 19\"","Rack fechado com ventilação forçada, régua com proteção, porta com chave, acesso frontal/traseiro","Organiza processamento e conexões","SOM-01 — sala de apoio esquerda","Junto ao palco e ao QD-AV","un",1,1,"Altura útil a definir pelos equipamentos + 30 % reserva","Ventilação da sala de apoio","Temperatura interna em uso; identificação de cabos/portas","Não","Equipamentos"),
 ("SOM-15","Som","Interface de cenas (operação da escola)","Painel/tablet com 5–6 botões: LIGAR · PALESTRA · FORMATURA · MÚSICA · VÍDEO · DESLIGAR (pode integrar o app Mariani Vision Control)","Equipe da escola opera eventos do dia a dia sem técnico","SOM-01 — FOH e sala de apoio","Dois pontos de acionamento","un",1,1,"","DSP/mesa com controle por rede","Equipe aciona cada cena em demonstração","Não","Configuração"),
 # VÍDEO
 ("VID-01","Vídeo","Painel LED indoor","5,00 × 2,81 m (16:9), pitch 2,6–2,9 mm, brilho regulável 600–1000 nits, refresh ≥ 3840 Hz, manutenção frontal","Conteúdo visível em toda a plateia, com luz acesa","VID-01 — palco, 3,0 m atrás da borda","Mantém área de apresentação à frente; tamanho pela regra 1/7 da última fileira","m²",0,14.05,"Altura ≥ 2,42 m (1/8 de 19,4 m)","Estrutura; pé-direito do palco; circuito elétrico","Legibilidade de texto padrão do fundo e laterais; uniformidade","Não","Equipamentos"),
 ("VID-02","Vídeo","Estrutura do painel LED","Estrutura de piso (ground stack) ou fixação em parede/estrutura com laudo","Suporte seguro do painel (~420 kg + estrutura)","VID-01","—","vb",0,1,"","Estrutural","Inspeção e ART","Parcial","Infraestrutura"),
 ("VID-03","Vídeo","Projeção laser + tela (alternativa / essencial)","Projetor laser ≥ 9.000 lm, tela 16:9 ≈ 5,0 m de base, motorizada ou fixa","Conteúdo visível com menor investimento","VID-01 — mesma posição","Exige controle da luz das janelas","un",1,0,"Luminância ≥ 200 cd/m² na tela","Controle de luz ambiente; ponto de fixação","Contraste e legibilidade com luz de palestra","Não","Equipamentos"),
 ("VID-04","Vídeo","Seletor/switcher de vídeo + extensores HDBaseT","Matriz com escalonamento, 4–6 entradas, extração de áudio","Seleção simples de fonte (púlpito, FOH, auxiliar, câmera)","VID-01 — rack/FOH","—","un",1,1,"","—","Troca de fonte < 3 s; sem perda de áudio","Não","Equipamentos"),
 ("VID-05","Vídeo","Processadora do LED","Processadora compatível com o painel, entrada 1080p","Escalonamento e brilho por cena","VID-01 — rack","—","un",0,1,"","Painel escolhido","Mapeamento sem pixel morto; brilho por cena","Não","Equipamentos"),
 ("VID-06","Vídeo","Monitor de retorno (confidence)","Monitor 43–55\" no piso do palco","Apresentador vê o slide sem virar de costas","VID-01 — borda do palco","—","un",1,1,"","—","Visível do púlpito","Não","Equipamentos"),
 ("VID-07","Vídeo","Câmera PTZ + captura (completo)","Câmera PTZ com saída IP/SDI e captura para transmissão/gravação","Gravar e transmitir formaturas e eventos","VID-01 — fundo","—","un",0,1,"","Rede","Imagem estável com cenas de luz","Não","Equipamentos"),
 # LUZ
 ("LUZ-01","Iluminação","Refletores elipsoidais LED (frontal)","Elipsoidal LED 150–250 W, branco variável, IRC ≥ 90, facas","Visibilidade de quem está no palco sem atingir a tela","LUZ-01 — vara FOH-1","40–50° de elevação sobre a área frontal","un",4,6,"Área de 9 × 3 m em 3 zonas","Pé-direito; fixação","Iluminância vertical no rosto ≥ ~500 lx (meta pré-projeto); sem luz na tela","Não","Equipamentos"),
 ("LUZ-02","Iluminação","Wash LED (preenchimento)","Wash/PAR LED RGBW ou branco variável","Reduz sombras e cria base de cor","LUZ-01 — vara PALCO-1 (8,2 m, dentro do leque do palco)","Sobre a área à frente do LED","un",4,6,"","—","Uniformidade visual na área de apresentação","Não","Equipamentos"),
 ("LUZ-03","Iluminação","Contraluz / cenário","Wash LED + moving heads (completo)","Destaca pessoas do fundo; cenas para teatro, música e formatura","LUZ-01 — vara PALCO-2 / torres","Atrás da área de atuação","un",2,8,"Ess.: 2 wash; Comp.: 4 wash + 4 moving","Pé-direito acima do LED","Cenas programadas","Não","Equipamentos"),
 ("LUZ-04","Iluminação","Varas, torres, garras e cabos de segurança","Barras de alumínio, torres laterais, garras e cabo de aço por refletor","Fixação segura e reposicionável","LUZ-01","—","vb",1,1,"","Estrutural (validação de pontos)","Inspeção de fixações; ART","Parcial","Materiais"),
 ("LUZ-05","Iluminação","Controle DMX","Ess.: interface com cenas gravadas + botoeira; Comp.: mesa DMX ≥ 2 universos + node Art-Net","Cenas simples para a escola e controle completo para o técnico","LUZ-01 — FOH / rack","—","un",1,1,"","Splitter e rede","Acionamento das 5 cenas pela equipe","Não","Equipamentos"),
 ("LUZ-06","Iluminação","Splitter DMX e cabeamento","Splitter óptico isolado, cabos DMX 5 pinos","Distribuição robusta por vara/torre","LUZ-01 — rack","—","vb",1,1,"","—","Teste de endereçamento","Não","Materiais"),
 ("LUZ-07","Iluminação","Controle da luz de plateia","Dimmer/relé DMX para circuitos existentes (ou troca por luminárias dimerizáveis)","Escurecer a plateia por cena (vídeo, apresentação)","LUZ-01 — QD existente","—","vb",1,1,"","Levantamento dos circuitos e luminárias existentes","Cenas de plateia funcionando; emergência independente","Não","Equipamentos"),
 # ACÚSTICA
 ("ACU-01","Acústica","Painéis absorventes de parede","Lã mineral/fibra 50 mm + tecido, α ≥ 0,90 de 500 a 4 kHz (ISO 354), classe de reação ao fogo exigida pelo CBMES","Reduz reverberação e reflexões laterais/fundo que prejudicam a fala","ACU-01 — parede inferior (1,2 m → forro da faixa), faces curtas do dente de serra e todas as faces da metade posterior; parede do fundo","Faces longas da metade frontal do dente de serra ficam refletoras (já distribuem a voz)","m²",120,120,"TR alvo 0,8–1,1 s (500–1k, ocupado) — área revisada após medição","Medição de TR; pé-direito; laudo de reação ao fogo","Medição de TR (ISO 3382-2) antes/depois","Não","Materiais"),
 ("ACU-02","Acústica","Nuvens / forro acústico","Painéis suspensos ou forro mineral NRC ≥ 0,70 no terço central/posterior","Controla reverberação e reflexões do teto","ACU-01 — teto y 6–17 m","Teto frontal fica refletor","m²",0,150,"Depende do pé-direito e do forro existente","Compatibilizar com luminárias, detectores, climatização e varas","Medição de TR; inspeção de fixação","Parcial","Materiais"),
 ("ACU-03","Acústica","Difusor no fundo (completo)","Difusor de madeira (QRD/policilíndrico) ≈ 4 × 2,5 m no centro da parede do fundo","Evita eco de retorno ao palco mantendo energia útil","ACU-01 — parede do fundo","Parede paralela ao palco a ≈ 18,7 m","m²",0,10,"","Medição/ensaio de eco","Teste de palmas/impulso no palco","Não","Materiais"),
 ("ACU-04","Acústica","Cortinas de palco","Fundo (≈ 6 m), pernas acompanhando o leque do palco, bambolinas e boca de cena em veludo pregueado (≥ 50 % de franzido), com trilhos; antichama. Verificar se o serrilhado da base são cortinas existentes","Acabamento cênico, controle de luz e absorção no palco","ACU-01 — palco","Caixa cênica hoje sem tratamento (a confirmar)","m²",60,90,"Ess.: fundo + boca; Comp.: + pernas/bambolinas","Estrutura para trilhos; pé-direito","Funcionamento dos trilhos; certificado antichama","Parcial","Materiais"),
 ("ACU-05","Acústica","Vedação/isolamento pontual","Vedação de portas (soleira/borracha), janelas ou dutos onde a medição indicar","Ruído externo e de climatização","ACU-01 — janelas/portas","Só onde houver transmissão relevante","vb",AL,AL,"Medição de ruído de fundo (NBR 10152:2017)","Medição","Ruído de fundo após intervenção","Parcial","Infraestrutura"),
 # INFRA
 ("INF-01","Infraestrutura","Quadro QD-AV","Quadro dedicado com DR, DPS, disjuntores por sistema (áudio, vídeo/LED, luz), barramento de terra","Alimentação segura e sem ruído para AV","INF-01 — sala de apoio esquerda","Junto ao rack","un",1,1,"Demanda preliminar 15–20 kVA (completo)","Capacidade do quadro geral/entrada","Medição de tensão, terra e atuação do DR (NBR 5410)","Sim","Infraestrutura"),
 ("INF-02","Infraestrutura","Eletrodutos/eletrocalhas e caixas","Duto FOH↔rack (2 × Ø2\"), caixas de piso no palco CP1–CP4, rotas para caixas, LED e varas","Caminho protegido para sinal e energia","INF-01","Vazio da arquibancada como plenum","vb",1,1,"","Arquibancada (completo); rota aparente no essencial","Inspeção; passagem de guia; identificação","Sim","Infraestrutura"),
 ("INF-03","Infraestrutura","Cabeamento de sinal","Cabos de caixa acústica, rede Cat6/fibra, HDMI/HDBaseT, DMX, microfone","Interligação dos sistemas","INF-01","—","vb",1,1,"","Layout final","Certificação de rede; teste de continuidade","Não","Materiais"),
 ("INF-04","Infraestrutura","Pontos de energia no palco e FOH","Tomadas dedicadas em CP1–CP4, FOH (2), varas e LED","Evita extensões e quedas de energia","INF-01","—","pt",8,14,"","QD-AV","Teste de tensão e polaridade","Sim","Infraestrutura"),
 # SERVIÇOS
 ("SRV-01","Serviços","Levantamento técnico (vistoria + medições)","Pé-direito, nível a laser, TR, ruído de fundo, elétrica, fotos","Fecha quantidades e custo","—","—","vb",1,1,"Roteiro de vistoria (doc. 07)","Acesso à escola","Relatório de vistoria","Não","Configuração"),
 ("SRV-02","Serviços","Simulação acústica/eletroacústica","Modelo 3D com materiais medidos; cobertura, SPL, STI","Define modelos, mira, delays e áreas de tratamento","—","—","vb",1,1,"","Vistoria","Relatório de simulação","Não","Configuração"),
 ("SRV-03","Serviços","Instalação AV","Montagem, fixação, cabeamento e identificação","—","—","—","vb",1,1,"","Obras civis concluídas","Checklist de instalação","Não","Instalação"),
 ("SRV-04","Serviços","Configuração e programação","DSP, mesa, cenas, switcher, LED, DMX","—","—","—","vb",1,1,"","Instalação","Cenas e presets documentados","Não","Configuração"),
 ("SRV-05","Serviços","Treinamento da equipe da escola","2 sessões + guia rápido impresso por cena","Operação do dia a dia sem técnico","—","—","h",4,8,"","Comissionamento","Equipe opera evento simulado sozinha","Não","Treinamento"),
 ("SRV-06","Serviços","Comissionamento e medições finais","Medição de TR, STI, cobertura, ruído, margem antes da microfonia; relatório as built","Prova de desempenho na entrega","—","—","vb",1,1,"Plano de testes (doc. 08)","Instalação e configuração","Relatório de comissionamento aprovado","Não","Comissionamento"),
 ("SRV-07","Serviços","Projeto executivo e ART","Pranchas executivas, memorial e ARTs (elétrica, estrutura, AV)","Documentação para a SEDU e para obra","—","—","vb",1,1,"","Vistoria e simulação","Aprovação da fiscalização","Não","Configuração"),
]

thin = Side(style="thin", color="BBBBBB")
BRD = Border(left=thin, right=thin, top=thin, bottom=thin)
HDR = PatternFill("solid", fgColor="1F2A44")
DISC = {"Arquitetura": "EDE4FB", "Som": "DFF1FB", "Vídeo": "DDF5EC", "Iluminação": "FDE9DC", "Acústica": "FBE2EE", "Infraestrutura": "E9ECF1", "Serviços": "F4F4F4"}

wb = Workbook()
ws = wb.active
ws.title = "Quadro técnico"
cols = ["Código", "Disciplina", "Item", "Especificação mínima (pré-projeto)", "Problema que resolve", "Local / prancha", "Por que nesse ponto",
        "Unid.", "Qtd. Essencial", "Qtd. Completo", "Critério de dimensionamento", "Dependências", "Teste de aceitação", "Exige obra civil?"]
widths = [9, 12, 30, 48, 38, 30, 34, 7, 10, 10, 34, 34, 36, 10]
ws.append(["QUADRO TÉCNICO ITEM A ITEM — EEEM Emir de Macedo Gomes (Linhares/ES) — Pré-projeto Mariani Áudio e Vídeo — Rev. 0"])
ws.append(["Quantidades preliminares. “a levantar” = sem base suficiente; definir após vistoria, medições e simulação."])
ws.append(cols)
for c in range(1, len(cols) + 1):
    cell = ws.cell(row=3, column=c)
    cell.font = Font(bold=True, color="FFFFFF"); cell.fill = HDR
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.column_dimensions[get_column_letter(c)].width = widths[c - 1]
ws["A1"].font = Font(bold=True, size=13)
ws["A2"].font = Font(italic=True, color="666666")
for it in I:
    row = list(it[:14])
    ws.append(row)
    r = ws.max_row
    for c in range(1, 15):
        cell = ws.cell(row=r, column=c)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = BRD
        cell.fill = PatternFill("solid", fgColor=DISC[it[1]])
ws.freeze_panes = "D4"
ws.auto_filter.ref = f"A3:N{ws.max_row}"

# ----- Orçamento
CATS = ["Equipamentos", "Materiais", "Infraestrutura", "Instalação", "Configuração", "Treinamento", "Comissionamento"]
wo = wb.create_sheet("Orçamento")
hdr = ["Código", "Item", "Categoria", "Unid.", "Qtd. Essencial", "Qtd. Completo", "Preço unitário (R$)", "Fonte do preço (fornecedor/cotação/tabela)", "Data do preço",
       "Subtotal Essencial (R$)", "Subtotal Completo (R$)", "Observação"]
wo.append(["ORÇAMENTO PRELIMINAR — campos de preço EM ABERTO até cotação. Registrar fonte e data de cada preço."])
wo.append(["Itens com quantidade “a levantar” não entram na soma até serem quantificados. Instalação/configuração/treinamento/comissionamento podem ser lançados como itens próprios abaixo."])
wo.append(hdr)
for c, w in enumerate([9, 40, 16, 7, 10, 10, 16, 36, 13, 18, 18, 30], 1):
    wo.column_dimensions[get_column_letter(c)].width = w
    cell = wo.cell(row=3, column=c)
    cell.font = Font(bold=True, color="FFFFFF"); cell.fill = HDR; cell.alignment = Alignment(wrap_text=True, horizontal="center")
wo["A1"].font = Font(bold=True, size=13)
wo["A2"].font = Font(italic=True, color="666666")
dv = DataValidation(type="list", formula1='"' + ",".join(CATS) + '"', allow_blank=False)
wo.add_data_validation(dv)
first = 4
for it in I:
    qe = it[8] if isinstance(it[8], (int, float)) else None
    qc = it[9] if isinstance(it[9], (int, float)) else None
    wo.append([it[0], it[2], it[14], it[7], qe if qe is not None else it[8], qc if qc is not None else it[9], None, "", "",
               None, None, "" if (qe is not None and qc is not None) else "quantidade a levantar"])
    r = wo.max_row
    wo.cell(row=r, column=10).value = f'=IF(AND(ISNUMBER(E{r}),ISNUMBER(G{r})),E{r}*G{r},0)'
    wo.cell(row=r, column=11).value = f'=IF(AND(ISNUMBER(F{r}),ISNUMBER(G{r})),F{r}*G{r},0)'
    dv.add(f"C{r}")
    for c in range(1, 13):
        cell = wo.cell(row=r, column=c); cell.border = BRD; cell.alignment = Alignment(wrap_text=True, vertical="top")
    for c in (7, 10, 11):
        wo.cell(row=r, column=c).number_format = '"R$" #,##0.00'
    wo.cell(row=r, column=7).fill = PatternFill("solid", fgColor="FFF6CC")
    wo.cell(row=r, column=8).fill = PatternFill("solid", fgColor="FFF6CC")
    wo.cell(row=r, column=9).fill = PatternFill("solid", fgColor="FFF6CC")
last = wo.max_row
for k in range(6):
    wo.append(["", "(linha livre)", "", "", None, None, None, "", "", None, None, ""])
    r = wo.max_row
    wo.cell(row=r, column=10).value = f'=IF(AND(ISNUMBER(E{r}),ISNUMBER(G{r})),E{r}*G{r},0)'
    wo.cell(row=r, column=11).value = f'=IF(AND(ISNUMBER(F{r}),ISNUMBER(G{r})),F{r}*G{r},0)'
    dv.add(f"C{r}")
last = wo.max_row
wo.freeze_panes = "C4"

# ----- Resumo
wr = wb.create_sheet("Resumo por cenário", 0)
wr.append(["RESUMO DO ORÇAMENTO PRELIMINAR — EEEM Emir de Macedo Gomes"])
wr["A1"].font = Font(bold=True, size=13)
wr.append(["Valores calculados a partir da aba Orçamento. Enquanto não houver cotação, os totais ficam em R$ 0,00."])
wr.append([])
wr.append(["Categoria", "Cenário ESSENCIAL (R$)", "Cenário COMPLETO (R$)", "Itens sem preço (ess./comp.)"])
for c in range(1, 5):
    cell = wr.cell(row=4, column=c); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = HDR
for cat in CATS:
    r = wr.max_row + 1
    wr.append([cat,
               f"=SUMIF(Orçamento!$C${first}:$C${last},A{r},Orçamento!$J${first}:$J${last})",
               f"=SUMIF(Orçamento!$C${first}:$C${last},A{r},Orçamento!$K${first}:$K${last})",
               f'=COUNTIFS(Orçamento!$C${first}:$C${last},A{r},Orçamento!$G${first}:$G${last},"")'])
r = wr.max_row + 1
wr.append(["TOTAL", f"=SUM(B5:B{r-1})", f"=SUM(C5:C{r-1})", ""])
for row in wr.iter_rows(min_row=5, max_row=r, min_col=2, max_col=3):
    for cell in row:
        cell.number_format = '"R$" #,##0.00'
wr.cell(row=r, column=1).font = Font(bold=True)
for c, w in zip("ABCD", [22, 26, 26, 26]):
    wr.column_dimensions[c].width = w
wr.append([])
wr.append(["Cenário ESSENCIAL: clareza da fala + operação simples (som principal, microfones, DSP com cenas, tratamento acústico de paredes, cortinas, projeção, luz frontal básica, P.C.R.). Sem obra civil pesada."])
wr.append(["Cenário COMPLETO: Essencial + arquibancada (obra civil e revisão do PSCIP), painel LED, subgraves, stagebox, luz cênica completa, nuvens/difusor, câmera."])

# ----- Pendências
wp = wb.create_sheet("Pendências")
wp.append(["Pendência", "Afeta", "Como levantar", "Responsável", "Status"])
for c in range(1, 6):
    cell = wp.cell(row=1, column=c); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = HDR
P = [
 ("Paredes superiores em dente de serra e leque do palco: altura de início, forro/viga da faixa sobre os corredores, material, natureza dos ⊗", "Rampas (altura livre), acústica, delays, varas, cortinas", "Trena laser, fotos de cada face, inspeção", "Mariani"),
 ("Pé-direito da plateia e do palco (e forma do forro/cobertura)", "Volume/TR, LED, varas de luz, altura das caixas, arquibancada", "Trena laser em 9 pontos (grade 3×3) + palco; foto do forro", "Mariani"),
 ("Nível real do piso da plateia e do palco", "Perfil da arquibancada, rampas", "Nível a laser em grade 2 × 2 m; cotas da soleira das portas", "Mariani"),
 ("Estrutura do piso existente (laje sobre solo? vazio?)", "Arquibancada, cargas", "Inspeção/sondagem; consulta a projeto estrutural da SEDU", "Estrutural"),
 ("Lotação aprovada no PSCIP e situação do processo no CBMES", "Saídas, P.C.R., layout", "Solicitar PSCIP aprovado e AVCB à SEDU", "SEDU/Escola"),
 ("Situação externa das portas do fundo (níveis, espaço)", "Compatibilização de saídas", "Fotos e cotas externas", "Mariani"),
 ("Estado e modelo das poltronas (estofadas? fixação?)", "Acústica (TR vazio), reaproveitamento", "Fotos, medidas, amostra", "Mariani"),
 ("Materiais existentes (paredes, forro, piso, janelas, cortinas)", "TR e áreas de tratamento", "Fotos + inventário por superfície", "Mariani"),
 ("TR e ruído de fundo medidos", "Especificação acústica final", "ISO 3382-2 (fonte impulsiva/sweep, 6+ posições); NBR 10152 (LAeq com climatização ligada/desligada)", "Mariani"),
 ("Quadro elétrico: capacidade, fases, disponibilidade de circuitos", "QD-AV, LED, luz", "Levantamento do QGBT e da entrada de energia", "Eletricista"),
 ("Equipamentos AV existentes", "Reaproveitamento e custo", "Inventário com fotos e teste", "Mariani"),
 ("Climatização (tipo, posição, ruído)", "Ruído de fundo, nuvens, varas", "Fotos + medição", "Mariani"),
 ("Plataforma elevatória: modelo, funcionamento, NBR ISO 9386-1", "Acessibilidade ao palco", "Teste e placa do equipamento", "Mariani"),
 ("Cotações de preço", "Orçamento", "3 cotações por item principal; registrar fonte e data", "Mariani"),
]
for p in P:
    wp.append(list(p) + ["aberta"])
for c, w in zip("ABCDE", [52, 44, 60, 16, 10]):
    wp.column_dimensions[c].width = w
for row in wp.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, vertical="top")

wb.save(OUT)
print("ok", OUT, len(I), "itens")
