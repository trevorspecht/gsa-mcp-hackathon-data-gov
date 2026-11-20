---
title: "Project plan: data.gov MCP server"
description: "Working plan, architecture options, open problems, and tracked work for a controlled-query MCP server over catalog.data.gov"
status: draft
tier: 1
last_updated: "2026-11-18"
related_files: ["RESEARCH_LOG.md", "ACCESS_BLOCKERS.md", "README.md"]
---

# Project plan: data.gov MCP server

## Submission update — November 20

Owner reports the deadline has been extended to **Monday, November 23, 2026,
11:59 p.m. Eastern Time**, superseding the November 20 deadline. The owner intends
to use the additional time to extend the project; specific additional features
remain to be selected. Preserve the verified baseline and rerun relevant evaluation
and technical review after changes. This extension does not confirm any change to
the temporary Databricks environment's expiration date.

Use the organizer's
PPTX and DOCX templates, downloaded to `.local/submission/templates/`. They are
worked CDC PLACES examples, not requirements to adopt Phoenix or copy example
scores. Adapt their sections using this project's actual evidence.

Next delivery scope requested: a private Databricks end-user App with appropriate
visuals; stronger topic-discovery/dataset-inventory examples; investigate up to two
scientific datasets for bounded supported queries; at least two additional evaluation
runs; then technical-quality review and final template-based submission materials.
Keep existing verified comparisons working, retain all evaluation attempts, and
separate future features from demonstrated capabilities. Review concrete new
workspace resources and grants before deployment. Preserve a portable archive
before the temporary Databricks environment expires.

## Latest delivery — November 19 evening

- Separate private `datagov-research-ui` deployed; successful live scientific
  question → MCP → answer/chart/table/download. No direct warehouse grants.
- Eight MCP tools now include fixed reviewed science capabilities and queries:
  NOAA Maryland climate plus USGS Chesapeake cover crops/tillage. Source methods,
  units and mismatched geography are explicit; no causal join supported.
- Additional rounds `20261119T232056Z` and `20261119T232423Z`: 9/9 completed each;
  five scientific responses per round independently match raw publisher data.
- Technical review: docs/TECHNICAL_REVIEW.md; 73 tests with UI extra, full checks
  pass. Documents are local drafts, not evidence of organizer submission.
- Submission deadline subsequently extended to November 23, 11:59 p.m. Eastern
  (owner update November 20). Portable backup must be copied off this machine
  before retiring the temporary environment.

## Answer-first user workflows — November 20

- Natural questions/list requests no longer require tool names or ranking requests.
  Agent uses readiness internally and keeps ranking mechanics out of normal prose.
- UI Answer & sources tab: answer first, used dataset cards before alternatives,
  readable linked metadata and charts. Evaluation & diagnostics tab isolates JSON
  traces/downloads. Optional names-and-links-only display available.
- Natural-input panel eval/user-workflows.json: first round 3/4 complete, Q1 had
  generic agent ValueError; retained. Q1 retry complete. Second round
  20261120T223719Z: 4/4 complete, automatic readiness in both list cases, Q1
  returned descriptive observations/evidence plus alternatives; no correlation
  coefficient invented. HTML evaluation reports generated; human scoring pending.
- 96 tests/full checks and UI tests passed. Local MCP and UI releases succeeded.
  Hosted natural relationship question completed; answer precedes used-source
  cards and alternatives. Diagnostics tab selection/download visible verified;
  download hidden on answer tab. No new grants/data loads or ownership changes.

## Ranked discovery readiness — November 20

- Ninth MCP tool assess_dataset_readiness inspects up to five harvest UUIDs,
  ranks candidates by explicit keyword overlap and distinguishes exact reviewed
  snapshot scopes from unverified API/file access routes. No generic retrieval.
- UI cards show ranking, readiness, scope and setup blockers independently.
- 94 tests and full make check passed. Live local MCP/catalog checks matched the
  NOAA NClimDiv parent to the narrow Maryland climate snapshot; other climate and
  water-quality records correctly remained access-unverified.
- Local MCP App deployment attempted twice; both failed before startup because
  Databricks could not authenticate the App for package repository settings.
  Initial UI release was held. Owner retry at 22:13 UTC succeeded; subsequent
  UI local release succeeded. Both Apps RUNNING/SUCCEEDED; browser UI → Sol → MCP
  readiness completed, showing reviewed NOAA Maryland scope vs unverified route.
  Workspace users CAN_USE verified preserved. Initial failures retained; platform
  root cause remains unknown. Keyword-score ties alphabetically order candidates,
  so the agent must still assess actual geographic/temporal/measure suitability.
- Prior staging archived in .local/staging-archive/20261120-readiness; source,
  tests, live observations and failing attempts retained. No App ownership change.

## Judge access — November 20

Owner-approved workspace `users` CAN_USE on the research UI App applied and
verified through the permissions API. Owner/admin CAN_MANAGE preserved; no direct
MCP/warehouse user grants added. Permission configuration is versioned in
config/hackathon-ui-permissions.json. Actual judge sign-in remains untested.

## Portable configuration — November 20

- Owner decision: keep configuration in versioned code and run approved deploys
  locally for the current hackathon workspace. Defer CI deployment setup and
  destination migration; the release workflow remains disabled. This decision
  does not itself authorize a deployment or transfer App state ownership.
- BUILD-15: Terraform prerequisites, portable bundle owning both Apps, explicit
  credential-free release settings and same-wheel staging implemented.
- Main release workflow waits for successful checks on the exact main SHA and is
  disabled until destination/OIDC/state adoption are explicitly configured.
- County analytics are omitted by default; destination-bound manifest attestation
  is required after separate verified bootstrap. Routine CI never loads data.
