# Submission artifacts

Submitted by the owner on November 23, 2026 (deadline 11:59 p.m. Eastern),
including a recorded video demo of the hosted research App. Run `uv run python scripts/build_submission.py` to
rebuild the 12-slide deck (`scripts/build_deck.py`, following the sample deck's slide
sequence and title-bar style), the evaluation DOCX and their PDFs in `submission/`.
Organizer templates are kept locally in `.local/submission/templates/`. Demo-slide
screenshots are in `submission/screens/`; evaluation tables are computed from
`eval/results/`. PDFs require LibreOffice and show its layout; PowerPoint or Word may
differ slightly. The committed deck includes the owner's final LibreOffice edits; rebuilding
regenerates it from `scripts/build_deck.py`.

| Required deliverable | Where |
| --- | --- |
| GitHub repository with documented MCP code | github.com/trevorspecht/gsa-mcp-hackathon-data-gov |
| Slide deck: problem, solution, technical approach, demonstration | `submission/Data.gov-Research-Hackathon.pptx` (and `submission/pdf/`) |
| Evaluation: methodology, metrics, security, lessons | `submission/Data.gov-Research-Evaluation.docx` (and `submission/pdf/`) |
| Evaluation runs, review pages and scores | `eval/results/` |
| Deployment and data-load verification logs | `verification/` |

## Video demo (hosted research App)

The recorded demo uses the climate and agriculture correlation question, which
fills all five tabs: answer with limits, sources with availability labels, change
charts, guided exploration (select temperature, precipitation and cover crops,
refresh NOAA live, check compatibility, run a suggested next step) and the tool
trace.

## Demonstration questions

1. "Is there a correlation between climate patterns and agricultural practices over
   time in Maryland and the Chesapeake Bay watershed?" — answer explains geography
   and sparse-year limits; Explore further previews data and checks compatibility.
2. "Which Maryland counties gained population while unemployment fell from 2022
   to 2024?" — Worcester County; Data & charts shows generic change bars.
3. "What datasets are available about climate, irrigation and cover-crop
   practices?" — ranked catalog candidates with availability in Sources.
4. "How did estimated cover-crop implementation in the Chesapeake Bay watershed
   change between 2002 and 2012?" — 481.509 → 1,770.5665 km².
