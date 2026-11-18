import pytest

from datagov_mcp.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        evidence_dir=tmp_path / "evidence",
        analytics_manifest=tmp_path / "manifest.json",
    )
