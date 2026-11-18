---
title: "Contributing"
description: "Verification and review expectations for AI-assisted project changes"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["AGENTS.md", "SECURITY.md"]
---

# Contributing

Track scoped work in `PROJECT_PLAN.md` until the remote repository is configured.
Use branches and reviewed pull requests once that repository exists. Include
context, approved plan, verification output, rollback and security impact in PRs.
Disclose AI assistance at PR level. Human review is required before deployment.

Run `make check` and appropriate live checks. Never use invented or synthetic
observations as live evaluation results. Pin dependencies and update `uv.lock`.
Keep test fixtures synthetic and exclude `.env`, local artifacts and handoff exports.

The project license awaits owner confirmation (BUILD-09). No third-party source
files have been vendored; the organizer's layout and public documentation inform
the independently written implementation.
