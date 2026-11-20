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

Ranked readiness is **live in the hosted UI** as of November 20, 22:15 UTC.
Two initial MCP releases failed with Databricks App authentication errors while
loading package-repository settings; a later owner retry succeeded. The dependent
UI release then succeeded. A browser test completed UI → Sol → MCP readiness,
showing a reviewed NOAA Maryland scope and a separate unverified access route.
Workspace users CAN_USE remained intact. Keyword-score ties use alphabetical
ordering; this is not semantic suitability ranking, and the answer must still
explain geography, years and measure compatibility.

## Answer-first workflow

Users ask ordinary research questions or request dataset lists; they do not need
to name ranking tools. The agent assesses candidate readiness internally and
answers as far as verified observations allow, retaining explicit limitations.

The **Answer & sources** tab shows the answer first, then sources actually used
for completed data queries, other discovered candidates, and structured charts.
Source cards contain readable descriptions, coverage, periods, access/use terms,
formats, dictionary information and dataset links. Capability inspection alone
is not counted as data use. Ready alternatives can still appear among other
candidates; availability remains distinct from relevance. An optional names-and-
links-only display reduces metadata detail for list requests.

The **Evaluation & diagnostics** tab contains raw traces, ranking details and the
answer/evidence JSON download. No raw JSON cards clutter the normal answer tab.

The interface code provides:

- Plain-language questions and examples; each question starts fresh.
- Answers with source links and explicitly stated limitations.
- Deduplicated catalog cards with publisher, periods, access, dictionaries and
  distribution metadata. Curated capabilities are not mislabeled as search hits.
- Ranked inspected candidates with visible relevance matches and readiness labels.
  Ready applies only to exact reviewed snapshot scopes, not whole publisher datasets
  or guaranteed question compatibility. Unassessed cards are explicitly labeled.
- API/file links and advertised sizes remain unverified metadata. No generic
  downloads, public-database queries or invented wait estimates are offered.
- Separate county change bars (percent versus percentage points).
- Annual climate line charts; sparse practice observations are unconnected points.
- Accessible data tables and downloadable JSON containing the answer and evidence.

The interface does not execute model-generated plotting code. Chart values come
only from structured tool results. No cross-geography climate/practice correlation
or causal chart is produced. Source metadata remains untrusted.

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
