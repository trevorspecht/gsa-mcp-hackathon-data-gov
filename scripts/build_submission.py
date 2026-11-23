"""Adapt organizer templates with actual project evidence; keep outputs local."""

import json
from pathlib import Path

from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/submission"
SLIDES = [
    (
        "Data.gov Research",
        "From a plain-language question to discoverable public data, and, where "
        "supported, a verifiable answer.\n"
        "Trevor Specht · GSA MCP / AI Agent Hackathon · November 2026\n"
        "Track: Dataset Access Server. A working stage in an ongoing project.",
    ),
    (
        "The challenge: finding data is not answering a question",
        "Data.gov lists hundreds of thousands of datasets with inconsistent "
        "metadata, formats, periods and definitions.\n"
        "A search hit does not show whether data can be retrieved, compared or "
        "used to answer the question.\n"
        "AI assistants without a structured layer guess: invented values, "
        "mismatched units, causal overreach.\n"
        "Mission: make public data usable for government and non-government "
        "research, service delivery and oversight.",
    ),
    (
        "The solution: discover, assess, query, explain",
        "Search across all of Data.gov in plain language.\n"
        "Rank candidates and say plainly which can be queried now and which need "
        "setup work.\n"
        "Query reviewed datasets and return values with units, definitions, "
        "sources and evidence IDs.\n"
        "Check whether datasets can be compared before relating them, and suggest "
        "next steps when the evidence is inconclusive.",
    ),
    (
        "Architecture",
        "Research App (Streamlit) → Databricks-hosted GPT-6.1 Sol agent → "
        "authenticated MCP server App.\n"
        "MCP server → Data.gov catalog API (discovery) and a reviewed dataset "
        "registry (data).\n"
        "Registry connectors: Databricks SQL warehouse table, packaged reviewed "
        "snapshot, fixed-route publisher CSV refresh.\n"
        "The UI has no direct warehouse access; all data flows through validated "
        "MCP tools. Configuration lives in code (bundle + Terraform).",
    ),
    (
        "Key decision: generic tools, reviewed data as configuration",
        "Nine tools, none specific to a dataset or question: search, inspect, "
        "filters, readiness, list_queryable_datasets, query_dataset, "
        "analyze_change, assess_compatibility, evidence.\n"
        "Dataset facts (measures, units, definitions, geography, periods, sources) "
        "live in registry/datasets.json.\n"
        "Adding a dataset means a reviewed registry entry, not a new tool.\n"
        "Change rules come from the registry: percent for population, percentage "
        "points for unemployment rates.",
    ),
    (
        "Key decision: discovery is broader than computation",
        "Any Data.gov record can be found and inspected; only reviewed datasets "
        "return observations.\n"
        "Readiness labels: ready within reviewed scope, setup required, access "
        "route unverified, metadata only.\n"
        "Tools never accept SQL, table names or URLs; SQL is generated from "
        "registry identifiers with bound parameters.\n"
        "Compatibility checks compare geography and periods; the server never "
        "computes correlations or causal estimates.",
    ),
    (
        "Key decision: evidence and honest limits",
        "Every query and analysis saves an evidence record: parameters, SQL or "
        "source hash, sources and rows.\n"
        "Summary counts cover every compared geography, so the agent quotes "
        "counts instead of counting rows.\n"
        "Missing years stay missing; endpoint change is never presented as a trend.\n"
        "Unsupported questions get a clear boundary plus useful discovery, not a "
        "substituted answer.",
    ),
    (
        "Demonstration: answer first, details in tabs",
        "",
    ),
    (
        "Evaluation setup",
        "Three panels, 25 questions, run on the generic tools (Nov 22–23): core "
        "(12), user workflows (4), science and inventory (9).\n"
        "Categories: discovery, methodology, analysis, unsupported and "
        "adversarial requests.\n"
        "Each run saves the exact prompt, model settings, source hashes, tool "
        "trace and completion status.\n"
        "Numbers are checked by independent arithmetic against the publisher "
        "data, not by an LLM judge.\n"
        "Offline HTML review pages support separate human and AI rubric scoring.",
    ),
    (
        "Evaluation results",
        "25/25 runs completed; 0 tool errors; median 16 s per question "
        "(range 7–36 s).\n"
        "All 4 county analyses matched the reference (rows, values, summary counts).\n"
        "All 8 climate/agriculture series checks matched the frozen publisher data.\n"
        "Correlation questions: compatibility checked, geography mismatch explained, "
        "no correlation invented.\n"
        "Iterative improvement since Nov 18: Opus 5 → GPT-6.1 Sol, summary counts, "
        "completion checks, generic tools. Not a controlled model comparison.",
    ),
    (
        "Security considerations",
        "Public government data only; private, authenticated Databricks Apps.\n"
        "Pydantic-validated inputs; fixed origins; bound SQL parameters; no "
        "redirects; time, byte, row and tool-call budgets.\n"
        "Catalog metadata treated as untrusted data, never as instructions.\n"
        "Secrets kept out of source and staging; secret scan, static analysis and "
        "dependency audit in CI.\n"
        "Adversarial SQL/localhost request refused. Not a full penetration test.",
    ),
    (
        "Lessons learned and next steps",
        "Real publisher files exposed encoding, file-name and series-ID errors "
        "that synthetic tests missed.\n"
        "Keeping tools generic forced a clear line between code and reviewed data.\n"
        "Deployment drift is real: releases now go through the code-based bundle.\n"
        "Next: more registry datasets and connectors, matched-geography sources, "
        "conversational memory, durable evidence, a new Databricks workspace.\n"
        "Repository: github.com/trevorspecht/gsa-mcp-hackathon-data-gov",
    ),
]

