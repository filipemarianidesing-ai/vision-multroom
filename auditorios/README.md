# Auditórios escolares — Mariani Áudio e Vídeo

Pré-projetos de modernização de auditórios: arquibancada, acústica, som, LED, luz DMX e infraestrutura.

| Pasta | Conteúdo |
|---|---|
| `agente/` | O **Agente Engenheiro de Auditórios**: metodologia, base de normas, cálculos (`calc_auditorio.py`), gerador de pranchas (`gerar_pranchas.py`), modelo de dados (`template_escola.json`) e lições do ABL (aguardando material) |
| `emir-macedo-gomes/` | Caso 1: EEEM Emir de Macedo Gomes (Linhares/ES). Ver `00_RESUMO.md` |
| `../.claude/agents/engenheiro-auditorio.md` | Definição do agente para o Claude Code (`/agents` → engenheiro-auditorio) |

## Nova escola em 5 passos
1. Crie `auditorios/<escola>/base/` e coloque a planta (de preferência PDF vetorial).
2. Peça ao Claude: *"use o agente engenheiro-auditorio para a escola X com a planta em auditorios/<escola>/base"*.
3. O agente calibra a planta, preenche `dados/escola.json` e roda `python3 agente/calc_auditorio.py dados/escola.json`.
4. Ele monta o layout e gera pranchas, planilha, diagnóstico, cenários, vistoria, testes e apresentação.
5. Depois da vistoria, atualize o `escola.json` com as medidas reais e regenere tudo.

Dependências: Python 3 com `pymupdf` e `openpyxl` (`pip install pymupdf openpyxl`).
