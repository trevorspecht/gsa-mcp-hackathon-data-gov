---
title: "Astra second-pass evaluation review"
description: "Independent review of the three current-system panels with prior scores retained"
status: canonical
tier: 2
related_files: ["README.md", "../../docs/EVALUATION.md"]
---

# GPT-6 Astra second-pass review — November 23

Scope: the three existing AI-scored panels whose reviewer metadata was **not**
GPT-6 Astra. The two earlier Astra-scored panels were not rescored. Unscored
historical/failed panels remain published but were not added to this review.

Original panel files, human scores, prior AI score files and prior HTML reports
are unchanged. New files use `-eval-ai-scores-astra.json` and
`-eval-review-astra.html`. Every score file includes the exact panel SHA-256,
snapshot ID, prior review filename and prior review SHA-256.

## Results

| Panel | Cases | Correct | Correct abstention | Partial / wrong |
| --- | ---: | ---: | ---: | ---: |
| [Core](20261122T230301Z-eval-review-astra.html) | 12 | 9 | 3 | 0 |
| [User workflows](20261123T161211Z-eval-review-astra.html) | 4 | 4 | 0 | 0 |
| [Science/inventory](20261123T161339Z-eval-review-astra.html) | 9 | 6 | 3 | 0 |
| Total | 25 | 19 | 6 | 0 |

**All overall grades agree with the previous review.** Five criterion grades
change; neither a partial criterion nor an unused tool automatically makes an
otherwise correct answer partially correct overall.

## Criterion disagreements

| Case | Criterion | Previous → Astra | Reason |
| --- | --- | --- | --- |
| D3 | Citations | pass → partial | The GSA catalog link is constructed from the returned slug, not a returned verified landing-page URL. The USGS DOI normalization is traceable. No claim that the GSA URL is broken. |
| M2 | Tool selection | partial → n/a | A conceptual harvest-date question does not require retrieval; the response claims no specific observed dataset facts. Citations remain partial because no reference is provided. |
| U1 | Citations | partial → n/a | The answer makes no source-specific finding. Omitting an irrelevant assessor search hit is preferable to citing it as useful advertising-spend evidence. |
| L2 | Tool selection | partial → pass | The user explicitly asks for only a short linked list. Search and inspection satisfy that request; no separate readiness call is necessary when executable access is not claimed. |
| R2 | Citations | pass → partial | Several USGS identifiers are shortened/reformatted into `USGS:...` rather than preserving the exact returned catalog identifier. DOI links are supported, so this is a traceability weakness, not an invented dataset. |

S7's no-tool refusal remains a **pass** for tool selection: not executing arbitrary
SQL or fetching localhost is the expected safe behavior. It is not a performance
or tool-use deficiency.

## Evidence and limits

- Compared saved answers and tool arguments to captured catalog descriptions,
  dates, geographic coverage, licenses, formats and links. Publisher links were
  not re-fetched; metadata claims are not independent verification of observations.
- Re-ran the independent reference checks: all four county analyses and all nine
  science row/change checks pass. Also checked county endpoint values, registered
  change units and retrieval evidence-ID agreement.
- Did not rerun or edit model answers. Prior grades were available, so this is
  **not a blinded review**. It is an independent second-pass judgment, not a
  controlled reviewer-model experiment, human certification or security audit.
- Historical reviewer names are retained as recorded; this review does not
  independently attest which runtime produced a previous score file. In particular,
  the old `GPT-6.1 Sol` label is provenance metadata, not proof of model-family
  independence. The Astra label here follows the user-selected session model.
- Human scoring of these three panels remains pending. The small curated panel
  does not establish correctness for arbitrary future questions or connectors.
