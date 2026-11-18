"""Scan publishable sources; never read ignored credentials or historical exports."""

import subprocess

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
if findings:
    for path, entries in findings.items():
        for entry in entries:
            print(
                f"FAIL possible secret: {path}:{entry['line_number']} ({entry['type']})"
            )
    raise SystemExit(1)
print("PASS secrets scan of publishable sources")