- No App/grant/data migration performed. Bundle validate may create workspace
  staging directories; initial shared-root validation passed, restricted-placeholder
  validation failed permission checks. Final schema validation is offline.
- Destination discovery, backend, federation, imports, model access, grants and
  first live migration remain BLOCKED pending post-hackathon review.
- Local full make check passed; Terraform init/validate and real same-wheel
  staging passed; both bundle files pass offline CLI schema checks. Repository
  deployment-enable variable is absent, so release CI is inert.
- Ownership/adoption instructions and verification boundaries: docs/PORTABILITY.md.

## Active build — November 18

The owner approved the three-day scoped implementation plan and project-local
tool installation. Mode: **scoped edit**, approved in this conversation. Build
broad catalog discovery plus a reviewed semantic registry and deterministic
Census/BLS comparisons. Maryland (including Baltimore city) is the starting
geography. Full Auto Ontology experimentation is explicitly skipped for this
submission. Databricks coordinates and credentials will be supplied via `.env`.
The owner selected a Databricks agent as the MCP client. A bounded model-agent
runner and authenticated App bundle are implemented pending live workspace checks.
Historical sections below preserve research, not current completion claims.

**Latest handoff:** `handoff/move-out-20261118/HANDOFF.md`. The owner is moving
development out of the network-restricted sandbox. Transfer the verified portable
archive described there; Git history now lives on GitHub (see BUILD-09). Re-establish credentials separately. Local PAT configuration
is format-valid; token validity remains untested because workspace requests were
refused before HTTP. User OAuth support exists but interactive login was not run.

| ID | Work | State | Completion evidence / trigger |
| --- | --- | --- | --- |
| BUILD-01 | Scaffold server, env, dependencies, setup/verify | LOCAL VERIFIED | make setup/check passed; wheel assets and exclusions checked |
| BUILD-02 | Flexible catalog search, inspection, vocabulary | LIVE VERIFIED (direct) | Real stdio search, inspection, vocabulary and cursor continuation; gateway/geometry execution still require checks |
| BUILD-03 | Reviewed metric registry and compatibility checks | IMPLEMENTED | Coverage/unit/period/unsupported tests pass; source methodology review requires BUILD-04 |
| BUILD-04 | Verify Census/BLS files and prepare snapshot | LIVE VERIFIED | Nov 18 03:05 UTC (`*-source-validation.json`): real files hashed; BLS Maryland file is `la.data.27.Maryland` (`.20` is 404); series IDs have 10 zeros; Census CSV is Latin-1. Parser fixed; 72-row reviewed snapshot `ad9580ad34ac9575d0867709` in `.local/data`; county sums equal state totals; BLS API matches sample counties |
| BUILD-05 | Configure warehouse and load curated snapshot | LIVE VERIFIED | Owner-approved load of 72 rows to `users.trevor_specht.county_indicators` (`*-load.txt`); stdio MCP comparison + evidence against real table (`*-stdio-warehouse-e2e.json`) |
| BUILD-06 | Compare indicators and persist evidence | LIVE VERIFIED | Real-table comparisons via stdio and hosted App; SQL dialect check 0 mismatches vs independent Python |
| BUILD-07 | Databricks App bundle and private deployment | LIVE VERIFIED | Owner-approved App `mcp-datagov-semantic` RUNNING; SP has USE SCHEMA + SELECT on table only. Fixes: uv-project staging (pip = Py3.11), bare App host normalization |
| BUILD-08 | Evaluation, demo and submission materials | DRAFTS READY | Private research UI verified; two climate/agriculture eval rounds 9/9 complete each. Organizer-template 12-slide PPTX + evaluation DOCX generated in .local/submission. Human proofreading, demo recording and final submission pending |
| BUILD-09 | Remote repo, license choice and CI configuration | DONE | Pushed to public `trevorspecht/gsa-mcp-hackathon-data-gov` (GPL-3.0 kept from the repo). CI `check` run 44350605532 passed on `main` |
| BUILD-10 | Live Databricks model-agent evaluation | SOL RUN COMPLETE; HUMAN REVIEW PENDING | Final Sol Responses panel `20261119T152023Z`: 18/18 complete, all 8 comparisons match reference, no incomplete outputs/tool errors. AI review: 13 correct / 5 correct abstentions; M2 citation criterion partial. New scored HTML ready. Earlier attempts and human Opus scores preserved; details in docs/EVALUATION.md |
| BUILD-11 | Gateway and spatial-filter live contract checks | TODO | Direct discovery already verified; gateway requires personal key, spatial filter requires bounded real geometry test |
| BUILD-12 | Finalize publisher catalog bindings and registry provenance | PARTIAL | BLS bound to Data.gov `DOL-BLS-3060-01`; no Vintage 2024 Census county-totals record exists on catalog.data.gov (only V2013–2019 API records), so Census stays null. Search cards still report queryable=false |
| BUILD-13 | Support user OAuth profiles for local warehouse access | LIVE VERIFIED | `databricks auth login --profile hackathon` completed on macOS (CLI 1.26.0, keyring storage); agent used it to call the App. OS trust store via `truststore` for the corporate TLS proxy |
| BUILD-14 | Enable sandbox access to the supplied Databricks workspace | DONE (moved to macOS) | Nov 18 02:56 UTC (`*-workspace-discovery.json`): PAT authenticates; 1 warehouse, catalogs users/workspace/models, 56 READY chat endpoints, existing `mcp-*` Apps. Previous: | User selected PAT for local discovery. Catalog/model/warehouse requests failed before HTTP; diagnostic confirmed connection refused (errno 111) at 02:49 UTC Nov. 18. Allow DATABRICKS_HOST hostname, then validate token and inventory resources. |


