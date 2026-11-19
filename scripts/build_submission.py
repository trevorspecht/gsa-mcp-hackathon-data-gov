"""Adapt organizer templates with actual project evidence; keep outputs local."""

import json
from pathlib import Path

from docx import Document
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/submission"
SLIDES = [
    (
        "Data.gov Research",
        (
            "From a plain-language question to discoverable publi"
            "c data—and, where supported, a verifiable answer.\nTr"
            "evor Specht · GSA MCP / AI Agent Hackathon · Novembe"
            "r 2026\nWorking milestone in an ongoing, portable res"
            "earch project."
        ),
    ),
    (
        "Problem: finding data is not finding an answer",
        (
            "Researchers must navigate inconsistent publisher met"
            "adata, formats, periods and meanings.\nA search match"
            " does not prove comparability, queryability or causa"
            "l relevance.\nMission: make public data useful to gov"
            "ernment and non-government research, service deliver"
            "y and oversight."
        ),
    ),
    (
        "Solution: discover, inspect, query, explain",
        (
            "Broad topic discovery across Data.gov.\nDataset inven"
            "tories with publisher, periods, formats, terms, dict"
            "ionaries and unknowns.\nReviewed bounded queries for "
            "Census/BLS and climate/agriculture.\nSources, scope l"
            "imits and downloadable evidence accompany answers."
        ),
    ),
    (
        "Architecture: reusable MCP core, private research App",
        (
            "Private Streamlit App → Databricks-hosted Sol agent "
            "→ authenticated MCP App.\nMCP routes discovery to Dat"
            "a.gov, county comparisons to a parameterized SQL war"
            "ehouse, and scientific queries to a reviewed fixed s"
            "napshot.\nUI has no direct warehouse grants. Eight go"
            "al-oriented tools; validated inputs and output budge"
            "ts."
        ),
    ),
    (
        "Key decision: discovery is broader than computation",
        (
            "Never execute arbitrary SQL or tool-supplied downloa"
            "d URLs.\nReviewed semantics and source hashes define "
            "supported computation.\nCatalog records stay discover"
            "y-only unless explicitly bound; do not infer compati"
            "bility from a search hit.\nRuntime tools validate geo"
            "graphy, years and permitted operations."
        ),
    ),
    (
        "Scientific example: climate and agricultural practices",
        (
            "NOAA: Maryland annual temperature and precipitation,"
            " 1985–2012.\nUSGS/Chesapeake Bay Program: allocated c"
            "over-crop and conservation-tillage implementation ar"
            "eas.\nPractice units are square kilometres, not acres"
            " or adoption percentages.\nDifferent geography and sp"
            "arse observation years prohibit direct causal joins."
        ),
    ),
    (
        "User-facing demonstration",
        (
            "1. Inventory climate/agriculture datasets; inspect p"
            "romising records and expose unknowns.\n2. Query cover"
            "-crop estimates: 481.509 km² (2002) → 1,770.5665 km²"
            " (2012).\n3. Show unconnected observation points, dat"
            "a table and evidence.\n4. Ask whether climate caused "
            "adoption: explain why the data cannot establish it.\n"
            "Live demo: private datagov-research-ui App; retain a"
            " recorded fallback."
        ),
    ),
    (
        "Graphics follow the data, not model guesses",
        (
            "Annual climate: line chart plus accessible table.\nSp"
            "arse practice observations: points only, no invented"
            " intervening years.\nCounty comparison: separate perc"
            "ent / percentage-point bars.\nCharts rendered from st"
            "ructured tool results, never model-generated executa"
            "ble plotting code.\nNo mismatched-geography correlati"
            "on chart."
        ),
    ),
    (
        "Evaluation setup",
        (
            "Core panel: 12 questions plus repeated M1/A1/U3 = 18"
            " trials.\nExpanded scientific/inventory panel: 9 case"
            "s, run twice.\nExact prompts, model settings, source "
            "hashes, tool traces and completion status retained.\n"
            "Independent arithmetic against raw publisher data; s"
            "eparate human and AI rubric reviews.\nNo-tool questio"
            "ns are not misrepresented as MCP-backed."
        ),
    ),
    (
        "Observed results and improvements",
        (
            "Final core Sol panel: 18/18 completed; all 8 compari"
            "sons matched reference.\nTwo added panels: 9/9 comple"
            "ted each; all 5 scientific queries per round matched"
            " raw sources.\nTests include protocols, boundaries, p"
            "arsers and UI rendering.\nFixed source encoding/IDs, "
            "summary counts, incomplete outputs, stale source sta"
            "tus and context-dependent wording.\nModel and prompt "
            "changed together: not a controlled model-only superi"
            "ority claim."
        ),
    ),
    (
        "Security and reliability",
        (
            "Public government data only; private authenticated s"
            "andbox Apps.\nScoped App access, fixed origins, param"
            "eterized SQL, bounded calls/time/bytes and no arbitr"
            "ary downloads.\nSecrets excluded from source and stag"
            "ing; dependency audit and static checks.\nOne explici"
            "t adversarial SQL/local-URL case declined; not a com"
            "prehensive security certification.\nEvidence is local"
            "ly stored: export before restart or environment reti"
            "rement."
        ),
    ),
    (
        "Lessons and next stage",
        (
            "Useful AI research requires visible uncertainty, pro"
            "venance and explicit analytical scope.\nNext: verifie"
            "d bindings, more sources, session-isolated conversat"
            "ional memory and durable evidence.\nPortability: keep"
            " MCP and UI separate; replace Databricks auth/model/"
            "warehouse adapters after sandbox closes.\nPreserve ra"
            "w data, snapshots, traces, scores and runnable artif"
            "acts.\nRepository: github.com/trevorspecht/gsa-mcp-ha"
            "ckathon-data-gov"
        ),
    ),
]


