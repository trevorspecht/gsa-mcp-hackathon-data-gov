---
title: "Databricks sandbox and agent setup"
description: "Configure the warehouse, authenticated MCP App, and Databricks model agent"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["../README.md", "DATA.md"]
---

# Databricks sandbox and agent setup

Selected client: a **Databricks model agent**. The model calls our six MCP tools;
our MCP server runs in an authenticated Databricks App and queries curated data
using the App service principal. This is shared access to public datasets, not
per-user Unity Catalog identity propagation.

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

## Source documentation reviewed November 18

- [Host an MCP server](https://docs.databricks.com/aws/en/agents/mcp-tools/custom-mcp)
- [Call MCP tools from Python agents](https://docs.databricks.com/aws/en/agents/custom-agents/use-mcp-tools)
- [Bundle resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources)

The hosting guide uses MCP SDK 2 while some agent-framework examples pin MCP SDK 1.
Our installed server and runner use FastMCP 4.2.1/MCP 2; do not install the older
framework example's dependency set into this same environment.