## Future feature — conversational memory

**Proposed; not implemented; outside the November 20 submission scope.** Retain
bounded, per-conversation history in the agent client so follow-ups such as
“do the same calculation for California” can inherit the prior metrics and years
while changing geography. Existing tool scope checks must still reject unsupported
requests; memory does not expand the registry's coverage.

Today, context is retained only within a single answer's model/tool loop. Each
CLI invocation and evaluation question starts fresh. Saved evidence is not
conversation memory, and the current panel does not demonstrate multi-turn use.
A future implementation should define session isolation, retention/reset behavior
and context limits, then add explicit multi-turn evaluation scenarios. Until then,
standalone evaluation questions should be self-contained; U2's “same comparison”
wording is a known ambiguity in the preserved panel.

Working document. Drafted by an AI agent on **2026-11-04** for the GSA MCP
Server and SI Agent Government Hackathon. Nothing here is approved yet.

> **Current status — 2026-11-04, 20:23 UTC research round:** event rules and
> most original sources are now read directly. Submission is **Nov. 20, 2026**
> (time unspecified); prototypes must stay in sandboxes and **must not be
> publicly deployed**. Required artifacts: documented GitHub repo, slides, and
> evaluation documentation. See §6 for rules and §13 for the current proposal.
> GovInfo's feature page remains unread; Digital Corps report is now reviewed
> (RESEARCH_LOG.md §13; plan additions in §14).
> Architecture choices remain proposals for discussion.

---

## 1. Goal

A user asks a plain-language question. An agent, through this MCP server,
finds relevant datasets across catalog.data.gov and returns an answer that
cites which datasets it used, with enough provenance that a reviewer can
check it.

### The hard part

The live catalog homepage displayed **535,020 datasets** in this research round;
the earlier repository README described 515,000+. These are time-specific
observations, not constants for code or tests. Three constraints follow:

1. **No uniform query surface.** The Catalog API searches *metadata*, not data
   values. Actual data sits behind heterogeneous distributions — CSV, ZIP,
   API endpoints, landing pages — and in DCAT-US 3.0 the `Distribution` class
   has `required: []`, so a record may expose no usable access path at all.
2. **Metadata quality varies.** The official migration guide reports 4,641
   datasets still failing validation after the v1.1→v3.0 migration script ran
   across 174,847 datasets. Field shapes differ between v1.1 and v3.0 records.
3. **Context economy.** Dataset count need not imply tool count. Use a small
   generic toolset, ranked metadata retrieval, and bounded results. Tool-search
   transforms address a separate problem if tool definitions themselves grow.

### Scope decision (recommended)

**Broad discovery, narrow execution.**

- *Discovery* works across the whole catalog via the Catalog API — search,
  filter, inspect metadata, inspect distributions.
- *Execution* (actually reading data values and computing an answer) is
  limited to a small, curated set of datasets with known schemas and
  validated joins.
- Datasets outside the curated set stay discoverable but are explicitly
  labeled **not queryable yet**, with the reason.

This is honest about the limits, demos well, and avoids the failure mode where
an agent confidently fabricates an answer from a dataset it could not actually
read. The GovInfo MCP preview (official repository documentation read) is
precedent: its public preview documents **two** tools — `searchGovInfo` and
`describePackageOrGranule` — rather than a large catalog.

---

## 2. Architecture options

### Option A — FastMCP server over the Catalog API only

Thin server; tools wrap `/search`, `/organizations`, `/keywords`,
`/harvest_record/*`. No Databricks.

- Cheapest and fastest; fewest moving parts; no identity propagation problems.
- Answers questions *about* datasets, largely not *from* them. Does not meet
  the stated goal on its own.
- **Verdict:** necessary foundation, insufficient alone. Build first.

### Option B — Catalog API + curated Databricks lakehouse (recommended)

Option A, plus: ingest a handful of curated datasets into Unity Catalog and
expose a bounded query tool. Start with deterministic parameterized analytics;
evaluate a curated Genie Agent as an extension using the same reference answers.

- Delivers real cross-dataset answers; uses the workspace the user already
  has; "Databricks resources as code" is satisfied via Databricks Asset
  Bundles (VERIFIED patterns in `databricks/bundle-examples`).
- Requires ingestion work, warehouse/permission setup, and careful identity
  handling. Genie's natural-language-to-SQL output needs verification before
  it is presented as fact.
- **Verdict:** recommended target. Keep the curated set small (2–3 datasets).

### Option C — Live federation at query time

Fetch and parse arbitrary distributions on demand.

- Maximum coverage in principle.
- Unbounded failure modes: arbitrary file sizes and formats, unknown schemas,
  SSRF exposure from following publisher-supplied URLs, and latency. The
  template's own security guidance warns specifically against passing
  tool-supplied URLs to an HTTP client, and notes a one-time DNS check does
  not stop DNS rebinding.
- **Verdict:** out of scope for the hackathon. Possible narrow exception:
  fetch a small, size-capped CSV from an **operator-allowlisted origin** only.

### Option D — Proxy/compose other federal MCP servers

Front GovInfo MCP (and others) via FastMCP `ProxyProvider`.

- Interesting composition story; FastMCP supports it (VERIFIED, Act II).
- Depends on third-party previews and adds credential-custody questions.
- **Verdict:** stretch goal only, if time remains.

---

## 3. Initial tool candidates (revised by §13)

This inventory predates the judging rubric. Keep vocabulary lookups and
distribution listing internal where possible; public tools should complete
user goals rather than mirror REST routes. The current proposal is in §13.

Deliberately small, following GovInfo's discovery-then-retrieve shape. Every
tool returns structured data with consistent keys and lets the model narrate;
every tool documents freshness and provenance in its docstring.

