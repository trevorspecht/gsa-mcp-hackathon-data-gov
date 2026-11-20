"""Export validated nonsecret bundle variables to the GitHub release job."""

import json
import os
from pathlib import Path

from stage_release import Release


def main():
    release = Release.model_validate_json(
        Path("config/releases/production.json").read_text()
    )
    if release.workspace_host != os.environ["DATABRICKS_HOST"].rstrip("/"):
        raise SystemExit("Release configuration does not match the approved CI host")
    if "configure" in release.workspace_host or "configure" in release.mcp_url:
        raise SystemExit("Configure the actual destination before enabling deployment")
    values = {"BUNDLE_VAR_" + key: value for key, value in release.variables().items()}
    with Path(os.environ["GITHUB_ENV"]).open("a") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise SystemExit("Invalid release environment value")
            stream.write(f"{key}={value}\n")
    print(json.dumps({"configured": True, "county_snapshot": bool(release.manifest)}))


if __name__ == "__main__":
    main()
