"""Portable releases do not inherit credentials or destination data readiness."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stage_release", ROOT / "scripts/stage_release.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
Release = module.Release


def config():
    return json.loads((ROOT / "config/releases/example.json").read_text())


def test_release_ignores_local_credentials(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "DATABRICKS_TOKEN=" + "test" + "\nAGENT_API=" + "chat" + "\n"
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "ambient-secret")
    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "ambient-profile")
    release = Release.model_validate(config())
    assert release.api == "responses"
    assert "secret" not in release.model_dump_json()
    assert module.checked_manifest(release, tmp_path) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"unknown": "value"},
        {"model": ""},
        {"catalog": "research; DROP"},
        {"mcp_url": "http://example.com/mcp"},
        {"max_output_tokens": 9000},
        {"api": "unknown"},
        {"manifest": "manifest.json"},
        {"workspace_host": "https://example.com/\ninjected"},
        {"ui_app_name": "datagov-ui\n"},
        {"schema_name": "public_data\n"},
    ],
)
def test_invalid_release(changes):
    with pytest.raises(ValueError):
        Release.model_validate(config() | changes)


def manifest_fixture():
    counties = ({f"24{c:03d}" for c in range(1, 48, 2)} - {"24007"}) | {"24510"}
    return {
        "snapshot_id": "a" * 24,
        "state_fips": "24",
        "years": [2022, 2023, 2024],
        "county_fips": sorted(counties),
        "sources": [
            {"id": name, "url": "https://example.gov/data", "sha256": "b" * 64}
            for name in ("census_population", "bls_laus")
        ],
        "data_sha256": "c" * 64,
        "row_count": 72,
        "domain_reviewed": True,
        "loaded_table": "`research`.`public_data`.`county_indicators`",
    }


def test_destination_attestation(tmp_path):
    raw = json.dumps(manifest_fixture()).encode()
    (tmp_path / "manifest.json").write_bytes(raw)
    release = Release.model_validate(
        config()
        | {
            "manifest": "manifest.json",
            "snapshot_attestation": "attestation.json",
        }
    )
    attestation = {
        "workspace_host": release.workspace_host,
        "loaded_table": manifest_fixture()["loaded_table"],
        "snapshot_id": "a" * 24,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": 72,
    }
    path = tmp_path / "attestation.json"
    path.write_text(json.dumps(attestation))
    assert module.checked_manifest(release, tmp_path) == raw
    path.write_text(
        json.dumps(attestation | {"workspace_host": "https://old.example.com"})
    )
    with pytest.raises(ValueError, match="destination"):
        module.checked_manifest(release, tmp_path)
    path.write_text(json.dumps(attestation))
    (tmp_path / "manifest.json").write_bytes(raw + b"\n")
    with pytest.raises(ValueError, match="destination"):
        module.checked_manifest(release, tmp_path)


def test_both_apps_same_wheel_and_no_credentials(monkeypatch, tmp_path):
    wheel_dir = tmp_path / "dist"
    wheel_dir.mkdir()
    (wheel_dir / "datagov_semantic_mcp-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (tmp_path / "uv.lock").write_text((ROOT / "uv.lock").read_text())
    monkeypatch.setattr(module, "ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(
        module.subprocess, "run", lambda command, **kw: calls.append(command)
    )
    output = tmp_path / "release"
    module.stage(Release.model_validate(config()), tmp_path, output)
    for name in ("app", "ui"):
        assert (
            output / name / "datagov_semantic_mcp-0.1.0-py3-none-any.whl"
        ).read_bytes() == b"wheel"
        assert not (output / name / ".env").exists()
        assert not (output / name / "manifest.json").exists()
        assert (
            "constraint-dependencies" in (output / name / "pyproject.toml").read_text()
        )
        assert "DATABRICKS_TOKEN" not in (output / name / "app.yaml").read_text()
    assert calls.count(["uv", "lock"]) == 2
    with pytest.raises(ValueError, match="exists"):
        module.stage(Release.model_validate(config()), tmp_path, output)


def test_bundle_ownership_and_release_gate():
    bundle = yaml.safe_load((ROOT / "databricks.yml").read_text())
    assert "resources" not in bundle["targets"]["sandbox"]
    apps = bundle["targets"]["portable"]["resources"]["apps"]
    assert set(apps) == {"datagov_mcp", "datagov_ui"}
    assert apps["datagov_ui"]["resources"][0]["app"]["permission"] == "CAN_USE"
    assert "sql_warehouse" not in str(apps["datagov_ui"])
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    gate = workflow["jobs"]["release"]["if"]
    assert "conclusion == 'success'" in gate
    assert "event == 'push'" in gate
    assert "DATABRICKS_DEPLOY_ENABLED == 'true'" in gate
    assert workflow["concurrency"]["cancel-in-progress"] is False
    text = (ROOT / ".github/workflows/deploy.yml").read_text()
    assert "workflow_run.head_sha" in text
    assert "terraform apply" not in text
