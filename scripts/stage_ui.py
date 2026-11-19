"""Stage the approved private UI App without credentials or local data."""

import json
import shutil
import subprocess
from pathlib import Path

from datagov_mcp.agent import AgentSettings

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = AgentSettings()
    target = ROOT / ".local/ui"
    if target.exists():
        raise SystemExit("Archive existing .local/ui before staging")
    subprocess.run(["uv", "build", "--wheel"], cwd=ROOT, check=True)
    target.mkdir()
    wheel = next((ROOT / "dist").glob("datagov_semantic_mcp-0.1.0-*.whl"))
    shutil.copy2(wheel, target / wheel.name)
    (target / "pyproject.toml").write_text(
        '[project]\nname="datagov-research-ui"\nversion="0.1.0"\n'
        'requires-python=">=3.12,<3.15"\ndependencies=["datagov-semantic-mcp[ui]"]\n'
        "[tool.uv]\npackage=false\n[tool.uv.sources]\n"
        f'datagov-semantic-mcp={{path="{wheel.name}"}}\n'
    )
    (target / ".python-version").write_text("3.12\n")
    (target / "launch.py").write_text(
        "import os, subprocess, sys\n"
        "from datagov_mcp import research_ui\n"
        'subprocess.run([sys.executable, "-m", "streamlit", "run", '
        'research_ui.__file__, "--server.address=0.0.0.0", '
        '"--server.port=" + os.environ["DATABRICKS_APP_PORT"], '
        '"--server.headless=true"], check=True)\n'
    )
    config = {
        "command": ["python", "launch.py"],
        "env": [
            {"name": "DATABRICKS_MCP_URL", "value": settings.databricks_mcp_url},
            {
                "name": "DATABRICKS_MODEL_ENDPOINT",
                "value": settings.databricks_model_endpoint,
            },
            {"name": "AGENT_API", "value": "responses"},
            {"name": "AGENT_MAX_OUTPUT_TOKENS", "value": "4000"},
            {"name": "AGENT_REASONING_EFFORT", "value": "low"},
        ],
    }
    # JSON is valid YAML and keeps all configured values explicitly quoted.
    (target / "app.yaml").write_text(json.dumps(config, indent=2))
    subprocess.run(["uv", "lock"], cwd=target, check=True)
    print("Staged .local/ui; no credentials or raw data")


if __name__ == "__main__":
    main()