def main():
    template = OUT / "templates/MCP-hackathon-sample-deck.pptx"
    deck = Presentation(template)
    if len(deck.slides) != len(SLIDES):
        raise ValueError("Organizer template slide count changed")
    for slide, (title, body) in zip(deck.slides, SLIDES, strict=True):
        for shape in list(slide.shapes):
            element = shape._element
            element.getparent().remove(element)
        titlebox = slide.shapes.add_textbox(
            Inches(0.55), Inches(0.35), deck.slide_width - Inches(1.1), Inches(0.8)
        )
        titlebox.text_frame.text = title
        titlebox.text_frame.paragraphs[0].font.size = Pt(27)
        box = slide.shapes.add_textbox(
            Inches(0.65),
            Inches(1.4),
            deck.slide_width - Inches(1.3),
            deck.slide_height - Inches(1.7),
        )
        frame = box.text_frame
        frame.word_wrap = True
        for i, line in enumerate(body.splitlines()):
            paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            paragraph.text = line
            paragraph.font.size = Pt(17)
            paragraph.space_after = Pt(10)
        slide.notes_slide.notes_text_frame.text = (
            "Adapted from organizer template; all project claims refer to "
            "saved actual evidence. " + body
        )
    science = json.loads((ROOT / "registry/science.json").read_text())
    slide = deck.slides[7]
    # Replace the explanatory body with actual data; preserve the title.
    element = slide.shapes[-1]._element
    element.getparent().remove(element)
    for id, x, label in [
        ("md_temperature", 0.45, "Maryland annual temperature (°F)"),
        ("chesapeake_cover_crops", 5.1, "Chesapeake cover crops (km²)"),
    ]:
        dataset = next(d for d in science["datasets"] if d["id"] == id)
        chart_data = CategoryChartData()
        chart_data.categories = [str(r["year"]) for r in dataset["observations"]]
        chart_data.add_series(label, [r["value"] for r in dataset["observations"]])
        kind = (
            XL_CHART_TYPE.LINE
            if id.startswith("md_")
            else XL_CHART_TYPE.COLUMN_CLUSTERED
        )
        chart = slide.shapes.add_chart(
            kind, Inches(x), Inches(1.35), Inches(4.4), Inches(3.25), chart_data
        ).chart
        chart.has_title = True
        chart.chart_title.text_frame.text = label
        chart.has_legend = False
        if id.startswith("md_"):
            chart.value_axis.minimum_scale = 52
            chart.value_axis.maximum_scale = 59
        else:
            chart.value_axis.minimum_scale = 0
            chart.value_axis.maximum_scale = 2000
    foot = slide.shapes.add_textbox(
        Inches(0.6), Inches(4.75), Inches(8.8), Inches(0.65)
    )
    foot.text_frame.word_wrap = True
    foot.text_frame.text = (
        "Sources: NOAA NCEI; USGS DOI 10.5066/P9SRZS8P. Different geographies: "
        "separate context, not a joined analysis or causal relationship. "
        "Only two cover-crop observations; no interpolation."
    )
    foot.text_frame.paragraphs[0].font.size = Pt(12)
    deck.save(OUT / "Data.gov-Research-Hackathon.pptx")

    document = Document(OUT / "templates/MCP-hackathon-sample-evaluation-document.docx")
    body = document._element.body
    for child in list(body):
        if not child.tag.endswith("sectPr"):
            body.remove(child)
    document.add_heading("Data.gov Research — Evaluation", 0)
    document.add_paragraph(
        "GSA MCP / AI Agent Hackathon · Trevor Specht · November 19, 2026"
    )
    sections = [
        (
            "1. Overview and Objectives",
            (
                "Evaluate whether a bounded MCP workflow makes public"
                " datasets easier to discover and supported results v"
                "erifiable. The prototype exposes eight tools coverin"
                "g metadata discovery, compatibility, county comparis"
                "on, scientific-series capabilities/querying and save"
                "d evidence. It is a milestone, not a universal data-"
                "joining or causal-analysis system."
            ),
        ),
        (
            "2. Testing Methodology",
            (
                "Core: 12 questions and repeated M1/A1/U3 (18 trials)"
                ". Additional climate/agriculture inventory panel: 9 "
                "questions run twice. Model system.ai.gpt-6-1-sol thr"
                "ough Responses; low reasoning effort; 4,000 output t"
                "okens. Each question starts fresh. Runs freeze quest"
                "ions, prompt, source hashes, model completion metada"
                "ta, arguments and results. Numeric references use in"
                "dependent arithmetic from the publisher files. Human"
                " review and AI review are recorded separately; no LL"
                "M grade substitutes for numerical validation. No con"
                "trolled no-tool baseline was executed."
            ),
        ),
        (
            "3. Performance Metrics and Results",
            (
                "Core final run 20261119T152023Z: 18/18 complete; all"
                " eight comparisons matched. Core AI first-pass revie"
                "w: 13 correct, five correct abstentions; M2 citation"
                " criterion partial. Earlier Opus human review: 16 co"
                "rrect and two partially correct. These are different"
                " runs with changed prompt/model and must not be trea"
                "ted as a controlled comparison. Additional runs 2026"
                "1119T232056Z and 20261119T232423Z: nine of nine comp"
                "lete in each; five scientific queries in each indepe"
                "ndently match raw-source rows and totals. Unsupporte"
                "d causal join, absent-year interpolation and arbitra"
                "ry SQL/local-URL requests were declined. Discovery i"
                "nventories were metadata-only and explicitly non-exh"
                "austive."
            ),
        ),
        (
            "4. Security Considerations",
            (
                "Only public government source data is used. Private "
                "Databricks Apps provide the authentication boundary;"
                " the UI calls MCP without direct warehouse access. M"
                "odel-service access was verified by a real UI query;"
                " an attempted additional grant was denied and no bro"
                "ader grant was added. Tool inputs are validated; ori"
                "gins and prepared sources are fixed; SQL is paramete"
                "rized. Limits bound tool calls, output size, executi"
                "on time and context. Secrets are excluded from sourc"
                "e/staging; checks include dependency audit and stati"
                "c analysis. The explicit SQL/localhost adversarial e"
                "valuation is one case, not a comprehensive penetrati"
                "on test. App-local evidence is not durable across re"
                "starts and is exported."
            ),
        ),
        (
            "5. Lessons Learned and Recommendations",
            (
                "Synthetic fixtures missed real Census encoding and B"
                "LS series/file issues; publisher validation was esse"
                "ntial. Summary counts reduced narrative miscounts. C"
                "ompletion metadata distinguishes interrupted answers"
                " from success. Historical question wording is preser"
                "ved and new questions are self-contained. Scientific"
                " metadata can hide units: practice inputs were acres"
                ", but published catchment fields are square kilometr"
                "es. Maryland climate and Chesapeake practices cannot"
                " be joined as equivalent geography. Future work: bro"
                "ader bindings, comparable geography, durable storage"
                ", client-side conversation memory, more adversarial "
                "tests and a no-tool baseline. Preserve artifacts bef"
                "ore temporary Databricks resources expire."
            ),
        ),
    ]
    for title, text in sections:
        document.add_heading(title, 1)
        document.add_paragraph(text)
    document.add_heading("Evidence and reproducibility", 1)
    document.add_paragraph(
        (
            "Repository: https://github.com/trevorspecht/gsa-mcp-"
            "hackathon-data-gov\nCommands: make check; uv run --ex"
            "tra ui pytest -q; scripts/run_eval.py; scripts/eval_"
            "report.py\nDetailed source and evaluation documentati"
            "on: docs/SCIENCE.md, docs/EVALUATION.md, docs/RESEAR"
            "CH_UI.md. Private verification artifacts are package"
            "d separately after review, not automatically publish"
            "ed."
        )
    )
    for name in ("20261119T232056Z", "20261119T232423Z"):
        run = json.loads(
            (ROOT / f".local/verification/{name}-eval-panel.json").read_text()
        )
        durations = sorted(r["seconds"] for r in run["runs"])
        document.add_paragraph(
            f"{name}: median {durations[len(durations) // 2]:.1f}s; "
            f"range {durations[0]:.1f}–{durations[-1]:.1f}s. "
            "Small observed sample, not a service-level guarantee."
        )
    document.save(OUT / "Data.gov-Research-Evaluation.docx")
    print("Wrote template-based PPTX and DOCX to", OUT)


if __name__ == "__main__":
    main()
