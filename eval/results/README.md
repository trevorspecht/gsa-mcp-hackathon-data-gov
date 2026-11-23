---
title: "Evaluation results"
description: "Every saved evaluation run, review page and score file, including failures"
status: canonical
tier: 2
related_files: ["../../docs/EVALUATION.md"]
---

# Evaluation results

Every evaluation run of the Data.gov Research MCP server, November 18–23, 2026,
including failed and interrupted runs. Each `*-eval-panel.json` holds the exact
questions, system prompt and hash, model settings, source-file hashes, every tool
call with arguments and results, model completion metadata and timing. Open any
`*-eval-review.html` in a browser for answers, full traces, automated checks and
rubric scoring fields (human scores are stored only in your browser).

**November 23 second-pass review:** see [Astra review and disagreements](ASTRA-REVIEW.md).
The three current-system panels now also have `*-eval-ai-scores-astra.json` and
`*-eval-review-astra.html`. Original reviews and human scores are preserved.
Both AI reviews agree on 19 correct / 6 correct abstentions; five criterion grades
differ. Reviewer names are recorded provenance, not independently attested runtime identities.

Score files are bound to the exact panel file by SHA-256:

- `*-eval-ai-scores.json`: read-only AI review, never a substitute for a human score.
- `*-eval-human-scores.json`: the project owner's exported browser scores.

Regenerate a page with `uv run python scripts/eval_report.py eval/results/<run>-eval-panel.json`
(needs the private reviewed county snapshot in `.local/data` for county checks).

## Runs

| Run (UTC) | Panel | Tools | Model | Outcome |
| --- | --- | --- | --- | --- |
| 20261118T154713Z | Core v1, 18 trials | Original 8 | Opus 5 | First live panel |
| 20261118T161659Z | Core v1, 18 trials | Original 8 | Opus 5 | Human: 16 correct, 2 partial; AI: 9 correct, 3 abstentions, 6 partial |
| 20261119T150947Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | Prompt revised after skipped definition checks |
| 20261119T151545Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | Interrupted by a concurrent App redeploy; retained |
| 20261119T152023Z | Core, 18 trials | Original 8 | GPT-6.1 Sol | 18/18; all 8 comparisons match; AI: 13 correct, 5 abstentions |
| 20261119T232056Z | Science/inventory, 9 | Original + science | GPT-6.1 Sol | 9/9; 5 science queries match raw sources |
| 20261119T232423Z | Science/inventory, 9 | Original + science | GPT-6.1 Sol | 9/9; repeat round |
| 20261120T223428Z | User workflows, 4 | + readiness | GPT-6.1 Sol | 3/4; relationship question failed (retained) |
| 20261120T223552Z | User workflows, Q1 | + readiness | GPT-6.1 Sol | Retry of failed question |
| 20261120T223719Z | User workflows, 4 | + readiness | GPT-6.1 Sol | 4/4 after prompt change |
| 20261122T180248Z | User workflows, 2 | + exploration | GPT-6.1 Sol | List question complete; relationship question failed (retained) |
| 20261122T180341Z | User workflows, Q1 | + exploration | GPT-6.1 Sol | Failed retry (retained) |
| **20261122T230301Z** | **Core, 12** | **Generic 9** | GPT-6.1 Sol | **12/12; 4 county analyses match; AI: 9 correct, 3 abstentions** |
| 20261122T230554Z | User workflows, 4 | Generic 9 | GPT-6.1 Sol | Network outage: 2 complete, 2 timeouts (retained) |
| 20261122T232926Z | Science/inventory | Generic 9 | GPT-6.1 Sol | Network outage: timeouts, stopped (retained) |
| **20261123T161211Z** | **User workflows, 4** | **Generic 9** | GPT-6.1 Sol | **4/4; series checks match; AI: 4 correct** |
| **20261123T161339Z** | **Science/inventory, 9** | **Generic 9** | GPT-6.1 Sol | **9/9; 6 series checks across 5 questions match; AI: 6 correct, 3 abstentions** |

Bold rows are the current-system results reported in the submission. Model, prompt
and tools changed between rounds, so rows are not a controlled comparison.

Publication note: the 20261118T154713Z copy has five opaque provider reasoning
signatures redacted; no answer, trace or result was changed. These files contain
only public data, public-source metadata and model output — no credentials. They
include the private hackathon App's hostname, which is behind workspace sign-in.
