---
title: "Evaluation methodology and current evidence"
description: "Fixed question panel, scoring criteria and honest verification status"
status: draft
tier: 2
last_updated: "2026-11-18"
related_files: ["../README.md", "DEMO.md"]
---

# Evaluation

## Climate/agriculture expansion — November 19

`eval/climate-agriculture.json` adds nine cases: two deep dataset inventories,
four scientific series, an incompatible causal join, a missing-year request and
an arbitrary SQL/local-URL request. Run with `scripts/run_eval.py --questions
eval/climate-agriculture.json --repeats 1`.

Two actual rounds (`20261119T232056Z`, `20261119T232423Z`) completed 9/9 each.
Each returned five scientific query responses (including a supported alternative
for the missing-year question); all five per round independently matched raw NOAA
CSV observations or Decimal sums of the 50,871-row USGS tables. Causal joins and
interpolation were declined; no arbitrary SQL or localhost fetch was executed.
Inventories used multiple searches and inspections and described result coverage,
metadata uncertainties, measurements versus models/projections/code, and terms.

These are successful execution and numeric checks, not a claim of comprehensive
human correctness scoring. The first round did not embed the science snapshot;
the second does, allowing the HTML to check rows/units/snapshot automatically.
Both preserve exact questions, model settings and source hashes. Reports are in
`.local/verification/`; no saved answers or human scores were replaced.

## Panel

`eval/questions.json` defines 12 questions: three discovery, three methodology,
three supported analyses and three unsupported cases. Run them against the chosen
Databricks model endpoint using `datagov-agent`. Preserve the actual answer and
tool trace. Keep model version, source snapshot, prompt and scoring rubric fixed.
Repeat A1, M1 and U3 three times to measure variability.

## Published results and current-system review — November 23

All 17 evaluation runs since November 18, including failed and interrupted runs,
are published with their HTML review pages and score files in
[eval/results](../eval/results/README.md). New runs are written to
`.local/verification/` and copied there after review.

