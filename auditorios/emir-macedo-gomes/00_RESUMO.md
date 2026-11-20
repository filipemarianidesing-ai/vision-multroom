# Pré-projeto — Auditório EEEM Emir de Macedo Gomes (Linhares/ES)

Mariani Áudio e Vídeo · Rev. 0 · 20/11/2026 · **Simulação de pré-projeto**
Apresentação online: https://claude.ai/artifact/9HhEhzUAs88HXJcxnyjDr8 (privada até ser compartilhada pelo menu Share)

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `01_Indice_Anexos.md` | Anexos usados e documentos que faltam pedir |
| `02_Diagnostico.md` | O que a planta confirma, divergências, problemas, hipóteses e pendências, com a fonte de cada dado |
| `03_Pranchas_Pre_Projeto_Emir.pdf` | 10 pranchas A3: ARQ-01 arquibancada · SOM-01 · VID-01 · LUZ-01 · ACU-01 · INF-01 · ARQ-02 corte com linhas de visão · DIA-01/02/03 fluxos de áudio, imagem e luz |
| `05_Quadro_Tecnico_e_Orcamento_Emir.xlsx` | Quadro item a item (51 itens: problema, local, porquê, quantidade, critério, dependências, teste) · orçamento por cenário com preço, fonte e data em aberto · resumo por categoria · pendências |
| `06_Cenarios_SEDU.md` | Cenários essencial e completo, o que exige obra civil e as etapas |
| `07_Roteiro_Vistoria.md` | Medidas e fotos priorizadas |
| `08_Plano_Testes_Entrega.md` | Testes com instrumento × demonstração e critérios de aceitação |
| `09_Apresentacao/` | Fonte da apresentação de 12 slides (a mesma do link acima) e imagens |
| `dados/escola.json` | Dados calibrados da planta (entrada dos scripts) |
| `dados/calculos_pre_projeto.md` | Linhas de visão, perfis da arquibancada, P.C.R., reverberação, cobertura, delay e LED |
| `dados/layout.json` | Posição de cada elemento por disciplina, em metros |
| `dados/gerar_pranchas_emir.py` · `dados/gerar_planilha_emir.py` | Regeneram as pranchas e a planilha |
| `base/` | Planta original |

## Principais números
- Plateia 18,60 × 19,45 m; palco 1,00 m acima; 15 fileiras com passo de 1,00 m; última fileira a 16,4 m da borda do palco.
- **Visibilidade:** com piso plano, C < 0,06 m da 4ª fileira em diante. O perfil B eleva até +0,82 no fundo, com rampas ≤ 8 %.
- **P.C.R.:** são exigidos 6 espaços e há 2 no desenho; mais 6 assentos reservados.
- **Reverberação estimada:** 1,4–2,2 s hoje e meta de 0,8–1,1 s. Essencial ≈ 0,9–1,2 s; completo ≈ 0,6–0,9 s.
- **Som:** Line Bonsai suspenso, 2 colunas de 8 caixas (inclinações 10°–32°), e 2 subwoofers de 18" no chão.
- **Portas do fundo:** corredor do fundo mantido em +0,20 ligando as 2 portas; 2 escadas de 4 degraus descem da fileira 15.
- **LED:** 5,00 × 2,81 m, P2,6–2,9; projeção laser ≈ 9.000 lm como alternativa.

## Decisões em aberto
1. Essencial ou completo, ou essencial agora e completo por etapas.
2. Arquibancada: corredor do fundo mantido em +0,20 com as duas portas e 2 escadas de 4 degraus (definido em 20/11/2026); falta a revisão do PSCIP pela mudança de layout.
3. Painel LED ou projeção.
4. Reaproveitar ou trocar as poltronas.
5. Lotação oficial: 266 + 2 P.C.R. no desenho × 270 no rótulo.
6. Modelos, potências e quantidades finais, que saem da vistoria, da simulação e das cotações.
