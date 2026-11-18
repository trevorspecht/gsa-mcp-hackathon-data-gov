---
title: "Evaluation methodology and current evidence"
description: "Fixed question panel, scoring criteria and honest verification status"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["../README.md", "DEMO.md"]
---

# Evaluation

## Panel

`eval/questions.json` defines 12 questions: three discovery, three methodology,
three supported analyses and three unsupported cases. Run them against the chosen
Databricks model endpoint using `datagov-agent`. Preserve the actual answer and
tool trace. Keep model version, source snapshot, prompt and scoring rubric fixed.
Repeat A1, M1 and U3 three times to measure variability.

## Run and review

```sh
uv run python scripts/run_eval.py          # writes .local/verification/<ts>-eval-panel.json
uv run python scripts/eval_report.py .local/verification/<ts>-eval-panel.json
open .local/verification/<ts>-eval-review.html
```

The review page is one offline HTML file. Each run shows the question and
expected behavior, the rendered answer and every tool call with its arguments,
returned rows and summary counts. Automated checks recompute comparison rows and
summary counts independently from `.local/data/indicators.json` and flag any
difference. The top of the page holds reference tables for each period and the
source hashes. Pick rubric and overall scores in the page. They are saved in the
browser; **Export scores JSON** writes `<ts>-eval-scores.json`, which you can
keep next to the panel. Automated checks cover numbers only, so a reviewer still
judges interpretation, citations and limitations.

Score each separately for tool selection, parameters, returned data, interpretation,
citations and limitations. Overall categories: correct, partially correct, wrong,
correct abstention, erroneous refusal, or environment-blocked. Report the denominator
and blocked cases explicitly. No LLM-generated grade replaces independent numbers.

## Numerical reference

Independently compute each county's percent population change as
`100 * (end_population - start_population) / start_population`, and unemployment
change as `end_rate - start_rate` percentage points. Compare county sets exactly,
population integers exactly, and derived decimals within 0.000001. Confirm source
vintage and periods, Baltimore city inclusion, duplicates and missing coverage.
The current SQL fixture test executes the actual template in SQLite against
synthetic rows; Databricks dialect and publisher data still require live testing.

## Current observed status

- Local protocol, boundary, SQL, parser and warehouse-response tests are implemented.
- Real stdio subprocess checks passed Nov. 18 for six registered tools, publisher
  and location resolution, population search, harvest inspection, cursor continuation,
  a second topic (water quality), and unsupported-analysis handling.
- Six real catalog calls took approximately 0.25–0.50 seconds each in the observed
  run; this is one small sample, not a service-level promise.
- Nov. 18 15:47 UTC panel run (`.local/verification/20261118T154713Z-eval-panel.json`):
  `datagov-agent` → `databricks-claude-opus-5` → hosted App `mcp-datagov-semantic`
  → warehouse table, snapshot `ad9580ad34ac9575d0867709`. 18/18 runs exited 0.

## Panel run 2 — summary counts (16:16 UTC Nov. 18)

`compare_public_indicators` now returns `summary` counts over every complete
requested county. These counts ignore direction filters and the row limit. The
agent prompt says to quote them. Run: `20261118T161659Z-eval-panel.json`, with its
review page `20261118T161659Z-eval-review.html`. All 18 runs exited 0.

Automated checks: 8 comparison calls matched the independent reference for row
sets, values and summary counts. One warning: in U2 the agent first sent a
single-year range (2020→2020). Input validation rejected it as designed, and the
agent then reported California as unsupported. All three U3 runs quoted the
correct counts (18 rose, 1 fell, 5 unchanged; 21 grew, 3 declined) and declined
the causal claim. Human scoring is pending in the review page.

## Panel run 1 results (first scoring pass, AI-assisted; needs human review)

Reference numbers were computed independently in Python from `indicators.json`:
21 counties grew 2022→2024; unemployment rose in 18, was flat in 5, fell in 1.

| ID | Tools used | Score | Notes |
| --- | --- | --- | --- |
| D1 | search, filters, inspect | correct | Federal water-quality records with harvest IDs |
| D2 | search ×4, filters, inspect ×3 | correct | Found HUD CHAS through vocabulary; flagged unverified fields |
| D3 | filters ×2, search ×2, inspect | correct | Location ID 21; explained intersect vs. within |
| M1 ×3 | assess | correct 3/3 | Civilian labor force denominator |
| M2 | search ×2 | correct | Harvest, issued and observation dates distinguished |
| M3 | assess, search | correct | Aggregate unemployed and labor force; no unweighted mean |
| A1 ×3 | assess, compare, evidence | correct 3/3 | Worcester (24047) only; matches reference |
| A2 | assess, compare, evidence | correct | 24510: −0.42 percent; +0.5 percentage points |
| A3 | assess, compare, evidence | correct | Ranking and 0.7–1.3 point range match reference |
| U1 | assess, search ×3, filters | correct abstention | No ad-spend metric; nothing substituted |
| U2 | assess ×2, search ×2 | correct abstention | One tool call errored on a single-year range; agent reported it |
| U3 ×3 | assess, compare, evidence | correct 1/3, partial 2/3 | Declined causation every time; runs 1–2 miscounted counties ("rose in all but one", "21 of 24" rose; reference is 18) |

Summary: 16 correct runs and 2 partially correct runs, out of 18 total.
The partial runs had correct tool output and abstention, but the model's prose
miscounted counties. Returning summary counts from the compare tool would reduce
this error. Two endpoints returned typed reasoning parts. The runner now keeps
only text parts. The panel ran before that fix, so saved answers include the raw parts.

Machine-readable actual output is under `.local/verification/`; retain failed runs
alongside successful runs. A source-CA mismatch was found and fixed before the live
pass. Full command results are recorded in `docs/VERIFICATION.md` after checks.

## Security and limitations

Tests cover fixed-origin transport, denied redirects, output size, quota behavior,
cursor filter binding, unsupported metrics, malformed inputs, duplicate grain,
missing rows, evidence path validation and query cancellation. The system does not
fetch arbitrary distributions. Hosted auth and permissions require real verification.
Catalog metadata claims may be incomplete or wrong; queryability is explicitly
separate from discovery. Methodology review remains a prerequisite for onboarding.
