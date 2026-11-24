"""Scan publishable sources; never read ignored credentials or historical exports."""

import re
import subprocess
from pathlib import Path

from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings

paths = (
    subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    .stdout.decode()
    .split("\0")
)
secrets = SecretsCollection()
with default_settings():
    for path in paths:
        if path and path != "uv.lock":
            secrets.scan_file(path)
findings = secrets.json()
# Only these generated public-file checksum fields are reviewed non-secret values.
if "registry/science.json" in findings:
    lines = Path("registry/science.json").read_text().splitlines()
    findings["registry/science.json"] = [
        item
        for item in findings["registry/science.json"]
        if not (
            item["type"] == "Hex High Entropy String"
            and re.fullmatch(
                r'\s*"(?:sha256|methodology_sha256)": "[a-f0-9]{64}",?',
                lines[item["line_number"] - 1],
            )
        )
    ]
    if not findings["registry/science.json"]:
        del findings["registry/science.json"]
# Published evaluation runs, verification logs and reviewed data contain SHA-256
# digests, 32-hex evidence IDs and 24-hex snapshot IDs. Only those exact hex JSON
# fields are exempt; all other rules still apply.
HEX_FIELD = re.compile(
    r'\s*"[^"]{1,120}": "(?:[a-f0-9]{24}|[a-f0-9]{32}|[a-f0-9]{64})",?'
)
for path in [
    p for p in findings if p.startswith(("eval/results/", "verification/", "data/"))
]:
    lines = Path(path).read_text().splitlines()
    findings[path] = [
        item
        for item in findings[path]
        if not (
            item["type"] == "Hex High Entropy String"
            and HEX_FIELD.fullmatch(lines[item["line_number"] - 1])
        )
    ]
    if not findings[path]:
        del findings[path]
if findings:
    for path, entries in findings.items():
        for entry in entries:
            print(
                f"FAIL possible secret: {path}:{entry['line_number']} ({entry['type']})"
            )
    raise SystemExit(1)
print("PASS secrets scan of publishable sources")
