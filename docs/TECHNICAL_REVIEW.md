---
title: "Pre-submission technical quality review"
description: "Review scope, verified corrections and remaining prototype limitations"
status: draft
tier: 2
related_files: ["VERIFICATION.md", "RESEARCH_UI.md", "SCIENCE.md", "EVALUATION.md"]
---

# Technical quality review — November 19

> Historical review of the November 19 system. Since then the six dataset-specific
> tools were replaced by nine dataset-agnostic tools backed by
> `registry/datasets.json` (see PROJECT_PLAN.md, "Generic tools and tabbed UI"), the
> UI was reorganized into tabs, and evaluation results were published in
> `eval/results/`. The findings and boundaries below remain accurate in substance.

Direct review of new science tooling, preparation, UI, evaluation integration,
staging and submission generation against the organizer's technical-quality rubric.
This is AI-assisted code review plus executed tests, not independent certification.

## Findings addressed

- Scientific areas above 1,000 were rounded to integers in the HTML reviewer.
  Display now retains four fractional digits; regression test covers 1770.5665.
- UI initially treated capability listings as catalog search results. Only actual
  discovery/inspection responses now populate inventory cards; UI test covers it.
- A formatting edit dropped spaces between adjacent preparation strings. Compared
  regenerated versus deployed asset, corrected literals, and reproduced the same
  snapshot ID `4aa4d12744b68926035a39e9` without changing evaluated values.
- Generated public-source SHA-256 fields triggered secret detection. Only exact
  checksum fields in the generated science asset are exempted from the high-entropy
  hex rule; other fields/files/rules continue to be scanned.
- Optional UI tests are explicitly run with the UI extra in CI. The server-only
  package does not require Streamlit/Plotly at runtime.

## Verified design boundaries

- Tools register centrally and use validated models with fixed dataset IDs and
  bounded years; no science tool accepts source URLs, SQL or filenames.
- Climate preparation validates declared units and calendar-year completeness;
  practice preparation validates exact columns, unique catchments and finite,
  nonnegative areas. Independent raw-file arithmetic matched both live eval rounds.
- Runtime verifies the prepared science content hash; queries return actual
  available years, units, source hashes, method and saved evidence.
- Scientific comparisons remain separate from the warehouse's reviewed county SQL.
  Explicit geography/grain/causal caveats prohibit a climate-adoption attribution.
- UI charts use structured numeric results, not generated code. Annual climate
  uses lines; sparse practice observations use points. Tables/evidence are available.
- Private UI service principal has MCP CAN USE and successfully invoked the model
  through inherited access. No direct warehouse grant or new broad model grant.
- Source text is untrusted; credentials/raw data/reviews are excluded from staging.

## Remaining limitations

- Single-user/small-team prototype, not load-tested production software. No new
  application-wide cost/rate controls or durable external evidence storage.
- Evidence is App-local; exports and verification archives must be retained.
- No cross-question conversation history; no arbitrary dataset execution or causal
  modeling. Reviewed scientific snapshot is historical and deliberately narrow.
- Data.gov catalog metadata can be inconsistent; reviewed source capabilities and
  search-card queryability are not yet fully integrated for all records.
- The explicit adversarial evaluation is only one test, not a penetration test.
- Scientific source preparation and artifact generation are operator workflows,
  not fully automated publisher refresh jobs. Submission documents require human
  presentation/proofreading and final submission via the organizer channel.
