"""Run the fixed evaluation panel through datagov-agent and save every actual output.

Requires DATABRICKS_CONFIG_PROFILE, DATABRICKS_MCP_URL and DATABRICKS_MODEL_ENDPOINT
(see docs/DATABRICKS.md). Failed runs are preserved alongside successful runs.
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from datagov_mcp.agent import AgentSettings

ROOT = Path(__file__).resolve().parents[1]
REPEATED = ("A1", "M1", "U3")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="Question IDs to run")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    settings = AgentSettings()
    questions = json.loads((ROOT / "eval/questions.json").read_text())
    if args.only:
        questions = [q for q in questions if q["id"] in args.only]
    runs = [(q, 1) for q in questions] + [
        (q, n)
        for q in questions
        if q["id"] in REPEATED
        for n in range(2, args.repeats + 1)
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = json.loads(settings.analytics_manifest.read_text())
    output = {
        "started_at": stamp,
        "model_endpoint": settings.databricks_model_endpoint,
        "mcp_url": settings.databricks_mcp_url,
        "snapshot_id": manifest["snapshot_id"],
        "runs": [],
    }
    path = ROOT / ".local/verification" / f"{stamp}-eval-panel.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    for question, repeat in runs:
        started = time.monotonic()
        process = subprocess.run(
            ["uv", "run", "datagov-agent", question["question"]],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=400,
        )
        record = {
            "id": question["id"],
            "repeat": repeat,
            "exit": process.returncode,
            "seconds": round(time.monotonic() - started, 1),
        }
        try:
            record.update(json.loads(process.stdout))
        except json.JSONDecodeError:
            record["error_output"] = (process.stdout + process.stderr)[-2000:]
        output["runs"].append(record)
        path.write_text(json.dumps(output, indent=1))
        tools = [step.get("tool") for step in record.get("trace", [])]
        print(question["id"], repeat, process.returncode, record["seconds"], tools)
    print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
