---
name: restaurar-base
description: Restaura a base de apostilas (original, índice, curadoria e conferência técnica) a partir do Google Drive privado, com verificação SHA-256. Use automaticamente quando o aviso de inicialização disser que a base PRECISA SER RECONSTRUÍDA, ou quando buscar.py disser que não há apostila indexada.
allowed-tools: Bash(python3 assessoria/ferramentas/base/base.py *) Read Glob Grep
---

1. Diagnóstico: `python3 assessoria/ferramentas/base/base.py estado`. Se tudo estiver DISPONÍVEL, pare e informe.
2. Leia `assessoria/referencias/apostilas/fontes.json`. Para cada documento em PRECISA_RECONSTRUIR:
   a. Baixe a origem com o conector Google Drive: `download_file_content` com `fileId = origem.drive_file_id`.
      O conector salva o binário em um arquivo local (caminho informado no resultado) — use esse caminho.
   b. Se `backup` existir, baixe também `backup.drive_file_id` (pacote com índice + conferência técnica).
   c. Rode: `python3 assessoria/ferramentas/base/base.py restaurar <slug> --origem "<arquivo_origem>" [--backup "<arquivo_pacote>"]`
      O script recusa qualquer arquivo cujo SHA-256 não confira com o registro e não altera nada nesse caso.
3. Confirme com `estado` e informe ao usuário em uma linha: DISPONÍVEL / RECONSTRUÍDA (de pacote ou por OCR) /
   INACESSÍVEL.
4. **INACESSÍVEL**: se o conector Google Drive não estiver disponível, o download falhar, o arquivo tiver sido
   removido/movido ou o hash não conferir — diga exatamente o motivo, não cite a apostila nesta sessão e indique a
   ação (reconectar o Drive, restaurar o arquivo ou reenviar o ZIP).
5. Sem pacote de backup, a reindexação por OCR recupera o texto e a numeração curada (versionada no repositório),
   mas **não** a conferência técnica privada — registre essa perda como pendência.

Nunca copie o conteúdo baixado para fora de `assessoria/referencias/apostilas/` nem o adicione ao git.
