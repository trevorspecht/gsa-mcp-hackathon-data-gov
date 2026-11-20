---
title: "Databricks sandbox and agent setup"
description: "Configure the warehouse, authenticated MCP App, and Databricks model agent"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["../README.md", "DATA.md"]
---

# Databricks sandbox and agent setup

Selected client: a **Databricks model agent**. The model calls our nine MCP tools;
our MCP server runs in an authenticated Databricks App and queries curated data
using the App service principal. This is shared access to public datasets, not
per-user Unity Catalog identity propagation.

## Portable configuration and releases

See [config-as-code and post-hackathon migration](PORTABILITY.md) for Terraform
prerequisites, a bundle target owning both private Apps, versioned model settings
and gated main-branch CI releases. No destination migration or deployment is
approved during preparation. Keep the legacy sandbox target for its current App
until its state ownership is explicitly transferred.

## Fill local configuration

### Email-code sign-in: local user OAuth

The project-local CLI is installed at `.local/tools/databricks-1.26.0/databricks`
(Linux ARM64, official release SHA-256 verified). For your own interactive login,
set these fields in the existing `.env`, preserving the warehouse ID:

```dotenv
DATABRICKS_HOST=https://YOUR-WORKSPACE-HOSTNAME
DATABRICKS_CONFIG_PROFILE=hackathon
DATABRICKS_TOKEN=
DATABRICKS_CLIENT_ID=
DATABRICKS_CLIENT_SECRET=
```

From an interactive terminal **in the project directory**, run:

```sh
export PATH="$PWD/.local/tools/databricks-1.26.0:$PATH"
uv run python scripts/databricks_login.py
```

The helper reads host/profile from `.env` without executing it as shell code, then
starts the official CLI's browser OAuth login. Open its sign-in URL if the sandbox
cannot launch a browser. Enter the email code on the Databricks page. The CLI stores
the profile and OAuth state in its normal user configuration, not in this repository.
If the browser redirects to localhost but cannot reach the sandbox's callback,
report that error; an interactive terminal alone does not establish browser callback
reachability. Device-code authorization is a separate workspace-admin-enabled beta,
not the email sign-in code, and is not assumed available.

After the CLI reports success:

```sh
databricks auth describe --profile hackathon
uv run datagov-setup-check
```

Do not run `auth token` to copy credentials into `.env`. The SDK uses the CLI profile
and refreshes OAuth credentials. Repeat the PATH export in each new terminal. The
setup check reports configuration presence only, not whether login is valid.
Catalog, schema and model endpoint can remain blank until workspace discovery.

Profile selection is explicit for both agent and warehouse. Mixing a profile with
a token/client credential is rejected; failed profile authentication never switches
to another method. Hosted Apps should leave the profile blank and use App-injected
OAuth service-principal credentials.

Sources: [User OAuth](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m),
[headless authorization](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-device-code).

Edit the existing ignored `.env`:

| Field | Value |
| --- | --- |
| `DATABRICKS_HOST` | HTTPS workspace origin |
| `DATABRICKS_WAREHOUSE_ID` | SQL warehouse ID, not its HTTP path |
| `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` | Existing curated-data location |
| `DATABRICKS_TOKEN` | Optional local warehouse token; not usable to call an App |
| `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` | OAuth M2M credentials, alternative to a local warehouse token |
| `DATABRICKS_MCP_URL` | App HTTPS URL with `/mcp`, available after deployment |
| `DATABRICKS_MODEL_ENDPOINT` | Available tool-calling chat-completions endpoint name |
| `DATABRICKS_CONFIG_PROFILE` | Named CLI OAuth profile for both local warehouse and agent access |

Run `uv run datagov-setup-check` to list missing settings without printing values.
The App automatically injects workspace host and OAuth client credentials.
Never copy local credentials into the deployment folder.

## Deployment resource review

`databricks.yml` and `resources/app.yml` propose one App and a reference to an
existing warehouse. Loading creates one Delta table in the configured existing
schema. Runtime needs warehouse CAN USE plus USE CATALOG, USE SCHEMA and SELECT
on that table. Loading uses separate operator write permissions. App callers need
CAN USE on the App. Review those concrete resources and grants before deployment.

Prepare/load the dataset using [DATA.md](DATA.md), then stage a minimal artifact:

```sh
uv run python scripts/stage_app.py
```

