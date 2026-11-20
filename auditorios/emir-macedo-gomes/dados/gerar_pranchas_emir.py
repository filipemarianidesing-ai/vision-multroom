#!/usr/bin/env python3
"""Pranchas de pré-projeto — EEEM Emir de Macedo Gomes.
Monta layout.json (elementos por disciplina, em metros) e gera o PDF de pranchas,
incluindo corte da arquibancada e diagramas de fluxo.

Sistema de coordenadas (metros): x = 0 no eixo do palco, positivo para a DIREITA DA PLANTA
(= esquerda de quem está sentado olhando o palco); y = 0 na borda do palco, positivo para o
fundo da plateia. Cotas de piso relativas à plateia existente (+0,20).

Uso (a partir desta pasta):  python3 gerar_pranchas_emir.py
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "agente"))
import pymupdf
import gerar_pranchas as G

ESC = json.load(open(os.path.join(HERE, "escola.json"), encoding="utf-8"))
BASE = os.path.join(HERE, "..", "base", "Planta_Auditorio_Emir_de_Macedo_Gomes.pdf")
OUT = os.path.join(HERE, "..", "03_Pranchas_Pre_Projeto_Emir.pdf")

# ---------------- geometria levantada da base (m)
XW = 9.30                      # face interna das paredes laterais (±)
Y_FUNDO = 18.70                # parede do fundo
Y_APOIO = -0.97                # alinhamento frontal das salas de apoio
Y_PALCO_FUNDO = -6.97          # parede de fundo do palco (gráfico)
XB = 6.26                      # bloco de poltronas (±)
ROW_FRONT = [2.05 + i for i in range(15)]          # borda frontal de cada fileira (1 = junto ao palco)
PERFIL_B = [0, 0, 0, 0.01, 0.04, 0.07, 0.11, 0.15, 0.20, 0.26, 0.32, 0.39, 0.46, 0.54, 0.62]
PERFIL_A = [0, 0, 0, 0.04, 0.09, 0.15, 0.22, 0.31, 0.40, 0.49, 0.60, 0.71, 0.83, 0.95, 1.08]

def R(x0, y0, x1, y1, **kw):
    d = {"tipo": "ret", "pts": [[x0, y0], [x1, y1]]}; d.update(kw); return d
def C(x, y, **kw):
    d = {"tipo": "circ", "pts": [[x, y]]}; d.update(kw); return d
def L(pts, **kw):
    d = {"tipo": "linha", "pts": pts}; d.update(kw); return d
def S(a, b, **kw):
    d = {"tipo": "seta", "pts": [a, b]}; d.update(kw); return d
def T(x, y, t, **kw):
    d = {"tipo": "linha", "pts": [[x, y], [x, y]], "texto": t, "espessura": 0.01}; d.update(kw); return d

# ---------------- ARQUIBANCADA
arq = []
for i, yf in enumerate(ROW_FRONT):
    h = PERFIL_B[i]
    y0 = yf - 0.33; y1 = yf + 0.67
    op = 0.06 + 0.5 * h / 0.62
    arq.append(R(-XB, y0, XB, y1, cor="arq", opacidade=op, espessura=0.4))
    arq.append(T(-XB - 0.15, yf + 0.45, f"F{i+1}  +{0.20 + h:.2f}".replace(".", ","), cor="arq", tam=5.6, txt_desloc=[-38, 0]))
# patamar do fundo
arq.append(R(-XW, 16.72, XW, Y_FUNDO, cor="arq", opacidade=0.42, espessura=0.6, tag="PATAMAR FUNDO +0,82", tag_desloc=[70, 22]))
# rampas laterais
for s in (-1, 1):
    x0, x1 = s * XB, s * XW
    arq.append(R(min(x0, x1), 4.72, max(x0, x1), 16.72, cor="arq", opacidade=0.14, tracejado=True))
    arq.append(S([s * 7.8, 5.2], [s * 7.8, 15.8], cor="arq", espessura=1.4))
    arq.append(T(s * 7.8 - 0.25, 10.0, "RAMPA i máx. 8% — 0,62 m", cor="arq", rot=90, tam=6, negrito=True))
    # corrimãos
    arq.append(L([[s * (XB + 0.08), 4.72], [s * (XB + 0.08), 16.72]], cor="arq", espessura=0.6, tracejado=True))
    arq.append(L([[s * (XW - 0.08), 4.72], [s * (XW - 0.08), 16.72]], cor="arq", espessura=0.6, tracejado=True))
# guarda-corpo na borda do patamar voltada à última fileira (onde houver desnível livre)
arq.append(L([[-XB, 16.72], [XB, 16.72]], cor="arq", espessura=1.6))
# lugares PCR (6) + acompanhante — distribuídos
pcr = [(-XB, 3.72, 1), (XB, 3.72, -1), (-XB, 10.72, 1), (XB, 10.72, -1), (-5.2, 17.35, 0), (4.2, 17.35, 0)]
for x, y, s in pcr:
    if s != 0:
        xa, xb = (x, x + s * 0.80)
        arq.append(R(min(xa, xb), y - 0.2, max(xa, xb), y + 1.0 - 0.2, cor=(0.0, 0.35, 0.9), opacidade=0.55, espessura=0.8))
    else:
        arq.append(R(x, y - 0.6, x + 1.0, y + 0.6, cor=(0.0, 0.35, 0.9), opacidade=0.55, espessura=0.8))
# espaços PCR existentes no desenho (frente)
arq.append(R(-6.19, 1.26, -3.58, 2.76, cor="alerta", preenchido=False, tracejado=True, espessura=0.8,
             tag="2 PCR NO DESENHO (DEC. 5.296: 6)", tag_desloc=[-30, 44]))
# operação
arq.append(R(-1.2, 17.0, 0.9, 17.85, cor="som", opacidade=0.5, tag="FOH / OPERAÇÃO", tag_desloc=[-30, -16]))
# alertas de saída
for s in (-1, 1):
    arq.append(R(s * XW - 0.3 if s > 0 else -XW, 16.6, s * XW if s > 0 else -XW + 0.3, 18.3, cor="alerta", opacidade=0.7))
arq.append(T(-8.9, 18.0, "PORTA +0,20 x PATAMAR +0,82", cor="alerta", tam=6, negrito=True))
arq.append(T(5.0, 18.0, "PORTA +0,20 x PATAMAR +0,82", cor="alerta", tam=6, negrito=True))
arq.append(T(-4.5, 1.0, "FILEIRAS 1–3 MANTIDAS EM +0,20 (zona acessível)", cor="arq", tam=6.2, negrito=True))
arq.append(T(-3.8, -3.5, "PALCO +1,20 (sem alteração)", cor="cinza", tam=7, negrito=True))

# ---------------- SOM
som = []
for s in (-1, 1):
    som.append(R(s * 7.0 - 0.15, -0.97, s * 7.0 + 0.15, -0.72, cor="som", opacidade=0.95, tag=f"PA-{1 if s<0 else 2}", tag_desloc=[-6 if s>0 else -20, 14]))
    ang_c = 90 + (-28 if s < 0 else 28)  # mira em direção ao centro-fundo
    som.append({"tipo": "leque", "pts": [[s * 7.0, -0.8]], "raio_m": 18.0, "ang_ini": ang_c - 48, "ang_fim": ang_c + 48, "cor": "som", "opacidade": 0.05})
    som.append(R(s * 2.6 - 0.35, -0.6, s * 2.6 + 0.35, 0.0, cor="som", opacidade=0.8, tag=f"SUB-{1 if s<0 else 2}", tag_desloc=[-8, 16]))
    som.append(R(s * 9.25 - (0.2 if s > 0 else 0), 11.2, s * 9.25 + (0.2 if s < 0 else 0), 11.6, cor="som", opacidade=0.6, tracejado=True,
                 tag=f"DLY-{1 if s<0 else 2}*", tag_desloc=[-34 if s > 0 else 4, -6]))
    for xm in (1.6, 3.6):
        som.append(R(s * xm - 0.3, -1.25, s * xm + 0.3, -0.85, cor="som", opacidade=0.5, preenchido=True))
for xf in (-2.0, 0.0, 2.0):
    som.append(R(xf - 0.2, -0.18, xf + 0.2, -0.02, cor="som", opacidade=0.4, tracejado=True))
som.append(T(-2.0, -1.55, "MON (retornos)", cor="som", tam=5.8))
som.append(T(-1.0, 0.45, "FF* front-fill", cor="som", tam=5.6))
som.append(R(-7.2, -1.5, -6.6, -2.2, cor="infra", opacidade=0.9, tag="RACK", tag_desloc=[-30, 4]))
som.append(R(-1.2, 17.0, 0.9, 17.85, cor="som", opacidade=0.6, tag="FOH: MESA + LUZ + VÍDEO", tag_desloc=[-48, -16]))
for (x, y, n) in [(-3.5, -0.55, "CP1"), (3.5, -0.55, "CP2"), (0, -6.2, "CP3"), (-5.6, -4.5, "CP4")]:
    som.append(C(x, y, raio_m=0.22, cor="infra", tag=n, tag_desloc=[4, -4]))
som.append(R(-3.45, -1.45, -2.95, -0.95, cor="video", opacidade=0.8, tag="PÚLPITO", tag_desloc=[-36, 14]))
for nome, y0, y1, cz in [("FRENTE", 1.7, 5.7, "PA + FF"), ("CENTRO", 5.7, 11.7, "PA"), ("FUNDO", 11.7, 18.6, "PA (+DLY se a simulação indicar)")]:
    som.append(L([[-XB, y1], [XB, y1]], cor="som", espessura=0.5, tracejado=True))
    som.append(T(-2.5, (y0 + y1) / 2, f"ZONA {nome}: {cz}", cor="som", tam=6.5, negrito=True))
som.append(T(-9.0, 7.0, "LATERAL", cor="som", tam=6.5, negrito=True))
som.append(T(7.0, 7.0, "LATERAL", cor="som", tam=6.5, negrito=True))

# ---------------- VÍDEO
vid = []
vid.append(R(-2.5, -3.08, 2.5, -2.92, cor="video", opacidade=1.0, espessura=1.6, tag="PAINEL LED 5,00 × 2,81 m (P2,6–2,9)", tag_desloc=[-80, -10]))
for s in (-1, 1):
    vid.append(L([[s * 2.5, -3.0], [s * (2.5 + 21.6 * math.tan(math.radians(60))) * 0 + s * 13.0, 19.0 - 0.0]], cor="video", espessura=0.6, tracejado=True))
vid.append(T(-8.8, 13.5, "limite de visada lateral ±60°", cor="video", tam=5.8))
vid.append(R(-0.4, -0.35, 0.4, -0.1, cor="video", opacidade=0.7, tag="MONITOR RETORNO", tag_desloc=[8, 12]))
vid.append(R(-3.45, -1.45, -2.95, -0.95, cor="video", opacidade=0.8, tag="PÚLPITO: HDMI/USB-C + rede", tag_desloc=[-120, 16]))
vid.append(R(-1.2, 17.0, 0.9, 17.85, cor="video", opacidade=0.5, tag="FOH: seletor de fontes + notebook", tag_desloc=[-60, -16]))
vid.append(R(-7.2, -1.5, -6.6, -2.2, cor="infra", opacidade=0.9, tag="RACK: processadora LED", tag_desloc=[-60, 18]))
for (x, y, n) in [(-3.5, -0.55, "CP1 vídeo"), (3.5, -0.55, "CP2 vídeo")]:
    vid.append(C(x, y, raio_m=0.22, cor="infra", tag=n, tag_desloc=[4, -4]))
vid.append(T(-4.8, 1.0, "1ª fileira a 5,4 m da tela | última a 19,4 m", cor="video", tam=6.2, negrito=True))
vid.append(T(-2.6, -5.2, "ALT.: projeção laser + tela 16:9", cor="video", tam=6))

# ---------------- LUZ
luz = []
luz.append(L([[-6.0, 3.0], [6.0, 3.0]], cor="luz", espessura=2.0, tag="VARA FOH-1", tag_desloc=[90, -4]))
for x in (-4.5, -2.7, -0.9, 0.9, 2.7, 4.5):
    luz.append(C(x, 3.0, raio_m=0.18, cor="luz"))
    luz.append(S([x, 3.0], [x * 0.6, -1.2], cor="luz", espessura=0.5, tracejado=True))
luz.append(L([[-5.0, 8.0], [5.0, 8.0]], cor="luz", espessura=1.4, tracejado=True, tag="VARA FOH-2 (completo)", tag_desloc=[70, -4]))
luz.append(L([[-5.8, -1.9], [5.8, -1.9]], cor="luz", espessura=2.0, tag="VARA PALCO-1 (wash/preenchimento)", tag_desloc=[30, 18]))
for x in (-4.6, -2.8, -1.0, 1.0, 2.8, 4.6):
    luz.append(C(x, -1.9, raio_m=0.16, cor="luz"))
luz.append(L([[-5.8, -3.5], [5.8, -3.5]], cor="luz", espessura=2.0, tag="VARA PALCO-2 (contraluz)", tag_desloc=[50, 14]))
for x in (-4.2, -1.4, 1.4, 4.2):
    luz.append(C(x, -3.5, raio_m=0.16, cor="luz"))
    luz.append(S([x, -3.5], [x, -1.2], cor="luz", espessura=0.5, tracejado=True))
for s in (-1, 1):
    for y in (-1.2, -4.2):
        luz.append(R(s * 5.9 - 0.2, y - 0.2, s * 5.9 + 0.2, y + 0.2, cor="luz", opacidade=0.8))
luz.append(T(-6.2, -5.0, "TORRES LATERAIS (luz cruzada)", cor="luz", tam=5.8))
luz.append(T(-5.6, -6.3, "Cenário/moving heads (completo) na vara PALCO-2", cor="luz", tam=5.8))
luz.append(R(-1.2, 17.0, 0.9, 17.85, cor="luz", opacidade=0.5, tag="FOH: mesa DMX", tag_desloc=[-30, -16]))
luz.append(R(-8.4, -1.5, -7.8, -2.2, cor="luz", opacidade=0.9, tag="SPLITTER DMX / QD-LUZ", tag_desloc=[-20, 30]))
luz.append(R(-2.5, -3.08, 2.5, -2.92, cor="video", opacidade=0.9))
luz.append(T(-4.0, 12.5, "Luz de plateia existente → controlada por DMX (dimmer/relé)", cor="luz", tam=6.2, negrito=True))
luz.append(T(-5.0, 6.0, "Ângulo 40–50° sobre a área frontal; ajustar posição da vara ao pé-direito", cor="luz", tam=6))

# ---------------- ACÚSTICA
acu = []
for s in (-1, 1):
    x0 = s * XW; x1 = s * (XW - 0.25)
    acu.append(R(min(x0, x1), 4.0, max(x0, x1), 18.7, cor="acu", opacidade=0.85))
acu.append(T(-8.9, 9.5, "PAINEL ABSORVENTE (1,2–3,6 m)", cor="acu", rot=90, tam=6, negrito=True, txt_desloc=[12, 0]))
acu.append(T(8.4, 9.5, "PAINEL ABSORVENTE (1,2–3,6 m)", cor="acu", rot=90, tam=6, negrito=True))
acu.append(R(-XW, 18.45, XW, 18.7, cor="acu", opacidade=0.85, tag="FUNDO: absorvente + difusor central (completo)", tag_desloc=[-150, -10]))
acu.append(R(-2.0, 18.3, 2.0, 18.45, cor=(0.6, 0.4, 0.1), opacidade=0.9))
acu.append(R(-6.0, 6.0, 6.0, 17.0, cor="acu", opacidade=0.10, tracejado=True, tag="NUVENS / FORRO ACÚSTICO ≈150 m² (completo)", tag_desloc=[-100, 10]))
acu.append(R(-6.0, 0.5, 6.0, 5.5, cor=(0.4, 0.4, 0.4), opacidade=0.06, tracejado=True))
acu.append(T(-4.8, 3.2, "Teto frontal refletor (mantém reflexão útil da fala)", cor="cinza", tam=6))
acu.append(L([[-6.3, -6.85], [6.3, -6.85]], cor="acu", espessura=3.0, tag="CORTINA DE FUNDO", tag_desloc=[30, -2]))
for s in (-1, 1):
    for y in (-2.4, -4.6):
        acu.append(L([[s * 4.6, y], [s * 6.3, y]], cor="acu", espessura=2.4))
acu.append(T(-6.2, -5.5, "PERNAS/BAMBOLINAS", cor="acu", tam=5.8))
acu.append(L([[-4.5, -0.15], [4.5, -0.15]], cor="acu", espessura=1.4, tracejado=True, tag="CORTINA BOCA DE CENA", tag_desloc=[40, 16]))
acu.append(T(-9.1, 1.0, "Janelas/elementos na parede: verificar vedação", cor="alerta", tam=5.6))
acu.append(T(-4.0, 13.5, "Medir TR e ruído de fundo antes de fechar áreas", cor="acu", tam=6.2, negrito=True))

# ---------------- INFRA
inf = []
rota = [[0.0, 17.3], [-7.6, 17.3], [-7.6, 1.0], [-8.6, 1.0], [-8.6, -1.6]]
inf.append(L(rota, cor="infra", espessura=1.8, tag="DUTO FOH↔RACK sob arquibancada (2× Ø2\" + cabo de rede/fibra)", tag_desloc=[-160, -50]))
inf.append(L([[-7.0, -1.8], [-3.5, -0.55], [3.5, -0.55]], cor="infra", espessura=1.2, tracejado=True))
inf.append(L([[-7.0, -1.8], [0.0, -6.2]], cor="infra", espessura=1.2, tracejado=True))
inf.append(L([[-7.0, -1.8], [-7.0, -0.85]], cor="infra", espessura=1.2))
inf.append(L([[-7.0, -0.9], [7.0, -0.9]], cor="infra", espessura=1.0, tracejado=True))
inf.append(L([[-7.6, 11.4], [-9.1, 11.4]], cor="infra", espessura=0.8, tracejado=True))
inf.append(L([[7.6, 11.4], [9.1, 11.4]], cor="infra", espessura=0.8, tracejado=True))
inf.append(L([[-7.6, 16.9], [7.6, 16.9], [7.6, 11.4]], cor="infra", espessura=0.8, tracejado=True))
inf.append(R(-7.2, -1.5, -6.6, -2.2, cor="infra", opacidade=0.9, tag="RACK AV", tag_desloc=[-36, 4]))
inf.append(R(-8.4, -1.5, -7.8, -2.2, cor="alerta", opacidade=0.8, tag="QD-AV (novo)", tag_desloc=[-52, 22]))
for (x, y, n) in [(-3.5, -0.55, "CP1"), (3.5, -0.55, "CP2"), (0, -6.2, "CP3"), (-5.6, -4.5, "CP4")]:
    inf.append(C(x, y, raio_m=0.22, cor="infra", tag=n, tag_desloc=[4, -4]))
inf.append(R(-2.5, -3.08, 2.5, -2.92, cor="video", opacidade=0.9, tag="LED: circuito dedicado (trifásico a confirmar)", tag_desloc=[-100, -10]))
inf.append(L([[-8.1, -1.9], [-8.1, -3.0], [-2.5, -3.0]], cor="alerta", espessura=1.0, tracejado=True))
inf.append(L([[-8.1, -1.9], [-6.0, 3.0]], cor="luz", espessura=0.8, tracejado=True))
inf.append(L([[-8.1, -1.9], [-5.8, -1.9]], cor="luz", espessura=0.8, tracejado=True))
inf.append(T(-5.0, 7.5, "Plenum da arquibancada = caminho de cabos protegido", cor="infra", tam=6.5, negrito=True))
inf.append(T(-5.0, 8.3, "(prever caixas de passagem com tampa a cada 6–8 m)", cor="infra", tam=6))
inf.append(R(-1.2, 17.0, 0.9, 17.85, cor="som", opacidade=0.5, tag="FOH: 2 TUG + rede + áudio", tag_desloc=[-56, -16]))

LEG_BASE = [("cinza", "ret", "Base: prancha 02/08 PSCIP (esmaecida). Equipamentos de incêndio, rotas e saídas existentes devem ser preservados.")]

layout = {"pranchas": [
    {"codigo": "ARQ-01", "titulo": "Arquibancada — elevação do piso", "descricao": "Arquitetura: perfil B (rampa acessível), lugares reservados, operação e pontos de compatibilização",
     "itens": arq,
     "legenda": LEG_BASE + [
        ("arq", "ret", "Patamares das fileiras — tom mais escuro = mais alto. Cotas absolutas F1…F15 (plateia existente +0,20)."),
        ("arq", "trac", "Corredores laterais em rampa (3,04 m) com corrimão duplo nos dois lados; inclinação variável ≤ 8 %; desnível total 0,62 m."),
        ("arq", "linha", "Guarda-corpo/borda de patamar (altura e tipo conforme NBR 14718 e NT CBMES)."),
        ((0.0, 0.35, 0.9), "ret", "Espaços P.C.R. propostos (6) + assento de acompanhante ao lado — distribuídos na frente, meio e fundo."),
        ("alerta", "trac", "Espaços P.C.R. do desenho original (2) — insuficientes para 270 lugares (Dec. 5.296/2004 art. 23)."),
        ("alerta", "ret", "Portas do fundo no nível +0,20: compatibilizar com o patamar +0,82 (ver notas)."),
        ("som", "ret", "Posição de operação (FOH) — centro-fundo, sobre o patamar."),
     ],
     "notas": [
        "Perfil B calculado para ver o apresentador a partir de 0,40 m acima do piso do palco com poltronas alternadas (C ≈ 0,06 m). Perfil A (C = 0,08) leva o fundo a +1,28 e exige degraus. Ver corte ARQ-02.",
        "Hoje, com piso plano, da 4ª fileira em diante a cabeça da frente encobre o apresentador da cintura para baixo (C < 0,06 m).",
        "Saídas do fundo: (a) degraus + rampa junto às portas, (b) nova soleira com patamar/rampa externa, ou (c) relocar a saída. Decisão depende da vistoria externa e da revisão do PSCIP no CBMES.",
        "Estrutura da arquibancada: estrutura metálica leve + painéis cimentícios/OSB com lã mineral no vazio (evita efeito tambor) ou alvenaria + laje. Carga de uso conforme NBR 6120 — validar com engenheiro estrutural.",
        "Pé-direito livre sobre o patamar do fundo deve ser verificado (meta ≥ 2,50 m livres abaixo de luminárias, dutos e caixas).",
        "Contagem gráfica do desenho: 14 fileiras × 18 + 14 poltronas na 1ª fileira = 266 poltronas + 2 espaços P.C.R. Legenda indica 270 lug. — validar lotação aprovada.",
     ]},
    {"codigo": "SOM-01", "titulo": "Sonorização — posições e cobertura", "descricao": "Sistema principal frontal, subgraves, retornos, reforços opcionais, operação e rack",
     "itens": som,
     "legenda": LEG_BASE + [
        ("som", "ret", "PA-1/PA-2: colunas direcionais (line array em coluna) nas faces das salas de apoio, base ≈ 2,2 m, mira para o centro-fundo."),
        ("som", "ret", "SUB-1/SUB-2: subgraves embutidos no espelho do palco (1,00 m de altura) — controle independente, desligáveis em palestras."),
        ("som", "trac", "FF* front-fills e DLY-* reforços com delay (≈ 44 ms iniciais): só se a simulação indicar. Infraestrutura prevista."),
        ("som", "ret", "MON: 4 retornos de chão; posição para reduzir vazamento e microfonia."),
        ("infra", "circ", "CP1–CP4: caixas de piso/parede no palco (microfones, linha, rede, vídeo, energia)."),
        ("video", "ret", "Púlpito com microfone gooseneck e ponto de vídeo."),
     ],
     "notas": [
        "Distância da caixa principal à 1ª fileira ≈ 7,6 m e à última ≈ 21 m. Fonte pontual: ≈ 9 dB de queda frente→fundo; coluna direcional: ≈ 4–5 dB antes da mira. Meta: ±3 dB (2 kHz) em toda a plateia.",
        "Colunas direcionais concentram energia na plateia e reduzem reflexões em paredes e teto — principal ganho de inteligibilidade em sala reverberante.",
        "Cobertura, SPL, STI e margem antes da microfonia: confirmar em simulação (EASE/fabricante) com pé-direito e materiais levantados.",
        "FOH no centro-fundo: escuta representativa da plateia. Alternativa: fileira 11–12 central com supressão de 4 lugares.",
        "Rack na sala de apoio esquerda (junto à plataforma): exige ventilação/climatização, porta com chave e acesso frontal e traseiro.",
     ]},
    {"codigo": "VID-01", "titulo": "Imagem — painel LED e pontos de vídeo", "descricao": "Painel LED no palco, visibilidade, pontos de conexão e alternativa por projeção",
     "itens": vid,
     "legenda": LEG_BASE + [
        ("video", "ret", "Painel LED 5,00 × 2,81 m (16:9), pitch 2,6–2,9 mm, sobre estrutura própria apoiada no piso do palco, 3,0 m atrás da borda; base a 1,00 m do piso do palco."),
        ("video", "trac", "Limite de visada lateral (±60° do eixo da tela)."),
        ("video", "ret", "Monitor de retorno para o apresentador e púlpito com HDMI/USB-C."),
        ("infra", "circ", "Pontos de vídeo no palco (CP1/CP2) ligados ao rack por HDBaseT/fibra."),
     ],
     "notas": [
        "Altura útil mínima pela regra 1/8 da última fileira (19,4 m): 2,42 m. Proposta 2,81 m (≈ 1/7). Texto mínimo recomendado nos slides: ≈ 4–5 cm de altura de letra na tela.",
        "P2,6 em 5,00 × 2,81 m ≈ 1920 × 1080 px nativos (Full HD). P2,9 reduz custo com 1724 × 969 px.",
        "Consumo médio ≈ 2,8 kW e máximo ≈ 8,4 kW; peso ≈ 420 kg + estrutura — validar com fabricante e estrutural.",
        "Posição a 3,0 m da borda preserva área de apresentação à frente; para teatro, avaliar trilho/estrutura móvel ou LED no fundo do palco (exigiria ≈ 5,5 × 3,1 m).",
        "Projeção (alternativa): laser ≈ 9.000 lm efetivos na mesma tela, exige controle de luz ambiente (janelas laterais) e tem menor contraste com luz acesa.",
     ]},
    {"codigo": "LUZ-01", "titulo": "Iluminação cênica — varas e controle DMX", "descricao": "Luz frontal, preenchimento, contraluz, luz cruzada, cenário e controle",
     "itens": luz,
     "legenda": LEG_BASE + [
        ("luz", "linha", "Varas (barras) de iluminação fixadas à estrutura/teto — posição final conforme pé-direito."),
        ("luz", "circ", "Refletores LED: elipsoidais na FOH (luz frontal, com facas para não atingir o LED), wash RGBW/branco variável no palco."),
        ("luz", "ret", "Torres laterais e splitter DMX/quadro de luz."),
        ("video", "ret", "Painel LED (referência para controle de luz incidente)."),
     ],
     "notas": [
        "Frontal: 40–50° de elevação sobre o apresentador, facas/recortes para não lavar a tela.",
        "Preenchimento (vara PALCO-1) reduz sombras; contraluz (vara PALCO-2) destaca pessoas do fundo — só acima do LED se o pé-direito permitir; senão, torres laterais.",
        "Cenas programadas: Palestra, Cerimônia/Formatura, Apresentação, Vídeo, Plateia/Intervalo. Acionamento simples por botoeira/tablet; mesa DMX completa para o técnico.",
        "Cargas: refletores LED reduzem consumo e calor; circuitos e pontos DMX a confirmar com o quadro elétrico.",
        "Fixações em teto/estrutura exigem validação estrutural, cabo de segurança em cada refletor e acesso seguro para foco (NR-35).",
     ]},
    {"codigo": "ACU-01", "titulo": "Tratamento acústico — superfícies prioritárias", "descricao": "Painéis absorventes, nuvens, difusores, cortinas e pontos de vedação",
     "itens": acu,
     "legenda": LEG_BASE + [
        ("acu", "ret", "Painéis absorventes (lã mineral 50 mm + tecido, classe de reação ao fogo conforme CBMES), faixa 1,2–3,6 m."),
        ("acu", "trac", "Nuvens/forro acústico no terço central e posterior (cenário completo)."),
        ((0.6, 0.4, 0.1), "ret", "Difusor central na parede do fundo (completo) — evita eco de retorno ao palco mantendo energia."),
        ("acu", "linha", "Cortinas de palco: fundo, pernas, bambolinas e boca de cena (veludo pregueado com afastamento)."),
     ],
     "notas": [
        "Estimativa (Sabine, hipóteses de pé-direito 4,5–6,5 m): TR atual 1,4–2,2 s com poltronas estofadas e até 4–5 s com cadeiras rígidas vazias. Meta pré-projeto: 0,8–1,1 s (500–1 kHz, ocupado).",
        "Cenário essencial (≈ 120 m² de painéis + 60 m² de cortinas) leva a ≈ 0,9–1,2 s; completo (+ ≈ 150 m² de nuvens + difusor) a ≈ 0,6–0,9 s.",
        "Áreas finais só após medir TR (ISO 3382-2) e ruído de fundo (NBR 10152:2017) e levantar pé-direito, forro e materiais.",
        "Paredes laterais do terço frontal e teto frontal permanecem refletores, para reforçar a voz natural nas primeiras fileiras.",
        "Verificar ruído da climatização e transmissão por janelas, portas e cobertura; propor vedação apenas onde a medição mostrar transmissão relevante.",
        "Painéis não podem cobrir extintores, sinalização, iluminação de emergência ou detectores.",
     ]},
    {"codigo": "INF-01", "titulo": "Infraestrutura — energia, sinal e caminhos", "descricao": "Dutos, caixas de piso, rack, quadro AV e alimentações",
     "itens": inf,
     "legenda": LEG_BASE + [
        ("infra", "linha", "Duto principal FOH ↔ rack aproveitando o vazio da arquibancada."),
        ("infra", "trac", "Eletrodutos/eletrocalhas para caixas de palco, caixas acústicas, reforços e varas."),
        ("alerta", "ret", "QD-AV: quadro dedicado (DR/DPS/aterramento) — capacidade a confirmar no quadro geral."),
        ("luz", "trac", "Alimentação e DMX das varas de luz."),
     ],
     "notas": [
        "Separar circuitos de áudio, vídeo/LED e iluminação; aterramento único equipotencial (NBR 5410).",
        "Demanda preliminar: áudio 3–5 kW, iluminação LED 3–5 kW, painel LED até 8,4 kW pico — total da ordem de 15–20 kVA a confirmar com equipamentos escolhidos e quadro existente.",
        "FOH: 2 tomadas dedicadas, 2 cabos de rede Cat6, link de áudio digital (stagebox) e DMX.",
        "Caixas de passagem acessíveis; nenhum cabo solto em rotas de fuga; identificação de cabos e portas nas duas pontas.",
     ]},
]}
json.dump(layout, open(os.path.join(HERE, "layout.json"), "w"), ensure_ascii=False, indent=1)

# ================= gera pranchas base
base = pymupdf.open(BASE)
doc = pymupdf.open()
total = len(layout["pranchas"]) + 4
for i, pr in enumerate(layout["pranchas"], 1):
    p = G.Prancha(doc, ESC, base, pr["titulo"], pr["codigo"], i, total, pr["descricao"])
    for it in pr["itens"]:
        p.item(it)
    p.escala()
    p.legenda([tuple(x) for x in pr["legenda"]], pr["notas"])

# ================= ARQ-02 corte longitudinal
p = G.Prancha(doc, ESC, None, "Corte longitudinal — linhas de visão", "ARQ-02", len(layout["pranchas"]) + 1, total,
              "Corte esquemático pelo eixo do palco: piso existente x perfis A/B, palco, LED, caixas e pé-direito a levantar")
pg = p.page
SC = 30.0  # pt por metro
OX, OY = 50 + 7.4 * SC, 560  # y=0 (borda palco) e z=0 (plateia +0,20)
def Q(y, z): return pymupdf.Point(OX + y * SC, OY - z * SC)
sh = pg.new_shape()
# palco
sh.draw_polyline([Q(-7.0, 0), Q(-7.0, 1.0), Q(0, 1.0), Q(0, 0)]); sh.finish(color=(0.3, 0.3, 0.3), fill=(0.85, 0.85, 0.85), width=1)
# piso existente
sh.draw_line(Q(0, 0), Q(18.7, 0)); sh.finish(color=(0.2, 0.2, 0.2), width=1.2)
sh.draw_line(Q(-7.0, 0), Q(-7.0, -0.3)); sh.finish(color=(0.2, 0.2, 0.2), width=0.6)
sh.commit()
def degraus(perfil, cor, dash=False, fill=None):
    pts = [Q(0, 0), Q(1.72, 0)]
    for i, yf in enumerate(ROW_FRONT):
        y0 = yf - 0.33
        pts += [Q(y0, perfil[i]), Q(y0 + 1.0, perfil[i])]
    pts += [Q(18.7, perfil[-1]), Q(18.7, 0)]
    s = pg.new_shape(); s.draw_polyline(pts)
    s.finish(color=G.hexrgb(cor), width=1.3, dashes="[4 2] 0" if dash else None, fill=fill, fill_opacity=0.25 if fill else 1)
    s.commit()
degraus(PERFIL_B, "arq", fill=G.hexrgb("arq"))
degraus(PERFIL_A, (0.5, 0.5, 0.5), dash=True)
# cabeças e olhos (perfil B), linhas de visão
foco = Q(0, 1.40)
for i, yf in enumerate(ROW_FRONT):
    ye = yf + 0.35; ze = PERFIL_B[i] + 1.12
    s = pg.new_shape()
    s.draw_circle(Q(ye + 0.05, ze + 0.05), 0.11 * SC); s.finish(color=(0.25, 0.25, 0.25), fill=(0.95, 0.9, 0.8), width=0.5)
    s.draw_line(Q(ye, PERFIL_B[i] + 0.45), Q(ye + 0.3, PERFIL_B[i] + 0.45)); s.finish(color=(0.3, 0.3, 0.3), width=1.2)
    if i in (3, 7, 11, 14):
        s.draw_line(Q(ye, ze), foco); s.finish(color=G.hexrgb("arq"), width=0.6, dashes="[3 2] 0")
    s.commit()
s = pg.new_shape(); s.draw_circle(foco, 3); s.finish(color=G.hexrgb("alerta"), fill=G.hexrgb("alerta")); s.commit()
p.texto(pymupdf.Point(foco.x - 120, foco.y - 6), "ponto focal: 0,40 m acima do piso do palco", size=6.5, cor="alerta")
# LED
s = pg.new_shape(); s.draw_rect(pymupdf.Rect(Q(-3.08, 4.81), Q(-2.92, 2.0))); s.finish(color=G.hexrgb("video"), fill=G.hexrgb("video"), width=1); s.commit()
p.texto(Q(-6.6, 5.0), "LED 2,81 m (base +1,00 do palco)", size=6.5, cor="video")
# coluna PA (projeção no corte)
s = pg.new_shape(); s.draw_rect(pymupdf.Rect(Q(-0.97, 3.8), Q(-0.77, 2.2))); s.finish(color=G.hexrgb("som"), fill=G.hexrgb("som"), width=1); s.commit()
p.texto(Q(-0.6, 4.0), "PA (coluna)", size=6.5, cor="som")
for yy in (0, 6, 12, 18):
    s = pg.new_shape(); s.draw_line(Q(-0.87, 3.0), Q(yy + 2.4, 1.3 + (PERFIL_B[min(14, int(yy))] if yy else 0))); s.finish(color=G.hexrgb("som"), width=0.4, dashes="[1 2] 0"); s.commit()
# vara FOH (hipótese)
for H, lab in ((4.5, "4,5"), (5.5, "5,5"), (6.5, "6,5")):
    s = pg.new_shape(); s.draw_line(Q(-7.0, H), Q(18.7, H)); s.finish(color=(0.6, 0.6, 0.6), width=0.5, dashes="[6 3] 0"); s.commit()
    p.texto(Q(-6.9, H + 0.08), f"pé-direito hip. {lab} m (a levantar)", size=6, cor="cinza")
s = pg.new_shape(); s.draw_circle(Q(3.0, 4.2), 4); s.finish(color=G.hexrgb("luz"), fill=G.hexrgb("luz")); s.commit()
s = pg.new_shape(); s.draw_line(Q(3.0, 4.2), Q(-1.0, 2.6)); s.finish(color=G.hexrgb("luz"), width=0.6, dashes="[3 2] 0"); s.commit()
p.texto(Q(3.3, 4.35), "vara FOH-1 (≈45°)", size=6.5, cor="luz")
# porta fundo
s = pg.new_shape(); s.draw_rect(pymupdf.Rect(Q(18.6, 2.3), Q(18.8, 0))); s.finish(color=G.hexrgb("alerta"), width=1.2); s.commit()
p.texto(Q(15.2, 2.55), "porta existente no nível +0,20", size=6.3, cor="alerta")
p.texto(Q(15.2, 1.95), "patamar proposto +0,82", size=6.3, cor="arq")
# cotas e rótulos
for i in (0, 3, 7, 11, 14):
    yf = ROW_FRONT[i]
    p.texto(Q(yf - 0.2, -0.45), f"F{i+1}", size=6.5, bold=True)
    p.texto(Q(yf - 0.35, -0.75), f"+{0.20 + PERFIL_B[i]:.2f}".replace(".", ","), size=6, cor="arq")
p.texto(Q(-5.8, 0.45), "PALCO +1,20", size=8, bold=True)
p.texto(Q(4.5, -1.3), "PLATEIA — distância à borda do palco (m)", size=7)
for yy in range(0, 19, 2):
    s = pg.new_shape(); s.draw_line(Q(yy, -0.95), Q(yy, -1.05)); s.finish(color=(0, 0, 0), width=0.5); s.commit()
    p.texto(Q(yy - 0.1, -1.05 - 0.25), str(yy), size=5.5)
# régua de escala
for i in range(5):
    s = pg.new_shape(); s.draw_rect(pymupdf.Rect(60 + i * SC, 790, 60 + (i + 1) * SC, 793)); s.finish(color=(0, 0, 0), fill=(0, 0, 0) if i % 2 == 0 else (1, 1, 1), width=0.4); s.commit()
p.texto(pymupdf.Point(60 + 5 * SC + 6, 793), "0–5 m (escala gráfica do corte)", size=6)
p.texto(pymupdf.Point(50, 80), "CORTE ESQUEMÁTICO — eixo longitudinal do auditório (mesma escala na horizontal e na vertical)", size=10, bold=True)
p.legenda([("arq", "ret", "Perfil B (recomendado): fileiras 1–3 em +0,20; elevação progressiva até +0,82 na 15ª fileira; rampas laterais ≤ 8 %."),
           ((0.5, 0.5, 0.5), "trac", "Perfil A (visibilidade plena, C = 0,08 m): fundo em +1,28; corredores com degraus — não recomendado sem reprojeto de saídas."),
           ("arq", "trac", "Linhas de visão das fileiras 4, 8, 12 e 15 ao ponto focal."),
           ("som", "trac", "Som direto da coluna PA à plateia elevada — incidência menos rasante sobre as cabeças."),
           ("cinza", "trac", "Hipóteses de pé-direito (não consta na planta) — levantar em vistoria."),
          ],
          ["Por que elevar: com piso plano e palco 1,00 m acima, da 4ª fileira em diante a plateia vê o apresentador apenas da cintura para cima; com o perfil B todas as fileiras veem a partir de 0,40 m do piso do palco (poltronas alternadas).",
           "Ganho acústico: a elevação reduz a incidência rasante do som direto sobre as cabeças (efeito de absorção da plateia), melhora a voz natural, o teatro e a música acústica, e encurta o caminho livre das caixas até o fundo. Com sistema de som, o ganho principal vem da mira das colunas; a elevação complementa.",
           "O vazio sob os patamares vira caminho de cabos (FOH ↔ palco) e recebe lã mineral para não ressoar.",
           "Cotas do perfil arredondadas a 1 cm; executivo deve ajustar ao piso real medido (nível a laser) e ao modelo de poltrona.",
          ])

# ================= Diagramas
def diag_page(cod, titulo, desc, n):
    pp = G.Prancha(doc, ESC, None, titulo, cod, n, total, desc)
    return pp

# --- Áudio
pp = diag_page("DIA-01", "Diagrama de fluxo — áudio", "Caminho do sinal de áudio e o que a equipe opera", len(layout["pranchas"]) + 2)
pg = pp.page
B = pymupdf.Rect
pp.texto(pymupdf.Point(40, 70), "FLUXO DE ÁUDIO — entradas → mesa digital → DSP → amplificação → caixas", size=11, bold=True)
ent = [("Mic. púlpito", "gooseneck"), ("Mic. sem fio ×4", "mão/headset (UHF)"), ("Mic. com fio ×6", "contingência/palco"),
       ("DI ×4", "instrumentos/teclado"), ("Notebook / vídeo", "áudio via USB/HDMI-extração"), ("Player / streaming", "Bluetooth/rede")]
for i, (t, s_) in enumerate(ent):
    G.caixa(pg, B(40, 100 + i * 70, 180, 150 + i * 70), t, s_, cor="som")
G.caixa(pg, B(240, 160, 380, 400), "STAGEBOX DIGITAL", "16 entradas / 8 saídas no palco (CP1/CP2) — um cabo de rede até a mesa", cor="infra")
G.caixa(pg, B(440, 160, 600, 400), "MESA DIGITAL (FOH)", "≥ 16 canais mic + estéreo; cenas salvas; controle por tablet; gravação USB; reserva ≥ 25 %", cor="som", fill=0.2)
G.caixa(pg, B(660, 130, 820, 430), "DSP / MATRIZ (RACK)", "roteamento, EQ, delay, limitador por via; presets: PALESTRA · FORMATURA · MÚSICA · VÍDEO", cor="som", fill=0.2)
outs = [("PA-1 / PA-2", "colunas direcionais"), ("SUB-1 / SUB-2", "graves — desligáveis"), ("Front-fill*", "se simulação indicar"),
        ("Delay*", "≈ 44 ms iniciais"), ("Retornos ×4", "vias de monitor"), ("Gravação / transmissão", "saída de linha da mesa/DSP")]
G.caixa(pg, B(660, 470, 820, 560), "AMPLIFICAÇÃO", "multicanal classe D (ou caixas ativas com ponto de energia + sinal)", cor="som")
for i, (t, s_) in enumerate(outs):
    G.caixa(pg, B(900 - 50, 100 + i * 75, 0, 0) if False else B(40 + i * 135, 640, 165 + i * 135, 690), t, s_, cor="som")
for i in range(6):
    G.seta(pg, (180, 125 + i * 70), (240, 280), cor="som")
G.seta(pg, (380, 280), (440, 280), cor="infra", txt="rede (AES50/Dante)")
G.seta(pg, (600, 280), (660, 280), cor="som", txt="AES/Dante/analógico")
G.seta(pg, (740, 430), (740, 470), cor="som")
for i in range(6):
    G.seta(pg, (740, 560), (102 + i * 135, 640), cor="som")
G.caixa(pg, B(440, 440, 600, 560), "OPERAÇÃO DA ESCOLA", "Painel/tablet com 5 botões: LIGAR · PALESTRA · FORMATURA · MÚSICA/TEATRO · VÍDEO · DESLIGAR. Volumes limitados por preset.", cor="arq", fill=0.15)
G.seta(pg, (520, 440), (520, 400), cor="arq", dash=True, txt="chama cena")
G.seta(pg, (600, 500), (660, 400), cor="arq", dash=True)
G.caixa(pg, B(240, 440, 380, 560), "TÉCNICO (EVENTO GRANDE)", "assume a mesa completa na FOH; libera vias, retornos e efeitos", cor="luz", fill=0.12)
G.seta(pg, (380, 500), (440, 360), cor="luz", dash=True)
pp.legenda([("som", "ret", "Áudio"), ("infra", "ret", "Rede/transporte digital"), ("arq", "ret", "Operação simplificada pela escola"), ("luz", "ret", "Operação técnica")],
           ["* itens condicionados à simulação/medição.",
            "Quantidades de microfones e canais são preliminares; dimensionar pelo roteiro de eventos da escola (formatura e música definem o máximo).",
            "Teste de aceitação: STI, cobertura ±3 dB, margem antes da microfonia ≥ 6 dB no púlpito, chamada de cenas pela equipe."])

# --- Vídeo
pp = diag_page("DIA-02", "Diagrama de fluxo — imagem", "Fontes, seleção, processamento e telas", len(layout["pranchas"]) + 3)
pg = pp.page
pp.texto(pymupdf.Point(40, 70), "FLUXO DE IMAGEM — fontes → seletor → processadora → painel LED / retornos", size=11, bold=True)
fontes = [("Notebook do apresentador", "púlpito — HDMI/USB-C (CP1)"), ("Notebook da operação", "FOH"), ("PC fixo / mídia", "rack"),
          ("Câmera (completo)", "palco/plateia — SDI/NDI"), ("Entrada auxiliar", "CP2 — palco")]
for i, (t, s_) in enumerate(fontes):
    G.caixa(pg, B(40, 110 + i * 85, 200, 170 + i * 85), t, s_, cor="video")
    G.seta(pg, (200, 140 + i * 85), (280, 320), cor="video")
G.caixa(pg, B(280, 220, 460, 420), "SELETOR / SWITCHER", "matriz HDMI/HDBaseT com escalonamento; seleção por botão: PÚLPITO · FOH · AUX · CÂMERA", cor="video", fill=0.2)
G.caixa(pg, B(520, 220, 680, 420), "PROCESSADORA LED", "recebe 1920×1080, escala para o painel, ajusta brilho por cena", cor="video", fill=0.2)
G.caixa(pg, B(740, 160, 840, 300), "PAINEL LED", "5,00 × 2,81 m", cor="video", fill=0.3)
G.caixa(pg, B(740, 340, 840, 460), "MONITOR DE RETORNO", "palco (apresentador)", cor="video")
G.caixa(pg, B(520, 480, 680, 580), "ÁUDIO DO VÍDEO", "de-embedder → mesa de som", cor="som")
G.seta(pg, (460, 320), (520, 320), cor="video", txt="HDBaseT/fibra")
G.seta(pg, (680, 300), (740, 230), cor="video", txt="rede LED")
G.seta(pg, (460, 380), (740, 400), cor="video")
G.seta(pg, (460, 400), (520, 530), cor="som")
G.caixa(pg, B(280, 480, 460, 580), "OPERAÇÃO DA ESCOLA", "botão de fonte no painel de cenas + liga/desliga do LED", cor="arq", fill=0.15)
G.seta(pg, (370, 480), (370, 420), cor="arq", dash=True)
pp.legenda([("video", "ret", "Vídeo"), ("som", "ret", "Áudio embutido"), ("arq", "ret", "Operação simplificada")],
           ["Alternativa por projeção: o projetor substitui a processadora + painel; mesma lógica de seleção.",
            "Teste de aceitação: legibilidade de texto padrão da última fileira e das laterais; tempo de troca de fonte; sem cintilação em câmera (taxa de atualização ≥ 3840 Hz)."])

# --- Luz
pp = diag_page("DIA-03", "Diagrama de fluxo — iluminação e cenas", "Controle DMX, universos e cenas de operação", len(layout["pranchas"]) + 4)
pg = pp.page
pp.texto(pymupdf.Point(40, 70), "FLUXO DE ILUMINAÇÃO — controle → DMX/Art-Net → splitter → refletores", size=11, bold=True)
G.caixa(pg, B(40, 120, 220, 230), "BOTOEIRA / TABLET DE CENAS", "PALESTRA · CERIMÔNIA · APRESENTAÇÃO · VÍDEO · PLATEIA · BLACKOUT", cor="arq", fill=0.15)
G.caixa(pg, B(40, 270, 220, 380), "MESA DMX (FOH)", "técnico: ≥ 2 universos, fixtures com biblioteca, cue list", cor="luz", fill=0.2)
G.caixa(pg, B(300, 190, 470, 320), "INTERFACE / NODE", "Art-Net/sACN ↔ DMX; guarda cenas para operação sem mesa", cor="luz")
G.caixa(pg, B(540, 190, 700, 320), "SPLITTER DMX", "saídas isoladas por vara/torre", cor="luz")
dest = [("VARA FOH-1", "6 elipsoidais LED — frontal"), ("VARA PALCO-1", "6 wash — preenchimento"), ("VARA PALCO-2", "4 wash + moving (completo) — contraluz/cenário"),
        ("TORRES LATERAIS", "4 refletores — cruzada"), ("LUZ DE PLATEIA", "dimmer/relé DMX"), ("PAINEL LED", "brilho por cena (via processadora)")]
for i, (t, s_) in enumerate(dest):
    G.caixa(pg, B(760, 90 + i * 80, 845, 150 + i * 80), t, s_, cor="luz")
    G.seta(pg, (700, 255), (760, 120 + i * 80), cor="luz")
G.seta(pg, (220, 175), (300, 240), cor="arq", dash=True)
G.seta(pg, (220, 325), (300, 280), cor="luz")
G.seta(pg, (470, 255), (540, 255), cor="luz")
# tabela de cenas
y = 440
pp.texto(pymupdf.Point(40, y), "CENAS PRÉ-PROGRAMADAS (o que a equipe aciona)", size=9, bold=True); y += 14
cenas = [("PALESTRA", "frontal 70 %, preenchimento 40 %, plateia 30 %, LED 40 %", "fala + vídeo; sub desligado"),
         ("CERIMÔNIA / FORMATURA", "frontal 85 %, cruzada 50 %, contraluz âmbar, plateia 50 %", "microfones + música"),
         ("APRESENTAÇÃO (teatro/música)", "cenas de cor, contraluz, plateia 0 %", "técnico assume a mesa"),
         ("VÍDEO", "frontal 0 %, plateia 10 %, LED 60 %", "áudio do notebook"),
         ("PLATEIA / INTERVALO", "plateia 100 %, palco 20 %", "música ambiente baixa")]
for c in cenas:
    pp.texto(pymupdf.Point(40, y), c[0], size=7, bold=True, cor="luz")
    pp.texto(pymupdf.Point(220, y), c[1], size=7)
    pp.texto(pymupdf.Point(560, y), c[2], size=7, cor="som")
    y += 13
pp.legenda([("luz", "ret", "Iluminação"), ("arq", "ret", "Operação simplificada")],
           ["Percentuais são pontos de partida, ajustados no comissionamento.",
            "Teste de aceitação: cada cena acionada pela equipe da escola em demonstração; luz frontal sem atingir o LED; sem ofuscamento da plateia."])

doc.save(OUT, garbage=3, deflate=True)
print("ok", OUT, doc.page_count)
