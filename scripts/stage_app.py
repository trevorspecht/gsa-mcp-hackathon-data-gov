"""Build a minimal deployment folder without credentials or conversation exports."""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run(["uv", "build", "--wheel"], cwd=ROOT, check=True)
    target = ROOT / ".local/app"
    if target.exists():
        raise SystemExit(
            "Staging folder exists; review/archive it before staging again"
        )
    target.mkdir(parents=True)
    wheels = list((ROOT / "dist").glob("datagov_semantic_mcp-0.1.0-*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Expected one project wheel")
    wheel = wheels[0]
    shutil.copy2(wheel, target / wheel.name)
    # Apps installs pip requirements on Python 3.11; a uv project with a lockfile
    # selects the Python version from requires-python (>=3.12 for this package).
    (target / "pyproject.toml").write_text(
        "[project]\n"
        'name = "datagov-mcp-app"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.12,<3.15"\n'
        'dependencies = ["datagov-semantic-mcp"]\n\n'
        "[tool.uv]\n"
        "package = false\n\n"
        "[tool.uv.sources]\n"
        f'datagov-semantic-mcp = {{ path = "{wheel.name}" }}\n'
    )
    (target / ".python-version").write_text("3.12\n")
    subprocess.run(["uv", "lock"], cwd=target, check=True)
    (target / "app.yaml").write_text("command: ['python', '-m', 'datagov_mcp.app']\n")
    manifest = ROOT / "data/reviewed/manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text())
        if data.get("domain_reviewed") is not True or not data.get("loaded_table"):
            raise SystemExit("Snapshot must be reviewed and loaded before staging")
        shutil.copy2(manifest, target / "manifest.json")
    print("Staged .local/app; no .env or raw data copied. Deployment not executed.")


if __name__ == "__main__":
    main()
