# Fontes oficiais prioritárias — obras escolares no Espírito Santo

> Consulta inicial feita em 26/11/2026 por busca na web. Os itens marcados **[NV]** ainda não foram conferidos no texto
> ou arquivo original e **não podem** fundamentar orçamento até essa conferência.

## 1. Como escolher a base (ordem de raciocínio, não de preferência por preço)

1. **O edital e seus anexos mandam.** Se indicam base, data-base e regime de encargos, siga-os.
2. **Origem dos recursos.** Recurso federal (convênio, transferência, FNDE etc.) costuma atrair a regra federal:
   Lei 14.133/2021, art. 23, §2º, que dá precedência ao **SINAPI** (edificações) e ao **SICRO** (infraestrutura de
   transportes) para obras e serviços de engenharia, seguidos de outras fontes. **[S, comentário — texto legal a conferir]**
3. **Ente contratante.** Estado do ES e municípios podem ter regulamentação própria e usam com frequência o
   **referencial do DER-ES** (Departamento de Edificações e de Rodovias). Um documento de controle municipal indica que
   órgãos do ES podem usar DER-ES, SINAPI-ES e outras, **sem mistura de tabelas no mesmo orçamento**, salvo itens
   ausentes na tabela escolhida. **[S, documento municipal — confirmar entendimento do TCE-ES]**
4. **UF e data-base.** Sempre a tabela do ES, na competência exigida. Não usar tabela de outro estado como se fosse equivalente.
5. **Regime de encargos.** Desonerado × não desonerado deve ser coerente com o edital e com a análise da empresa.
   A situação da desoneração após 2024 está em transição legislativa e há notas do DER-ES com rótulos que precisam de
   conferência. **[NV]**
6. **Itens sem referência oficial** (equipamentos de áudio/vídeo, CFTV, redes): pesquisa de preços com fornecedores,
   contratações similares (PNCP) e composição própria justificada.

## 2. Mapa das fontes

