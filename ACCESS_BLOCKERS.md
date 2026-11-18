---
title: "Research access blockers"
description: "Sandbox network failures and the actions needed to resume source verification"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["PROJECT_PLAN.md", "RESEARCH_LOG.md", "docs/DATA.md"]
---

# Research access blockers

## Active build status — November 18

**Resolved 03:00–15:50 UTC Nov 18:** development moved to the owner's macOS host.
Workspace, Census and BLS hosts are reachable; see docs/VERIFICATION.md. The
sandbox observations below are historical.

### Workspace discovery attempt — 02:49 UTC

The user configured the workspace host, warehouse ID and personal access token;
setup validation now reports only catalog/schema missing. Read-only requests for
catalogs, serving endpoints and warehouse status all failed before an HTTP response.
One bounded diagnostic confirmed `ConnectionRefusedError`, errno 111, not a DNS or
certificate-verification error. Token validity and resource permissions remain
untested. Allow the hostname configured in `DATABRICKS_HOST` through sandbox egress,
then repeat discovery. This does not establish a Databricks service outage.
Sanitized observations: `.local/verification/20261118T024937Z-workspace-discovery.json`.
No workspace resources were modified. Tracked as BUILD-14.

- Catalog direct JSON search, organization lookup, location lookup and harvest
  inspection are reachable. Real MCP subprocess checks passed after explicitly
  using the sandbox-approved system CA bundle (`SSL_CERT_FILE`). TLS verification
  remains enabled; no proxy or certificate bypass was used.
- **Publisher data blocked:** bounded HTTPS probes to `www2.census.gov`,
  `www.bls.gov` and `download.bls.gov` returned connection refused. Required files
  and local-file preparation instructions are in `docs/DATA.md` (BUILD-04).
- **Workspace pending:** the user will populate `.env`. Warehouse, App deployment
  and Databricks model-agent verification remain blocked (BUILD-05/07/08).
- GovInfo feature access was resolved November 5; the page agreed with the saved
  GitHub public-preview/search-and-retrieval findings. NET-05 is resolved.

Historical observations below remain preserved and are superseded by this section.

Prepared by an AI agent at the user's request. First observed **2026-11-04**;
**re-tested 2026-11-04T15:40:09Z** after the user updated the allow list.

## Current status: report now read; GovInfo feature access still pending

**Latest round, Nov. 4:** User approved a PDF extractor. Installed pinned,
hash-verified pypdf 6.21.4 in a temporary target directory and read the 47-page
Digital Corps report. **NET-07 is fully resolved.** Persistent PDF and extracted
text are in `handoff/recreation-20261104/`; summary in RESEARCH_LOG.md §13.
GovInfo official GitHub MCP documentation was re-read successfully; NET-05's
feature page remains pending the user's next sandbox recreation. No retry of
that blocked page was made in this round. For later live MCP tests, the separate
host `api.govinfo.gov` may also need allowlisting; its access is not yet tested.

### Previous 20:23 UTC status (historical)

This section supersedes the historical failure table below. Verified by the AI
research agent after the user's latest sandbox recreation.

| ID | Latest result | Remaining action |
| --- | --- | --- |
| NET-01 | RESOLVED: event page retrieved and read | Confirm submission time/portal and participant-only updates; published due date Nov. 20, 2026 |
| NET-02 | RESOLVED: homepage read; direct search returned HTTP 200 JSON without credentials | Complete bounded contract checks |
| NET-03 | RESOLVED: supplied page documents Genie One; linked Genie Agent page also read | Confirm product availability/permissions in workspace |
| NET-04 | RESOLVED: DevHub docs MCP page read | Actual MCP connection not configured/tested |
| NET-05 | STILL BLOCKED: web-reader transport error; local HTTPS connection refused at 20:23:26Z | Allow www.govinfo.gov or provide page; official GitHub corroboration is available |
| NET-06 | RESOLVED: both DCAT-US3 and Data tools pages read directly | None |
| NET-07 | NETWORK RESOLVED; READING BLOCKED: PDF downloaded (2,380,128 bytes) | Supply text/Markdown or authorize a PDF extractor; model cannot read PDF input and no extractor is installed |
| NET-08 | RESOLVED: Nextgov article body read at canonical URL | Treat as commentary, not product documentation |
| NET-09 | RESOLVED: FRED connector documentation read | MCP host mcp.stlouisfed.org and sign-in not tested |
| NET-10 | RESOLVED: https://data.gov/user-guide/ read | Direct and gateway API contracts must be distinguished |

