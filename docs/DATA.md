---
title: "Curated source preparation"
description: "Reproducible Maryland county population and unemployment snapshot workflow"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["DATABRICKS.md", "../ACCESS_BLOCKERS.md"]
---

# Curated source preparation

Source download is currently blocked by sandbox network access. The parsers are
implemented and tested against synthetic format fixtures; real publisher bytes
and methodology still require validation before any analytic result is claimed.

## Source files

1. Census Vintage 2024 county all-data CSV:
   `https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv`
2. BLS Maryland LAUS series file:
   `https://download.bls.gov/pub/time.series/la/la.data.27.Maryland`

Place downloaded files under `.local/raw/`. Verify publisher provenance, the
Census Vintage 2024 dictionary, BLS series coding and the M13 annual-average
definition using authoritative documentation. Review that county boundaries and
periods are comparable. Exact catalog identifiers remain to be bound after source
verification; URLs in the registry are proposed source references, not live proof.

The adapter selects Maryland county/county-equivalent records for 2022–2024,
Census SUMLEV 050, and BLS not-seasonally-adjusted county measure 03, period M13.
It requires all 24 geographic units (23 counties plus Baltimore city), rejects
duplicates, invalid rates and missing coverage, and writes 72 county/year rows.
All population observations use the same vintage. The population measure is a
July 1 estimate while unemployment is an annual average; comparisons are descriptive.

```sh
uv run datagov-prepare --population .local/raw/co-est2024-alldata.csv --laus .local/raw/la.data.27.Maryland
```

Use `--domain-reviewed` only after completing the source/methodology review above.
Preparation records original SHA-256 hashes, a snapshot ID and normalized data hash.
Without review, the runtime cannot execute the snapshot. Output folders are immutable:
use `--output` and set `ANALYTICS_MANIFEST` when preparing a new snapshot.

## Load after resource approval

```sh
uv run datagov-load             # preview resource and row count
uv run datagov-load --execute   # operator write identity required
```

Loading verifies the normalized file hash and row count, creates the configured
table if absent, and inserts a new snapshot. An existing snapshot causes a stop
rather than duplicate insertion. Do not run simultaneous loaders. The runtime
queries only the configured snapshot and saves query IDs and source evidence.

## Rollback

Point the runtime to the last verified manifest/table and redeploy the last reviewed
wheel. Preserve evidence and source files. Deleting tables, snapshots or Apps is a
separate operator-approved action; setup and runtime do not perform it.
