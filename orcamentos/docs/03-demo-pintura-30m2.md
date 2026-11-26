# Demonstração do fluxo — "Preciso pintar 30 m² de parede de uma escola"

> Demonstração de **método**. Não contém códigos, descrições oficiais nem preços: nenhum foi conferido em arquivo
> oficial nesta etapa. Onde haveria código/preço, consta **"pendente de consulta"**.

## A. Finalidade e dados informados
| Dado | Valor | Origem |
|---|---|---|
| Serviço | Pintura de parede | [F] |
| Quantidade | "30 m²" | [F] — grandeza a confirmar |
| Local | Escola (sem município, órgão ou ambiente) | [F] |
| Finalidade do orçamento | Não informada | pendente |

## B. Perguntas que alteram materialmente o orçamento (agrupadas)
**Grandeza e geometria** — consequência: sem isso nenhuma quantidade é confiável
1. "30 m²" é área de **superfície de parede**, **comprimento de parede (m)** ou **área de piso**? (não se converte uma na outra sem dimensões)
2. Altura das paredes e comprimento total; descontar ou não portas/janelas (seguir o critério de medição da composição)?

**Estado da superfície** — consequência: define se entram raspagem, tratamento, reparos e massa
3. Pintura nova (reboco novo/massa) ou repintura? Ambiente interno ou externo?
4. Há pintura solta/descascando, umidade, mofo, eflorescência, trincas? Em que área (m² medidos ou fotos)?
5. Precisa lavagem (gordura, fuligem, mofo)?

**Especificação** — consequência: muda a composição escolhida
6. Tinta (látex PVA, acrílica fosca/acetinada/semibrilho, epóxi), cor (mudança forte de cor pode exigir mais demãos), nº de demãos exigido.
7. Massa: corrida (PVA) ou acrílica; integral ou só correções localizadas?
8. Fundo/selador exigido?

**Condições de execução** — consequência: andaime, horário e proteção
9. Altura de trabalho (>~3 m exige andaime/plataforma — critério a confirmar em norma de segurança e na composição).
10. Ambiente ocupado (aulas)? Trabalho noturno/fim de semana? Mobiliário e equipamentos a proteger ou remover?

**Contratação** — consequência: base, data-base e BDI
11. Órgão contratante, município, origem do recurso, data-base e base exigida (SINAPI × DER-ES), regime de encargos.
12. É estimativa interna, orçamento de referência, proposta em licitação ou serviço em contrato existente?

## C. Decomposição técnica e classificação
Hipótese de trabalho para demonstrar o raciocínio: **[E] repintura interna, 30 m² de superfície de parede,
altura ≤ 3 m, alvenaria rebocada com pintura látex existente em estado regular.**

| # | Etapa | Classificação | Comentário |
|---|---|---|---|
| 1 | Vistoria e medição | Tarefa operacional / pendente | Normalmente não é item medido; confirmar dimensões e áreas com problema |
| 2 | Retirada/proteção de mobiliário e equipamentos | **Condicional** | Depende de ocupação do ambiente; pode estar coberta pelo BDI/administração ou ser item próprio, se houver composição |
| 3 | Proteção de piso | **Condicional** + verificar inclusão | Conferir se a composição de pintura já inclui proteção; se item separado, quantidade = área de faixa de piso, **não** a área de parede |
| 4 | Proteção de esquadrias, tomadas, interruptores (fita, lona) | **Incluída?** — verificar | Muitas composições de pintura tratam isso como operacional; conferir no caderno técnico (pendente de consulta) |
| 5 | Lavagem da superfície | **Condicional** | Só se houver sujidade/mofo constatados |
| 6 | Raspagem de pintura solta | **Condicional** | Área medida em vistoria; não presumir 30 m² |
| 7 | Tratamento de mofo/umidade | **Condicional** + diagnóstico | Se houver infiltração, a causa é outro serviço (impermeabilização/hidráulica) — pintar por cima não resolve |
| 8 | Reparo de trincas e reboco | **Condicional** | Quantificar em m (trincas) ou m² (reboco) medidos |
| 9 | Lixamento | **Incluído?** — verificar | Em geral é etapa interna de emassamento/pintura; não cobrar à parte sem verificar |
| 10 | Emassamento | **Condicional** | Repintura em estado regular: correções localizadas, área a medir; integral só se especificado |
| 11 | Fundo/selador | **Condicional** | Necessário sobre massa/reboco novo ou conforme especificação; repintura sobre látex íntegro pode dispensar — confirmar com especificação e fabricante |
| 12 | Pintura (acabamento) | **Confirmada** (serviço principal) | Verificar na descrição da composição o nº de demãos e a unidade (m² de área pintada); não multiplicar 30 × demãos se já consideradas |
| 13 | Andaime/plataforma | **Não aplicável** na hipótese (≤ 3 m) | Vira item se altura maior; verificar se a composição já prevê |
| 14 | Limpeza final | **Incluída?** — verificar | Limpeza de respingos costuma ser operacional; limpeza geral pode ser item próprio |
| 15 | Resíduos (latas, lixas) | **Incluída?** / condicional | Pequeno volume; destinação adequada de embalagens; verificar exigência do edital |
| 16 | Recomposição de mobiliário | Condicional | Par da etapa 2 |
| 17 | Entrega/registro fotográfico | Tarefa operacional | Exceto se o edital exigir relatório como item |

