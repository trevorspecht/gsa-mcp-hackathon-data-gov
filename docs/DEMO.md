---
title: "Hackathon demonstration and slide outline"
description: "A short evidence-first demo with submission slide content"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["EVALUATION.md", "DATABRICKS.md"]
---

# Demo

## Sequence

1. Ask the Databricks agent to find and inspect water-quality datasets. Show actual
   tool calls and publisher references, demonstrating breadth beyond the seed domain.
2. Ask which Maryland counties grew while unemployment fell from 2022 to 2024.
   Show the compatibility response, query results and evidence artifact.
3. Ask whether population growth caused the unemployment change. Show a bounded
   descriptive answer with an explicit causal limitation.
4. Ask for an unsupported state/year or advertising metric. Show the honest coverage
   boundary and useful discovery rather than fabricated computation.

Steps 2–4 require the live workspace/model and reviewed data. Do not label an
unrehearsed scenario a working demo. Record a fallback only after a successful run.

## Slide outline

1. **Problem:** government data is discoverable, but finding a dataset does not
   establish that two measures can be meaningfully compared.
2. **Solution:** broad Data.gov search, reviewed meanings, controlled computation,
   and reproducible evidence through six goal-oriented MCP tools.
3. **Architecture:** Databricks agent → authenticated MCP App → catalog metadata
   or approved SQL warehouse snapshot; versioned registry and evidence artifacts.
4. **Demonstration:** one discovery question, one cross-source comparison, one
   unsupported case. Include actual outputs only after live rehearsal.
5. **Evaluation:** 12-question panel, independent numerical reference, methodology
   and abstention scores; report observed results and blocked cases honestly.
6. **Lessons:** semantics and source vintages matter; discovery is broader than
   computation; generated answers need measurable evidence and coverage boundaries.

The saved event requirements call for repository, slides and evaluation document.
Organizer templates and final submission logistics remain BUILD-08/09 work.
