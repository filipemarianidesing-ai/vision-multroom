---
name: salvar-base
description: Salva uma nova versão do pacote privado da base de apostilas (índice + conferência técnica) no Google Drive e registra o hash. Use depois de indexar uma apostila nova ou alterar curadoria/conferência.
argument-hint: "<slug>"
allowed-tools: Bash(python3 assessoria/ferramentas/base/base.py *) Read
---

Slug: `$0`

1. `python3 assessoria/ferramentas/base/base.py status-conferencia $0` (atualiza o resumo público, sem transcrições).
2. Gere o pacote no scratchpad (fora do repositório):
   `python3 assessoria/ferramentas/base/base.py empacotar $0 <scratchpad>/base-$0-<AAAAMMDD-HHMM>.zip` — anote sha256.
3. Envie ao Drive com `create_file`: `title` = nome do arquivo, `parentId` = `_pasta_backup_drive.drive_folder_id`
   de `fontes.json`, `contentMimeType` = `application/zip`, `disableConversionToGoogleType` = true e
   `base64Content` = referência `sha256:<hash>:<caminho absoluto>`. Nunca sobrescreva versões anteriores.
4. Confira as permissões do arquivo criado (`get_file_permissions`): somente o proprietário. Se houver outro acesso,
   avise o usuário — não altere permissões sem autorização.
5. `python3 assessoria/ferramentas/base/base.py registrar-backup $0 <pacote> --drive-id <id> --titulo <nome>`
6. Faça commit de `fontes.json` e `curadoria/` (só metadados e hashes) e confirme `estado`.
