---
title: "Reviewer guide"
description: "Where to find the evidence for each judging criterion without running the live Apps"
status: canonical
tier: 1
related_files: ["README.md", "eval/results/README.md", "submission/README.md", "verification/README.md"]
---

# Reviewer guide

The hosted Databricks Apps were demonstrated during the hackathon; the hackathon
workspace is disabled on November 30, 2026. Everything needed to assess the project
is in this repository: the submitted documents, every evaluation run with full tool
traces, the source data, and logs of the live checks.

## Start here (10 minutes)

1. **[Slide deck (PDF)](submission/pdf/Data.gov-Research-Hackathon.pdf)**: problem,
   solution, design decisions, demo screenshots, results, security, lessons.
2. **[Evaluation summary (PDF)](eval/results/EVALUATION-SUMMARY.pdf)**: six pages of
   charts showing every evaluation run over time.
3. **[Evaluation document (PDF)](submission/pdf/Data.gov-Research-Evaluation.pdf)**:
   methodology, metrics, security considerations, lessons and recommendations.

## Evidence by judging criterion

| Criterion | Where to look |
| --- | --- |
| **Code readability and maintainability** | [src/datagov_mcp/tools/](src/datagov_mcp/tools/) (one module per tool group, registered in `__init__.py`); [src/datagov_mcp/datasets.py](src/datagov_mcp/datasets.py) (generic connectors); [registry/datasets.json](registry/datasets.json) (dataset facts as configuration, not code); [tests/](tests/) (100 tests) |
| **Server performance and reliability (evaluation setup and results)** | [eval/results/EVALUATION-SUMMARY.pdf](eval/results/EVALUATION-SUMMARY.pdf); [eval/results/README.md](eval/results/README.md) (all 17 runs, failures included); question panels in [eval/](eval/); harness [scripts/run_eval.py](scripts/run_eval.py) and independent checks [scripts/eval_report.py](scripts/eval_report.py); [docs/EVALUATION.md](docs/EVALUATION.md) |
| **MCP design principles** | Tool descriptions and Pydantic inputs: [tools/](src/datagov_mcp/tools/), [models.py](src/datagov_mcp/models.py); tool list in the [README](README.md#tools); design record [docs/decisions/0001-semantic-registry.md](docs/decisions/0001-semantic-registry.md) |
| **Innovation** | Readiness labels (what can be queried now vs. needs setup), compatibility checks before relating datasets, answer-first UI with guided next steps: [docs/RESEARCH_UI.md](docs/RESEARCH_UI.md), [src/datagov_mcp/readiness.py](src/datagov_mcp/readiness.py) |
| **Mission alignment** | Slide deck slides 2–3; climate and agriculture use case in [docs/SCIENCE.md](docs/SCIENCE.md) |
| **Presentation** | [submission/](submission/README.md) (deck, evaluation document, PDFs, screenshots); video demo submitted separately |
| **Security** | [SECURITY.md](SECURITY.md); evaluation document section 4; input-validation and fixed-route tests in [tests/test_datasets.py](tests/test_datasets.py) and [tests/test_catalog.py](tests/test_catalog.py) |

## Seeing the agent's actual behavior without the Apps

Each `*-eval-review.html` file in [eval/results/](eval/results/README.md) is a
self-contained page: download it and open it in a browser. For every question it
shows the agent's answer, every tool call with arguments and full results, the
automated numeric checks, and the AI reviewers' rubric scores with reasons. The
current-system runs are:

- `20261122T230301Z-eval-review.html`: core panel (12 questions)
- `20261123T161211Z-eval-review.html`: user-workflow questions (4)
- `20261123T161339Z-eval-review.html`: science and dataset-inventory panel (9)

Screenshots of the hosted research UI are in [submission/screens/](submission/screens/).
Logs of the live Databricks checks (data load, warehouse queries, App deployments,
hosted agent runs) are in [verification/](verification/README.md).

## Running it yourself (optional, no Databricks needed)

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
uv run python scripts/try_offline.py   # real MCP calls over stdio
make check                             # lint, 100 tests, security checks, build
```

`try_offline.py` starts the server, searches the live Data.gov catalog, queries
the packaged NOAA climate and USGS agricultural-practice datasets, and shows the
compatibility check. The Maryland county dataset needs a Databricks SQL warehouse;
without one the server reports exactly which settings are missing instead of
failing. The server also works with any MCP client (for example MCP Inspector or
Claude Desktop) by launching `uv run datagov-mcp`.
