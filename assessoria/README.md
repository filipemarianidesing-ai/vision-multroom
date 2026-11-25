# Assessor técnico Mariani — guia de uso

Sistema de agentes do Claude Code para engenharia acústica, eletroacústica e áudio profissional.
As regras gerais estão no `CLAUDE.md` da raiz; os agentes estão em `.claude/agents/`; os comandos estão em `.claude/skills/`.

## Estrutura

```
.claude/
  agents/            7 agentes (coordenador + 6 especialistas)
  skills/            /novo-projeto  /indexar-apostila  /consultar-apostila  /consulta-tecnica
  settings.json      permissões das ferramentas do assessor
assessoria/
  ferramentas/
    apostila/        indexar.py · buscar.py · renderizar_pagina.py · taxonomia.json
    calc/acustica.py biblioteca de cálculos (dB, propagação, Sabine/Eyring, Dc, modos, cobertura de teto,
                     70/100 V, cabos, PAG/NAG, lei da massa (ordem de grandeza), níveis elétricos)
    novo_projeto.py  cria a pasta de um projeto a partir do modelo
    testes/          pytest (cálculos + pipeline da apostila com PDF sintético)
  modelos/           relatório técnico · memória de cálculo · revisão · plano de medição · registro de norma
  projetos/
    _modelo/         ficha de entrada, pendências, decisões, recebidos/, calculos/, pesquisas/, relatorios/, medicoes/
    <cliente>/<AAAA-MM-projeto>/   (ignorado pelo git)
  referencias/
    apostilas/originais/<slug>/    originais preservados, somente leitura (ignorado pelo git)
    apostilas/indice/<slug>/       texto por página, manifest, estrutura, mapa de assuntos (ignorado pelo git)
    apostilas/indice/busca.sqlite  base de busca full-text de todas as apostilas (ignorado pelo git)
    apostilas/CATALOGO.md          metadados das apostilas (versionado)
    normas/registro-normas.md      normas verificadas e temas a verificar
  conhecimento/licoes-aprendidas.md
```

## Como usar

**Demanda técnica (recomendado):** abra o Claude Code na raiz do repositório e escreva a demanda, ou use
`/consulta-tecnica <demanda>`. A sessão segue o protocolo do coordenador e aciona os especialistas.
Para que a sessão inteira *seja* o coordenador: `claude --agent coordenador-projetos`.

**Chamar um especialista diretamente:** "Use o agente eletroacustica-sonorizacao para…" ou `@agente` no prompt.

### Adicionar uma nova apostila
1. Coloque o PDF no repositório (ex.: arraste para o chat ou copie para qualquer pasta).
2. `/indexar-apostila caminho/arquivo.pdf` (ou direto:
   `python3 -I assessoria/ferramentas/apostila/indexar.py arquivo.pdf --titulo "…" --autor "…" --edicao "…"`).
3. O original é preservado (somente leitura, SHA-256), cada página vira texto (OCR automático quando a página é
   digitalizada), a numeração impressa é comparada com a do PDF, fórmulas/tabelas são sinalizadas para conferência
   visual e a base de busca é atualizada.
   **PDF com senha:** `APOSTILA_SENHA='…' python3 -I assessoria/ferramentas/apostila/indexar.py arquivo.pdf` (ou
   `--pedir-senha` no terminal). A senha fica só na memória do processo — não é gravada em nenhum arquivo nem no git.
   Para renderizar páginas desse PDF depois, use a mesma variável.
4. Consulte: `/consultar-apostila tempo de reverberação` ou
   `python3 -I assessoria/ferramentas/apostila/buscar.py "tempo de reverberação"`.

Dependências: `poppler-utils` (pdftotext/pdfinfo/pdftoppm), `tesseract-ocr` + `tesseract-ocr-por` (OCR), Python 3
com `pypdf` (opcional, sumário) e `pytest`/`reportlab`/`Pillow` (somente testes). Em sessões novas na nuvem, o OCR
pode precisar ser reinstalado: `apt-get install -y tesseract-ocr tesseract-ocr-por`.

### Iniciar um novo projeto
1. `/novo-projeto "Colégio X" "Sonorização quadra" "Vitória/ES"` — cria `assessoria/projetos/colegio-x/AAAA-MM-sonorizacao-quadra/`.
2. Coloque plantas, fotos e fichas técnicas em `recebidos/` (originais, nunca editados).
3. Peça a demanda: "Pré-dimensione a sonorização da quadra do projeto colegio-x…". O coordenador lê a ficha e os
   documentos, preenche o que puder, delega, faz a revisão independente e salva o relatório em `relatorios/`.

## Privacidade e persistência — IMPORTANTE
- O repositório é **público**. Projetos de clientes e conteúdo das apostilas ficam **fora do git** (`.gitignore`).
- O container do Claude Code na nuvem é **temporário**: o que não está no git se perde ao fim da sessão.
  Opções: (a) tornar este repositório privado e remover essas linhas do `.gitignore`; (b) criar um repositório
  privado só para `assessoria/projetos` e `referencias/apostilas`; (c) usar o Claude Code localmente, onde os
  arquivos ficam no seu computador; (d) guardar no Google Drive da empresa.

## Testes
`python3 -m pytest -q assessoria/ferramentas/testes`