Additional hosts now reachable: `api.gsa.gov` v4 search returned HTTP 200 with
header-based `DEMO_KEY`; `api.data.gov/docs/developer-manual/` and
`open.gsa.gov/api/datadotgov/` were read. The latter describes legacy CKAN/v3.
`https://catalog.data.gov/api/keywords?size=1` returned HTTP 200 JSON.
The gateway reported `X-RateLimit-Remaining: 9`; no further gateway calls were
made. No rate header on the direct API does not imply unlimited use.

PDF temporary path: `/tmp/opencode/MCP_Report.pdf` (not a persistent handoff
artifact). SHA-256:
`3db8c24c975c30902cccac5c836608d9a5fb82af0f2d1aced620b6b7138cb689`.
No report-content claims have been made.

### Previous recreation attempt (historical)

**2026-11-04T17:52:47Z:** The user returned with an imported session after
recreating the sandbox. A bounded local HTTPS probe of all ten original
non-GitHub URLs (NET-01 through NET-09, including both NET-06 pages) still
returned `[Errno 111] Connection refused`. Web-reader requests to the event,
Genie MCP, Databricks docs MCP, and GovInfo feature pages also returned transport
errors. The cause is not established; these observations do not identify which
network component refused connections.

Official raw GitHub files remain accessible: the catalog normalizer, GPO MCP
documentation, and organizer evaluation guide were retrieved successfully.
The original handoff checksum verification passed for all five listed files
before this round's edits. The manifest remains a historical snapshot; the
three working documents now intentionally differ from those original hashes.

NET-01–NET-09 below retain their historical evidence and unresolved page-access
status. The additional API hosts were not re-tested in this round.

### Previous sandbox history

The user updated the allow-list file, and every host was re-tested. **All of
them still failed**, so the change had not taken effect in this sandbox
session. The user has since confirmed the sandbox must be **deleted and
recreated** for the new allow list to apply. A handoff package was written to
`handoff/` for that transition.

## Earlier recovery instructions (historical)

Re-run the probe in the recovery checklist below and update this file with the
new results. **Do not supply passwords or tokens in chat or in these
documents** — use environment variables. The highest-priority missing source
remains the hackathon event page: its requirements are still unverified.

| ID | Host | Requested resource | Observation (both rounds) | Recovery status |
| --- | --- | --- | --- | --- |
| NET-01 | www.gsa.gov | https://www.gsa.gov/super-intelligence/si-community-of-practice/events-and-training/mcp-server-and-si-agent-government-hackathon | Web reader transport error; local HTTPS connection refused | BLOCKED: event schedule, eligibility, judging, deliverables, and submission rules unknown |
| NET-02 | catalog.data.gov | https://catalog.data.gov/ | Same errors | PARTIAL: official catalog source and API documentation recovered on GitHub; live catalog unverified |
| NET-03 | docs.databricks.com | https://docs.databricks.com/aws/en/agents/mcp-tools/genie-mcp | Same errors | PARTIAL: official bundle examples recovered; managed Genie MCP endpoint pattern corroborated via vendor repos; product documentation still unverified |
| NET-04 | developers.databricks.com | https://developers.databricks.com/docs/tools/ai-tools/docs-mcp-server | Same errors | BLOCKED: docs MCP setup, endpoint, transport, and authentication unknown. Do not substitute the Genie Code CLI's GitHub MCP setup for this |
| NET-05 | www.govinfo.gov | https://www.govinfo.gov/features/mcp-public-preview | Same errors | CORROBORATED: official GPO docs read at https://raw.githubusercontent.com/usgpo/api/main/docs/mcp.md (endpoint, `x-api-key`, two tools). The feature page itself is still unread |
| NET-06 | resources.data.gov | https://resources.data.gov/resources/dcat-us3/ and https://resources.data.gov/categories/data-tools/ | Same errors | PARTIAL: exact page sources and related documentation recovered from GSA/resources.data.gov |
| NET-07 | digitalcorps.gsa.gov | https://digitalcorps.gsa.gov/pdfs/MCP_Report.pdf | Same errors | BLOCKED: report not read; no official GitHub copy located |
| NET-08 | www.nextgov.com | https://www.nextgov.com/ideas/2026/10/feds-35-year-open-data-bet-model-ai-era/416658/ | Same errors, including original newsletter URL | BLOCKED: article not read |
| NET-09 | fred.stlouisfed.org | https://fred.stlouisfed.org/help/data/connecting-fred-to-ai-services/FRED-MCP-Connector | Same errors | BLOCKED: official connector documentation not read; no official GitHub corroboration located |