| Tool | Purpose | Notes |
| --- | --- | --- |
| `search_datasets` | Keyword/filter search over the catalog | Wraps `/search`; exposes `org_slug`, `org_type`, `keyword`, spatial filters, `sort`; returns cursor envelope |
| `describe_dataset` | Full metadata for one dataset | By `identifier` or `slug`; normalizes the `dcat` blob; surfaces access/use/CUI restrictions explicitly |
| `list_distributions` | What access paths exist for a dataset | Separates `downloadURL` vs `accessURL` vs `accessService`; reports `mediaType`, `byteSize`, and whether it is queryable here |
| `list_organizations` / `list_keywords` | Vocabulary for building good filters | Cheap; cacheable; helps the agent construct valid queries |
| `query_curated_data` | Natural-language question against the curated set | Databricks Genie or direct SQL; **returns generated SQL plus results**, never prose alone |
| `catalog_coverage` | What is and is not queryable, and why | Honesty tool; prevents fabricated answers |

Plus MCP **resources** (free until read): a `data.gov://about` provenance and
freshness statement; a curated-dataset dictionary; a DCAT-US 3.0 field guide.
And **prompts**: a "research a question across federal data" recipe that forces
search → describe → check restrictions → query → cite.

If the tool list grows past roughly 8–10, apply `BM25SearchTransform` on a
separate server view rather than trimming capability (VERIFIED pattern,
FastMCP 201 Act IV; note that a catalog transform replaces the whole tool list,
backend middleware does not carry through a view, and any view exposing a
`task=True` tool needs its own `TasksExtension`).

---

## 4. Performance and request management

- **Cursor pagination only.** `/search` returns an opaque `after` token; all
  other parameters must stay constant across pages. Never synthesize page
  numbers.
- **Respect the gateway.** `DEMO_KEY` is 30 req/IP/hour and 50/day; a personal
  key is 1,000/hour. Read `X-RateLimit-Remaining` and surface it; handle 429
  (`OVER_RATE_LIMIT`, clears after an hour) as a first-class, actionable error.
- **Cache aggressively.** Organizations and keywords change slowly; dataset
  metadata changes on harvest cadence. Cache with explicit TTLs and report
  `last_harvested_date` so answers can state staleness.
- **Cap everything.** Keep the template's 5 MB response ceiling, 30 s timeout,
  `follow_redirects=False`, `trust_env=False`, and fixed-origin
  `fetch_json(relative_path)` contract.
- **Separate ingestion from questions.** Run ingestion as scheduled/operator-run
  jobs. For slow queries, prefer backend query IDs and explicit status/cancel
  operations. Consider MCP Tasks only after checking client support and durable
  state; the training demo's in-memory task store loses state on restart.
- **Push aggregation down.** Let the SQL warehouse aggregate; return summarized
  rows, not raw dumps. Bounded SQL aggregation should suffice for the initial
  scope without experimental code execution.

---

## 5. Security and compliance posture

- **Public data only.** No PII, no CUI. Honor DCAT-US `accessRestriction`,
  `useRestriction`, `cuiRestriction`, and `accessRights` — a dataset marked
  restricted must not be fetched, and the tool should say why.
- **No tool-supplied URLs to the HTTP client.** Operator-controlled origins
  only; validated relative paths; percent-decode before validating. Keep the
  template's SSRF regression tests, including the `169.254.169.254` case.
- **Secrets via environment/secret scope.** The api.data.gov key goes in an env
  var, never in source, logs, errors, commits, or these documents.
- **Sanitized errors.** Never return upstream bodies, headers, full URLs, query
  strings, or stack traces. Keep `UpstreamServiceError`'s sanitized messages.
- **Private sandbox deployment.** The event prohibits public deployment.
  Verify authenticated App access and backing-table/warehouse permissions from
  the first hosted milestone. The template's unauthenticated default is not
  this project's hosted target. Local stdio remains useful for development.
- **Audit the path, not the prompt.** Add `LoggingMiddleware` (or
  `StructuredLoggingMiddleware` for SIEM-ready JSON) plus outbound redaction
  middleware so every call is logged with allowlisted fields.
- **Label AI-generated output.** Genie's SQL is a hypothesis; show it, let it
  be checked. GPO's own MCP documentation warns that LLM interpretation of
  authoritative data still needs quality assurance.

---

## 6. Verified event rules and required deliverables

Source: https://www.gsa.gov/super-intelligence/si-community-of-practice/events-and-training/mcp-server-and-si-agent-government-hackathon
(read directly; page last updated Nov. 4, 2026).

- **Track:** Dataset Access Server fits this project; alternatives are Service
  Read and Service Write integrations.
- **Scope:** sandbox environments; only already-public government data;
  prototypes will not be publicly deployed.
- **Eligibility:** government employees with .gov/.mil email, solo or teams;
  recommended maximum five team members. Registration is closed.
- **Deadline:** Friday **Nov. 20, 2026**; cutoff time and submission portal not
  stated. Closing ceremony Dec. 16, 1 p.m. Eastern. Dates subject to change.
  Remaining relevant training: MCP Server Governance, Nov. 12, 1–3 p.m.
- **Effort estimate:** research/setup 10 hours, initial build 10 hours,
  evaluation/improvement 20 hours. These are estimates, not requirements.
- **Judging:** technical quality (maintainability, performance/reliability,
  agent-oriented MCP design), innovation, mission alignment, presentation.
  Pydantic inputs, precise tool descriptions, and actual evaluation inputs and
  results are explicitly called out. Thin REST wrappers alone are discouraged.