## D. Memória de cálculo (estrutura; números só onde fornecidos)
| Item | Fórmula | Variáveis | Resultado |
|---|---|---|---|
| Pintura de parede | A_pintura = A_superfície − A_vãos (conforme critério de medição) | A_superfície = 30 m² [F]; A_vãos = pendente; critério de desconto = pendente de consulta | **30 m² [F]** provisório |
| Emassamento | A_massa = área medida em vistoria | A_massa = pendente [V] | não quantificado |
| Raspagem | A_rasp = área medida | pendente [V] | não quantificado |
| Proteção de piso (se item separado) | A_prot = L_parede × b_faixa | L_parede = 30 m² ÷ h; h = pendente; b_faixa = largura adotada [E] | ex.: **se** h = 3,0 m e b = 1,0 m ⇒ 10 m linear × 1,0 m = 10 m² **[E — ilustração, não usar sem medição]** |
| Fundo/selador | A_fundo = A_pintura ou A_massa, conforme especificação | pendente | não quantificado |

## E. Planilha sintética (forma; sem códigos ou preços)
| Item | Etapa/ambiente | Base | Código | Descrição oficial | Complemento | Un | Qtd | Custo unit. | Custo total | BDI | Preço unit. | Preço total | Data-base | Status | Fonte |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pintura — sala X | SINAPI ou DER-ES (definir) | pendente de consulta | pendente de consulta | Repintura interna, n demãos | m² | 30 [F] | pendente | — | pendente | — | — | pendente | Confirmado | — |
| C1 | Emassamento localizado | idem | pendente | pendente | Correções | m² | a medir | — | — | — | — | — | — | Condicional | — |
| C2 | Raspagem | idem | pendente | pendente | — | m² | a medir | — | — | — | — | — | — | Condicional | — |
| C3 | Fundo/selador | idem | pendente | pendente | — | m² | a definir | — | — | — | — | — | — | Condicional | — |
| C4 | Proteção de piso | idem | pendente | pendente | Se não incluída | m² | a medir | — | — | — | — | — | — | Condicional | — |

Totais: não calculados (sem preços verificados). Itens **C** ficam fora do total até confirmação.

## F. Duplicidades a impedir (regras que o sistema deve aplicar)
- Lixamento cobrado à parte quando já contido no emassamento/pintura.
- Pintura multiplicada pelo número de demãos quando a composição já especifica as demãos.
- Proteção de piso com quantidade igual à área de parede.
- Limpeza de respingos cobrada separadamente quando operacional na composição.
- Emassamento integral presumido em repintura.

## G. Recursos usados nesta demonstração
Raciocínio de decomposição e classificação (executável já, sem sistema). Não foi possível nesta etapa: consultar
caderno técnico e composição analítica do SINAPI/DER-ES, obter preços, calcular totais.
