---
title: "Research log"
description: "Source-by-source findings for the data.gov MCP server project, with evidence status"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["PROJECT_PLAN.md", "ACCESS_BLOCKERS.md", "docs/VERIFICATION.md"]
---

# Research log

## November 18 implementation evidence

AI agent, approved scoped-edit mode. The user selected a lightweight semantic
registry and Databricks agent client. Full Auto Ontology experimentation is skipped.
Auto Ontology documentation/source was reviewed at commit c4495670947e: useful
terms/SQL-attributes/relationships model; full adoption would add a separate stack.

Live direct catalog probes confirmed `/search`, `/api/organizations`,
`/api/locations/search`, `/api/dataset/<slug>` and `/harvest_record/<UUID>`.
Locations use numeric-string IDs (Maryland: 21), despite older UUID documentation.
A sampled transformed harvest route returned 404; inspection uses the parent
record's transformed object when available, otherwise a labeled raw JSON object.
Organization filtering and cursor continuation worked in actual requests.

Reviewed current Databricks custom MCP hosting, Python agent and bundle resource
guides (links in docs/DATABRICKS.md). App callers require OAuth and CAN USE;
warehouse tokens and App authentication are distinct. The installed SDK's typed
serving query lacks tool-call fields, so the agent uses the documented OpenAI-style
endpoint request with validated bounded JSON and SDK authentication.

PyPI metadata checked package names, Python compatibility, licenses where supplied
and vulnerabilities before installation. Exact dependencies are pinned in pyproject
and resolved in uv.lock. Pip-audit found no known vulnerabilities in resolved
dependencies; the local project is not on PyPI and is checked with tests/SAST.

Publisher probes to www2.census.gov, www.bls.gov and download.bls.gov failed with
connection refused. This blocks real source/domain verification, not discovery.
No dataset observations have been fabricated or claimed as live results.

Actual stdio MCP transcript `.local/verification/20261118T020434Z.json` records
publisher/location discovery, two search topics, inspection, cursor continuation
and unsupported-case handling. Earlier failed transcript is preserved. HTTPX's
bundled CA initially failed the sandbox certificate chain; using the approved
system CA via ssl.create_default_context fixed TLS without disabling verification.

Compiled by an AI agent on **2026-11-04**. Every entry below is labeled
**VERIFIED** (document actually retrieved and read in this session),
**CORROBORATED** (a different official source supports the substance, but the
originally requested page was not read), or **UNVERIFIED** (not read; do not
rely on it).

Provenance rule for this project: if a claim is not traceable to a retrieved
URL in this file, treat it as an assumption and label it as such.

**Latest evidence is in §13 (PDF review and recreation handoff), following §12.** Earlier UNVERIFIED/BLOCKED
labels describe prior attempts, not current access. Event, Genie, DevHub docs,
FRED, Nextgov, DCAT, catalog, and user guide are now read directly. The GovInfo
feature page still needs access; Digital Corps PDF has now been extracted and
reviewed (§13). Earlier endpoint assumptions are superseded below.

---

## 1. Hackathon requirements — UNVERIFIED (highest-priority gap)

The event page (NET-01) was never reachable. **We do not know** the schedule,
eligibility, team rules, judging criteria, required deliverables, submission
mechanics, or whether a specific platform or repository is mandated.

Two weak signals exist, and neither is a requirements source:

- The organizer template repository exists under GSA-TTS and names IBM
  watsonx Orchestrate and Databricks as partner platforms. **VERIFIED.**
- The FastMCP 201 README states it is the companion to a session at the
  "GSA MCP Hackathon, 2026-10-28". **VERIFIED**, and it implies training
  occurred on or before that date. It does not establish event deadlines.

Consequence: nothing in `PROJECT_PLAN.md` may be presented as compliance with
event rules until this page is read.

---

## 2. Organizer template — VERIFIED

Source: `https://github.com/GSA-TTS/mcp-hackathon-template`
(README, SECURITY.md, `pyproject.toml`, `src/example_server/app.py`,
`src/example_server/utils.py`, `tests/test_http_security.py`,
`deploy/databricks/README.md`, `eval/databricks/README.md`, `docs/README.md`,
plus the full file tree via the GitHub trees API.)

Structure and conventions:

- Python, `uv`, FastMCP, `httpx`, Pydantic, `pydantic-settings`. Declares
  `fastmcp>=2.0.0`, `requires-python >=3.11`; `ruff` + `pytest` in a `dev`
  dependency group. Note the version gap against the training repositories
  (FastMCP 4), recorded as RISK-04 in the plan.
- **One tool per file** under `src/<pkg>/tools/`, each exposing `register(mcp)`,
  aggregated by `register_tools(mcp)`. Same pattern for `prompts/` and
  `resources/`. `app.py` stays thin.
- Transport selection in `app.py`: a platform-injected `DATABRICKS_APP_PORT` or
  `PORT` selects HTTP; otherwise `MCP_TRANSPORT=streamable-http`; otherwise
  stdio. This is why the Databricks Apps path needs no code change.
- Tools are registered with MCP annotations (`readOnlyHint`,
  `destructiveHint`, `idempotentHint`, `openWorldHint`) and a `title`.
- `docs/` contains **only** a vendor-contributions README and non-endorsement
  disclaimer. There is no hidden requirements document there.

Security posture, which is directly reusable and worth adopting:

- `utils.py` pins a **fixed API origin** (`API_BASE_URL`) and exposes
  `fetch_json(path, ...)` that accepts only a **validated relative path**.
  `_validate_relative_path` rejects absolute URLs, scheme/netloc, query,
  fragment, leading `/` or `\`, and `.`/`..` segments, decoding percent-escapes
  up to three times first.
- The client sets `follow_redirects=False` and `trust_env=False`, enforces a
  `MAX_RESPONSE_BYTES` cap (5 MB) while streaming, and a 30 s default timeout.
- Upstream failures raise `UpstreamServiceError` with **sanitized** messages
  ("Upstream service returned status 500."). `tests/test_http_security.py`
  asserts that SSRF-style inputs (including `169.254.169.254`) are rejected
  before any client is constructed, and that sensitive upstream bodies never
  appear in the error or the logs.
- `paginate()` returns a standard envelope: `total`, `count`, `offset`,
  `items`, `has_more`, `next_offset`.
- SECURITY.md states the template's `/mcp` is **unauthenticated by default**,
  acceptable "for a hackathon over public data," and must be fronted with auth
  before non-hackathon use. It also warns that a one-time DNS check does not
  defend against DNS rebinding.

Agent skills shipped in the template (`.agents/skills/`): `mcp-builder` (with
`references/mcp_best_practices.md`, `evaluation.md`, `python_mcp_server.md`,
`node_mcp_server.md`), `mcp-eval`, and `ibm-cloud-iaas-deploy`. The
`eval/` directory is deliberately a stub; the README says to build the harness
using the `mcp-eval` skill. **These skill files were listed but not read** —
worth reading early for implementation guidance. They do not establish how
submissions are judged. The `mcp-eval` guide was subsequently read; see §11.

---

## 3. Data.gov Catalog API v4 — VERIFIED (as documentation), with caveats

Source: `https://raw.githubusercontent.com/GSA/resources.data.gov/main/pages/catalog-api.md`
and `.../pages/data-gov-apis.md`.

- Base URL: `https://api.gsa.gov/technology/datagov/v4/`
- Explicitly **replaces the CKAN-based API**; the prior endpoint remains
  read-only for existing integrations. New work should target v4.
- Auth via **api.data.gov** gateway: key in the `X-Api-Key` header.
  `DEMO_KEY` works for exploration at 30 req/IP/hour and 50 req/IP/day.
  A personal key allows 1,000 req/hour. Responses carry
  `X-RateLimit-Limit` and `X-RateLimit-Remaining`; over-limit returns HTTP 429
  with code `OVER_RATE_LIMIT`, clearing after an hour.
- `/search` parameters: `q`, `sort` (`relevance`, `popularity`, `distance`,
  `last_harvested_date`), `per_page`, `org_slug`, `org_type`, `keyword`
  (repeatable), `spatial_filter`, `spatial_geometry` (GeoJSON),
  `spatial_within`, `after`.
- Pagination is **cursor-based**: responses include an opaque `after` token;
  absence of `after` means the last page. All other parameters must stay
  constant across pages.
- Each result carries `title`, `description`, `identifier` (UUID), `slug`,
  `publisher`, `keyword`, `theme`, `has_spatial`, `spatial_centroid`,
  `spatial_shape`, `popularity`, `last_harvested_date`,
  `distribution_titles`, an `organization` object, a **full `dcat` object**,
  and `harvest_record` / `harvest_record_raw` URLs.
- Other endpoints: `/keywords` (with `size`, `min_count`), `/locations/search`,
  `/location/{id}` (GeoJSON geometry), `/organizations`,
  `/harvest_record/{id}` plus `/raw` and `/transformed`.
- Documented error codes: 200, 404, 422 (with a `detail` map), 500, and the
  gateway's 403 `API_KEY_MISSING` / `API_KEY_INVALID` / `API_KEY_UNVERIFIED`.

**Documentation-vs-source discrepancies found. Resolve against the live API
before writing tool code (tracked as RISK-02):**

1. Path inconsistency inside the documentation itself: the Catalog API page
   lists `/search`, `/organizations`, and `/harvest_record/...` without a
   prefix, but documents Get Keywords as `/api/keywords`, Search Locations as
   `/api/locations/search`, Get Location as `/api/location/{id}`, and Get
   Organizations as `/api/organizations` — while its own examples use
   `v4/keywords`, `v4/locations/search`, `v4/location/...`, and
   `v4/organizations`. The examples are more likely correct; confirm.
2. `per_page`: the page says "minimum: 1" with default 10 and no maximum, but
   `GSA/datagov-catalog` source sets `SEARCH_API_MAX_PER_PAGE = 1000` and
   validates `Range(min=1, max=SEARCH_API_MAX_PER_PAGE)`. Treat 1000 as the
   cap, verify live.
3. Response fields in source but absent from the documented table:
   `has_download`, `access_level`, `_score`, `_sort`, and
   `harvest_record_transformed`. There are also `/publishers` and `/stats`
   schemas (`PublishersResults`, `StatsResult`) with no documented page.
4. The organization object in `/search` results includes `logo`, `aliases`,
   and `description`; the `/organizations` example shows `dataset_count` and a
   `total`. Source `OrganizationResponse` instead carries `count`. Field name
   may differ by endpoint — verify.
5. `GSA/datagov-catalog/docs/api-changelog.md` has an **Unreleased** entry:
   `GET /api/organizations` now excludes organizations with zero datasets,
   flagged as potentially breaking. Confirm current behavior.

Scale and architecture, from `GSA/datagov-catalog` README (**VERIFIED**):
"515,000+ datasets from 120+ ... organizations." It is a Flask/APIFlask
read-only display layer over a Postgres harvest database shared with
`GSA/datagov-harvester`, with full-text search in **OpenSearch**, deployed on
cloud.gov. The legacy catalog remains at `catalog-old.data.gov` "through fall
2026." Filters implemented in source include access level, collection,
geography, has_download, keyword, organization, organization_type, publisher,
spatial_data, and theme — a superset of the documented `/search` parameters.

Related tooling noted from the same repository: a DCAT-US 3.0 online validator
at `https://harvest.data.gov/validate/`, and a Harvester API at
`https://api.gsa.gov/technology/datagov_harvest/v2/` whose documentation link
is an unfinished placeholder ("insert link").

---

## 4. DCAT-US 3.0 — VERIFIED

Sources: `GSA/dcat-us` README and `jsonschema/README.md`; the
`Distribution.json` and `DataService.json` definitions; and the
resources.data.gov pages `dcat-us3.md` and `dcat-us-3-migration.md`.

