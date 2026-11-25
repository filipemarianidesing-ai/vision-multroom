---
name: consultar-apostila
description: Consulta as apostilas indexadas e responde com citação de arquivo e página (PDF e impressa), conferindo a página inteira e, para fórmulas e tabelas, a imagem da página.
argument-hint: "<pergunta ou termos>"
allowed-tools: Bash(python3 -I assessoria/ferramentas/apostila/*) Read Grep Glob
---

Pergunta: $ARGUMENTS

1. `python3 -I assessoria/ferramentas/apostila/buscar.py --listar` (se vazio: informe que nenhuma apostila foi
   indexada e oriente `/indexar-apostila`; não responda "pela apostila" sem ela).
2. Busque com 2–4 formulações (sinônimos, termos técnicos, sem acento, prefixo*):
   `python3 -I assessoria/ferramentas/apostila/buscar.py "<termos>" --limite 8`
3. Abra as páginas mais relevantes por inteiro (`--pagina <slug> <pág>`). Se houver fórmula, tabela ou OCR,
   renderize (`renderizar_pagina.py`) e confira a imagem antes de citar valores.
4. Responda: conteúdo encontrado, classificação (didático / recomendação técnica / exigência normativa /
   obrigação legal), citação **arquivo — p. PDF X (impressa Y)**, e o que deve ser confrontado com fonte atual
   (normas, legislação, produtos). Se a apostila não cobre o tema, diga isso claramente.
