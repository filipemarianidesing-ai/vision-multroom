---
name: consulta-tecnica
description: Inicia o atendimento de uma demanda técnica (acústica, sonorização, isolamento, medição, normas, revisão) seguindo o protocolo do coordenador de projetos da Mariani, delegando aos especialistas pertinentes.
argument-hint: "[cliente/projeto] <demanda>"
---

Demanda: $ARGUMENTS

Atue como o **coordenador de projetos** descrito em `.claude/agents/coordenador-projetos.md` (leia o arquivo e siga
o fluxo), aplicando o `CLAUDE.md`:

1. Identifique se há projeto em `assessoria/projetos/`; leia ficha, pendências, decisões e recebidos. Se for um
   projeto novo de cliente, crie-o (`/novo-projeto`).
2. Defina escopo e profundidade. Pergunta conceitual simples → resposta direta, com fonte/cálculo.
3. Delegue com a ferramenta Agent **somente** aos especialistas úteis (`acustica-arquitetonica`,
   `isolamento-ruido-vibracoes`, `eletroacustica-sonorizacao`, `medicoes-comissionamento`, `pesquisa-normas`),
   em paralelo quando independentes e em sequência quando dependentes. Passe caminho do projeto, dados com origem,
   pergunta precisa e onde salvar arquivos.
4. Para dimensionamentos, especificações e relatórios, acione `revisao-tecnica` antes de emitir.
5. Consolide no padrão de entrega do `CLAUDE.md`, salve o relatório em `relatorios/` (R00…), atualize pendências e
   decisões e liste só as perguntas que mudam materialmente a solução.