SCREENS = [
    (
        "q-answer.png",
        "“Is there a correlation between climate patterns and agricultural "
        "practices…?” Answer tab: limits explained first; no invented correlation.",
    ),
    (
        "charts.png",
        "“Which Maryland counties gained population while unemployment fell?” "
        "Data & charts tab: generic bars from analyze_change (Worcester County).",
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
    # Slide 8: actual hosted UI screenshots captured during browser verification.
    slide = deck.slides[7]
    element = slide.shapes[-1]._element
    element.getparent().remove(element)
    width = (deck.slide_width - Inches(1.2)) / len(SCREENS)
    for index, (name, caption) in enumerate(SCREENS):
        left = Inches(0.45) + index * width
        slide.shapes.add_picture(
            str(OUT / "screens" / name), left, Inches(1.2), width=width - Inches(0.2)
        )
        label = slide.shapes.add_textbox(
            left, Inches(3.95), width - Inches(0.2), Inches(0.7)
        )
        label.text_frame.word_wrap = True
        label.text_frame.text = caption
        label.text_frame.paragraphs[0].font.size = Pt(11)
    foot = slide.shapes.add_textbox(Inches(0.6), Inches(4.95), Inches(8.8), Inches(0.5))
    foot.text_frame.word_wrap = True
    foot.text_frame.text = (
        "Two questions in the hosted private App, Nov 23. Five tabs: Answer · "
        "Sources (datasets used, then other candidates, with links) · Data & charts "
        "· Explore further (select datasets, preview, compatibility, next step) · "
        "Evaluation (tool trace, evidence download)."
    )
    foot.text_frame.paragraphs[0].font.size = Pt(11)
    deck.save(OUT / "Data.gov-Research-Hackathon.pptx")

    write_evaluation()
    print("Wrote template-based PPTX and DOCX to", OUT)


PANELS = {
    "20261122T230301Z": "Core (12)",
    "20261123T161211Z": "User workflows (4)",
    "20261123T161339Z": "Science and inventory (9)",
}

EVALUATION = [
    (
        "1. Overview and Objectives",
        None,
        [
            "Data.gov Research is an MCP server that helps an AI assistant answer "
            "plain-language questions with public government data. It searches the "
            "whole Data.gov catalog, says which datasets can be queried now, queries "
            "reviewed datasets, and returns values with units, definitions, sources "
            "and saved evidence.",
            "This evaluation asks four questions: (1) Does the agent pick the right "
            "tools and parameters? (2) Are returned numbers correct, checked against "
            "the publisher data? (3) Does the agent stay inside what the data "
            "supports, refusing unsupported, causal or unsafe requests? (4) Is the "
            "server stable "
            "across a varied question set?",
            "The server has nine dataset-agnostic tools. Dataset-specific facts live "
            "in a reviewed registry (registry/datasets.json), currently five datasets: "
            "Maryland county population and unemployment (Census/BLS, Databricks SQL "
            "warehouse), Maryland annual temperature and precipitation (NOAA, with a "
            "fixed-route live refresh), and Chesapeake Bay watershed cover-crop and "
            "conservation-tillage estimates (USGS).",
        ],
    ),
    (
        "2. Testing Methodology",
        "Framework & reproducibility",
        [
            "scripts/run_eval.py runs each question as a fresh, independent agent "
            "process against the hosted MCP App and saves everything: the exact "
            "question, system prompt and its SHA-256, model settings, source-file "
            "hashes, every tool call with arguments and results, model completion "
            "metadata and timing. Failed and interrupted runs are kept, not discarded. "
            "scripts/eval_report.py builds an offline HTML review page per run with "
            "answers, full traces, automated checks and rubric fields.",
            "Model: system.ai.gpt-6-1-sol on Databricks through the Responses API; "
            "low reasoning effort; 4,000 output tokens; at most 10 model turns and 12 "
            "tool calls per question. No conversation memory between questions.",
        ],
    ),
    (
        None,
        "Golden dataset",
        [
            "25 questions in three committed panels: eval/questions.json (core: "
            "discovery, methodology, analysis, unsupported), eval/user-workflows.json "
            "(natural dataset-list and research questions that never name tools) and "
            "eval/climate-agriculture.json (inventories, scientific queries, "
            "unsupported joins, interpolation and an adversarial SQL/localhost "
            "request). Each question records its expected behavior.",
            "Numeric references are computed independently of the server: county "
            "changes from the reviewed 72-row Census/BLS snapshot, and science values "
            "from the frozen publisher-derived snapshot embedded in each panel.",
        ],
    ),
    (
        None,
        "Evaluators",
        [
            "Automated checks compare returned rows, row order, values (within "
            "1e-6) and summary counts against the independent reference, and flag "
            "incomplete runs, tool errors and answers with no tool calls. These do "
            "not depend on an LLM.",
            "Qualitative scoring uses a six-criterion rubric (tool selection, "
            "parameters, returned data, interpretation, citations, limitations) with "
            "overall labels: correct, partially correct, wrong, correct abstention, "
            "erroneous refusal, environment-blocked. Human scores and a separate, "
            "read-only AI review are stored independently and bound to the exact "
            "panel file hash.",
        ],
    ),
    (
        None,
        "Test design rationale",
        [
            "Questions cover breadth (discovery across unrelated topics), depth "
            "(exact county and scientific values), definitions (denominators, "
            "aggregation, harvest vs observation dates), boundaries (unsupported "
            "geography, measures and years), causal and correlation overreach, and "
            "unsafe input. User-workflow questions are phrased the way a person would "
            "ask, so they test whether the agent uses readiness and compatibility "
            "checks without being told to.",
        ],
    ),
    (
        "3. Performance Metrics",
        "Metrics tracked",
        [
            "Completion rate, tool errors, numeric accuracy against reference, "
            "summary-count accuracy, number of tool calls, wall-clock time per "
            "question, and rubric scores.",
        ],
    ),
    (None, "Results", None),
    (
        None,
        "Failure analysis",
        [
            "Two answers (M2: harvest vs observation dates; S7: unsafe SQL/localhost "
            "request) used no tools. Both were correct, but they are reported as not "
            "MCP-backed. A November 22 network outage caused four timeouts in the "
            "workflow and science panels; those runs are preserved and the panels "
            "were rerun after recovery. Earlier iterations exposed real problems "
            "that were fixed: unfinished answers, an invented page count, "
            "metadata/vintage confusion, county miscounts (fixed with summary "
            "counts), and a deployment that silently dropped the MCP App's warehouse "
            "settings (fixed by releasing only through the code-based bundle).",
            "Earlier panels (Nov 18–19, Opus 5 then GPT-6.1 Sol) are retained. The "
            "final human review of the Nov 18 panel scored 16 correct and 2 partially "
            "correct. Model, prompt and tools changed between rounds, so these are "
            "not a controlled model comparison. Human and AI scoring of the Nov 22–23 "
            "panels is pending.",
        ],
    ),
    (
        "4. Security Considerations",
        "Data classification",
        [
            "Only already-public government data is used. Prototypes run as private, "
            "authenticated Databricks Apps in a hackathon sandbox; nothing is publicly "
            "deployed.",
        ],
    ),
    (
        None,
        "Scope containment as a control",
        [
            "Tools accept only registry IDs, measure IDs, geography IDs and periods, "
            "validated by Pydantic models with strict patterns. No tool accepts SQL, "
            "table names or URLs. Warehouse SQL is generated from validated registry "
            "identifiers with every request value bound as a parameter. Live refresh "
            "uses only the fixed publisher route in the registry, with no redirects "
            "and size, time and format validation. The server never computes "
            "correlations, joins or causal estimates.",
        ],
    ),
    (
        None,
        "Secrets & configuration",
        [
            "Credentials live in an ignored .env file or the OS keyring and are never "
            "written to source, staging folders or logs. Apps use injected OAuth "
            "service-principal credentials. CI runs a secret scan, static analysis "
            "(Bandit) and dependency audit (pip-audit). Deployment configuration is "
            "code: a Databricks bundle for the Apps and Terraform for prerequisites.",
        ],
    ),
    (
        None,
        "Untrusted input & prompt injection",
        [
            "Catalog metadata is labeled untrusted data and the agent is instructed "
            "never to follow it as instructions. Only advertised MCP tools can be "
            "called, within call, output-size, context and time budgets. An "
            "adversarial request for arbitrary SQL and a localhost download was "
            "refused. This is one case, not a full penetration test.",
        ],
    ),
    (
        None,
        "Transport & isolation",
        [
            "Databricks Apps provide HTTPS and authentication. The research UI calls "
            "the MCP App with its own service principal and has no direct warehouse "
            "access; only the MCP App's principal can read the reviewed table. TLS is "
            "verified through the OS trust store. Evidence is stored on the MCP App's "
            "local disk and may not survive restarts; users can download it.",
        ],
    ),
    (
        "5. Lessons Learned & Recommendations",
        "What worked",
        [
            "Generic tools plus a reviewed registry kept tool code independent of any "
            "dataset. Independent numeric checks caught errors an LLM judge would "
            "miss. Summary counts stopped the agent from miscounting rows. Separating "
            "discovery from computation let the agent be helpful about every topic "
            "while staying exact about the data it can query.",
        ],
    ),
    (
        None,
        "Limitations",
        [
            "Only five datasets can return observations; most catalog records are "
            "discovery-only. The climate and agricultural series cover different "
            "geography, so they cannot support a correlation. No conversation memory. "
            "Small evaluation sample; no no-tool baseline; scoring of the newest "
            "panels is pending. The Databricks workspace is temporary.",
        ],
    ),
    (
        None,
        "Recommendations",
        [
            "Validate against real publisher files early: they exposed an encoding "
            "issue, a wrong file name and a wrong series-ID format that synthetic "
            "fixtures missed. Keep deployment configuration in code and verify hosted "
            "behavior after every release. Save every evaluation run, including "
            "failures. Next steps: more registry datasets and connectors, sources "
            "with matching geography and periods, conversational memory, durable "
            "evidence storage, and migration to a long-lived workspace.",
        ],
    ),
]


def panel_rows():
    import statistics

    rows = []
    for name, label in PANELS.items():
        panel = json.loads(
            (ROOT / f".local/verification/{name}-eval-panel.json").read_text()
        )
        runs = panel["runs"]
        seconds = [r["seconds"] for r in runs]
        errors = sum(
            1
            for r in runs
            for s in r.get("trace", [])
            if isinstance(s.get("result"), dict) and s["result"].get("error")
        )
        rows.append(
            [
                label,
                name,
                f"{sum(r.get('status') == 'complete' for r in runs)}/{len(runs)}",
                str(errors),
                f"{statistics.median(seconds):.1f} s",
                f"{min(seconds):.1f}–{max(seconds):.1f} s",
            ]
        )
    return rows


def write_evaluation():
    document = Document(OUT / "templates/MCP-hackathon-sample-evaluation-document.docx")
    body = document._element.body
    for child in list(body):
        if not child.tag.endswith("sectPr"):
            body.remove(child)
    document.add_heading("Data.gov Research — Evaluation", 0)
    document.add_paragraph(
        "GSA MCP / AI Agent Hackathon · Trevor Specht · November 23, 2026 · "
        "github.com/trevorspecht/gsa-mcp-hackathon-data-gov"
    )
    for section, subsection, paragraphs in EVALUATION:
        if section:
            document.add_heading(section, 1)
        if subsection:
            document.add_heading(subsection, 2)
        if paragraphs is None:
            table = document.add_table(rows=1, cols=6)
            headers = ["Panel", "Run", "Completed", "Tool errors", "Median", "Range"]
            for cell, text in zip(table.rows[0].cells, headers, strict=True):
                cell.text = text
            for values in panel_rows():
                for cell, text in zip(table.add_row().cells, values, strict=True):
                    cell.text = text
            for line in [
                "Numeric accuracy: all 4 county analyses (A1, A2, A3, U3) matched "
                "the independent reference for rows, order, values and summary "
                "counts. All 8 science checks (S1–S4, S6, Q1, Q2) matched the "
                "frozen publisher-derived snapshot.",
                "Boundaries: unsupported geography (California), measure "
                "(advertising spend), causation, interpolation of a missing year, "
                "and a climate–practice join were all declined with explanations. "
                "Correlation questions called assess_compatibility and reported "
                "the geography mismatch instead of computing a correlation.",
                "Tool use: median 4 tool calls per question (maximum 11). Times "
                "are a small observed sample, not a service-level guarantee.",
            ]:
                document.add_paragraph(line)
            continue
        for text in paragraphs:
            document.add_paragraph(text).paragraph_format.space_after = Pt(8)
    document.add_heading("Evidence and reproducibility", 1)
    document.add_paragraph(
        "Commands: make check (lint, 99 tests, docs, secret scan, static "
        "analysis, dependency audit, build); scripts/run_eval.py --questions "
        "<panel>; scripts/eval_report.py <panel>. Method details: "
        "docs/EVALUATION.md, docs/SCIENCE.md, docs/RESEARCH_UI.md. Run files and "
        "review pages are kept privately and can be shared with judges on request."
    )
    document.save(OUT / "Data.gov-Research-Evaluation.docx")


if __name__ == "__main__":
    main()