| Fonte | Uso típico em escolas do ES | Onde | Formato | Situação |
|---|---|---|---|---|
| **SINAPI — CAIXA/IBGE** | Edificações em geral; prioritária com recurso federal | [caixa.gov.br/sinapi](https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/Paginas/default.aspx) | Pacotes mensais ZIP (XLSX e PDF): insumos, composições sintéticas e analíticas, famílias e coeficientes, manutenções, % de mão de obra; cadernos técnicos e notas | **[S]** página oficial localizada. A partir de 2025 os relatórios aparecem em "Relatórios Mensais" com arquivos únicos para todas as UFs (ex.: `SINAPI-2026-01-formato-xlsx.zip`). Estrutura interna das planilhas **[NV]** — o importador será construído sobre um arquivo real baixado |
| **DER-ES — Referencial de Edificações** | Obras estaduais/municipais no ES | [der.es.gov.br](https://der.es.gov.br) → Tabela Referencial de Preço → Referencial de Edificações | Planilhas de preços, notas de uso, cadernos de especificações por grupo de serviço | **[S]** cadernos de especificações localizados (ex.: [16.08 Rede lógica](https://der.es.gov.br/Media/der/Documentos/Tabela%20Referencial%20de%20Preço/Referencial%20de%20Edificações/CADERNO_ESPECIFICACOES/16.08%20-%20OUTRAS%20INSTALAÇÕES%20-%20INSTALAÇÕES%20DE%20REDE%20LOGICA.pdf)). Planilha de preços de edificações vigente e competência mais recente **[NV]** |
| **DER-ES — notas de BDI e encargos** | Referência de encargos sociais e BDI do ES | ex.: [nota técnica BDI/encargos sem desoneração, fev/2026](https://der.es.gov.br/media/Documentos/Tabela%20Referencial%20de%20Pre%C3%A7o/Referencial%20de%20Rodovias/2026/08_nota-tecnica-informativa-bdi-e-encargos-sociais-de-obras-e-servicos-sem-desoneracao.pdf) | PDF | **[S]** localizada no referencial de **rodovias**; aplicabilidade a edificações **[NV]** |
| **SICRO — DNIT** | Só quando o objeto for de infraestrutura de transportes (acessos, pavimentação externa extensa) | gov.br/dnit | XLSX/PDF | Não consultado nesta etapa |
| **ORSE (SE), SEINFRA (CE), SIURB (São Paulo), FDE (SP)** | Subsidiárias, para itens ausentes na base principal, se admitidas e justificadas | portais dos órgãos | variados | Não consultadas; uso sempre justificado item a item |
| **PNCP** | Contratações similares (preços praticados, planilhas de outros órgãos) | [pncp.gov.br](https://pncp.gov.br) | consulta/API | Não consultado nesta etapa |
| **Compras.gov.br — Painel/Pesquisa de Preços** | Bens e serviços comuns (equipamentos AV, CFTV, rede) | gov.br/compras | consulta | Não consultado nesta etapa |
| **Fabricantes e distribuidores** | Equipamentos especializados sem referência oficial | cotações formais | PDF/e-mail | Por demanda, com registro completo |

## 3. Normas jurídicas a consultar no texto oficial

| Norma | Tema | Situação |
|---|---|---|
| Lei 14.133/2021, art. 23 ([Planalto](https://planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm)) | Valor estimado; §2º obras e serviços de engenharia | Núcleo confirmado só por comentários ([TCE-SP](https://www.tce.sp.gov.br/legislacao-comentada/lei-14133-1o-abril-2021/23), [TCU](https://licitacoesecontratos.tcu.gov.br/4-4-3-6-orcamento-detalhado/)); texto integral **[NV]** |
| IN SEGES/ME 91/2022 | Regulamenta o art. 23, §2º no âmbito federal | **[S]** citada; vigência **[NV]** |
| IN SEGES/ME 65/2021 ([gov.br](https://www.gov.br/transferegov/pt-br/legislacao/instrucoes-normativas/instrucao-normativa-seges-me-no-65-de-7-de-julho-de-2021-1)) | Pesquisa de preços de bens e serviços em geral (federal) | **[S]**; aplicação a ES/municípios depende de norma local; vigência **[NV]** |
| Decreto 7.983/2013 ([Câmara](https://www2.camara.leg.br/legin/fed/decret/2013/decreto-7983-8-abril-2013-775701-normaatualizada-pe.pdf)) | Regras de orçamento de obras com recursos da União | Aplicabilidade sob a Lei 14.133 citada em comentário; **[NV]** |
| Decretos estaduais ES 5307-R/2023, 5353-R/2023, 5354-E/2023, 5545-R/2023, 6127-R/2025 ([SEGER-ES](https://seger.es.gov.br)) | Governança, transição, SRP, gestão de contratos | **[S]** localizados; **não** foi localizado decreto estadual específico de pesquisa de preços de obras **[NV]** |
| Acórdãos do TCU sobre BDI (faixas referenciais e fórmula) | BDI de obras e de fornecimento de equipamentos | Não consultados nesta etapa — **não usar de memória** |
| Orientações do TCE-ES | Uso de tabelas, BDI, pesquisa de preços por municípios | Não consultadas nesta etapa |

## 4. Próximos passos de pesquisa (antes do primeiro orçamento real)
1. Baixar o pacote SINAPI mais recente (XLSX) e o caderno técnico de pintura; registrar hash e estrutura.
2. Localizar a planilha de preços do Referencial de Edificações do DER-ES vigente, com a nota de uso.
3. Ler o texto oficial do art. 23 da Lei 14.133 e verificar regulamentação do ES e dos municípios-alvo.
4. Verificar a regra de desoneração vigente na competência do orçamento.
5. Consultar a orientação do TCU/TCE-ES sobre BDI (obras × fornecimento de equipamentos).
