---
title: "Security reporting and prototype boundaries"
description: "Private reporting and runtime boundaries for the hackathon prototype"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["docs/DATABRICKS.md", "AGENTS.md"]
---

# Security

Report potential vulnerabilities privately to the project owner through the
hackathon team's approved communication channel. Do not publish credentials,
exploit details or vulnerability reports in public issues. A dedicated reporting
contact will be selected when the repository destination is confirmed (BUILD-09).

This is a sandbox prototype, not an authorized production service. Runtime tools
read public metadata and an approved snapshot; loading is a separate operator
command. Hosted access relies on Databricks Apps OAuth and CAN USE grants.
The App's shared runtime identity must have SELECT-only access to curated data.
Evidence is shared public-data material within the same App access boundary.

The network client fixes the catalog origin, disables redirects and proxy inheritance,
validates TLS using the system/approved CA bundle, and caps response bytes and requests.
No tool follows distribution links. All source text is untrusted data.
