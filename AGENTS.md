---
title: "Data.gov MCP project instructions"
description: "Project-specific scope, commands, and verification boundaries"
status: canonical
tier: 1
last_updated: "2026-11-18"
related_files: ["PROJECT_PLAN.md", "README.md", "docs/DATABRICKS.md"]
---

# Project instructions

This project follows the installed universal behavioral contract. These instructions
add project context. Use one agent unless the user explicitly requests delegation.

- Public government data only, private authenticated sandbox deployment.
- Active scope: flexible catalog discovery, reviewed registry, Maryland Census/BLS
  comparison, Databricks model agent as client. Full Auto Ontology is out of scope.
- Tool modules live in `src/datagov_mcp/tools/` and register through `__init__.py`.
- Tool schemas, fixed-origin HTTP, registry dispatch and parameterized SQL are the
  execution boundaries. Never accept tool-supplied SQL, table names or download URLs.
- Configuration lives in ignored `.env`; `.env.example` documents fields. Do not
  read secrets into logs or overwrite user-filled values.
- `make setup` bootstraps; `make check` verifies; `make live` performs bounded real
  catalog requests through an MCP subprocess. `datagov-setup-check` reports presence.
- `PROJECT_PLAN.md` is the durable local tracker until a remote repository exists.
- `.local/verification/` contains timestamped actual outputs. Preserve failures.
- `handoff/` contains historical exports, is not publishable, and is never modified.
- Record warehouse/App/agent checks as BLOCKED until credentials and source files
  exist. Synthetic data tests are not evidence of a real federal-data result.
- Deployment and grants require review of concrete workspace resources. CI creation
  awaits explicit pipeline approval and repository details (BUILD-09).
