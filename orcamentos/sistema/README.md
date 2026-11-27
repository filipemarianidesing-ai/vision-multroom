# Sistema de orçamentação — Mariani (etapa 1: núcleo sem IA)

Django 6 + PostgreSQL 16. Todo o cálculo é determinístico (Decimal); nenhuma função depende de IA.

## Situação (27/11/2026)

| Item | Situação |
|---|---|
| Login, perfis (Administrador, Orçamentista, Revisor, Leitura) com permissão verificada no servidor | implementado · testado |
| Cadastro de empresa (com documentos e validade), clientes, obras, ambientes | implementado · testado |
| Importação SINAPI (pacote mensal XLSX) com prévia, validação, hash, recusa de duplicidade e de leiaute diferente | implementado · testado com o arquivo oficial 10/2026 |
| Consulta por código, descrição (sem acento), unidade e data-base; analítico com recálculo | implementado · testado |
| Composições próprias CP-xxx e cotações | implementado · testado |
| Orçamento com itens, memória de cálculo, BDI, arredondamento declarado, condicionais fora do total | implementado · testado |
| Modelos de serviço com perguntas e regras editáveis pela tela (modelo inicial: pintura de parede) | implementado · testado |
| Versões congeladas com SHA-256; atualização explícita de preços com comparação e nova versão | implementado · testado |
| Exportação XLSX (fórmulas editáveis, recalculadas no LibreOffice no teste) e PDF | implementado · testado |
| Backup (banco + arquivos + manifesto), retenção e teste de restauração | implementado · testado localmente |
| Implantação Docker (app + Postgres + Caddy HTTPS + backup diário) | escrito · **não testado** (sem Docker neste ambiente) |
| Publicação em servidor | **não publicado** — depende da escolha de hospedagem |

## Rodar localmente

```bash
pip install -r requirements.txt
export ORC_DEBUG=1                      # desenvolvimento; em produção use ORC_SECRET_KEY
export ORC_DB_NAME=orcamento ORC_DB_USER=postgres ORC_DB_HOST=localhost
python manage.py migrate
python manage.py inicializar            # perfis + modelo "Pintura de parede (interna)"
python manage.py createsuperuser
python manage.py runserver
```

Primeiro acesso: cadastre a empresa (menu Empresa), depois importe a base em Bases → Importar SINAPI com o
arquivo `SINAPI-AAAA-MM-formato-xlsx.zip` baixado do site da CAIXA, confira a prévia e confirme.

## Testes

```bash
python -m pytest                                          # unidade + fluxo completo pelas views
SINAPI_ARQUIVO=/caminho/SINAPI-2026-10-formato-xlsx.zip python -m pytest   # inclui o arquivo oficial
# Aceite pelas telas (navegador real), com o servidor rodando:
BASE_URL=http://127.0.0.1:8000 ADMIN_SENHA=... SINAPI_ARQUIVO=... CAPTURAS=/tmp/capturas node e2e/aceite.js
```

## Regras de cálculo (registradas em cada versão)
- Quantidade = fórmula da memória (variáveis com origem F/V/E/C/M), arredondada meio para cima.
- BDI (%) = ((1+AC+S+R+G)(1+DF)(1+L)/(1−I) − 1) × 100, 2 casas; ou percentual informado. BDI diferenciado
  opcional para fornecimento de equipamentos. A fonte do BDI deve ser registrada na justificativa.
- Preço unitário = custo × (1+BDI), arredondado ou truncado (escolha por orçamento). Totais = quantidade × preço.
- Composição própria: Σ TRUNC(coeficiente × preço; 2), mesma regra da planilha analítica do SINAPI.
- Sem custo ou sem quantidade: o item não entra no total e aparece em Pendências. Nunca vira zero.
- No SINAPI, custo 0 com %AS vazio (ou "SEM CUSTO" no analítico) é gravado como sem custo.

## Backup e restauração
- `python manage.py backup` — `pg_dump -Fc` + `tar.gz` dos arquivos (originais das bases, evidências, documentos)
  + `manifesto.json` com SHA-256 e contagens. Pasta: `ORC_BACKUP_DIR` (padrão `$ORC_DADOS/backups`).
- **Frequência:** diária (serviço `backup` do docker-compose). **Retenção:** 30 diários + último de cada mês por 12 meses.
- **Local:** pasta do servidor `ORC_BACKUP_HOST_DIR`, que deve ser sincronizada com armazenamento externo privado
  (ex.: Google Drive da empresa ou bucket S3). Sem cópia externa, o backup não protege contra perda do servidor.
- `python manage.py testar_restauracao` — restaura o último backup num banco temporário, confere contagens e
  recalcula o hash de cada versão. Rodar após a implantação e mensalmente.
- Restauração real: `python manage.py restaurar PASTA --banco NOME --arquivos DIR` (confere hashes antes;
  não sobrescreve o banco em uso sem `--substituir`).

## Limitações conhecidas
- Um único importador (SINAPI XLSX a partir de 2025). DER-ES e outras bases exigem importadores próprios.
- Inclusões/exclusões de cada composição não vêm no XLSX: conferir no caderno técnico da CAIXA.
- Permissões por perfil (não por obra): todos os usuários ativos veem todas as obras.
- 2FA não implementado.
