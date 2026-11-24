"""User-run terminal login; reads host/profile without sourcing .env as shell code."""

import os
import shutil
import subprocess
from pathlib import Path

from pydantic import ValidationError

from datagov_mcp.config import Settings, configuration_errors


def main():
    try:
        settings = Settings()
    except ValidationError as exc:
        for item in configuration_errors(exc):
            print(f"{item['field']}: {item['hint']}")
        raise SystemExit(1) from None
    if not settings.databricks_host or not settings.databricks_config_profile:
        raise SystemExit(
            "Set DATABRICKS_HOST and DATABRICKS_CONFIG_PROFILE in .env first"
        )
    local = (
        Path(__file__).resolve().parents[1]
        / ".local/tools/databricks-1.26.0/databricks"
    )
    cli = shutil.which("databricks") or (str(local) if local.is_file() else None)
    if not cli:
        raise SystemExit("Databricks CLI not found; see docs/DATABRICKS.md")
    env = os.environ.copy()
    # Use the selected workspace/profile without ambient credentials.
    for name in list(env):
        if name.startswith("DATABRICKS_"):
            del env[name]
    result = subprocess.run(
        [
            str(cli),
            "auth",
            "login",
            "--host",
            settings.databricks_host,
            "--profile",
            settings.databricks_config_profile,
        ],
        env=env,
        check=False,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
