import os

os.environ.setdefault("ORC_DEBUG", "1")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _dados_temporarios(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "arquivos"
    settings.BACKUP_DIR = tmp_path / "backups"
