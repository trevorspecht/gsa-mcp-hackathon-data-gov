---
title: "Private research App"
description: "User-facing discovery, scientific series and evidence display"
status: draft
tier: 2
related_files: ["DATABRICKS.md", "SCIENCE.md", "EVALUATION.md"]
---

# Data.gov Research App

A separate Streamlit App, `datagov-research-ui`, calls the authenticated MCP App
through the same bounded Sol agent used for evaluation. It has no direct warehouse
credentials or grants. App-injected OAuth credentials authenticate its service
principal. CAN USE was granted on `mcp-datagov-semantic`; model invocation works
through existing model-service access. An attempted extra model-service grant was
rejected because the operator lacks MANAGE; no broader privilege was added.

The interface provides:

- Plain-language questions and examples; each question starts fresh.
- Answers with source links and explicitly stated limitations.
- Deduplicated catalog cards with publisher, periods, access, dictionaries and
  distribution metadata. Curated capabilities are not mislabeled as search hits.
- Separate county change bars (percent versus percentage points).
- Annual climate line charts; sparse practice observations are unconnected points.
- Accessible data tables and downloadable JSON containing the answer and evidence.

The interface does not execute model-generated plotting code. Chart values come
only from structured tool results. No cross-geography climate/practice correlation
or causal chart is produced. Source metadata remains untrusted.

## Local use

```sh
uv sync --locked --extra ui
DATABRICKS_TOKEN= DATABRICKS_CONFIG_PROFILE=hackathon uv run --extra ui streamlit run src/datagov_mcp/research_ui.py
```

Keep the local server loopback-only when configuring an explicit bind address.
The hosted App's authentication is provided by Databricks. This is not a
production deployment or an approval to expose an unauthenticated server.

## Reproduce the private deployment

After reviewing the concrete App and caller permissions, stage using
`scripts/stage_ui.py`. It writes a wheel, uv project/lock, launcher and non-secret
App configuration to `.local/ui`. It refuses to overwrite an existing staging
folder; archive that folder before rebuilding. Import the folder into your own
workspace path, start the App compute and deploy it. No credentials, data files,
evaluation transcripts or human reviews belong in the staging folder.

The current deployment uses the existing `mcp-datagov-semantic` App and
`system.ai.gpt-6-1-sol`. For another workspace, configure those destinations before
staging and review new grants. No warehouse resources are created by UI staging.

## Migration

UI dependencies are an optional package extra. The Streamlit UI and MCP server can
run outside Databricks; the agent authentication/model adapter and warehouse backend
still require replacement and verification. Preserve the raw source files,
normalized snapshots, evidence and evaluations before this workspace expires.
Do not assume App filesystem evidence survives restart. Download evidence promptly.
