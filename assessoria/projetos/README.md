# Projetos de clientes

Cada projeto fica em `projetos/<cliente>/<AAAA-MM-projeto>/`, criado com:

    python3 assessoria/ferramentas/novo_projeto.py "Cliente" "Projeto" --cidade "Cidade/UF"

ou `/novo-projeto "Cliente" "Projeto" "Cidade/UF"` no Claude Code.

**Privacidade:** tudo aqui (exceto `_modelo/` e este arquivo) é ignorado pelo git, porque o
repositório é público. Guarde os projetos em armazenamento privado (repositório privado,
Google Drive da empresa ou backup local) — o container do Claude Code na nuvem é temporário.