| Required artifact | Required contents | Proposed evidence |
| --- | --- | --- |
| GitHub repository | Complete, documented MCP code | Reproducible setup/verify, private sandbox connection guide, IaC, metric registry |
| Slide deck | Problem, solution, technical approach/key decisions, demo | Cross-agency question, controlled comparison, citations, unsupported-case demo |
| Evaluation document | Methodology, metrics, security considerations, lessons/recommendations | Fixed question set, reference SQL, traces, cold/warm latency, failure analysis |

Organizer templates linked on the event page (contents not yet read):
[slides](https://www.gsa.gov/system/files/MCP-hackathon-sample-deck.pptx),
[evaluation](https://www.gsa.gov/system/files/MCP-hackathon-sample-evaluation-document.docx).
Repo visibility, cutoff time, portal, and participant-only updates need
confirmation. The page does not mandate a cloud vendor or evaluation framework.

### Proposed engineering deliverables supporting the required artifacts

1. A FastMCP server in the organizer template's layout, one tool per file.
2. A working client connection (Claude Code/Desktop via stdio; HTTP for remote).
3. Databricks resources as code: bundle YAML for the Genie space, the app, and
   the warehouse reference, round-trippable with `bundle generate`.
4. An eval harness built with the template's `mcp-eval` skill, with a small
   question set and recorded pass/fail.
5. Documentation: README, this plan, `RESEARCH_LOG.md`, `ACCESS_BLOCKERS.md`,
   and a short demo script.
6. A verification transcript: lint, tests, security checks, and live end-to-end
   output.

---

## 7. Phased approach

**Phase 0 — Confirm.** Event rules and small live API probes are done. Choose
one mission question, confirm private workspace access and submission logistics,
and finish the contract checks in RESEARCH_LOG.md §12.

**Phase 1 — Foundation.** Clone/adapt the template, rename the package, wire
`search_datasets` + `describe_dataset` against the live API with caching,
pagination, and sanitized errors. Tests green, lint clean.

**Phase 2 — Make it useful.** Add `list_distributions`, vocabulary tools, DCAT
normalization tolerant of both v1.1 and v3.0 shapes, and the resources/prompts.

**Phase 3 — Curated depth.** Pick 2–3 datasets that genuinely join (a shared
geography or time key). Ingest into Unity Catalog. Define the Genie space as
code. Add `query_curated_data` returning SQL + results. Add
`catalog_coverage`.

**Phase 4 — Prove and improve.** Auth, logging, and budgets start in Phase 1;
test throughout. Reserve roughly half the effort for evaluation/improvement,
including independent numeric checks and recorded live end-to-end outputs.

**Phase 5 — Polish.** Demo script, README, rollback notes, stretch goals
(GovInfo proxy, `BM25SearchTransform`) only if Phase 4 is genuinely done.

---

## 8. Open problems

| ID | Problem | Why it matters |
| --- | --- | --- |
| P-01 | Participant-only submission logistics unknown | Public rules are read; cutoff time, portal, repo visibility still need confirmation |
| P-02 | Which curated datasets? | Needs a real shared join key; drives the whole demo's credibility |
| P-03 | `dcat` blob shape varies (v1.1 / v3.0 / partial) | Naive field access will crash or silently mislead |
| P-04 | Genie accuracy and verification | NL→SQL can be confidently wrong; must show SQL and bound the schema |
| P-05 | Identity propagation | App service principal needs warehouse + table access, not just `CAN_RUN` on the space |
| P-06 | FastMCP version target | Template says `>=2.0.0`; training material pins 4.1.4; governance features assume 4.x |
| P-07 | Rate limits under demo load | A live demo can exhaust `DEMO_KEY` in minutes |
| P-08 | Distribution fetching boundary | Any real data fetch reopens the SSRF question |
| P-09 | Freshness semantics | `last_harvested_date` ≠ data currency; answers must not overstate |
| P-10 | Chat-level stream timeouts | Observed repeatedly; unexplained; could disrupt a live demo |

---

## 9. Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| RISK-01 | Missing participant-only submission updates | Confirm portal, cutoff time, repo visibility against saved public rules |
| RISK-02 | API contract differs from docs | Probe live before coding against exact fields; pin findings in the log |
| RISK-03 | Over-scoping to "all datasets" | Hold the broad-discovery/narrow-execution line; ship `catalog_coverage` |
| RISK-04 | FastMCP major-version mismatch | Decide the target version in Phase 1 and pin it |
| RISK-05 | Databricks bundle/UI drift | Review remote/local diffs; export intended UI edits before deploy; avoid blind force-overwrites |
| RISK-06 | Agent fabricates unsupported answers | Return SQL + rows; label non-queryable datasets explicitly |
| RISK-07 | Secret leakage | Env vars/secret scopes; redaction middleware; no keys in docs or logs |
| RISK-08 | Demo-day fragility | Cache warm paths; rehearse; have a recorded fallback |

---

## 10. Tracked work

Local tracker until a repository and issue tracker exist. Per the behavioral
contract, deferred and blocked work is tracked the moment it is named.

| ID | Item | State | Trigger / next step |
| --- | --- | --- | --- |
| WORK-01 | Read event page; align plan with rules | DONE | §6/§7 updated; remaining logistics in WORK-19 |
| WORK-02 | Read remaining original sources | PARTIAL | Report now read; only GovInfo feature page remains; GitHub docs rechecked |
| WORK-03 | Live Catalog API contract probe | PARTIAL | Direct search/keywords and gateway search succeeded; further checks in RESEARCH_LOG.md §12 |
| WORK-04 | Obtain a personal api.data.gov key via env var | TODO | Before any load beyond exploration |
| WORK-05 | Read template `.agents/skills/` (`mcp-builder` refs, `mcp-eval`) | PARTIAL | Eval guide read after recreation; builder references remain |
| WORK-06 | Read `GSA/datagov-catalog/app/dcat_normalizer.py` and search filter modules | PARTIAL | Normalizer read; preserve distribution-level rights; filter modules remain |
| WORK-07 | Choose curated datasets; document the join key | TODO | Phase 3 entry |
| WORK-08 | Confirm workspace: cloud/region, Apps enabled, Genie, warehouse, CLI ≥1.3.0 | TODO | Phase 3 planning |
| WORK-09 | Decide and pin the FastMCP version | TODO | Phase 1 |
| WORK-10 | Build the eval harness | TODO | Phase 4 |
| WORK-11 | Initialize git, set up one-command bootstrap/verify, CI | TODO | Phase 1 |
| WORK-12 | Diagnose chat stream timeouts | OPEN | Recurs; capture exact client/provider error text |

---

## 11. Questions for the user

1. **Submission logistics** — any participant-only updates on the Nov. 20
   cutoff time, submission portal, repo visibility, and demo duration?
2. **Subject matter** — is there a question you actually want answered? That
   choice drives the curated dataset selection (P-02) more than anything else.
3. **Databricks** — workspace URL/cloud/region, whether Apps and Genie are
   enabled for you, which SQL warehouse to use, and whether you can create
   service principals and secret scopes.
4. **Repository** — GitHub org/visibility, license, and whether the organizer
   template should be forked or vendored.
5. **api.data.gov key** — do you have a personal key? Provide it via an
   environment variable, not in chat.
6. **Platform constraint** — Databricks only, or is IBM watsonx Orchestrate
   also in play? It affects the deployment kit choice.
7. **Ambition** — polished narrow demo, or broader coverage with rougher
    edges?

## 12. Refined proposal after restoration

**Historical status at 17:52 UTC:** documentation proposal, not implementation
approval; original sites still failed then. The 20:23 UTC round restored most
access and supersedes that status; see §13 and RESEARCH_LOG.md §12.

### Recommended first demonstration

Choose one geography and a fixed, overlapping time period. Candidate stories
below are hypotheses: their exact catalog records, distribution URLs, licensing,
availability, and joinability have not been verified.

| Candidate | Potential sources | Question and main difficulty |
| --- | --- | --- |
| County economic change (first choice) | Census population estimates + BLS local unemployment | Which counties grew while unemployment fell over a chosen period? Align county FIPS, boundary vintage, denominators, and annual vs monthly measures. |
| Housing affordability | Census ACS + HUD rent estimates | Where is rent high relative to income? Align geographic units and years; medians and ACS multi-year estimates are not interchangeable. |
| Disaster exposure and population | FEMA declarations + Census population | Which counties had repeated declarations? Deduplicate county/disaster records; declarations do not measure physical damage or causal effects. |

Start with two sources; add a third only if it materially improves the answer.
For the chosen pair, record stable catalog IDs, publisher IDs, exact release,
data dictionary, common key, units, row grain, null rules, and expected output
computed independently. A discovery-only response remains useful when no
supported analytic route exists.

### Execution policy: make the control boundary explicit

The agent plans a question; the server validates a bounded request. Expose
dataset IDs and registered metric/filter names, not arbitrary URLs, tables, or
unrestricted SQL. Map IDs to approved Unity Catalog tables/views server-side.
Use parameterized values and allowlisted identifiers, with a principal that
can read only the curated analytic surfaces. Ingestion uses a separate identity.

**Recommended baseline:** deterministic parameterized analytic queries for the
demo's known metrics. **Genie extension:** a curated space for broader natural
language questions, evaluated against the same reference answers. Genie can run
SQL before returning it; showing that SQL afterward is not a pre-execution
approval or cost limit. Verify timeout/cancel behavior and warehouse/resource
limits before claiming controlled execution. Managed MCP, Conversation API,
custom Apps MCP, and docs MCP are distinct interfaces.

`describe_dataset` needs a verified lookup route: the listed Catalog API docs
do not establish a generic identifier/slug lookup endpoint. Initially it can use
the metadata already returned by search and a validated harvest-record reference.
Keep catalog, publisher, distribution, and harvest-record identifiers distinct.

### Initial budgets to test (proposed, not measured)

- Search: default 10 results, maximum 25 per tool response, at most 3 pages
  per question. Do not walk the whole catalog on an interactive request.
- Question: at most 3 supported datasets, 2 concurrent backend requests, and
  a 60-second deadline. Retry transient failures at most twice within that
  deadline, respecting rate-limit guidance; never retry a denied request.
- Results: at most 100 aggregate rows and 64 KiB serialized tool output;
  return explicit truncation/coverage flags. A SQL `LIMIT` bounds output,
  not scan cost—use approved queries, predicates, and backend controls too.
- Cache: begin with 15-minute search and 24-hour vocabulary TTLs; expose age.
  Key query caches by parameters, data snapshot/version, policy version, and
  authorization scope. Reuse public metadata caches without mixing query rights.
- Measure cold and warm paths separately. Initial targets: warm discovery
  under 3 seconds and curated answers under 30 seconds; verify before promising.

Every answer should carry dataset/distribution references, publisher, observation
period, source-modified time if known, catalog-harvest time, ingestion time,
snapshot/version, applied filters, metric definitions, SQL/query ID, row counts,
missing-source information, and limitations. Null timestamps remain unknown.

### Databricks resources as code

Use a bundle for App, ingestion Job, Genie space/serialized instructions, and
resource references supported by the installed CLI. The official examples call
for CLI 1.3.0+ and `engine: direct` for Genie; validate in this workspace. Keep
catalog/schema/warehouse names as configuration. Track table/view DDL and
transformations in source. Use secret references, not secret values.

Inventory existing resources before creating any. For resources not supported
by bundles, choose a single owner (existing workspace resource, Terraform, or
explicit SDK provisioning) after confirming the actual gap. Avoid managing one
resource through multiple state systems. Review UI edits before exporting or
redeploying; automatic `--force` is not a substitute for a diff review.

AI Gateway can govern model endpoints where configured; it does not replace
dataset permissions or SQL query budgets. The docs MCP server is a development
aid, not a runtime dependency for users' data questions.

### Definition of a credible MVP

1. A real client discovers and calls the registered MCP tools.
2. Broad metadata discovery returns source references and queryability status.
3. At least one question is answered from two real datasets with a validated
   join; numeric results match independent reference SQL within declared tolerance.
4. Unsupported data, incompatible grain/units, empty results, and upstream
   failures produce explicit, accurate responses rather than invented answers.
5. Boundary tests cover denied datasets, invalid filters, malicious metadata,
   output limits, rate limiting, and query timeout/cancellation.
6. Record latency, upstream-call count, result size, citations, and cold/warm
   cache state. Preserve actual live output; mocked tests are complementary.
7. Re-deploy supported resources from code and rerun the demonstration.

Use a compact evaluation set (initially 12 questions: 4 discovery, 4 analytic,
4 failure/unsupported cases). Prefer MLflow already available in Databricks
unless event rules require another system. Phoenix remains a documented option,
not an assumed requirement. Returning SQL alone does not satisfy correctness.

### Additional tracked work

| ID | Item | State | Dependency / completion evidence |
| --- | --- | --- | --- |
| WORK-13 | Confirm dataset pair, dictionary, join grain, reference answer | TODO | WORK-07; actual publisher/catalog records and independently checked output |
| WORK-14 | Specify controlled query policy and Genie execution boundary | TODO | WORK-08/13; demonstrated permissions, timeout, cancel, and output bounds |
| WORK-15 | Map each Databricks resource to its IaC owner | TODO | WORK-08; validate bundle support and review drift strategy |
| WORK-16 | Build broad-discovery tools and metadata normalization | PROPOSED | WORK-03/09/11 plus implementation approval; live search and contract tests |
| WORK-17 | Build curated ingestion and query tools | PROPOSED | WORK-13/14/15/16; reproducible snapshots and reference-matched answers |
| WORK-18 | Rehearse live demo and finalize submission artifacts | BLOCKED | WORK-01/10/17; actual rules, passing evaluations, recorded live outputs |

The next useful discussion is the target question and preferred dataset pair.
Implementation remains subject to an approved scoped plan; no code, credentials,
workspace resources, dependencies, or remote repository were changed here.

## 13. Current proposal after source access recovery

Prepared by the AI research agent on Nov. 4, 2026. This section supersedes earlier
tool/deployment assumptions. **Recommend broad metadata discovery plus controlled
cross-dataset comparisons over two curated public-government sources.** The
innovation is an explicit compatibility check and evidence trail that makes a
cross-agency answer reproducible, not the number of APIs wrapped.

### Goal-oriented MCP surface

| Proposed tool | User goal | Server-side work |
| --- | --- | --- |
| `find_data_for_question` | Find evidence relevant to a question, place, and period | Bounded catalog search, vocabulary resolution, deduplication, compact source cards with fit/coverage/queryability reasons |
| `assess_comparison` | Can selected measures be compared? | Check approved registry, geography/time grain, units, denominator, join cardinality, rights and freshness; return a bounded plan or specific incompatibility |
| `compare_public_indicators` | Perform an approved cross-source comparison | Parameterized query over curated UC views; registered metric/filter names, server-enforced budgets; return aggregates and evidence ID |
| `get_analysis_evidence` | Explain and reproduce an answer | Source/distribution URLs, versions, query/parameters, units, observation dates, caveats, missing-data and truncation flags |

Names and exact schemas are proposals, not implemented API contracts. Use
Pydantic models and unambiguous descriptions. A read-only resource can list
supported indicators and coverage; prompts assist the workflow but do not enforce
policy. Keep low-level organization/keyword/download lookup internal. This
directly addresses the rubric's warning against thin endpoint wrappers.

### Recommended demonstration and evidence

Retain §12's county population/unemployment candidate as first choice, subject
to actual catalog records, compatible years and a domain check. Pick one state
and two releases first. Show: ordinary-language question → source selection →
compatibility result → deterministic comparison → citations and limitations.
Then ask an incompatible/unsupported variant to demonstrate graceful handling.
No causal claim follows from a correlation or ranking.

Borrow FRED's metric-card approach: source, units, frequency, seasonal adjustment
where relevant, notes, missing-value meaning and revision/as-of date. A source
modified timestamp, catalog harvest time, observation period, and retrieval time
must remain distinct. A downloadable evidence artifact is a later enhancement,
not required to add a fifth tool now.

The user guide confirms Data.gov does not host the data or repair publisher
links. Queryability is therefore a capability of our registered adapter and
curated tables, not an intrinsic property of every search hit. Preserve
distribution-level terms; non-federal catalog entries are not uniformly licensed.

### Catalog transport choice

Both direct catalog search without auth and keyed gateway v4 worked in live
one-record probes. Make the origin/interface an operator-selected configuration;
default recommendation remains the documented v4 gateway for managed usage
after obtaining a key. A documented direct interface is viable for a sandbox
prototype if its terms/budget are confirmed. Never silently switch to evade
quotas. Use publisher identifiers as strings (a live result was a URL), separate
harvest-record IDs, and an explicit capability map for per-interface paths.

Search discovery is not authorization: free-text accessRights can fall outside
canonical filters. Registry onboarding must verify rights and working access;
missing data is not zero, and absent metadata is not permission.

### Genie and resources as code

For optional natural-language analytics prefer **Genie Agent** scoped to the
curated tables, not whole-workspace Genie One. Its MCP endpoint remains
`/api/2.0/mcp/genie/{genie_space_id}`, Public Preview, read-only, no conversation
history, and outside Unity Gateway policies/tracing. Confirm Managed MCP Servers
preview and permissions. Use application-level tracing and budgets; showing
generated SQL after execution is not pre-execution control.

Genie One is a separate GA service through Unity Gateway, with asynchronous
ask/poll and optional MCP Apps views. Its old **unscoped** `/api/2.0/mcp/genie`
endpoint retires Nov. 30; that date is not a documented retirement of the scoped
Genie Agent route. Do not mix those contracts. Documented features must still be
verified in this hackathon workspace/cloud/region.

Keep App, ingestion job and Genie definitions in bundles where supported;
review UI/bundle drift. DevHub docs MCP at `https://developers.databricks.com/api/mcp`
offers `list_docs_resources` and `get_doc_resource(slug)` for development.
Installation remains an explicit setup step; it is not a runtime dependency.

### Proposed schedule to November 20

Dates are planning targets, not claims of completed work; adjust to availability.

| Window | Outcome | Exit evidence |
| --- | --- | --- |
| Nov. 5–6 | Confirm question, dataset pair, API contract, workspace and repo; approve implementation plan | Source cards, join contract, reference answer, resource inventory |
| Nov. 7–10 | Build discovery and one two-source comparison; register all MCP dispatch points | In-memory tests plus real client/tool/warehouse smoke test |
| Nov. 11–15 | Evaluate/improve; add optional Genie only if baseline is solid | 12-question set, independent numeric checks, error/budget tests, latency and citation metrics |
| Nov. 16–18 | Freeze scope, prepare slides/evaluation report and rehearse | Reproducible sandbox deployment, live and recorded demo, documented failures/lessons |
| Nov. 19–20 | Final verification and submission | Repo, slides and evaluation ready before confirmed cutoff |

Use existing Databricks MLflow if suitable; the event does not require Phoenix.
Report cold/warm latency, correctness, provenance completeness, refusal accuracy,
upstream calls and output size. Compare deterministic baseline against any Genie
extension on the same questions. Reserve substantial time for fixes and reruns.

### Updated tracked work

| ID | Work | State | Completion condition |
| --- | --- | --- | --- |
| WORK-19 | Confirm submission portal/time, repo visibility and template contents | TODO | Participant instructions and organizer attachments reviewed; feeds WORK-18 |
| WORK-20 | Verify selected Genie product/preview and execution controls | TODO | Workspace tests distinguish curated Agent from One; feeds WORK-14/15 |
| WORK-21 | Specify goal-oriented tool contracts and metric cards | PROPOSED | Approved schemas map user goals to adapters and evidence; feeds WORK-16/17 |
| WORK-22 | Read Digital Corps PDF | DONE | 47 pages extracted; findings and limitations in RESEARCH_LOG.md §13 |
| WORK-23 | Optionally configure DevHub docs MCP | DEFERRED | User approves setup when implementation starts; endpoint/tools now documented |

WORK-01 is complete and unblocks submission planning. WORK-02 remains partial
only for the GovInfo feature page; PDF review is complete (§14). WORK-03 is
partial, no longer network-blocked.
Next decisions: choose the mission question/dataset pair and confirm workspace
coordinates, permissions, time budget, and participant-only submission details.

## 14. Report-informed refinements and restart checkpoint

The Digital Corps pilot supports the existing small-toolset/curated-execution
proposal. It also shows why unsupported questions must be evaluated explicitly:
models sometimes repurposed available tools to give wrong answers rather than
acknowledging missing capability. Its reported accuracy is evidence from a
limited 2025 pilot, not a performance promise for our implementation.

Refine the initial **12-question evaluation panel** to 3 discovery/retrieval,
3 methodology/compatibility, 3 supported cross-dataset comparisons, and
3 unsupported/failure cases. Maintain expected tool/parameter/data/interpretation
checks separately. Classify full correctness, partial correctness, wrong answer,
correct abstention, and erroneous refusal. Repeat key questions to measure
variability. When comparing MCP against a baseline, hold model, question set,
data snapshot, and scoring rules constant and disclose differing access tools.

Before onboarding a dataset, add a short domain review covering observation vs
release year, valid units/aggregation, geographic grain, missing values,
methodological caveats and supported comparisons. A versioned metric/release
lookup like the CDC pilot's is preferable to assuming universal year offsets.
Keep computational definitions in reviewed SQL/views or the owning API; the MCP
layer coordinates calls, validates requests and shapes bounded responses.

The report proposes Data.gov as a possible future MCP-registry host. This
prototype will not build a government registry or claim official status. It can
demonstrate the useful smaller idea: map selected catalog records to known,
supported query capabilities with transparent evidence and coverage boundaries.

| ID | Item | State | Completion evidence |
| --- | --- | --- | --- |
| WORK-24 | Add methodology and abstention scoring to evaluation design | PROPOSED | WORK-10 panel covers all four categories above; independent expected answers |
| WORK-25 | Domain review of chosen metric/release mappings | TODO | WORK-13/21: reviewer or authoritative documentation confirms semantic rules |
| WORK-26 | CLI session export truncates when pipe-captured | MITIGATED | Direct stdout-to-file export parses correctly; preserve workaround in handoff; root cause not diagnosed |

**Restart:** use `handoff/recreation-20261104/HANDOFF.md` for the latest package,
not the original `handoff/session.json`. Working documents are the source of
current project state. On return, verify checksums, read GovInfo's feature page
once access is enabled, reconcile it against the saved GitHub findings, then
confirm the target question and implementation scope with the user.
