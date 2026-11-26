# Catálogo de apostilas e referências indexadas

Somente **metadados** (o conteúdo fica fora do git). Atualizado pelo fluxo `/indexar-apostila`.

| Slug | Arquivo | Título | Autor | Edição / data | Páginas PDF | Leitura (texto/OCR) | Pendências de leitura | Indexado em |
|---|---|---|---|---|---|---|---|---|
| fundamentos-de-acustica | Apostila+Fundamentos+de+Acústica-1725438095-ExportedImages.zip (49 imagens de página; o PDF original com senha não foi recebido) | Apostila Fundamentos da Acústica (Apostila - Portal Viva de Acústica) | Pablo Giordani Serrano; Janaina Costa; Yuri Pinheiro (Portal Acústica) | Fev/2023 (sem nº de edição) | 49 (miolo: impressas 1–39 = posições 8–46) | OCR 100% (imagens ~96 dpi, ampliadas 3×); texto 89–96%; fórmulas exigem conferência visual | Posições 12, 26, 27, 31–33 sem conferência visual; sumário com OCR fraco (lido na imagem) | 2026-11-25 |

Observação: cópia licenciada ao usuário (uso interno). Arquivos curados por apostila: `indice/<slug>/curadoria.json`, `mapa-curado.md`, `conferencia.md`.

## Catálogos de fornecedores

| Slug | Arquivo | Título | Fabricante | Edição | Páginas | Leitura | Dados técnicos | Indexado em |
|---|---|---|---|---|---|---|---|---|
| lady-inovawall | Lady_Acustica_Catalogo_WallPanels_Inovawall.pdf | Wall Panels Inovawall | Lady Acústica (Ladytex) | Rev. 003 — Jun/2022 | 14 (páginas duplas) | texto (12) + OCR (2) | posição 12: lã de vidro, 28 mm, 80 kg/m³, NRC 0,80, reação ao fogo II-A | 2026-11-25 |
| lady-ecoshapes-wood | Lady_Acustica_Catalogo_EcoshapesWood_JUN25.pdf | Ecoshapes Wood | Lady Acústica (Ladytex) | Rev. 003 — Jul/2025 | 11 | texto (10) + OCR (1) | posição 9: 70% PET reciclado, 9 e 3 mm; **sem dado acústico nem reação ao fogo** | 2026-11-25 |

Dados estruturados para cálculo: `assessoria/referencias/materiais/materiais.json`.

## Referências de mercado — Vicoustic (documentos públicos do fabricante, obtidos em 2026-11-26)

| Slug | Arquivo | Páginas | Leitura | Uso |
|---|---|---|---|---|
| vicoustic-catalogo-hifi-cinema-2026 | Vicoustic-Hi-Fi_Home_Cinema-Catalog-2026.pdf | 66 | texto (65) + OCR (1) | construções e curvas α/d/s em terços de oitava (16 produtos) |
| vicoustic-wp-restaurantes | Vicoustic-Public_Spaces-White_Paper-Restaurantes-PT.pdf | 48 | texto | guia prático e quantidade de tratamento para restaurantes |
| vicoustic-wp-cinema | Vicoustic-Hi-Fi_Home_Cinema-White_Paper-Cinema_Rooms.pdf | 56 | texto | guia de home cinema |
| vicoustic-wp-salas-audicao | Vicoustic-Hi-Fi_Home_Cinema-White_Paper-Listening_Rooms.pdf | 64 | texto | guia de salas de audição |
| vicoustic-pet-hd-lookbook | UniVicoustic-PET_HD_Line_LookBook.pdf | 28 | texto (20) + OCR (8) | linha PET HD (visual) |

Originais públicos no Drive do fabricante (IDs em `fontes.json`); cópias no Drive da Mariani não enviadas (limite de
3 MB por envio do conector). Dados estruturados: `assessoria/referencias/materiais/referencias-mercado-vicoustic.json`.
Não obtidos (acima de 10 MB): catálogo Public Spaces 2026, catálogo Professional Audio 2026, white paper Control Rooms.
