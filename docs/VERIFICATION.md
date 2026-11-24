# Verification transcript

AI agent: GPT 6 Astra. Mode: scoped edit, owner-approved November 18, 2026.
Chronological record of checks, starting with the initial build. The cited logs
are published in [verification/](../verification/README.md); current evaluation
results are in [eval/results/](../eval/results/README.md). Earlier sections note
states (for example "no remote CI") that later work superseded.

## Observed checks

| Command/check | Observed result |
| --- | --- |
| `uv lock`, `uv sync --locked` | 108 resolved packages; 105 installed, Python 3.14.4 |
| `make setup` | Passed; locked dependencies available, pre-commit hook installed |
| `make check` at 02:09 UTC | Exit 0: lint, format, 41 tests, 13 Markdown documents, secrets, SAST, dependency audit, sdist/wheel |
| `make live` equivalent (`uv run python scripts/live_smoke.py`) | Passed actual stdio protocol + catalog calls; transcript 20261118T020434Z.json |
| Built wheel inspection | 31 entries; registry and SQL included; credentials/handoffs excluded |
| Built source distribution inspection | 63 entries; credentials/handoffs/local evidence excluded |
| `uv run datagov-setup-check` | Reports missing workspace coordinates/auth and absent analytic snapshot without values |

The final check after follow-on test/documentation changes is captured separately
under `.local/verification/`; test totals may increase from the initial pass above.
At this point no remote CI existed; GitHub CI was added later (BUILD-09) and now
runs `make check` on every push.

## Errors found and handled

- FastMCP exception conversion bypassed middleware's domain-error handler. Moved
  error conversion into signature-preserving tool wrappers; protocol regression passed.
- HTTPX bundled CA rejected the sandbox certificate chain. Explicit system SSL
  context honors the approved CA bundle while retaining certificate verification.
- Formatting and a deprecated MCP schema accessor were corrected.
- Secrets scanner identified a synthetic credential-shaped URL; the test now uses
  a username-only URL to exercise rejection without a password-shaped fixture.
- Bandit reports the required App bind and operator-controlled SQL identifier
  interpolation. Narrow B104/B608 annotations document reviewed cases. Local HTTP
  binds loopback; table identifiers are restricted to alphanumeric/underscore and
  all row values are bound parameters. Identifier rejection tests are included.
  Bandit emits advisory messages about these annotations but exits 0.
- Pip-audit reports no known dependency vulnerabilities. It cannot audit this
  unpublished project on PyPI; local source is covered by tests and SAST.

## Live boundary

### User OAuth update

Approved scoped auth update: shared named CLI OAuth selection for warehouse/agent,
static field-level setup hints, and a user-run login helper. Focused authentication,
configuration and warehouse tests passed (21 tests). Full post-update verification
is captured in a timestamped `-oauth-check.txt` under `.local/verification/`.

CLI `version` returned `Databricks CLI v1.26.0`; `auth login --help` confirms
`--host` and `--profile`. Official Linux ARM64 ZIP SHA-256:
`6a06c30e0a62e5cf9664f0a3b9b1e4805c1b5634cca854b3f9a1c34c112ed123`.
Release license is the Databricks License, allowing use in connection with its
services; binary installed in ignored `.local/tools/`, not redistributed. No
interactive login or workspace request was executed by the AI agent in this update.

Status at that time: BLOCKED pending network access. Superseded by the section below.

### Live Databricks vertical slice — November 18 (macOS, outside sandbox)

The files cited below are published in [verification/](../verification/README.md)
(owner email and name redacted); the full local log set stays in `.local/verification/`.

- `*-workspace-discovery.json`: PAT authenticates; warehouse running; catalogs and
  READY chat endpoints listed. Owner has ALL PRIVILEGES on `users.trevor_specht`.
- `*-source-validation.json`: real Census V2024 and BLS LAUS files hashed. Fixes:
  Maryland LAUS is `la.data.27.Maryland`; county series IDs carry 10 zeros; Census
  CSV is Latin-1. County sums equal state totals; BLS API v2 matches sample counties;
  2022–2024 M13 values have no footnotes (2025 is an 11-month average, excluded).
- `*-sql-dialect.json`: the former `compare.sql` ran on the warehouse; 0 mismatches vs. Python (historical; replaced Nov 22 by registry-generated SQL — see docs/RESEARCH_UI.md).
- `*-load.txt`: owner-approved 72-row load to `users.trevor_specht.county_indicators`.
- `*-stdio-warehouse-e2e.json`: stdio MCP → real table, evidence retrieved.
- `*-bundle-run.txt`: owner-approved App `mcp-datagov-semantic` deployed and running.
  App service principal granted USE SCHEMA + SELECT on the table only. First deploy
  failed (pip path is Python 3.11); staging now emits a uv project. Second crashed on
  App-injected bare `DATABRICKS_HOST`; config now normalizes bare hostnames.
- `*-agent-e2e.json`, `*-agent-discovery.json`: `datagov-agent` with user OAuth and
  `databricks-claude-opus-5` called the hosted App (analysis and discovery traces).
  Endpoint probing: several models reject `temperature`; the runner omits it.
  The local corporate TLS proxy required OS trust (`truststore`); verification on.
- `*-eval-panel.json`: 12-question panel plus A1/M1/U3 repeats (scoring pending).

## Change review and rollback

Context: three-day hackathon delivery, broad discovery and reviewed analytics.
Changes follow the approved plan: package, tools, registry, SQL, source preparation,
env configuration, App bundle, Databricks agent runner and evaluation documentation.
Security impact: fixed-origin outbound metadata access; new optional warehouse
connection; shared authenticated App access when deployed. Review grants first.
Rollback: restore the last reviewed wheel and manifest; preserve evidence. No
automatic deletion, force-push, workspace deployment or remote commit was performed.
