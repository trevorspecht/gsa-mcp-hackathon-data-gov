"""Check committed Markdown: a title heading, balanced code fences, working links."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = [
    ROOT / name
    for name in subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()
]
for path in paths:
    text = path.read_text()
    name = path.relative_to(ROOT)
    if not text.lstrip().startswith("# "):
        raise SystemExit(f"FAIL missing title heading: {name}")
    if sum(line.startswith("```") for line in text.splitlines()) % 2:
        raise SystemExit(f"FAIL unbalanced fences: {name}")
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
        if "://" in target or target.startswith("mailto:"):
            continue
        if not (path.parent / target).exists():
            raise SystemExit(f"FAIL broken link: {name}: {target}")
print(f"PASS Markdown titles, fences and local links: {len(paths)} files")
