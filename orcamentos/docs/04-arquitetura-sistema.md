# Sistema web de orçamentação — arquitetura proposta

> Status geral: **planejado**. Nada do sistema foi implementado. Este documento existe para decisão antes de programar.

## 1. Princípios
1. **Núcleo determinístico sem IA.** Cálculo, importação, regras de decomposição, versionamento e exportação funcionam
   com IA desligada. IA, se vier, é módulo opcional de sugestão e interpretação, nunca de cálculo.
2. **Imutabilidade das referências.** Cada importação gera uma *versão de base* imutável; cada versão de orçamento
   guarda uma cópia (*snapshot*) dos dados usados. Atualizar preços é ação explícita, com comparação e nova versão.
3. **Nada ausente vira zero.** `NULL` = "sem preço/não informado"; o cálculo recusa itens sem preço no total e lista a pendência.
4. **Decimal em tudo** (`numeric` no banco, `Decimal` no código) com política de arredondamento declarada no orçamento.
5. **Permissões no servidor** e trilha de auditoria de toda alteração relevante.

## 2. Stack recomendada
| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem/framework | **Python 3.12 + Django 5** | Login, perfis/permissões, migrações, admin e auditoria prontos; `Decimal` nativo; mesma linguagem das ferramentas já usadas neste repositório |
| Interface | Templates Django + **HTMX** (sem SPA) | Menos peças móveis, funciona bem em telas de formulário/planilha, fácil manutenção |
| Banco | **PostgreSQL 16** | `numeric` exato, busca textual em português (`tsvector`/`unaccent`/`pg_trgm`) para "pesquisa por descrição", transações |
| Arquivos | Disco do servidor ou armazenamento S3-compatível privado | Originais das bases, documentos da empresa, cotações (acesso só autenticado) |
| XLSX | `openpyxl` | Gera planilha com **fórmulas editáveis** |
| PDF | `WeasyPrint` (HTML → PDF) | Mesmo layout das telas de conferência |
| Importação | `openpyxl`/`pandas` + importadores por base | Um importador por fonte/estrutura, com validação |
| Testes | `pytest` + `pytest-django` + Playwright (teste de aceite pelas telas) | Teste final de aceite automatizado |
| Implantação | **Docker Compose** (app + Postgres + backup) | Reprodutível em qualquer servidor |

## 3. Módulos e modelo de dados (resumo)
- **Contas:** Usuário, Perfil (Administrador, Orçamentista, Revisor, Leitura), permissões por objeto (obra).
- **Cadastros:** Empresa (dados, regime tributário, documentos com validade), Órgão/Cliente, Obra, Ambiente.
- **Bases de referência:** Fonte (SINAPI, DER-ES…), *VersãoDeBase* (UF, competência, regime de encargos, arquivo original + SHA-256,
  importado por/em, resultado), Insumo, Composição, ItemDeComposição (coeficiente), Preço por versão. Imutáveis após confirmação.
- **Composições próprias:** CP-001… com versões, insumos, coeficientes, produtividade, fontes, premissas.
- **Cotações:** fornecedor, data, validade, especificação, quantidade, preço, frete, tributos, prazo, evidência (arquivo), tratamento de outliers.
- **Modelos de serviço (sem IA):** perguntas (tipo, opções, unidade), regras "se resposta X → sugerir etapa Y com quantidade = expressão",
  dependências (Y exige Z), **exclusões** (X já inclui Y ⇒ bloquear Y), editáveis pela interface.
- **Orçamento:** cabeçalho (finalidade, base, data-base, regime, BDI, arredondamento), Itens (etapa, ambiente, referência, snapshot de
  código/descrição/unidade/preço, complemento, quantidade, status confirmado/condicional), **Memória de cálculo** (expressão segura
  com variáveis nomeadas e origem [F]/[V]/[E]), BDI e encargos discriminados, *VersãoDoOrçamento* (congelada: R00, R01…).
- **Auditoria:** quem, quando, o quê, valor anterior/novo.