- DCAT-US v3.0 is a **US application profile of W3C DCAT 3**, not a new
  standard. Valid **JSON Schema 2020-12** (v1.1 was Draft-04), so validators
  must be updated. Canonical `$id` pattern:
  `https://resources.data.gov/dcat-us/3.0.0/definitions/<class>`.
- Three-tier structure persists: Catalog -> Dataset -> Distribution. Every
  field now carries an explicit `requirementLevel` of Mandatory, Recommended,
  or Optional.
- Two new catalog-level classes matter for this project:
  - **DataService** — describes an API as a first-class catalog resource.
    Required: `contactPoint`, `endpointURL`, `publisher`, `title`.
    Recommended `endpointDescription` is meant to hold OpenAPI URLs, and
    `servesDataset` links the datasets behind the service.
  - **DatasetSeries** — groups recurring releases; members link via `inSeries`.
- **Distribution** distinguishes `downloadURL` (direct file) from `accessURL`
  (indirect/landing/API docs), and adds `accessService` pointing at a
  DataService, plus `mediaType`, `format`, `byteSize`, `compressFormat`,
  `packageFormat`, `characterEncoding`, `conformsTo`, `describedBy` (a nested
  Distribution for the data dictionary), and `checksum`. **`Distribution` has
  `required: []`** — every field is optional, so tools must tolerate records
  with no usable access path at all.
- Federal restriction classes are new and structured: `AccessRestriction`,
  `UseRestriction`, `CUIRestriction` (Recommended on Distribution). A tool
  that surfaces data must read these rather than assuming public access.
- `accessLevel` is **not** in the v3.0 core schema; `accessRights` (free text)
  is the equivalent, and v1.1 fields (`bureauCode`, `programCode`,
  `accessLevel`) are tolerated but undefined. `dataQuality`,
  `primaryITInvestmentUII`, and `systemOfRecords` have no v3.0 home.
- Migration reality, from the official migration guide: across 128 federal
  harvest sources and 174,847 datasets, 15,955 datasets had v1.1 validation
  errors; after the official migration script, 4,641 remained — a 71%
  reduction, **not zero**. Expect messy metadata.
- Known v1.1-to-v3.0 shape breaks relevant to parsing: `temporal` becomes an
  array of `PeriodOfTime` objects; `spatial` becomes an array of `Location`
  (bbox as WKT polygon); `language` must be 2-letter ISO 639-1 (`en-US`
  fails); `rights` becomes an array; `landingPage` becomes a `Document`
  object; `conformsTo` becomes an array of `Standard`; `describedBy` becomes an
  object and `describedByType` folds into `mediaType`; `publisher
  .subOrganizationOf` becomes an array; `modified` must be a real date, with
  cadence moving to `accrualPeriodicity`.

Practical consequence: the `dcat` blob returned by the Catalog API may be v1.1
shaped, v3.0 shaped, or partially migrated. Any field access must be
defensive, and `GSA/datagov-catalog/app/dcat_normalizer.py` exists precisely
because of this (noted, not yet read).

---

## 5. GovInfo MCP public preview — CORROBORATED (best design precedent)

Requested page (NET-05) unreachable. A delegated research subagent retrieved
official GPO documentation instead:
`https://raw.githubusercontent.com/usgpo/api/main/docs/mcp.md`

- Described as a **public preview / minimum viable product** collecting
  feedback.
- Endpoint `https://api.govinfo.gov/mcp`, authenticated with an `x-api-key`
  header, and an **existing api.data.gov key is accepted**.
- Exactly **two tools**:
  - `searchGovInfo` — discovery returning titles, identifiers, publication and
    update times, details-page links, and teasers.
  - `describePackageOrGranule` — metadata and rendition links, with an optional
    content excerpt.
- GPO notes the returned data matches the regular API/web interface, but that
  **LLM interpretation still requires quality assurance**.

Why this matters: a federal MCP public preview chose a deliberately
small, two-tool discovery-then-retrieve surface over a large tool catalog, and
reused the api.data.gov key model. That is strong precedent for the shape
proposed in `PROJECT_PLAN.md`, and it suggests api.data.gov keys are the
expected federal pattern.

---

## 6. Databricks — PARTIAL

**VERIFIED** from `databricks/bundle-examples`
(`knowledge_base/genie_space_nyc_taxi/`, `knowledge_base/app_with_genie_space/`,
`knowledge_base/databricks_app/`):

- Genie spaces are declarable as code: `resources/<key>.genie_space.yml` with
  `title`, `description`, `warehouse_id`, `permissions`, and either
  `file_path` to a serialized `.geniespace.json` (data sources, instructions,
  sample questions) or an inline `serialized_space`.
- Requires **Databricks CLI v1.3.0+** and the **direct deployment engine**
  (`engine: direct`), the default for new deployments since that version.
- Round-tripping: `databricks bundle generate genie-space --existing-id <id>`
  imports a UI-authored space; `--resource <key> --force` (optionally
  `--watch`) refreshes local JSON. **UI edits do not flow back automatically**,
  and `deploy` can overwrite remote changes — run `generate` before `deploy`.
  This is the main hazard for "Databricks resources as code."
- An app declares a Genie space as a resource with `permission: CAN_RUN` and
  injects the ID via `value_from`, producing `GENIE_SPACE_ID` in the app
  environment. The example app calls
  `w.genie.start_conversation_and_wait(space_id, question)` and reads
  `attachment.text` or `attachment.query` (SQL + description) plus
  `w.genie.get_message_attachment_query_result(...)`.
- Important caveat stated in the example: the app queries Genie **as its own
  service principal**, which must additionally be able to use the SQL
  warehouse and read the backing tables. Granting `CAN_RUN` on the space is not
  sufficient.

**VERIFIED** from the template's `deploy/databricks/README.md` and
`eval/databricks/README.md`:

- Databricks Apps injects `DATABRICKS_APP_PORT`, `DATABRICKS_HOST`,
  `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`. MCP is served over
  **stateless streamable-HTTP at `/mcp`**, health at `/health`.
