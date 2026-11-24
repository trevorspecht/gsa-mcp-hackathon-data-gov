---
title: "Security reporting and prototype boundaries"
description: "Private reporting and runtime boundaries for the hackathon prototype"
status: draft
tier: 2
last_updated: "2026-11-23"
related_files: ["docs/DATABRICKS.md", "AGENTS.md"]
---

# Security

Report potential vulnerabilities privately to the repository owner (GitHub:
trevorspecht), not in a public issue. Do not publish credentials or exploit details.

This is a sandbox prototype, not an authorized production service. Runtime tools
read public catalog metadata and reviewed registry datasets (a warehouse snapshot,
packaged snapshots and fixed-route publisher files); tools never accept SQL, table
names or URLs. Loading is a separate operator command. Hosted access relies on Databricks Apps OAuth and CAN USE grants.
The App's shared runtime identity must have SELECT-only access to curated data.
Evidence is shared public-data material within the same App access boundary.

The network client fixes the catalog origin, disables redirects and proxy inheritance,
validates TLS using the system/approved CA bundle, and caps response bytes and requests.
No tool follows distribution links. All source text is untrusted data.
