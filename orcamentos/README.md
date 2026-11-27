# Orçamentista Público — Mariani Áudio e Vídeo

Agente de apoio (`.claude/agents/orcamentista-publico.md`) e planejamento do sistema web de orçamentação.

| Documento | Conteúdo |
|---|---|
| [docs/01-cadastro-empresa-documentos.md](docs/01-cadastro-empresa-documentos.md) | Documentos mínimos para cadastrar a Mariani |
| [docs/02-fontes-oficiais-es.md](docs/02-fontes-oficiais-es.md) | Fontes oficiais e normas para obras escolares no ES |
| [docs/03-demo-pintura-30m2.md](docs/03-demo-pintura-30m2.md) | Fluxo demonstrado com 30 m² de pintura |
| [docs/04-arquitetura-sistema.md](docs/04-arquitetura-sistema.md) | Arquitetura, dependências, etapas e decisões |
| [sistema/README.md](sistema/README.md) | **Sistema web (etapa 1 implementada e testada localmente)**: como rodar, testar, fazer backup |

## Uso do agente
`claude --agent orcamentista-publico`, ou peça na sessão para acionar o subagente `orcamentista-publico`.

## Pastas privadas (ignoradas pelo git — repositório público)
- `orcamentos/empresa/` — documentos da Mariani (cartão CNPJ, contrato social, certidões, CATs).
- `orcamentos/obras/<orgao>/<obra>/` — recebidos, memória de cálculo, cotações, orçamentos R00, R01…
- `orcamentos/bases/` — arquivos oficiais baixados (SINAPI, DER-ES) com hash.

## O que já funciona × o que exige o sistema
| Recurso | Situação |
|---|---|
| Decompor serviços, classificar etapas, listar perguntas e duplicidades | Executável agora pelo agente |
| Ler planilhas/PDFs enviados (edital, SINAPI, DER-ES) e montar planilha com rastreio | Executável agora, arquivo a arquivo |
| Pesquisa web de fontes e normas | Executável, com conferência obrigatória no original |
| Cálculo determinístico (Python/Decimal) e XLSX com fórmulas / PDF | Executável agora por script, por orçamento |
| Login, perfis, cadastro persistente, importação validada, versões, modelos de serviço editáveis, backup | **Implementado e testado localmente** em `sistema/`; ainda **não publicado** |
