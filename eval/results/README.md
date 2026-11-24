---
title: "Evaluation results"
description: "Every saved evaluation run, review page and score file, including failures"
status: canonical
tier: 2
related_files: ["../../docs/EVALUATION.md"]
---

# Evaluation results

**Start here:** [EVALUATION-SUMMARY.pdf](EVALUATION-SUMMARY.pdf) is a six-page visual
summary of every run over time: completion, graded quality, numeric checks,
response time, current-system grades by question and a run-by-run table.
Regenerate it with `uv run python scripts/eval_summary.py`.

Every evaluation run of the Data.gov Research MCP server, November 18–23, 2026,
including failed and interrupted runs. Each `*-eval-panel.json` holds the exact
questions, system prompt and hash, model settings, source-file hashes, every tool
call with arguments and results, model completion metadata and timing. Open any
`*-eval-review.html` in a browser for answers, full traces, automated checks and
rubric scoring fields (human scores are stored only in your browser).

**Two AI reviews of the current system.** The three bold panels below were scored by
Claude Opus 5.5 and then, as a second opinion, by GPT-6 Astra. Neither generated the
answers (GPT-6.1 Sol did). No overall score changed: both give 19 correct and 6 correct
abstentions. See [second-opinion review](SECOND-OPINION-REVIEW.md).

Score files are bound to the exact panel file by SHA-256:

- `*-eval-ai-scores.json`: read-only AI review, never a substitute for a human score.
- `*-eval-ai-scores-astra.json`, `*-eval-review-astra.html`: GPT-6 Astra second opinion.
- `*-eval-human-scores.json`: the project owner's exported browser scores.

Regenerate a page with `uv run python scripts/eval_report.py eval/results/<run>-eval-panel.json`
(county checks use the reviewed snapshot in `data/reviewed/`).

## Runs

| Run (UTC) | Panel | Tools | Answer model | Outcome |
| --- | --- | --- | --- | --- |
| 20261118T154713Z | Core v1, 18 trials | Original 8 | Opus 5 | First live panel |
| 20261118T161659Z | Core v1, 18 trials | Original 8 | Opus 5 | Human: 16 correct, 2 partial; AI (Astra): 9 correct, 3 abstentions, 6 partial |
| 20261119T150947Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | Prompt revised after skipped definition checks |
| 20261119T151545Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | Interrupted by a concurrent App redeploy; retained |
| 20261119T152023Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | 18/18; all 8 comparisons match; AI (Astra): 13 correct, 5 abstentions |
| 20261119T232056Z | Science/inventory, 9 | Original + science | GPT-6.1 Sol | 9/9; 5 science queries match raw sources |
| 20261119T232423Z | Science/inventory, 9 | Original + science | GPT-6.1 Sol | 9/9; repeat round |
| 20261120T223428Z | User workflows, 4 | + readiness | GPT-6.1 Sol | 3/4; relationship question failed (retained) |
| 20261120T223552Z | User workflows, Q1 | + readiness | GPT-6.1 Sol | Retry of failed question |
| 20261120T223719Z | User workflows, 4 | + readiness | GPT-6.1 Sol | 4/4 after prompt change |
| 20261122T180248Z | User workflows, 2 | + exploration | GPT-6.1 Sol | List question complete; relationship question failed (retained) |
| 20261122T180341Z | User workflows, Q1 | + exploration | GPT-6.1 Sol | Failed retry (retained) |
| **20261122T230301Z** | **Core, 12** | **Generic 9** | GPT-6.1 Sol | **12/12; 4 county analyses match; Opus and Astra: 9 correct, 3 abstentions** |
| 20261122T230554Z | User workflows, 4 | Generic 9 | GPT-6.1 Sol | Network outage: 2 complete, 2 timeouts (retained) |
| 20261122T232926Z | Science/inventory | Generic 9 | GPT-6.1 Sol | Network outage: timeouts, stopped (retained) |
| **20261123T161211Z** | **User workflows, 4** | **Generic 9** | GPT-6.1 Sol | **4/4; series checks match; Opus and Astra: 4 correct** |
| **20261123T161339Z** | **Science/inventory, 9** | **Generic 9** | GPT-6.1 Sol | **9/9; 6 series checks across 5 questions match; Opus and Astra: 6 correct, 3 abstentions** |

Bold rows are the current-system results reported in the submission. Model, prompt
and tools changed between rounds, so rows are not a controlled comparison.

Publication note: the 20261118T154713Z copy has five opaque provider reasoning
signatures redacted; no answer, trace or result was changed. These files contain
only public data, public-source metadata and model output — no credentials. They
include the private hackathon App's hostname, which is behind workspace sign-in.
