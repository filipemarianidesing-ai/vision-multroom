# Referência construtiva para fabricação de painéis acústicos (benchmark de mercado)

> Para a fabricação própria da Mariani. Fonte dos números: valores **declarados** pela Vicoustic (catálogo Hi-Fi &
> Home Cinema 2026 e páginas de produto, consultados em 2026-11-26), sem norma, laboratório ou montagem de ensaio
> informados → **[S-declarado]**. Servem para orientar o projeto de construções; o desempenho do material fabricado
> pela Mariani só se comprova com **ensaio próprio** (ABNT NBR ISO 354 / ISO 354) da construção real.
> Dados completos: `assessoria/referencias/materiais/referencias-mercado-vicoustic.json`
> (cálculo: `materiais.superficie_referencia(..., aceitar_declarado=True)`).

## 1. Comparação por construção — α médio por oitava (média de 3 terços)

| Construção (referência) | 125 | 250 | 500 | 1k | 2k | 4k | αw decl. |
|---|---|---|---|---|---|---|---|
| Placa de lã de PET 20 mm colada na parede | 0,05 | 0,17 | 0,45 | 0,75 | 0,90 | 0,96 | 0,45 (D) |
| Placa de lã de PET 40 mm colada | 0,15 | 0,32 | 0,69 | 0,83 | 0,90 | 0,96 | 0,60 (C) |
| PET HD moldado 3D (38–52 mm) com moldura | 0,11 | 0,45 | 0,61 | 0,76 | 0,86 | 0,85 | 0,65 (C) |
| MDF ranhurado + lã de PET | 0,15 | 0,48 | 0,73 | 0,90 | 0,80 | 0,75 | 0,75 (C) |
| MDF ranhurado com HPL + espuma de PU, 44 mm | 0,22 | 0,58 | 0,83 | 0,96 | 0,70 | 0,65 | 0,75 (C) |
| Ripas 12 mm (PET + HPL) + câmara de ar + camada de PET, 66 mm | 0,29 | 0,65 | 0,92 | 0,96 | 0,88 | 0,84 | 0,90 (A) |
| Espuma de PU revestida de tecido | 0,26 | 0,72 | 1,00 | 0,97 | 0,99 | 1,00 | 0,95 (A) |
| Lã de PET 60 mm em módulo com MDF | 0,30 | 0,75 | 1,00 | 0,99 | 0,98 | 1,00 | 1,00 (A) |
| Lã de PET 120 mm em módulo com MDF | 0,55 | 0,90 | 1,00 | 0,99 | 1,00 | 1,00 | 1,00 (A) |

Páginas de produto (só número único): placas de **PET HD 11–12 mm coladas** → αw 0,20–0,25 (classe E), NRC
0,25–0,45; a mesma placa **com 40 mm de PET atrás** → αw 0,85–0,90 (classe A–B). Densidade superficial da placa
12 mm: 2400 g/m² (≈ 200 kg/m³); condutividade térmica declarada 0,0418 W/m·K.

## 2. Lições para projetar e fabricar
1. **Espessura e câmara de ar mandam nos graves.** Placa fina colada absorve quase só agudos. A 125 Hz: 20 mm → 0,05;
   40 mm → 0,15; 60 mm → 0,30; 120 mm → 0,55. Para fala (500–2000 Hz) 40 mm já funcionam; para música e cinema, ≥ 60 mm
   ou câmara de ar.
2. **Câmara de ar é o recurso mais barato.** Uma placa decorativa de 12 mm passa de classe E para A–B só ao ganhar
   40 mm de material poroso atrás; um sistema de ripas finas com câmara e camada de PET chega a αw 0,90. Para a Mariani:
   projetar acabamentos decorativos (ripado, impresso, perfurado) sempre como **face sobre câmara com miolo poroso**.
3. **Face rígida ranhurada derruba os agudos.** MDF ranhurado/HPL tem pico em 500–1000 Hz e perde absorção acima de
   2 kHz (0,65–0,80). É bom para salas onde não se quer "matar" os agudos (salas de música, auditórios); para fala muito
   seca, prefira face porosa (tecido) ou ranhura mais aberta.
4. **3D/moldado em PET HD** dá absorção média (classe C) e boa aparência; usar como complemento, não como tratamento
   principal de grave.
5. **Difusores exigem dados próprios.** O catálogo traz curvas de **difusão (d)** e **espalhamento (s)** além de α:
   espalhamento s ≥ 0,7 só a partir de **800 Hz** (Multifuser Wood MKII 64, Multifuser DC4, Cinema Round Ultra Fuser),
   **1250 Hz** (Multifuser Wood MKII 36) ou **1,6 kHz** (Wavewood Diffuser Ultra MKII); abaixo de ~400 Hz praticamente
   não difundem. A geometria muda a faixa útil (os modelos 36 e 64 têm curvas diferentes). Um difusor feito pela Mariani deve ser projetado
   (sequência QRD/PRD, profundidade, largura de poço) e, idealmente, medido (ISO 17497).
6. **Reação ao fogo é o ponto fraco do mercado.** Espuma de PU aparece como **Euroclass F / combustível**; vários painéis
   de PET têm "matéria-prima B-s1,d0" mas **produto final não ensaiado**. Para escolas, igrejas, restaurantes e
   auditórios, a Mariani deve escolher miolo/acabamento com laudo do produto montado conforme a IT do Corpo de Bombeiros
   do estado (ES: CBMES) — sem isso, não especificar.

## 3. Regra prática de quantidade (restaurantes) — recomendação do fabricante, não norma
White paper de restaurantes (PT), posição 25: tempo de reverberação **proposto pela Vicoustic** 0,8 s (60–150 m³) a
< 1,0 s (600 m³), com estimativa de 7–76 m² de painéis conforme o volume. Conferir sempre com cálculo por banda
(`acustica.rt_por_banda`). Observação: a tabela converte 50 m² como 430 ft² (o correto é ≈ 538 ft²).

## 4. Isolamento (cabines)
Cabines VicBooth Ultra declaram **NIC 30 dB** (ASTM E413, a partir de medições internas pela ASTM E596 na configuração
1×1) — construção: aço revestido, vidro laminado, MDF/HPL, lã de PET. É referência de ordem de grandeza para cabines
de locução/estúdio; não confundir com isolamento de parede de edificação.

## 5. Onde consultar (base indexada — citar arquivo e página)
| Documento (slug) | Conteúdo útil |
|---|---|
| `vicoustic-catalogo-hifi-cinema-2026` | Construções, dimensões, materiais, reação ao fogo e **curvas α/d/s** por terço de oitava |
| `vicoustic-wp-restaurantes` (PT) | Problemas típicos, posicionamento e quantidade de tratamento em restaurantes |
| `vicoustic-wp-cinema` | Passos de tratamento para home cinema (primeiras reflexões, graves, difusão traseira) |
| `vicoustic-wp-salas-audicao` | Salas de audição high-end: zonas de reflexão, controle de graves, difusão |
| `vicoustic-pet-hd-lookbook` | Linha PET HD (visual/acabamentos; pouco texto técnico) |

Não baixados (acima do limite de 10 MB do conector; links públicos do fabricante): catálogo Public Spaces 2026,
catálogo Professional Audio 2026 e white paper Control Rooms — podem ser enviados manualmente para indexação.