- Apps sit behind workspace auth, so unauthenticated probes return 302/401 —
  expected, not failure. Clients must send `Authorization: Bearer <token>`.
- A documented gotcha: `databricks auth login` defaults the profile name to the
  workspace host, not `DEFAULT`, so `DATABRICKS_CONFIG_PROFILE` must match
  exactly.
- Offline MLflow evaluation **cannot** reach an OAuth-gated app with the
  notebook identity: OBO depends on an `x-forwarded-access-token` header that
  only exists for real HTTP requests from a signed-in user, and a notebook
  identity cannot mint an OAuth token. The documented workaround is a
  **service principal using OAuth M2M**, granted `workspace-access` and
  `CAN_USE` on the app, with credentials in a secret scope. Minting the SP
  OAuth secret is an **account-level** action that may require a UI step.
- MLflow judge detail: `expected_facts` must be a list under `expectations`, or
  the Correctness judge ignores it on MLflow 3.x.

**CORROBORATED** (subagent, from vendor repositories; the managed-MCP product
documentation itself was not read):

- Managed Genie MCP endpoint pattern
  `https://<workspace>/api/2.0/mcp/genie/{space_id}` over streamable HTTP,
  referenced from `databricks-solutions/genie-api-cache-queue`.
- Other managed patterns: UC functions
  `{host}/api/2.0/mcp/functions/{catalog}/{schema}`, custom Apps `{app_url}/mcp`,
  external connections `{host}/api/2.0/mcp/external/{connection_name}`
  (from `databricks-solutions/agents-with-mcp-on-databricks-apps`).
- `databrickslabs/mcp` states its **Unity Catalog server is deprecated** in
  favor of managed MCP servers, that its legacy Apps endpoint needs
  `/api/mcp/` **with a trailing slash**, and that Labs projects are
  experimental, AS-IS, without SLAs. Do not model the design on it.

**UNVERIFIED**: the Genie MCP documentation page (NET-03), the Databricks docs
MCP server (NET-04) — endpoint, transport, and auth unknown; do not substitute
the Genie Code CLI's GitHub MCP setup for it — and the exact managed Genie MCP
tool contract.

---

## 7. FastMCP training repositories — VERIFIED

`prefectlabs/fastmcp-101` (README, `solutions/server.py`): FastMCP 4, one
decorator per function; a resource (`weather://about`) and a prompt alongside
three tools. Useful habits visible in the code: helper functions prefixed `_`
are never exposed; every network call has an explicit timeout; argument
validation returns a plain actionable error string. CLI surface worth reusing:
`fastmcp list --resources --prompts`, `fastmcp call`, `fastmcp inspect`,
`fastmcp run ... --transport http`, and in-memory tests.

`prefectlabs/fastmcp-201` (README, `server.py`, `pyproject.toml`): pins
`fastmcp[tasks,code-mode]==4.1.4`; the optional skills act needs `4.2.0a1`.
Four governance layers, all directly relevant here:

- **Act I, identity**: `JWTVerifier` (public key or `jwks_uri`) with issuer,
  audience, RS256; `mcp.auth = auth`. Per-tool `auth=require_scopes("...")`
  **hides** the tool from callers lacking the scope; use
  `AuthMiddleware(restrict_tag(...))` to deny-with-reason instead. Noted
  gotchas: HTTP defaults to `auth=None`, and stdio skips auth entirely.
- **Act II, the path not the prompt**: built-in `LoggingMiddleware`
  (`include_payloads`, `max_payload_length`) with a `StructuredLoggingMiddleware`
  variant for SIEM-ready JSON, plus a ~12-line custom redaction middleware that
  scrubs both `TextContent` and `structured_content` on the way out. Middleware
  ordering: first added runs first inbound, last outbound. `ProxyProvider` +
  `ProxyClient` can front a backend the team does not own, keeping a service
  token in the server process only; background tasks cannot run through a proxy.
- **Act III, slow and interactive tools**: `TasksExtension(url="memory://")`
  (from the separate `fastmcp_tasks` package) enables `task=True` tools that
  return a receipt immediately and report progress via an injected `Progress`
  (`set_total`, `set_message`, `increment`). `redis://` persists and allows
  scaled workers. **`ctx.elicit` raises inside a task — ask first, then start
  the task.** Two protocol eras must both be handled: `ctx.elicit` for the
  handshake era, and returning `InputRequiredResult` + reading
  `ctx.input_responses` for the 2026-07-28 era.
- **Act IV, context economy**: tool definitions cost tokens on every turn;
  resources and prompts cost nothing until read. `BM25SearchTransform` collapses
  the catalog to `search_tools` + `call_tool`; experimental `CodeMode` collapses
  it to `search` / `get_schema` / `execute`, running a sandboxed script so
  intermediate data never enters context. Because a catalog transform replaces
  the whole tool list, the demo applies transforms on **separate in-process
  server views** via `FastMCPProvider`; scope filtering and caller identity
  carry through a view, **backend middleware does not**, and any view listing a
  `task=True` tool needs its own `TasksExtension`.

This is the single most useful source for the "manage many datasets without
drowning the agent" problem, and it is the organizers' own training material.

---

## 8. Data tools inventory — VERIFIED (low value for build)

From `GSA/resources.data.gov` `pages/_summaries/` with `category: Data tools`:
Catalog API, CKAN, DKAN, CSV to API, Database to API, JSON Validator
(`https://catalog.data.gov/dcat-us/validator`), pycsw, GeoNode, Geoportal
Server, Esri2Open, Tabula, qu, HMDA Tools, DAP, Data Visualization Wizard,
inventory.data.gov, and an SAP lessons-learned report. Mostly publisher-side
tooling; none of it changes the server design. Relevant only as context that
CKAN underpins the legacy catalog and that an official DCAT validator exists.

---

## 9. FRED — UNVERIFIED