After the tools were made dataset-agnostic, three panels (25 runs: core
`20261122T230301Z`, user workflows `20261123T161211Z`, science/inventory
`20261123T161339Z`) completed 25/25 with no tool errors. Every county analysis and
series check matched the independent reference. A separate AI review (GPT-6.1 Sol,
read-only, bound to each panel's SHA-256) scored 19 correct and 6 correct
abstentions. Criterion-level weaknesses: M2 and S7 used no tools, M2 cites no
source, L2 skipped the readiness check for a brief list, and U1 did not name the
catalog record it found. The same model family produced and reviewed the answers;
human scoring of these runs has not been done.

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

New runs embed the exact question definitions, system prompt and hash, source-code
hashes, API choice, token budget and reasoning effort. Individual results retain
model completion metadata. The HTML uses the embedded questions; older runs use
`eval/questions-v1.json`, so changing U2 cannot relabel historical answers.
U2 now explicitly asks for California population/unemployment changes from 2020
to 2024; no prior conversation is assumed. New reports expose model completion
metadata and flag incomplete output even when its partial answer contains data.

Score each separately for tool selection, parameters, returned data, interpretation,
citations and limitations. Overall categories: correct, partially correct, wrong,
correct abstention, erroneous refusal, or environment-blocked. Report the denominator
and blocked cases explicitly. No LLM-generated grade replaces independent numbers.

## Human review and next-run adjustments — November 19

Human scores were exported from the review page to
`.local/verification/20261118T161659Z-eval-human-scores.json`. The owner explicitly
corrected all three U3 overall grades to **correct**, retaining individual rubric
scores; the file preserves that correction history. Human totals are **16 correct,
2 partially correct** (D3 and M3). AI scores remain separate, not averaged into a
single grade. “Correct abstention” versus “correct” is not treated as a substantive
disagreement for an unsupported question.

Priorities informed by both reviews (implemented for the Sol runs below):

1. Detect incomplete model output and retain completion status/finish reasons.
   D2/D3/M3 have unfinished endings even though the process exited successfully.
2. Make caveats explicit in the answer, rather than referring to hidden JSON
   (“the caveats”), as the human M1 note requests. Keep methodology and catalog
   availability claims within the evidence actually returned.
3. Reconcile stale source-verification labels with verified snapshot readiness.
4. Make U2 self-contained and freeze exact question text, prompt/model settings
   and completion metadata with future runs. Preserve this baseline unchanged.

The owner requested investigation of GPT-6.1 Responses support before applying
these changes or starting a new panel; see [Databricks setup](DATABRICKS.md).

## Separate AI reviewer scores

The latest panel (`20261118T161659Z`) now has an advisory GPT-6 Astra review of
all 18 saved answers and traces, distinct from the answering model (Claude Opus 5).
Scores and a reason for each of the six rubric items are saved in
`.local/verification/20261118T161659Z-eval-ai-scores.json`. The report generator
automatically loads that sibling file, or accepts `--ai-review PATH`. It checks
that the review matches the exact panel SHA-256, snapshot and all run IDs.

The HTML shows **AI reviewer assessment** separately from **Your score**. It
never fills or replaces human dropdowns, notes, browser storage or exports.
Regenerate the same HTML path to retain existing human browser scores. This
review is AI-assisted, not blind evaluation or human certification.

The reviewer graded 9 runs correct, 3 correct abstentions and 6 partially correct
(D2, D3, M2, M3, U1 and U3 repeat 1). All eight comparison outputs still match the
independent numeric reference; the partial grades concern the answer text:

- D2 and D3 end mid-sentence; M3 ends with an unfinished caveat heading. The saved
  run does not retain a finish reason, so the cause is not established here.
- D3 says “page 1 of 10,” although the trace reports ten records and a next cursor,
  not a total page count.
- M2 conflates harvest timing with vintage in one sentence despite its otherwise
  correct observation-date explanation.
- M3 adds unsupported methodology/weighting claims; U1 overstates absence from
  two narrowly filtered searches as absence from the catalog.
- U3 repeat 1 describes an inverse pattern as opposing the proposed inverse
  relationship and asserts typical revision magnitudes without evidence.

Some methodology responses quote stale “awaiting source download” source labels
returned alongside `ready_to_execute=true`. These are inconsistent tool metadata,
not model-fabricated blockers. Original panel outputs remain unchanged for audit;
reviewing this run does not silently repair or rerun the evaluated system.

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

## Final Sol evaluation — November 19

Final run: `20261119T152023Z-eval-panel.json` with scored review page
`20261119T152023Z-eval-review.html` under `.local/verification/`.
Model: `system.ai.gpt-6-1-sol`, Responses API, low reasoning effort, maximum
4,000 output tokens. All 18 runs exited 0 and every model turn reported completed.
All eight analytical comparisons matched the independent reference and source
hashes; no incomplete outputs or tool errors were observed. Mean duration was
15.7 seconds per question in this small run, not a latency guarantee.

AI-assisted review: 13 correct and 5 correct abstentions. M2's conceptual answer
is correct but lacks an external citation/live example (citation criterion partial).
Human review remains separate and pending. The HTML retains the no-tool warning
for M2 rather than presenting it as MCP-backed. All repeated M1 answers checked
registered definitions, A1 returned Worcester only, and U3 declined causation while
correctly distinguishing county counts from statewide aggregate rates.

Preserved iterations:

- `20261119T150947Z`: all 18 completed, but several definition/refusal answers
  skipped registry assessment; prompt tightened afterward.
- `20261119T151545Z`: 17 completed; D3 failed with MCPError during redeployment.
  Failure retained rather than replaced with a retry.
- `20261119T152023Z`: full rerun against stable deployment, 18 completed.

This is a system iteration, not a controlled claim that Sol alone improved scores:
model, prompt, API/output budget, source-status handling and U2 wording changed.
Historical Opus answers, human scores and AI scores remain unchanged.

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
