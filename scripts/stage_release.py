"""Stage both Apps from one wheel and an explicit credential-free release file."""

import argparse
import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from datagov_mcp.agent import SYSTEM, AgentSettings
from datagov_mcp.config import Settings
from datagov_mcp.snapshot import Manifest

ROOT = Path(__file__).resolve().parents[1]


class Release(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workspace_host: str
    warehouse_id: str
    catalog: str
    schema_name: str
    table: str = "county_indicators"
    app_name: str = Field(pattern=r"^mcp-[a-z0-9-]+$")
    ui_app_name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    mcp_url: str
    model: str
    api: str = "responses"
    max_output_tokens: int = 4000
    reasoning_effort: str = "low"
    manifest: str | None = None
    snapshot_attestation: str | None = None

    @model_validator(mode="after")
    def settings(self):
        if any(
            isinstance(value, str) and any(ord(char) < 32 for char in value)
            for value in self.model_dump().values()
        ):
            raise ValueError("Release settings must not contain control characters")
        validated = AgentSettings(
            _env_file=None,
            databricks_host=self.workspace_host,
            databricks_warehouse_id=self.warehouse_id,
            databricks_catalog=self.catalog,
            databricks_schema=self.schema_name,
            databricks_table=self.table,
            databricks_mcp_url=self.mcp_url,
            databricks_model_endpoint=self.model,
            agent_api=self.api,
            agent_max_output_tokens=self.max_output_tokens,
            agent_reasoning_effort=self.reasoning_effort,
            databricks_token="",
            databricks_client_id="",
            databricks_client_secret="",
            databricks_config_profile="",
        )
        if not all(
            (
                self.workspace_host,
                self.warehouse_id,
                self.catalog,
                self.schema_name,
                self.mcp_url,
                self.model,
            )
        ):
            raise ValueError("Release destination and model fields must be nonempty")
        self.workspace_host = validated.databricks_host
        if self.app_name == self.ui_app_name:
            raise ValueError("Apps must have distinct names")
        if bool(self.manifest) != bool(self.snapshot_attestation):
            raise ValueError("County manifest requires destination attestation")
        return self

    def variables(self):
        return {
            "app_name": self.app_name,
            "ui_app_name": self.ui_app_name,
            "warehouse_id": self.warehouse_id,
            "catalog": self.catalog,
            "schema": self.schema_name,
            "table": self.table,
            "mcp_url": self.mcp_url,
            "model": self.model,
            "agent_api": self.api,
            "agent_max_output_tokens": str(self.max_output_tokens),
            "agent_reasoning_effort": self.reasoning_effort,
        }


def checked_manifest(release, config_dir):
    if not release.manifest:
        return None
    path = config_dir / release.manifest
    raw = path.read_bytes()
    manifest = Manifest.model_validate_json(raw)
    settings = Settings(
        _env_file=None,
        databricks_catalog=release.catalog,
        databricks_schema=release.schema_name,
        databricks_table=release.table,
        databricks_token="",
        databricks_client_id="",
        databricks_client_secret="",
        databricks_config_profile="",
    )
    attestation = json.loads((config_dir / release.snapshot_attestation).read_text())
    expected = {
        "workspace_host": release.workspace_host,
        "loaded_table": settings.table_name,
        "snapshot_id": manifest.snapshot_id,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": 72,
    }
    if (
        attestation != expected
        or not manifest.domain_reviewed
        or manifest.loaded_table != settings.table_name
    ):
        raise ValueError("County snapshot is not attested for this destination")
    return raw


def stage(release, config_dir, output):
    manifest = checked_manifest(release, config_dir)
    if output.exists():
        raise ValueError("Release staging directory exists; archive it first")
    subprocess.run(["uv", "build", "--wheel"], cwd=ROOT, check=True)
    wheels = list((ROOT / "dist").glob("datagov_semantic_mcp-0.1.0-*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one project wheel")
    wheel = wheels[0]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    constraints = sorted(
        {
            f"{p['name']}=={p['version']}"
            for p in lock["package"]
            if p["name"] != "datagov-semantic-mcp"
        }
    )
    output.mkdir(parents=True)
    for name, extra in (("app", ""), ("ui", "[ui]")):
        target = output / name
        target.mkdir()
        shutil.copy2(wheel, target / wheel.name)
        (target / "pyproject.toml").write_text(
            '[project]\nname="datagov-release-' + name + '"\nversion="0.1.0"\n'
            'requires-python=">=3.12,<3.15"\n'
            'dependencies=["datagov-semantic-mcp' + extra + '"]\n'
            "[tool.uv]\npackage=false\nconstraint-dependencies="
            + json.dumps(constraints)
            + "\n[tool.uv.sources]\n"
            + 'datagov-semantic-mcp={path="'
            + wheel.name
            + '"}\n'
        )
        (target / ".python-version").write_text("3.12\n")
        command = ["python", "-m", "datagov_mcp.app"]
        if name == "ui":
            command = ["python", "launch.py"]
            (target / "launch.py").write_text(
                "import os, subprocess, sys\n"
                "from datagov_mcp import research_ui\n"
                'subprocess.run([sys.executable, "-m", "streamlit", "run", '
                'research_ui.__file__, "--server.address=0.0.0.0", '
                '"--server.port=" + os.environ["DATABRICKS_APP_PORT"], '
                '"--server.headless=true"], check=True)\n'
            )
        elif manifest:
            (target / "manifest.json").write_bytes(manifest)
        (target / "app.yaml").write_text(json.dumps({"command": command}))
        subprocess.run(["uv", "lock"], cwd=target, check=True)
    (output / "release-metadata.json").write_text(
        json.dumps(
            {
                "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "instructions_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
                "county_snapshot_included": manifest is not None,
                "variables": release.variables(),
            },
            indent=2,
        )
    )
    return release.variables()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/release")
    args = parser.parse_args()
    release = Release.model_validate_json(args.config.read_text())
    stage(release, args.config.resolve().parent, args.output)
    print("Both Apps staged without .env; no deployment performed")


if __name__ == "__main__":
    main()
