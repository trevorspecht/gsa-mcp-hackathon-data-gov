"""Adapt organizer templates with actual project evidence; keep outputs local."""

import json
from pathlib import Path

from build_deck import build_deck
from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/submission"


def main():
    build_deck()
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
            "not a controlled model comparison.",
            "Two AI reviewers from different model families scored all 25 "
            "current-system runs, reading every answer and full trace and checking "
            "catalog claims against the inspected metadata: Claude Opus 5.5, then "
            "GPT-6 Astra as a second opinion. Neither generated the answers "
            "(GPT-6.1 Sol did). No overall score changed: both give 19 correct and "
            "6 correct abstentions, with no partial or wrong answers.",
            "Five of 150 criterion grades differ: Astra rates citations partial for "
            "D3 (a link built from a catalog slug) and R2 (shortened identifiers), "
            "rates M2 tool selection and U1 citations not applicable, and L2 tool "
            "selection a pass for the brief list. Both agree S7 correctly used no "
            "tools for an unsafe request. Astra saw the Opus scores, so the second "
            "review was not blinded. Human scoring of these runs has not been done. "
            "See eval/results/SECOND-OPINION-REVIEW.md.",
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
            "Small evaluation sample; no no-tool baseline; the current runs have AI "
            "but not human scores. The Databricks workspace is temporary.",
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
                "counts. All 9 series checks across seven questions (S1–S4, S6, "
                "Q1, Q2) matched the frozen publisher-derived snapshot.",
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
        "docs/EVALUATION.md, docs/SCIENCE.md, docs/RESEARCH_UI.md. All 17 run "
        "files since Nov 18 — including failed and interrupted runs — plus HTML "
        "review pages and AI/human score files are in eval/results/ in the "
        "repository; open any review page in a browser."
    )
    document.save(OUT / "Data.gov-Research-Evaluation.docx")


if __name__ == "__main__":
    main()