This stages the wheel, a uv `pyproject.toml` + `uv.lock` (Apps' pip path is
Python 3.11, below this package's 3.12 floor), app.yaml and, when available,
the reviewed loaded manifest. It excludes credentials, raw data and handoff exports.
An existing staging folder is never silently overwritten.

After installing a verified Databricks CLI and signing in, validate with explicit
bundle variables (the CLI does not automatically load this project's `.env`):

```sh
databricks bundle validate -t sandbox --var warehouse_id=YOUR_ID,catalog=YOUR_CATALOG,schema=YOUR_SCHEMA
```

After resource approval, deploy the bundle, then run its App resource using the
same variables. Record actual CLI output and confirm the resulting App URL.
Bundle validation and deployment are **not yet live-verified** in this workspace.

## Run the Databricks agent

The included runner uses a Databricks-hosted tool-calling model via its OpenAI-style
chat-completions interface and FastMCP as the MCP client. It can run in a terminal
or Databricks notebook environment with the project installed. It uses the same
wire protocol as Databricks agent frameworks without adding another agent framework
to the server environment. It is not a deployed Model Serving agent artifact.

```sh
uv run datagov-agent "Find federal datasets about water quality and inspect one."
```

The runner prints the answer and actual tool trace. It caps model turns (10),
tool calls (12), model output and overall run time (300 seconds). Source metadata
is treated as untrusted data. A final prose answer without a tool trace is not
evidence that MCP was used. Endpoint compatibility and the hosted flow require
live verification with the supplied workspace.

For the fastest interactive demo, the Databricks guide also describes App discovery
in AI Playground: an App name beginning with `mcp-` enables recognition. UI and
feature availability depend on the workspace.

## Run GPT-6.1 Sol through Responses

The agent supports explicit `AGENT_API=chat` (default) or `AGENT_API=responses`.
For the verified GPT-6.1 model service, configure these non-secret fields:

```dotenv
DATABRICKS_MODEL_ENDPOINT=system.ai.gpt-6-1-sol
AGENT_API=responses
AGENT_MAX_OUTPUT_TOKENS=4000
AGENT_REASONING_EFFORT=low
```

Use the existing user OAuth profile. If `.env` retains a PAT for operator tasks,
clear it for this command only (do not expose or copy tokens):

```sh
DATABRICKS_TOKEN= DATABRICKS_CONFIG_PROFILE=hackathon uv run datagov-agent "Compare Baltimore city's population and unemployment in 2022 and 2024."
DATABRICKS_TOKEN= DATABRICKS_CONFIG_PROFILE=hackathon uv run python scripts/run_eval.py
```

Responses uses client-held output items and `function_call_output` continuation,
not server-stored responses. Only advertised MCP functions can execute. The same
10-turn, 12-tool-call, 300-second and byte/context budgets apply to both APIs.
Completion status, usage and reported model identity are saved for every turn.
Incomplete/refused/empty output is not reported as a successful completed answer;
an incomplete result retains the answer/trace and exits with code 2. The evaluation
runner also preserves per-question timeouts and continues with the other questions.

The November 19 Sol smoke test completed assessment, a real warehouse comparison
and evidence retrieval through the deployed authenticated App. This is distinct
from the earlier synthetic protocol checks below.

## GPT-6.1 Responses investigation — November 19

Historical investigation results below preceded the implemented adapter above.
At investigation time the runner used Chat Completions only; protocol probes did
not constitute a completed evaluation panel.

Verified with user OAuth through this workspace:

- Opus 5.5, Sonnet 5.5 and GPT-6 Astra serving endpoints return access-disabled 403s.
- GPT-6.1 Chat Completions rejects reasoning plus function calls; setting reasoning
  to `none` also fails for Sol. Do not silently strip reasoning to force compatibility.
- The native Responses route is `/ai-gateway/openai/v1/responses`.
  Old `databricks-gpt-6-1-*` endpoint names return a 403 directing callers to model
  services. **`system.ai.gpt-6-1-sol` and `system.ai.gpt-6-1-terra` both work.**
- Both model services completed a synthetic function-call/tool-result round trip
  with `reasoning: {effort: low}` and an explicit output-token bound.
- Sol accepted all six actual MCP tool schemas with `strict: false`, called the
  authenticated App's `assess_comparison`, and summarized its real readiness result.
  This was a readiness probe, not a warehouse comparison or full panel.

Actual evidence: `.local/verification/20261119T050545Z-responses-roundtrip.json`
(failed old names), `20261119T050607Z-responses-model-services.json` (successful
protocol probes), and `20261119T050638Z-responses-mcp-readiness.json` (real MCP).

A future adapter should select Chat Completions versus Responses explicitly,
pass model-service names in the request body, translate MCP tools to Responses
function definitions, retain output items and append `function_call_output` using
its `call_id`. Preserve the local allowlist and existing tool/time/size budgets.
Record response status, incomplete details, model identity and usage; an incomplete
answer must not be scored as successful. Use client-held history within one answer:
Databricks documents `store` and `previous_response_id` as unsupported for these
pay-per-token models. This does not implement cross-question conversation memory.
No new SDK dependency is required; the verified probes used the existing HTTP client.

Source: [Databricks OpenAI Responses API](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-openai-responses).

## Source documentation reviewed November 18

- [Host an MCP server](https://docs.databricks.com/aws/en/agents/mcp-tools/custom-mcp)
- [Call MCP tools from Python agents](https://docs.databricks.com/aws/en/agents/custom-agents/use-mcp-tools)
- [Bundle resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources)

The hosting guide uses MCP SDK 2 while some agent-framework examples pin MCP SDK 1.
Our installed server and runner use FastMCP 4.2.1/MCP 2; do not install the older
framework example's dependency set into this same environment.
