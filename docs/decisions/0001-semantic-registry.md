# Use a reviewed semantic registry for bounded analytics

## Context and Problem Statement

The owner approved the scoped implementation plan on November 18. Submission is
November 20. Catalog metadata spans heterogeneous sources; meaningful computation
requires reviewed measures and compatible data. This AI-authored record documents
that approval for human review; it is not an ATO determination.

## Decision Drivers

- Deliver working discovery and one independently checked cross-source comparison.
- Keep data meanings, source vintages and unsupported operations explicit.
- Bound requests, execution time and result size independently of model behavior.

## Considered Options

1. Full Auto Ontology deployment with generated semantic definitions and NL-to-SQL.
2. Reviewed JSON registry, FastMCP discovery, and parameterized Databricks SQL.
3. Arbitrary live distribution fetching and query generation.

## Decision Outcome

Use option 2. FastMCP supplies protocol/client interoperability; HTTPX supplies
bounded asynchronous catalog transport; Pydantic validates configuration and tool
inputs; the Databricks SDK supplies native authentication and statement execution.
Pin direct dependencies exactly and commit the resolved lockfile. Use public
catalog search with an explicitly selected direct or gateway interface. Do not
download caller-selected distribution URLs. Keep historical handoffs out of Git.

### Positive Consequences

Broad discovery works while warehouse setup is pending. Reviewed metric IDs and
registry entries remain the only analytic dispatch path. Evidence is saved as bounded
JSON artifacts in an operator-configured local directory, with random IDs.

### Negative Consequences

New computations need reviewed definitions and query implementations. Local caches,
request budgets and evidence storage assume one server process; replica-wide state
requires a separate design. Evidence must be downloaded before an ephemeral App
restart if it must survive that restart.

### Compliance Consequences

Use a read-only warehouse identity for runtime and a separate operator identity
for loading. Proposed controls guide engineering; no authorization claim is made.
Hosted transport is permitted only behind the Databricks Apps authentication layer.

## November 18 user OAuth amendment

The owner explicitly approved user-profile authentication for local development.
Both the warehouse and Databricks model-agent client select the named profile with
SDK `auth_type=databricks-cli`. Profile plus explicit credentials is rejected; a
failed profile login cannot fall back to PAT/M2M. Hosted Apps continue using their
injected service principal. Browser/email verification is completed by the user.
The CLI is local disposable tooling, not an application/runtime dependency. Live
login and workspace permission validation remain pending.

## November 22 amendment: generic tools

The registry approach was extended: dataset-specific tools were replaced by nine
dataset-agnostic tools, and all dataset facts moved to `registry/datasets.json`
(measures, units, definitions, change rules, geography, sources and connector
type). Warehouse SQL is generated from validated registry identifiers with bound
parameters rather than per-dataset SQL templates. The decision drivers above are
unchanged.

## References

- [Organizer template](https://github.com/GSA-TTS/mcp-hackathon-template)
- [Auto Ontology](https://github.com/NVIDIA/auto-ontology)
