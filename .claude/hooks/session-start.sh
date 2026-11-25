#!/bin/bash
# SessionStart — informa o estado da base de apostilas do assessor Mariani.
# Rápido e somente leitura: não baixa nada nem instala pacotes. Se a base precisar ser
# reconstruída, a saída instrui o assistente a executar /restaurar-base (download pelo
# conector Google Drive, com verificação SHA-256). Nunca bloqueia o início da sessão.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
python3 assessoria/ferramentas/base/base.py estado --hook 2>&1 || echo "BASE DE APOSTILAS: verificação falhou (ver assessoria/ferramentas/base/base.py)."
if ! command -v tesseract >/dev/null 2>&1; then
  echo "(OCR/tesseract ausente neste container: restauração pelo pacote de backup funciona sem ele; reindexação completa exigiria apt-get install -y tesseract-ocr tesseract-ocr-por)"
fi
exit 0
