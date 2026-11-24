# Instruções do repositório

## Projetos de clientes: sempre gerar uma página HTML para compartilhar

Todo projeto novo de cliente (sala de reunião, auditório, acústica, audiovisual, obra, estrutura metálica etc.) deve ter uma página HTML pronta para enviar ao cliente.

- **Onde salvar:** uma pasta por projeto, `<cliente>-<ambiente>/projeto.html` (exemplo: `perim-sala-reuniao/projeto.html`). Fotos, marcações e outros arquivos do projeto ficam na mesma pasta.
- **Publicar:** publicar a página como Artifact e entregar o link ao usuário, lembrando que o link é privado até ele compartilhar pelo menu Share.
- **Modelo:** usar `perim-sala-reuniao/projeto.html` como referência de estrutura e visual:
  1. cabeçalho com nome do projeto, revisão, data e dados principais (medidas, área, volume);
  2. modelo 3D interativo (Three.js) com câmeras prontas;
  3. resumo do que entra no ambiente;
  4. desenhos técnicos com cotas em metros: planta baixa, planta de forro e elevações;
  5. detalhes construtivos;
  6. cálculo acústico, quando o projeto tiver acústica;
  7. lista de materiais;
  8. pontos a confirmar antes da execução.
- **Idioma:** português do Brasil, linguagem clara para o cliente final.
- **O que não vai na página do cliente:** preços, custos internos ou margens, a menos que o usuário peça.
- **Antes de projetar:** confirmar com o usuário a leitura das fotos e das medidas (marcar as fotos, se precisar).
- **Ao terminar:** fazer commit e push da pasta do projeto.