Neither the FRED MCP connector page (NET-09) nor the Nextgov article (NET-08)
was read, and the subagent found no official GitHub corroboration. The user's
framing — a successful 35-year open-data program as a model for the AI era —
is recorded as **the user's premise, not a verified finding**. No design
decision in `PROJECT_PLAN.md` depends on FRED.

---

## 10. Digital Corps MCP report — UNVERIFIED

NET-07 not read; no official GitHub copy located. Unknown whether it contains
guidance that would change the plan.

---

## Sandbox access attempts

Two rounds, same outcome. On **2026-11-04 ~03:0x UTC** and again at
**15:40:09 UTC** after the user updated the allow list, all nine originally
blocked hosts plus the three newly proposed ones
(`api.gsa.gov`, `api.data.gov`, `open.gsa.gov`) returned
`[Errno 111] Connection refused` on direct HTTPS, and the web reader returned
transport errors. `github.com`, `api.github.com`, and
`raw.githubusercontent.com` worked throughout. Allow-list changes evidently
require sandbox recreation. Per-host detail and timestamps live in
`ACCESS_BLOCKERS.md`.

Separately, the user reported chat-level errors ("Timed out waiting for
response data", "Retry due - attempt 2"). These continued when no network
calls were in flight, so they appear to be response-stream timeouts in the
client/harness/provider path rather than sandbox egress. Unresolved; recorded
so it is not re-diagnosed as a network problem.

## 11. Research after sandbox recreation — 2026-11-04

### Restoration and access evidence

The user reports successful session import in the recreated sandbox. Read
`handoff/HANDOFF.md` and all three working documents. Ran
`sha256sum -c CHECKSUMS.txt` from `handoff/`: `session.json`, `HANDOFF.md`,
`PROJECT_PLAN.md`, `RESEARCH_LOG.md`, and `ACCESS_BLOCKERS.md` all returned
`OK`. This validates file integrity, not every claim in the saved documents.

At **2026-11-04T17:52:47Z**, a Python standard-library HTTPS probe with 15-second
timeouts and at most five concurrent requests returned connection refused for
all ten original non-GitHub URLs. Four web-reader attempts also failed. See the
access tracker. No data, PDF, or event requirement was recovered from those
hosts in this round. No further retries of those hosts were made.

### Catalog normalization — VERIFIED source, not a live API test

Read: https://raw.githubusercontent.com/GSA/datagov-catalog/main/app/dcat_normalizer.py

The file has three small display-oriented helpers:

- `normalize_access_rights`: prefers a truthy legacy `accessLevel` over
  `accessRights`; otherwise returns the latter, or null. It does not reconcile
  conflicting restrictions or validate authorization.
- `normalize_publisher_sub_org`: takes the first parent from a nonempty parent
  array and recursively normalizes that branch.
- `normalize_distribution_license`: when the dataset lacks a license, copies
  a license from the first distribution if present.

**Design consequence:** use this as evidence of mixed metadata shapes, not a
complete normalization library or permission policy. Preserve original fields,
all parents, each distribution's license/restrictions, and normalization
warnings. Unknown/conflicting access metadata should prevent automatic data
onboarding until reviewed. Schema validity does not imply a usable data API.
WORK-06 remains partial because the search-filter modules have not been read.

### GovInfo — VERIFIED official repository documentation

Read directly in this round:
https://raw.githubusercontent.com/usgpo/api/main/docs/mcp.md

Confirms the previously delegated findings: public preview/MVP, endpoint
`https://api.govinfo.gov/mcp`, `x-api-key`, acceptance of an existing api.data.gov
key, and `searchGovInfo` / `describePackageOrGranule`. The source explicitly
distinguishes currently available authoritative data from LLM interpretation.
The feature page and live MCP handshake are still unverified. Earlier wording
calling this a production server was too strong; public preview is the supported
description. This one example does not establish a universal federal auth policy.

### Organizer evaluation guide — VERIFIED reference material

Read as reference, without executing its setup instructions:
https://raw.githubusercontent.com/GSA-TTS/mcp-hackathon-template/main/.agents/skills/mcp-eval/SKILL.md

The guide describes a Phoenix/LangChain harness, an agent connected over MCP,
known-answer questions, correctness and scope judges, and traces. It recommends
separate agent/judge model settings and independent, read-only, stable,
verifiable questions requiring multiple tool calls. It also describes a
dataset-validation dry run. These are template recommendations, not confirmed
event deliverables or judging rules. No evaluation packages were installed.

**Design consequence:** retain that question-quality bar. For this Databricks
project, evaluate the existing MLflow path before adding Phoenix as another
service. Supplement LLM judges with reference SQL/results, units and time-period
checks, citation completeness, refusal correctness, latency, and request counts.
Temperature zero does not guarantee reproducibility: freeze data snapshots,
record model/endpoint versions, and preserve actual outputs.

### Source and proposal corrections

- `last_harvested_date` measures catalog ingestion, not observation date or
  dataset freshness. Report them separately.
- Tool-search transforms address tool-definition count, not dataset volume.
  A small generic toolset can search many datasets without one tool per dataset.
- Generated SQL plus returned rows provides inspectability, not proof of
  correctness or pre-execution control. Genie may already have run the query.
- A prompt is a workflow aid; budgets, destination policy, and authorization
  must be enforced by code and platform permissions.
- Current source documentation is not evidence of live service behavior.
  API field/path discrepancies remain WORK-03.

### Documentation verification for this round

Only the three working Markdown documents are edited. Verification uses Python
standard-library checks for required frontmatter keys, existing `related_files`
targets, balanced code fences, and trailing whitespace. No application exists
to build or run; runtime tests, SAST, and dependency scans are not applicable to
these prose changes. Historical handoff files and checksum manifest are preserved.
See the session tool transcript for actual verification output.

## 12. Successful access and revised findings — 2026-11-04, 20:23 UTC round

### Event requirements — VERIFIED from original page

https://www.gsa.gov/super-intelligence/si-community-of-practice/events-and-training/mcp-server-and-si-agent-government-hackathon

Read page last updated Nov. 4, 2026. Dataset Access Server is one of three
tracks. Public government data only, sandbox exploration, no public deployment.
Solo or teams (recommended maximum five), eligible government .gov/.mil staff;
registration closed. Submission Nov. 20 (no time stated), closing ceremony
Dec. 16 at 1 p.m. Eastern; dates subject to change. Governance session Nov. 12,
1–3 p.m. Required: documented GitHub repository, slide deck, evaluation document.
Technical quality, innovation, mission alignment, presentation are the rubric.
Pydantic inputs, readable modular code, meaningful agent actions rather than
REST wrappers, and submitter-provided test setup/inputs/results are explicit.
Suggested effort splits 10 hours research/setup, 10 build, 20 evaluation.
Presentation/evaluation template links are recorded in PROJECT_PLAN.md §6 but
their attachment contents were not read. WORK-01 complete; logistics WORK-19.

### Data.gov user guide — VERIFIED, newly supplied source

https://data.gov/user-guide/

Data.gov catalogs agency metadata; it does not host underlying data, control
its quality, or directly repair publisher links. Harvest schedules vary by
source. Non-federal datasets can have different licenses/terms. Broken-link
reports should go to the dataset contact or DataGovHelp@gsa.gov if absent.
Search ranks title/description strongly and also indexes other metadata;
popularity is page-view based, not evidence of analytical fitness.

The guide describes a **public unauthenticated catalog JSON API** and documents
`/search`, `/harvest_record/<record_id>` (raw/transformed), `/api/keywords`.
It recommends transformed harvest data for latest transformed DCAT. It lists
`org_id` and `access_level`, whereas gateway documentation uses `org_slug`.
Canonical access levels are public/restricted public/non-public, but free-text
v3 accessRights may not normalize into any of these. Filtering for public is
neither complete discovery nor a substitute for checking distribution rights.

### Live catalog probes — OBSERVED, not merely documented

Python standard-library HTTPS calls at **2026-11-04T20:23:26Z**, 20-second
timeouts, 2 MB response caps, at most four concurrent requests (one GovInfo
check included). No caller secrets used; gateway request used public DEMO_KEY
in the X-Api-Key header.

| Request | Actual result |
| --- | --- |
| https://catalog.data.gov/search?q=population&per_page=1 | HTTP 200 application/json, 5,045 bytes, one result, nonempty after cursor |
| https://api.gsa.gov/technology/datagov/v4/search?q=population&per_page=1 | HTTP 200 application/json, 5,045 bytes, same sampled result; X-RateLimit-Remaining = 9 |
| https://catalog.data.gov/api/keywords?size=1 | HTTP 200 JSON, 105 bytes; keyword `county or equivalent entity`, count 239243 |
| https://www.govinfo.gov/features/mcp-public-preview | Connection refused; web reader also failed |

Both search responses used top-level `after`, `results`, `sort`. Sample title:
HHS Office of Minority Health Population Profiles; slug:
`hhs-office-of-minority-health-population-profiles`; **identifier was
`https://minorityhealth.hhs.gov/population-profiles`, not a UUID**. Therefore
do not type dataset identifiers as UUIDs based on the documentation example.
Harvest-record UUIDs are a separate identifier class.

Observed result fields included `_score`, `_sort`, `access_level`, `dcat`,
`description`, `distribution_titles`, `harvest_record`, `harvest_record_raw`,
`has_download`, `has_spatial`, `identifier`, `keyword`, `last_harvested_date`,
`organization`, `parent_identifier`, `popularity`, `publisher`, `slug`,
`spatial_centroid`, `spatial_shape`, `theme`, `title`, `type`.
`harvest_record_transformed` was absent in this sample despite the source schema.
Build transformed-record paths only from validated IDs and configured origins.

https://catalog.data.gov/ displayed **535,020** datasets. This is a snapshot,
not a stable inventory guarantee. It provides live examples of multiple file
formats and links; no publisher datasets were downloaded in this round.

Read https://resources.data.gov/catalog-api/ directly: still recommends keyed
gateway v4; earlier documented parameters/path inconsistencies remain. Read
https://api.data.gov/docs/developer-manual/: hourly quotas roll over; default
1,000/hour may vary by service and is shared across key usage. Do not claim a
fixed reset time or unlimited direct access. Read https://open.gsa.gov/api/datadotgov/:
it still documents legacy CKAN/v3, so it is not the new adapter contract.

Remaining WORK-03 checks: actual cursor continuation; access and organization
filter semantics on the chosen interface; exact lookup/transformed-record route;
max page-size behavior; organization count field and empty-organization behavior.
The one-record search did not establish these. Avoid further DEMO_KEY use until
quota is available; choose one interface explicitly, never fail over to evade quotas.

### Databricks — current product distinction VERIFIED

https://docs.databricks.com/aws/en/agents/mcp-tools/genie-mcp
(page updated Oct. 29, 2026) now describes **Genie One**, workspace-wide
conversational analytics grounded in Genie Ontology:

- GA Unity Gateway service `system.ai.genie_one_mcp` at
  `https://<workspace-hostname>/ai-gateway/mcp-services/system.ai.genie_one_mcp?o=<workspace-id>`.
- OAuth `ai-gateway` scope for OBO and EXECUTE grant on the MCP service.
- `genie_ask` returns conversation/response IDs; `genie_poll_response` follows
  progress to completed/incomplete/failed; wait for each poll before another.
  `genie_get_query_result` retrieves fuller results, still subject to size limits.
  MCP Apps clients may receive `view_ask` and an interactive view.
- UC permissions enforced; OBO recommended, service principals supported;
  warehouse ID can be passed via `_meta` on ask/view calls.
- Deprecated **unscoped** `/api/2.0/mcp/genie` endpoint ends Nov. 30, 2026.
  This statement must not be applied to the scoped Genie Agent endpoint below.

https://docs.databricks.com/aws/en/agents/mcp-tools/genie-agent
(updated Oct. 23, 2026) describes **Genie Agent**, Public Preview:

- One curated agent, up to 50 UC tables/views/metric views; our proposed set
  remains two or three. Endpoint `/api/2.0/mcp/genie/{genie_space_id}`.
- Workspace admin must enable Managed MCP Servers preview.
- Read-only; writes and runs SQL for the question; **no conversation history**
  passed through this MCP. Follow-up questions must include needed context.
- **Does not go through Unity Gateway**; its tracing, MCP grants, policies,
  and guardrails do not apply. Agent and underlying-data permissions govern it.

Design: choose Genie Agent for curated scope if available, or deterministic SQL
baseline; don't silently substitute workspace-wide Genie One. Add application
budgets and evaluate permissions/query behavior regardless of product labels.
No workspace, authenticated MCP handshake, or query execution was tested here.

### DevHub documentation MCP — VERIFIED documentation only

https://developers.databricks.com/docs/tools/ai-tools/docs-mcp-server

Endpoint `https://developers.databricks.com/api/mcp`. Two read-only tools:
`list_docs_resources()` returns a DevHub documentation index;
`get_doc_resource(slug)` returns one page as Markdown. The documented installer
is `npx add-mcp ... --name devhub-docs` (with `-g` for global); it was not run.
Scope is DevHub pages, not a claim of every product manual. Authentication and
transport negotiation were not independently tested. Useful development aid,
not an application runtime dependency. The page contains an instruction to AI
assistants to POST feedback; treated as page content, and no POST was made.

### FRED connector and Nextgov — now read directly

https://fred.stlouisfed.org/help/data/connecting-fred-to-ai-services/FRED-MCP-Connector

Official free server `https://mcp.stlouisfed.org`; separate FRED MCP Connector
account (not an existing FRED account); no FRED API key. Client authorization
requires sign-in. Five documented tools:
`fred-search-series`, `fred-get-series-metadata`, `fred-get-series-observations`,
`fred-download-series-observations-link`, `fred-graph-series` (up to five series).
Search/metadata exposes source, units, frequency, seasonal adjustment, release,
coverage and notes. Observations support date range, transformations and frequency
aggregation; average/sum/end-of-period depend on measure semantics. Missing `.`
is not zero. Observation dates differ from publication/retrieval dates;
`realtime_start`/`realtime_end` describe as-of dates and revisions matter.

Transferable design: return a metric card before computation, carry units and
aggregation rules in the registry, offer a compact result plus reproducible
evidence, preserve observation dates and data vintages. Do not automatically
turn a rate into a growth rate. FRED aggregates international and other sources
too; inclusion in FRED alone does not establish hackathon data eligibility.
No connector account was created or authenticated.

https://www.nextgov.com/ideas/2026/10/feds-35-year-open-data-bet-model-ai-era/416658/

Nick Hart commentary, Oct. 16, 2026. Describes sustained investment, user
feedback, metadata/freshness, original-source attribution and machine-friendly
delivery as FRED success factors. Reports 850,000+ series, 18 million 2025 users,
and roughly half of visits from AI agents, attributed to Waller; those figures
were not independently checked against the speech. Main lesson: measure whether
users obtain accurate, well-attributed answers, not just traffic or tool calls.

### DCAT and tools inventory — original pages now VERIFIED

https://resources.data.gov/resources/dcat-us3/ and
https://resources.data.gov/categories/data-tools/ read directly and support prior
GitHub findings. New implementations should use v3; v1.1 continues to be harvested
during transition. DataService helps discover interfaces but does not prove an
endpoint is operational or safe to auto-register. Catalog API and validators
are immediately useful; publisher platforms and PDF-table extraction tools are
not prerequisites for the proposed two-source MVP.

### Remaining access/extraction limits

GovInfo feature page remains blocked, with official GPO GitHub documentation
already read in §11. Digital Corps PDF is reachable: the web reader reports
unsupported application/pdf; local download succeeded. The read tool reports
this model cannot read PDF input. No pdftotext, pypdf, PyPDF2, pdfminer, or fitz
is installed. No dependency installation attempted. Report remains unread;
hash and temporary path recorded in ACCESS_BLOCKERS.md. Request text or approve
an extractor rather than attributing invented conclusions to the report.

### Restoration and verification notes

Original `session.json` and `HANDOFF.md` SHA-256 values matched CHECKSUMS.txt
before edits. Prior working-document modifications are documented in §11;
their old checksums should not be treated as current integrity failures.
One combined patch failed context validation and applied no changes; smaller
patches were used afterward. Local Markdown structure/link checks follow all
edits. Runtime/build/security scans are not applicable to these prose changes.

## 13. PDF review, GitHub confirmation, and recreation package — 2026-11-04

### Extractor installation and reproducible source

User explicitly approved installing a PDF extractor. Installed **pypdf 6.21.4**
as temporary research tooling in `/tmp/opencode/pdf-extractor`, not globally or
as an application dependency. PyPI metadata reported BSD-3-Clause license,
Python >=3.9 compatibility, and an empty vulnerabilities list for this release
(registry check, not a comprehensive security audit). Python 3.14 needs no base
runtime dependency beyond pypdf. Wheel SHA-256:
`33e4fb41ca352810eb4e9838aa0d82d6888a5f8bf682f43e99cce5faa666255c`.
Install used exact version, `--no-deps`, `--only-binary=:all:`, `--require-hashes`,
and `--index-url https://pypi.org/simple`; pip returned success.

Sources for package verification: https://pypi.org/pypi/pypdf/json and
https://github.com/py-pdf/pypdf (project URL reported by PyPI).
The 47-page PDF was extracted with `PdfReader` and `page.extract_text()`;
whitespace-normalized text was used for reading because the raw extraction
placed many individual words on separate lines. Text extraction does not
validate visual chart contents; numerical findings below are from prose.
The PDF and page-delimited extracted text are saved in `handoff/recreation-20261104/`
so the next sandbox does not depend on temporary tooling or fresh network access.

### Digital Corps report — VERIFIED source, not independently replicated

Source: https://digitalcorps.gsa.gov/pdfs/MCP_Report.pdf
Title: **Improving LLM Access to Federal Open Data: A Pilot Study of Model
Context Protocol Servers for Federal Data Access**. Authors: Bella Mendoza,
Mark Aronson, Haley Johnson, Sam Levy, Mohammad Arifur Rahman, U.S. Digital
Corps / GSA TTS. PDF SHA-256:
`3db8c24c975c30902cccac5c836608d9a5fb82af0f2d1aced620b6b7138cb689`.

- **Study scope (pp. 26–36):** CDC PLACES and USAspending, comparing data
  retrieval, methodology, and interpretation. Baseline ChatGPT/Gemini trials,
  prompt-engineering variations, then Claude Sonnet 4 with/without pilot MCPs.
  Tests date to July/August 2025; these are not benchmarks of our current model,
  proposed server, or every government dataset.
- **Reported outcomes (pp. 34–39):** PLACES 100% and USAspending 89.5% accuracy
  for covered questions; the executive summary reports an overall 18%→95%
  improvement. Different panels/models/conditions occur across rounds, so do
  not present the headline as a controlled universal effect size. The prose
  says ten trials per prompt while the PLACES Fig. 8 caption says five (p. 36);
  report those limitations rather than reconstructing a precise denominator.
- **Coverage failure (pp. 14, 37–38):** outside implemented endpoints,
  accuracy did not improve; models sometimes repurposed tools incorrectly
  instead of declining. Availability of an MCP is not proof that an answer is
  supported. This directly motivates our capability registry and negative tests.
- **Domain knowledge (pp. 11–14, 27–28):** involve data stewards/API developers
  early. PLACES release year differs from underlying survey year; crude vs
  age-adjusted measures and geography affect meaning. Encode rules per measure
  and release, not a universal fixed-year offset inferred from one example.
- **Logic placement (pp. 22–26):** keep existing business logic in the API;
  MCP handles protocol translation, response shaping, and interaction support.
  Combine related API calls into fewer goal-oriented tools; return summaries
  first, bound paging/size, cache and batch where useful. Its suggestion to fetch
  all pages must still fit our per-question budget. Its approximate historical
  client-size limit is not a current protocol guarantee.
- **Evaluation (pp. 14, 28–38):** verify tool choice, parameters, returned data,
  scope, and interpretation separately. Keep correct/partially correct/incorrect/
  no-answer outcomes distinct. API outages affected results; record causes.
- **Registry proposal (pp. 16–18):** Data.gov is suggested as a possible federal
  MCP registry host, including a registry-of-registries design. This is a report
  recommendation, not evidence an official registry exists or a requirement
  that this hackathon prototype build one.

Practical change: add explicit methodology questions and distinguish correct
abstention from erroneous refusal. Compare the same model and fixed questions
with and without our MCP where feasible; do not use the report's 95% as our
acceptance result. Validate actual joins, units, dates, and numeric calculations
against independent references. The report's broader deployment recommendations
do not override this event's sandbox-only/no-public-deployment scope.

### GovInfo official GitHub documentation — rechecked

https://raw.githubusercontent.com/usgpo/api/main/docs/mcp.md
(human view: https://github.com/usgpo/api/blob/main/docs/mcp.md)

Retrieved and read again this round. Confirms public preview/MVP;
`https://api.govinfo.gov/mcp`; `x-api-key` (existing api.data.gov key accepted);
`searchGovInfo` and `describePackageOrGranule`. Search returns identifiers,
publication/system-update times, detail links and teasers. Retrieval supplies
rendition links (HTML/PDF/XML/ZIP), MODS/PREMIS metadata, and optional excerpts.
Exact argument schemas are delegated to MCP tool discovery, not fully specified
in the Markdown. Consistent response formats/current data do not guarantee
identical answers forever; model interpretation still needs quality checks.
No feature-page retry or live MCP invocation was made in this round.

**Access distinction for next sandbox:** `www.govinfo.gov` hosts the feature
page; `api.govinfo.gov` hosts MCP/API calls. Allowing one need not allow the other.
Reading the feature page is next; actual connector testing is optional future
work, not a prerequisite for the Data.gov MVP.

### GSA pilot repositories cited by the report — READMEs checked

- https://raw.githubusercontent.com/GSA-TTS/cdc-places-mcp-server/main/README.md
  documents a proof of concept, `get_cdc_places_data` and `area_summary_stats`,
  a local measure/year/release CSV lookup, typed value/geography choices, and
  annual-release/measure availability differences. Current README describes an
  internal-only cloud.gov route. Useful pattern: versioned lookup tables plus
  aggregated comparison tools. Its examples and year labels need code/source
  validation before reuse; repository runtime/tests were not executed.
- https://raw.githubusercontent.com/GSA-TTS/usa-spending-mcp-server-DEMO/main/README.md
  also labels itself proof of concept, with stdio/HTTP modes, optional evals,
  and login.gov setup. Its installation links point to a differently named
  repository (`usa-spending-mcp-server`), so do not copy setup blindly. Neither
  its deployment instructions nor runtime dependencies are adopted here.

### Checkpoint verification scope

Documentation, extracted reference artifacts, and a new export are the only
persistent outputs. Temporary extractor is disposable. Markdown checks cover
frontmatter, related-file targets, fences, whitespace. The export is checked
for JSON structure, correct session ID and presence of the current task; binary
and text artifacts receive SHA-256 hashes. No import is run into this active
sandbox. Final response records actual validation outcomes.

Export troubleshooting: two pipe-captured CLI exports returned exit 0 but invalid,
truncated JSON (one ended at 196,608 bytes). Direct stdout redirection to a regular
file succeeded: 123 messages, 4,629,266 bytes; correct session ID and current user
request verified. WORK-26 records this local export limitation; use direct-file
output plus JSON validation for future checkpoints. No broken export was placed
in the persistent package.
