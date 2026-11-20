---
title: "Hackathon demonstration and slide outline"
description: "A short evidence-first demo with submission slide content"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["EVALUATION.md", "DATABRICKS.md"]
---

# Demo

## Submission artifacts and end-user demo

Extended deadline reported by owner on November 20: **Monday, November 23, 2026,
11:59 p.m. Eastern Time**. This supersedes the original November 20 deadline.
Organizer templates are in `.local/submission/templates/`. Run
`uv run python scripts/build_submission.py` to produce the adapted 12-slide deck
and evaluation DOCX in `.local/submission/`. Both are drafts requiring presenter
review. The slide deck includes charts using verified values and keeps climate and
practice geography separate.

Use the private `datagov-research-ui` App for the end-user demonstration:

1. Ask for a climate/agriculture dataset landscape; show cards, metadata and unknowns.
2. Query Chesapeake cover-crop estimates; show sparse points, table and evidence.
3. Ask whether Maryland climate caused adoption; show the geography/causality limit.
4. Optionally demonstrate the verified Census/BLS county comparison as a second domain.

A live science query and chart were verified in the authenticated UI. A video
fallback still needs recording; do not describe the slide charts as a recorded demo.

## Original county demo sequence

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
   and reproducible evidence through eight goal-oriented MCP tools.
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
