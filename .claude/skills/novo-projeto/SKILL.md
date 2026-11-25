---
name: novo-projeto
description: Abre um novo projeto de cliente da Mariani (pasta isolada com ficha de entrada, pendências, decisões, recebidos, cálculos, pesquisas, relatórios e medições) e já preenche a ficha com o que estiver disponível.
argument-hint: '"<cliente>" "<projeto>" [cidade/UF]'
allowed-tools: Bash(python3 assessoria/ferramentas/novo_projeto.py *) Read Write Edit Glob Grep
---

Abra o projeto com os argumentos: cliente = `$0`, projeto = `$1`, cidade = `$2`.

1. Se faltar cliente ou projeto, pergunte apenas isso. Rode:
   `python3 assessoria/ferramentas/novo_projeto.py "$0" "$1" --cidade "$2"`
   (o script recusa sobrescrever projeto existente — se já existir, use a pasta existente).
2. Se o usuário anexou ou indicou arquivos (plantas, fotos, fichas técnicas), copie-os SEM ALTERAR para
   `recebidos/` do projeto (preserve nome; nova versão = novo nome com data/rev) e registre na seção 8 da ficha.
3. Leia os documentos recebidos e preencha `00-ficha-projeto.md` marcando a origem de cada dado
   ([F]/[V]/[M]/[E]/[?]). Não invente dados ausentes.
4. Liste, no final, somente as perguntas que alteram materialmente a solução (seção 10 da ficha) e registre
   pendências em `pendencias.md`.
5. Lembre o usuário: a pasta `assessoria/projetos/` está no `.gitignore` (repositório público) — combine onde
   esses dados serão guardados de forma persistente e privada.
