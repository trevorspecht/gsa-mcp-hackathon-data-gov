---
title: "Private research App"
description: "User-facing discovery, scientific series and evidence display"
status: draft
tier: 2
related_files: ["DATABRICKS.md", "SCIENCE.md", "EVALUATION.md"]
---

# Data.gov Research App

A separate Streamlit App, `datagov-research-ui`, calls the authenticated MCP App
through the same bounded agent runner used for evaluation (model configured in
the staged `app.yaml`). It has no direct warehouse
credentials or grants. App-injected OAuth credentials authenticate its service
principal. CAN USE was granted on `mcp-datagov-semantic`; model invocation works
through existing model-service access. An attempted extra model-service grant was
rejected because the operator lacks MANAGE; no broader privilege was added.

Catalog candidates are ranked by keyword overlap with the question (ties are
alphabetical); this is not semantic suitability ranking, and the answer must still
explain geography, years and measure compatibility.

## Interface layout (November 22)

Results appear in five tabs so the answer is not cluttered:

1. **Answer** — the model's answer only.
2. **Sources** — registered datasets actually queried (with publisher links), then
   other catalog candidates with readable metadata and availability. An optional
   toggle shows names and links only.
3. **Data & charts** — every completed query or change analysis, rendered
   generically from the result: change → bars by geography; observations →
   series by period (sparse periods shown as unconnected points); tables; caveats.
4. **Explore further** — select any ready registered dataset to preview its
   observations (optionally refreshing from a registered live publisher route),
   check geography/period compatibility, and run a suggested follow-up question
   that carries the original question forward. The follow-up answer appears in
   this tab below its button; the original answer and previews stay in place.
5. **Evaluation** — raw tool trace and the answer/evidence JSON download.

Charts and tables are built only from structured tool results. No model-generated
plotting code is executed; no correlation or causal chart is produced. Selection
does not make unregistered catalog datasets retrievable. The original question,
previews and follow-up persist only within the current UI session and reset when a
new question is asked; this is not general conversation memory.

## Hackathon judge access

On November 20, the owner approved and the operator verified `CAN_USE` for the
workspace `users` group on `datagov-research-ui`. Owner and inherited admin
`CAN_MANAGE` permissions were preserved. Judges who are members of this temporary
workspace can sign in and use the App at:

https://datagov-research-ui-7474654188777746.aws.databricksapps.com/

The reviewed local configuration is `config/hackathon-ui-permissions.json`.
Reapply only to this approved temporary workspace using an additive update:

```sh
databricks apps update-permissions datagov-research-ui -p hackathon --json @config/hackathon-ui-permissions.json
```

This does not grant direct MCP or warehouse permissions to workspace users.
Research executes through the UI service principal. An actual judge-account
session remains untested; workspace membership and App sign-in are required.
Do not carry this workspace-wide grant into another workspace without review.

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
`scripts/stage_ui.py` (see also the release procedure in docs/DATABRICKS.md). It writes a wheel, uv project/lock, launcher and non-secret
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