The failures are consistent with a sandbox network restriction, **not proof of a remote outage or an authentication failure**. Code Mode HTTPS probes to GSA, Databricks docs, and Resources.data.gov also failed. TLS verification was never disabled; no third-party proxy was used.

## Separate issue: chat stream timeouts

The user reported repeated client-side errors: "Timed out waiting for response
data" and "Retry due - attempt 2 - Time out waiting for response data". These
**continued while no network calls were in flight**, so they appear to be
response-stream timeouts in the client/harness/provider path, not sandbox
egress. Cause unresolved. Recorded here so it is not re-diagnosed as a
network-allow-list problem. Tracked as WORK-12 / P-10.

## Additional access to validate next

These were proposed additions; all three were **tested in the 15:40:09Z round
and also returned `Connection refused`**:

| Host/resource | Why needed | Status |
| --- | --- | --- |
| api.gsa.gov | Documented Catalog API base: `https://api.gsa.gov/technology/datagov/v4/` | BLOCKED (tested 2026-11-04T15:40:09Z) |
| api.data.gov | API key registration and rate-limit documentation | BLOCKED (tested 2026-11-04T15:40:09Z) |
| open.gsa.gov | Data.gov API onboarding referenced by GSA documentation | BLOCKED (tested 2026-11-04T15:40:09Z) |
| harvest.data.gov | Official DCAT-US 3.0 validator at `/validate/` | NOT TESTED |
| User's Databricks workspace and its App host | Validate feature availability, identity propagation, and live MCP | NOT TESTED; host not supplied |
| Selected dataset publisher/API hosts | Download or query the eventual demo datasets | NOT SELECTED; approve exact origins rather than arbitrary outbound access |

## Hosts that worked

Confirmed reachable in both rounds:

- `github.com`: organizer template and both FastMCP training repositories.
- `api.github.com`: public repository discovery, file trees, metadata.
- `raw.githubusercontent.com`: official source documents and example code.

Observed limits: GitHub **code search** returned 401 without authentication,
and one repository-tree request returned 403 (rate limit). Repository search
and raw-file retrieval otherwise succeeded.

## Current recovery checklist

- [x] Re-probe all original non-GitHub URLs after recreation; failures recorded at 17:52:47Z. Additional API hosts still need a new check after network remediation.
- [x] Read the hackathon page; capture rules in PROJECT_PLAN.md §6–§7 (WORK-01).
- [x] Extract and read Digital Corps PDF; persist source/text (WORK-22 complete).
- [ ] Read GovInfo feature page after next sandbox recreation; official GitHub docs already rechecked (WORK-02).
- [x] Probe direct catalog search/keywords and keyed gateway search (WORK-03 remains partial).
- [ ] Resolve the documentation-vs-source discrepancies in RESEARCH_LOG.md §3: endpoint path prefixes, `per_page` cap, undocumented fields, organization count field, `/organizations` empty-org behavior.
- [ ] Obtain workspace coordinates through approved configuration; confirm cloud/region, Apps enabled, Genie, warehouse, CLI ≥ 1.3.0 (WORK-08).
- [ ] Update each NET row with actual results; preserve prior observations rather than overwriting them.

Related tracked work: WORK-01, WORK-02, WORK-03, WORK-04, WORK-08, and WORK-12
in `PROJECT_PLAN.md`. This file is the local durable access-issue record until a
remote issue tracker exists.
