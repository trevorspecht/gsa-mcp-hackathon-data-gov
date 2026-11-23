---
title: "Hackathon demonstration and slide outline"
description: "A short evidence-first demo with submission slide content"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["EVALUATION.md", "DATABRICKS.md"]
---

# Submission artifacts

Deadline: **Monday, November 23, 2026, 11:59 p.m. Eastern** (extended from Nov 20).
A live demo is not required. Organizer templates are at the repository root
(`MCP-hackathon-sample-deck.pptx`, `MCP-hackathon-sample-evaluation-document.docx`).
Run `uv run python scripts/build_submission.py` to
produce the 12-slide deck and evaluation DOCX in `.local/submission/`. The deck's
demonstration slide uses screenshots from the hosted private App saved in
`.local/submission/screens/`; the evaluation tables are computed from the saved
November 22–23 panel files. Both documents need human proofreading before upload.

| Required deliverable | Where |
| --- | --- |
| GitHub repository with documented MCP code | github.com/trevorspecht/gsa-mcp-hackathon-data-gov |
| Slide deck: problem, solution, technical approach, demonstration | `.local/submission/Data.gov-Research-Hackathon.pptx` |
| Evaluation: methodology, metrics, security, lessons | `.local/submission/Data.gov-Research-Evaluation.docx` |
| Evaluation runs, review pages and scores | `eval/results/` in the repository |

## Demonstration questions (hosted research App)

1. "Is there a correlation between climate patterns and agricultural practices over
   time in Maryland and the Chesapeake Bay watershed?" — answer explains geography
   and sparse-year limits; Explore further previews data and checks compatibility.
2. "Which Maryland counties gained population while unemployment fell from 2022
   to 2024?" — Worcester County; Data & charts shows generic change bars.
3. "What datasets are available about climate, irrigation and cover-crop
   practices?" — ranked catalog candidates with availability in Sources.
4. "How did estimated cover-crop implementation in the Chesapeake Bay watershed
   change between 2002 and 2012?" — 481.509 → 1,770.5665 km².
