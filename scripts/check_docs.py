"""Check authored Markdown frontmatter and local related-file links."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
paths = list(ROOT.glob("*.md")) + list((ROOT / "docs").rglob("*.md"))
for path in paths:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise SystemExit(f"FAIL missing frontmatter: {path.name}")
    metadata = yaml.safe_load(text.split("---", 2)[1])
    if not {"title", "description", "status", "tier"} <= metadata.keys():
        raise SystemExit(f"FAIL incomplete frontmatter: {path.name}")
    for link in metadata.get("related_files", []):
        if not (path.parent / link).exists():
            raise SystemExit(f"FAIL related link: {path.name}: {link}")
    if sum(line.startswith("```") for line in text.splitlines()) % 2:
        raise SystemExit(f"FAIL unbalanced fences: {path.name}")
print(f"PASS Markdown structure and related links: {len(paths)} files")