## 4. Importação de bases
Fluxo: upload do arquivo oficial → hash → detectar estrutura (cabeçalhos esperados) → **prévia** com contagens, erros e avisos →
confirmação → versão imutável. Regras: rejeitar arquivo já importado (hash), sinalizar mudança de estrutura em vez de “adivinhar”,
registrar campos vazios como ausentes, validar unidades contra lista conhecida, preservar o original para download.
**Primeiro importador:** um só (SINAPI-ES **ou** DER-ES Edificações — decisão abaixo), escrito sobre um arquivo real baixado.

## 5. Cálculo
- Custo unitário de composição = Σ (coeficiente × preço do insumo), reproduzindo a composição analítica oficial quando usada; o sistema
  compara com o custo sintético publicado e aponta divergência.
- BDI por componentes, com a fórmula escolhida registrada no orçamento (a fórmula usual de referência do TCU será conferida no acórdão
  original antes de ser cadastrada — **[NV]**). BDI diferenciado para fornecimento de equipamentos como opção por item.
- Arredondamento: configurável por orçamento (ex.: preço unitário com BDI arredondado/truncado a 2 casas; total = qtd × preço unitário),
  porque editais diferem. Padrão a decidir.
- Encargos: se a base já traz mão de obra com encargos, o sistema bloqueia aplicação adicional.

## 6. Segurança e backup
- HTTPS, senhas com hash forte, 2FA opcional, bloqueio após tentativas, sessões com expiração.
- Permissão verificada em cada requisição do servidor; arquivos servidos só a usuários autorizados.
- **Backup:** `pg_dump` diário + cópia dos arquivos; retenção proposta **30 diários + 12 mensais**; cópia fora do servidor
  (armazenamento privado em nuvem). **Restauração testada** em ambiente limpo antes de liberar para uso, e repetida periodicamente
  (proposta: trimestral). Procedimento escrito.

## 7. Dependências externas
| Dependência | Para quê | Situação |
|---|---|---|
| Servidor com Docker (VPS) ou PaaS com Postgres | Rodar o sistema | **Decisão do usuário** (custo mensal) |
| Domínio e certificado TLS | Acesso seguro | Decisão |
| Armazenamento de backup fora do servidor | Backup | Decisão (Google Drive já conectado nesta sessão, ou S3-compatível) |
| Arquivos oficiais (SINAPI, DER-ES) | Importação | Download manual ou assistido; formato a verificar |
| Repositório **privado** para o código | O repositório atual é público | Recomendado criar |
| IA (opcional, fase posterior) | Sugestões de enquadramento | Não necessária para o MVP |

Observação: o Netlify conectado a esta sessão hospeda sites estáticos e funções sem servidor; **não** é adequado sozinho para um
sistema com banco relacional, sessões e permissões no servidor.

## 8. Etapas de construção
| Etapa | Entrega | Critério de "testado" |
|---|---|---|
| 0 | Repositório privado, esqueleto Django, Docker Compose, CI de testes | Sobe localmente; testes passam |
| 1 | Login, perfis, cadastros (empresa, órgão, obra, ambiente), auditoria | Testes de permissão no servidor |
| 2 | Importador da base prioritária + consulta por código/descrição/unidade/data-base | Importa arquivo real; rejeita duplicata; prévia com erros |
| 3 | Orçamento: itens, memória de cálculo, BDI/encargos, arredondamento, versões | Testes de cálculo com valores conferidos à mão |
| 4 | Composições próprias e cotações | CP calculada e usada em orçamento |
| 5 | Modelos de serviço com regras (pintura como primeiro modelo) | Perguntas → etapas sugeridas, dependências e bloqueio de duplicidade |
| 6 | Exportação XLSX (fórmulas) e PDF; atualização explícita de preços com comparação | Arquivo abre e recalcula; versões preservadas |
| 7 | Backup/restauração, implantação, teste final de aceite (8 passos) com IA desligada | Restauração testada; Playwright percorre o aceite |

Cada etapa será reportada como: implementado · como testar · funciona sem IA · testes e resultados · limitações.
