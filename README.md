---
title: "Data.gov Research MCP"
description: "Plain-language Data.gov discovery and evidence-backed queries of reviewed datasets"
status: draft
tier: 1
last_updated: "2026-11-23"
related_files: ["REVIEWERS.md", "PROJECT_PLAN.md", "docs/EVALUATION.md", "submission/README.md"]
---

# Data.gov Research MCP

An MCP server that lets an AI assistant answer plain-language questions with
public government data: search the whole Data.gov catalog, say which datasets can
be queried now, query reviewed datasets with units, definitions and sources, and
check whether datasets can be compared before relating them. Built for the GSA
MCP & AI Agent Hackathon (November 2026) and continuing as an ongoing project.
Public government data only; hosted use is confined to authenticated Databricks Apps.

> **Hackathon judges:** start with the **[reviewer guide](REVIEWERS.md)**. It maps
> each judging criterion to the evidence in this repository. The live Databricks Apps
> are not available to judges (the hackathon workspace is disabled November 30), so
> everything needed is here:
>
> - [Slide deck (PDF)](submission/pdf/Data.gov-Research-Hackathon.pdf) ·
>   [Evaluation document (PDF)](submission/pdf/Data.gov-Research-Evaluation.pdf) ·
>   [Evaluation summary charts (PDF)](eval/results/EVALUATION-SUMMARY.pdf)
> - [Every evaluation run](eval/results/README.md), with offline HTML pages showing
>   each answer and full tool trace
> - Try it without Databricks: `uv sync --locked && uv run python scripts/try_offline.py`

## Start

Requires Python 3.12+ and `uv`. From this directory:

```sh
make setup
uv run datagov-setup-check
uv run datagov-mcp
```

The default server uses **stdio**: an MCP client launches it and exchanges JSON-RPC
through standard input/output. Waiting silently for client input is normal.
Copy `.env.example` to `.env` only if `.env` does not already exist. Fill in
Databricks values there; never put credentials in client JSON or commit them.
The documented public direct catalog interface works without an API key.
Select `CATALOG_INTERFACE=gateway` and supply `DATA_GOV_API_KEY` to use v4 instead.
Transport selection is explicit; quota errors never trigger interface switching.

## Verify

```sh
make check  # lint, tests, documentation, secrets, SAST, dependency audit, build
make live   # bounded real catalog calls through an MCP subprocess
```

Live checks write timestamped observations under the ignored `.local/verification/`;
published deployment and data-load logs are in [verification/](verification/README.md),
summarized in [docs/VERIFICATION.md](docs/VERIFICATION.md). CI runs `make check`
and a Terraform validation on pushes and pull requests (`.github/workflows/check.yml`);
the separate release workflow is disabled until a destination workspace is configured.
To review agent answers visually, see [evaluation](docs/EVALUATION.md#run-and-review).

## Databricks agent

The client used here is a Databricks-hosted tool-calling model (configurable in
`.env`); any MCP-capable client can call the server. See
[workspace and agent setup](docs/DATABRICKS.md) and [source preparation](docs/DATA.md).
After the authenticated MCP App exists and `.env` is populated:

```sh
uv run datagov-agent "Find federal water quality datasets and inspect one."
```

The runner returns the model answer and actual tool trace. App calls require
OAuth; a local warehouse PAT cannot authenticate to a Databricks App.

For migration-ready Terraform prerequisites, both App bundle releases and gated
main-branch deployment, see [portable configuration](docs/PORTABILITY.md).
Deployment stays disabled until destination resources and identity are reviewed.

## Tools

All tools are dataset-agnostic. Dataset-specific facts — measures, units,
definitions, geography, periods, sources and connector settings — live in the
reviewed registry [registry/datasets.json](registry/datasets.json), not in tool code.

Discovery (any Data.gov dataset):

- `find_data_for_question`: bounded keyword/filter catalog search.
- `inspect_dataset`: inspect a harvest record with per-distribution terms.
- `suggest_search_filters`: resolve publisher, topic and location vocabulary.
- `assess_dataset_readiness`: rank inspected candidates and separate registered
  queryable datasets from unverified API/file routes.

Data (any registered dataset):

- `list_queryable_datasets`: registered measures, units, definitions, coverage.
- `query_dataset`: observations filtered by measure, geography and period;
  optional bounded live refresh where a fixed publisher route is registered.
- `analyze_change`: start-to-end change per geography using each measure's
  registered definition (percent or difference), with direction counts.
- `assess_compatibility`: geography/period/readiness overlap across datasets;
  never computes correlations or causal estimates.
- `get_analysis_evidence`: retrieve saved query, parameters, sources and result.

Generic connector types: `warehouse` (reviewed Databricks table, SQL generated
from registry identifiers with bound parameters), `packaged_snapshot`, and an
optional fixed-route `publisher_csv` live refresh. Tools never accept SQL, table
names or URLs. Adding a dataset means adding a reviewed registry entry and, if
needed, a parser — not a new tool.

The resource `data.gov://capabilities` lists registered datasets and setup status.
A catalog match is not proof of analytic compatibility.

## Research interface and science example

The separate private **Data.gov Research** App shows each answer first, then tabs
for sources, data and charts, guided exploration (select datasets, preview data,
check compatibility, run a suggested next step) and the full tool trace. See
[UI setup](docs/RESEARCH_UI.md). Conversation memory is not implemented.

The current registry contains five worked examples: Maryland county population and
unemployment (Census/BLS, warehouse), Maryland annual temperature and precipitation
(NOAA, with live refresh) and Chesapeake watershed cover-crop and tillage estimates
(USGS). The different geographies must not be joined for causal claims. See
[scientific scope and units](docs/SCIENCE.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/datagov_mcp/` | MCP server, tools, agent runner and research UI |
| `registry/` | Reviewed dataset registry and packaged science snapshot |
| `data/` | Raw public source files and the reviewed county snapshot |
| `eval/` | Question panels; `eval/results/` holds every run, review page and score |
| `verification/` | Published live deployment, data-load and hosted-agent checks |
| `submission/` | Hackathon slide deck, evaluation document, PDFs and screenshots |
| `REVIEWERS.md` | Guide for judges: where to find evidence for each criterion |
| `databricks.yml`, `resources/`, `infra/` | Databricks bundle and Terraform configuration |

`.local/` (git-ignored) holds credentials-adjacent and generated material: CLI
binaries, App release staging folders built by `scripts/stage_*.py`, the App's
evidence cache, organizer templates and the full local log set.

## Status and ownership

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for current status and next steps. Licensed
under GPL-3.0. AI-generated code requires human review before deployment. Setup does
not create workspace resources.
