---
title: "Curated source preparation"
description: "Reproducible Maryland county population and unemployment snapshot workflow"
status: draft
tier: 2
last_updated: "2026-11-23"
related_files: ["DATABRICKS.md", "../data/README.md"]
---

# Curated source preparation

The county snapshot was prepared from real publisher files on November 18 and
loaded to the hackathon workspace warehouse (see docs/VERIFICATION.md). The exact
files are in `data/raw/`; the reviewed snapshot is in `data/reviewed/`. To use it in
a new workspace, load it there with `datagov-load`.

## Source files

1. Census Vintage 2024 county all-data CSV:
   `https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv`
2. BLS Maryland LAUS series file:
   `https://download.bls.gov/pub/time.series/la/la.data.27.Maryland`

The exact publisher files used for the reviewed snapshot are committed in
`data/raw/` (hashes in `data/reviewed/manifest.json`); put new downloads there too.
For a new snapshot, verify publisher provenance, the Census Vintage 2024
dictionary, BLS series coding and the M13 annual-average definition using
authoritative documentation, and check that county boundaries and periods are
comparable. The BLS source is bound to Data.gov record `DOL-BLS-3060-01`; no
Vintage 2024 Census county-totals record exists on catalog.data.gov.

The adapter selects Maryland county/county-equivalent records for 2022–2024,
Census SUMLEV 050, and BLS not-seasonally-adjusted county measure 03, period M13.
It requires all 24 geographic units (23 counties plus Baltimore city), rejects
duplicates, invalid rates and missing coverage, and writes 72 county/year rows.
All population observations use the same vintage. The population measure is a
July 1 estimate while unemployment is an annual average; comparisons are descriptive.

```sh
uv run datagov-prepare --population data/raw/co-est2024-alldata.csv --laus data/raw/la.data.27.Maryland
```

Use `--domain-reviewed` only after completing the source/methodology review above.
Preparation records original SHA-256 hashes, a snapshot ID and normalized data hash.
Without review, the runtime cannot execute the snapshot. Output folders are immutable:
use `--output` and set `ANALYTICS_MANIFEST` when preparing a new snapshot.

## Load into a workspace

```sh
uv run datagov-load             # preview resource and row count
uv run datagov-load --execute   # operator write identity required
```

Loading verifies the normalized file hash and row count, creates the configured
table if absent, and inserts a new snapshot. An existing snapshot causes a stop
rather than duplicate insertion. Do not run simultaneous loaders. The runtime
queries only the configured snapshot and saves query IDs and source evidence.
`data/reviewed/manifest.json` records the hackathon workspace table in
`loaded_table`; a new workspace needs its own load, which updates that field.

## Rollback

Point the runtime to the last verified manifest/table and redeploy the last reviewed
wheel. Preserve evidence and source files. Deleting tables, snapshots or Apps is a
separate operator-approved action; setup and runtime do not perform it.
