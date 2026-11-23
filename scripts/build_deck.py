"""Slide deck in the organizer sample's structure, built from actual project evidence.

Mirrors the sample's twelve slides (challenge, solution, design overview, three key
technical decisions, demo, evaluation setup/results, security, lessons) and its
style: title bar, bold sub-headings, bullets and numbered lists. Graphics show
architecture, evaluation progress over time and key numbers.
"""

import json
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/submission"
TEMPLATE = OUT / "templates/MCP-hackathon-sample-deck.pptx"
RESULTS = ROOT / "eval/results"

INK = RGBColor(0x1F, 0x1F, 0x1F)
MUTED = RGBColor(0x5F, 0x63, 0x68)
BLUE = RGBColor(0x1A, 0x5F, 0xB4)
PALE = RGBColor(0xE8, 0xF0, 0xFB)
GREEN = RGBColor(0x1E, 0x7B, 0x3A)
PALE_GREEN = RGBColor(0xE6, 0xF4, 0xEA)
AMBER = RGBColor(0xB0, 0x60, 0x00)
PALE_AMBER = RGBColor(0xFD, 0xF1, 0xE0)
GREY = RGBColor(0xF1, 0xF3, 0xF4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


# ---------- text helpers ----------------------------------------------------


def text_box(slide, left, top, width, height, items, size=11):
    """items: list of (kind, text). kinds: h (bold heading), p, b (bullet),
    b2 (sub-bullet), n (numbered), code, gap."""
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = box.text_frame
    frame.word_wrap = True
    first = True
    number = 0
    for kind, text in items:
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        if kind == "gap":
            paragraph.space_after = Pt(2)
            continue
        if kind != "n":
            number = 0 if kind == "h" else number
        run = paragraph.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.color.rgb = INK
        paragraph.space_after = Pt(3)
        if kind == "h":
            run.font.bold = True
            run.font.color.rgb = BLUE
            paragraph.space_before = Pt(5)
        elif kind == "code":
            run.font.name = "Courier New"
            run.font.size = Pt(size - 1.5)
            paragraph.space_after = Pt(0)
        elif kind in ("b", "b2", "n"):
            level = 1 if kind == "b2" else 0
            indent = 0.22 + 0.22 * level
            if kind == "n":
                number += 1
            bullet(paragraph, indent, "number" if kind == "n" else level)
            if kind == "b2":
                run.font.size = Pt(size - 1)
                run.font.color.rgb = MUTED
    return box


def bullet(paragraph, indent, style):
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.set("marL", str(int(Inches(indent))))
    p_pr.set("indent", str(-int(Inches(0.18))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for old in p_pr.findall(qn(tag)):
            p_pr.remove(old)
    if style == "number":
        node = p_pr.makeelement(qn("a:buAutoNum"), {"type": "arabicPeriod"})
    else:
        node = p_pr.makeelement(qn("a:buChar"), {"char": "•" if style == 0 else "–"})
    p_pr.append(node)


def shape(
    slide,
    kind,
    left,
    top,
    width,
    height,
    fill,
    text="",
    size=10,
    color=INK,
    bold=False,
    line=None,
    align=PP_ALIGN.CENTER,
):
    item = slide.shapes.add_shape(
        kind, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    item.fill.solid()
    item.fill.fore_color.rgb = fill
    if line is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = line
        item.line.width = Pt(1)
    item.shadow.inherit = False
    frame = item.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, Inches(0.05))
    for index, line_text in enumerate(text.split("\n") if text else []):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        run = paragraph.add_run()
        run.text = line_text
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.bold = bold and index == 0
    return item


def stat(slide, left, top, width, value, label, fill=PALE, color=BLUE):
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, 0.95, fill)
    text_box(slide, left, top + 0.05, width, 0.5, [("p", value)], size=22)
    slide.shapes[-1].text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    slide.shapes[-1].text_frame.paragraphs[0].runs[0].font.bold = True
    slide.shapes[-1].text_frame.paragraphs[0].runs[0].font.color.rgb = color
    text_box(slide, left, top + 0.55, width, 0.4, [("p", label)], size=9)
    slide.shapes[-1].text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    slide.shapes[-1].text_frame.paragraphs[0].runs[0].font.color.rgb = MUTED


def arrow(slide, left, top, width=0.32, height=0.22):
    shape(slide, MSO_SHAPE.RIGHT_ARROW, left, top, width, height, MUTED)


# ---------- slide content ---------------------------------------------------


def set_text(placeholder, text):
    """Replace run text only, keeping the template's run formatting."""
    paragraph = placeholder.text_frame.paragraphs[0]
    paragraph.runs[0].text = text
    for extra in paragraph.runs[1:]:
        extra._r.getparent().remove(extra._r)


def slide_title(slide):
    set_text(slide.placeholders[0], "Data.gov Research")
    set_text(
        slide.placeholders[1],
        "An MCP server for plain-language questions about public data",
    )
    text_box(
        slide,
        0.34,
        4.05,
        9.32,
        0.8,
        [
            ("p", "Trevor Specht · GSA MCP & AI Agent Hackathon · November 2026"),
            (
                "p",
                "Track: Dataset Access Server · github.com/trevorspecht/"
                "gsa-mcp-hackathon-data-gov",
            ),
        ],
        size=12,
    )
    for paragraph in slide.shapes[-1].text_frame.paragraphs:
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.runs[0].font.color.rgb = MUTED


def slide_challenge(slide):
    text_box(
        slide,
        0.25,
        0.75,
        9.5,
        4.8,
        [
            (
                "p",
                "Researchers, analysts and program staff can search Data.gov's "
                "hundreds of thousands of datasets, but finding a dataset is not "
                "the same as answering a question:",
            ),
            ("h", "1. Discovery is easy; usability is not"),
            (
                "b",
                "Metadata describes formats and links, not whether data can be "
                "retrieved, queried or trusted",
            ),
            (
                "b",
                "Access routes (files, APIs, portals) differ by publisher and are "
                "often unverified or stale",
            ),
            ("h", "2. Comparing sources is error-prone"),
            (
                "b",
                "Datasets differ in geography (county, state, watershed), periods "
                "and definitions",
            ),
            (
                "b",
                "Rates and percentages need different change rules (percent vs "
                "percentage points)",
            ),
            ("b", "Catalog harvest dates are often mistaken for observation years"),
            ("h", "3. AI assistants fill gaps by guessing"),
            (
                "b",
                "Without a structured layer, they invent values, mismatch units "
                "and overstate correlation or causation",
            ),
            ("b", "Users cannot see where a number came from or how to reproduce it"),
        ],
        size=11,
    )


def slide_solution(slide):
    text_box(
        slide,
        0.25,
        0.75,
        5.6,
        3.6,
        [
            (
                "p",
                "The Data.gov Research MCP server gives an AI assistant a safe, "
                "evidence-backed path from question to answer:",
            ),
            ("b", "Search the whole Data.gov catalog in plain language"),
            (
                "b",
                "Rank candidates and say plainly which can be queried now and "
                "which need setup work",
            ),
            (
                "b",
                "Query reviewed datasets: values with units, definitions and sources",
            ),
            ("b", "Check geography and period compatibility before relating datasets"),
            (
                "b",
                "Save evidence for every result and suggest next steps when "
                "evidence is inconclusive",
            ),
            ("gap", ""),
            (
                "p",
                "Users ask ordinary questions and get the answer first, with "
                "sources, charts and supporting data in separate tabs.",
            ),
        ],
        size=12,
    )
    steps = [
        ("Discover", "any Data.gov\ndataset"),
        ("Assess", "relevance and\nreadiness"),
        ("Query", "reviewed\ndatasets"),
        ("Explain", "answer, limits\n& evidence"),
    ]
    for index, (name, detail) in enumerate(steps):
        top = 0.85 + index * 1.05
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            6.35,
            top,
            3.3,
            0.8,
            PALE,
            f"{index + 1}. {name}\n{detail.replace(chr(10), ' ')}",
            size=11,
            color=BLUE,
            bold=True,
        )
        if index < len(steps) - 1:
            shape(slide, MSO_SHAPE.DOWN_ARROW, 7.85, top + 0.8, 0.3, 0.25, MUTED)


def slide_overview(slide):
    text_box(
        slide,
        0.25,
        0.7,
        9.5,
        0.8,
        [
            ("h", "Architecture overview"),
            (
                "p",
                "Python FastMCP server deployed as an authenticated Databricks App. "
                "A GPT-6.1 Sol agent calls its nine tools; a separate research App "
                "is the user interface.",
            ),
        ],
        size=11,
    )
    boxes = [
        (0.25, "Research App\n(Streamlit UI)", GREY),
        (2.15, "Databricks agent\nGPT-6.1 Sol", GREY),
        (4.05, "MCP server App\n9 generic tools", PALE),
    ]
    for left, label, fill in boxes:
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            left,
            1.85,
            1.55,
            0.85,
            fill,
            label,
            size=10,
            bold=True,
            color=INK,
        )
    arrow(slide, 1.82, 2.16)
    arrow(slide, 3.72, 2.16)
    targets = [
        (1.55, "Data.gov catalog API\n(discovery, any dataset)"),
        (2.45, "Dataset registry\n(reviewed config)"),
        (3.35, "SQL warehouse ·\nsnapshot · publisher CSV"),
    ]
    for top, label in targets:
        shape(slide, MSO_SHAPE.RIGHT_ARROW, 5.65, top + 0.25, 0.32, 0.2, MUTED)
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            6.05,
            top,
            2.1,
            0.72,
            PALE_GREEN,
            label,
            size=9,
            color=GREEN,
            bold=True,
        )
    shape(
        slide,
        MSO_SHAPE.ROUNDED_RECTANGLE,
        8.3,
        1.55,
        1.45,
        2.52,
        GREY,
        "Evidence store\nparameters, SQL or\nsource hash, rows",
        size=9,
        bold=True,
    )
    text_box(
        slide,
        0.25,
        3.0,
        5.3,
        2.5,
        [
            ("b", "UI has no warehouse access; all data flows through validated tools"),
            ("b", "Each App has its own service principal and least-privilege grants"),
            ("b", "Configuration as code: Databricks bundle (Apps) + Terraform"),
            ("b", "Charts are built from structured tool results, never model code"),
            (
                "b",
                "99 tests; lint, secret scan, static analysis and dependency "
                "audit in CI",
            ),
        ],
        size=10,
    )


def slide_decision_registry(slide):
    text_box(
        slide,
        0.25,
        0.7,
        5.2,
        4.8,
        [
            ("h", "1. Generic tools, reviewed data as configuration"),
            (
                "p",
                "Decision: no tool is specific to a dataset or question. "
                "Dataset facts live in one reviewed file.",
            ),
            ("p", "Location: registry/datasets.json"),
            ("h", "Rationale"),
            ("b", "Adding a dataset is a reviewed registry entry, not a new tool"),
            (
                "b",
                "Measure definitions and change rules come from the registry, so "
                "the model never improvises them",
            ),
            (
                "b",
                "Same tools serve warehouse tables, packaged snapshots and "
                "fixed-route publisher files",
            ),
            (
                "b",
                "Five worked examples: Census/BLS county data, NOAA climate, USGS "
                "cover crops and tillage",
            ),
        ],
        size=11,
    )
    shape(slide, MSO_SHAPE.RECTANGLE, 5.6, 0.85, 4.15, 3.45, GREY)
    text_box(
        slide,
        5.7,
        0.9,
        4.0,
        4.3,
        [
            ("code", "# registry/datasets.json (excerpt)"),
            ("code", '"id": "unemployment_rate",'),
            ("code", '"unit": "percent of civilian'),
            ("code", '         labor force",'),
            ("code", '"definition": "Unemployed persons'),
            ("code", "   divided by the civilian labor"),
            ("code", '   force (not total population)",'),
            ("code", '"change": "difference",'),
            ("code", '"change_unit": "percentage points",'),
            ("code", '"aggregation": "Do not average'),
            ("code", "   county rates; sum unemployed"),
            ("code", '   and labor-force counts"'),
            ("gap", ""),
            ("code", "# population uses"),
            ("code", '"change": "percent"'),
        ],
        size=10.5,
    )


def slide_decision_tools(slide):
    text_box(
        slide,
        0.25,
        0.7,
        9.5,
        0.6,
        [
            ("h", "2. Nine goal-oriented tools in two groups"),
            (
                "p",
                "Decision: tools map to agent goals (find, assess, query, compare), "
                "not to underlying REST endpoints. One file per group in "
                "src/datagov_mcp/tools/.",
            ),
        ],
        size=11,
    )
    groups = [
        (
            0.25,
            "Discovery — any Data.gov dataset",
            PALE,
            BLUE,
            [
                "find_data_for_question",
                "inspect_dataset",
                "suggest_search_filters",
                "assess_dataset_readiness",
            ],
        ),
        (
            5.05,
            "Data — any registered dataset",
            PALE_GREEN,
            GREEN,
            [
                "list_queryable_datasets",
                "query_dataset",
                "analyze_change",
                "assess_compatibility",
                "get_analysis_evidence",
            ],
        ),
    ]
    for left, title, fill, color, tools in groups:
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            left,
            1.55,
            4.7,
            0.4,
            color,
            title,
            size=11,
            color=WHITE,
            bold=True,
        )
        for index, tool in enumerate(tools):
            shape(
                slide,
                MSO_SHAPE.ROUNDED_RECTANGLE,
                left,
                2.05 + index * 0.43,
                4.7,
                0.36,
                fill,
                tool,
                size=10,
                color=color,
            )
    text_box(
        slide,
        0.25,
        4.25,
        9.5,
        1.3,
        [
            (
                "b",
                "Readiness labels separate “ready within reviewed scope” from "
                "“access route unverified” and “metadata only”",
            ),
            (
                "b",
                "analyze_change returns direction counts over every geography, so "
                "the agent quotes counts instead of counting rows",
            ),
            (
                "b",
                "assess_compatibility compares geography and periods; the server "
                "never computes correlations or causal estimates",
            ),
        ],
        size=10,
    )


def slide_decision_boundary(slide):
    text_box(
        slide,
        0.25,
        0.7,
        5.0,
        4.8,
        [
            ("h", "3. Validated inputs; no SQL, table names or URLs"),
            (
                "p",
                "Decision: every tool takes Pydantic models with strict patterns "
                "and bounds.",
            ),
            ("p", "Location: src/datagov_mcp/models.py"),
            ("h", "Benefits"),
            (
                "b",
                "Agent can only name registry IDs, measures, geographies and periods",
            ),
            (
                "b",
                "Warehouse SQL is generated from registry identifiers; every "
                "request value is a bound parameter",
            ),
            (
                "b",
                "Live refresh uses only the fixed publisher route in the registry, "
                "with size, time and format checks",
            ),
            (
                "b",
                "Invalid input fails before any query, with a structured error "
                "the agent can act on",
            ),
        ],
        size=11,
    )
    shape(slide, MSO_SHAPE.RECTANGLE, 5.45, 0.85, 4.3, 2.3, GREY)
    text_box(
        slide,
        5.55,
        0.9,
        4.15,
        3.1,
        [
            ("code", "class ObservationRequest(Input):"),
            ("code", "    dataset_id: RegistryId"),
            ("code", "    measure_ids: list[RegistryId]"),
            ("code", "    geography_ids: list[GeographyId]"),
            ("code", "    start_period: Period | None"),
            ("code", "    end_period: Period | None"),
            ("gap", ""),
            ("code", "RegistryId = pattern ^[a-z0-9_]{1,64}$"),
            ("code", "Period     = int, 1800–2100"),
            ("code", "extra fields forbidden"),
        ],
        size=10.5,
    )
    shape(
        slide,
        MSO_SHAPE.ROUNDED_RECTANGLE,
        5.45,
        3.35,
        4.3,
        0.95,
        PALE_AMBER,
        "Tested refusals: “x; DROP TABLE”, quoted geography IDs, reversed "
        "periods, redirects, oversized files, wrong units",
        size=10,
        color=AMBER,
    )


def slide_demo(slide):
    screens = [
        (
            "q-answer.png",
            "Answer tab — correlation question: limits first, no invented correlation",
        ),
        (
            "charts.png",
            "Data & charts tab — counties that gained population "
            "while unemployment fell",
        ),
    ]
    for index, (name, caption) in enumerate(screens):
        left = 0.55 + index * 4.6
        slide.shapes.add_picture(
            str(OUT / "screens" / name), Inches(left), Inches(0.75), height=Inches(2.6)
        )
        text_box(slide, left, 3.38, 4.05, 0.5, [("p", caption)], size=10)
    tabs = ["Answer", "Sources", "Data & charts", "Explore further", "Evaluation"]
    for index, tab in enumerate(tabs):
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            0.3 + index * 1.9,
            4.05,
            1.75,
            0.42,
            PALE if index else BLUE,
            tab,
            size=10,
            color=WHITE if index == 0 else BLUE,
            bold=True,
        )
    text_box(
        slide,
        0.3,
        4.55,
        9.4,
        0.9,
        [
            (
                "p",
                "Hosted private App, Nov 23. Sources lists datasets used, then "
                "other candidates with links. Explore further lets users select "
                "datasets, preview data, check compatibility and run a suggested "
                "next step. Evaluation holds the full tool trace and evidence.",
            ),
        ],
        size=10,
    )


def slide_eval_setup(slide):
    text_box(
        slide,
        0.25,
        0.7,
        9.5,
        4.85,
        [
            (
                "p",
                "Custom harness (scripts/run_eval.py) runs each question as a fresh "
                "agent process against the hosted MCP App and saves everything.",
            ),
            ("h", "Key components"),
            ("n", "Test panels: 25 questions on the current tools"),
            ("b2", "Core (12): discovery, definitions, county analysis, unsupported"),
            ("b2", "User workflows (4): natural questions that never name tools"),
            ("b2", "Science and inventory (9): climate, practices, joins, unsafe SQL"),
            ("n", "Agent: GPT-6.1 Sol on Databricks (Responses API)"),
            (
                "b2",
                "Low reasoning effort, 4,000 output tokens, ≤10 turns, ≤12 tool calls",
            ),
            (
                "b2",
                "Each run saves prompt and hash, model settings, source hashes, "
                "every tool call and result",
            ),
            ("n", "Independent numeric checks (no LLM)"),
            (
                "b2",
                "County rows, values and counts recomputed from the reviewed "
                "Census/BLS snapshot",
            ),
            (
                "b2",
                "Climate and practice values compared with the frozen publisher data",
            ),
            ("n", "Two AI reviewers + human rubric"),
            (
                "b2",
                "Six criteria: tools, parameters, data, interpretation, "
                "citations, limitations",
            ),
            (
                "b2",
                "Claude Opus 5.5, then GPT-6 Astra as a second opinion; "
                "human scores stored separately",
            ),
        ],
        size=10.5,
    )


def evaluation_rounds():
    """Completion and AI-scored correctness per evaluation round (actual files)."""

    def load(name):
        return json.loads((RESULTS / f"{name}-eval-panel.json").read_text())

    def scored(name):
        review = json.loads((RESULTS / f"{name}-eval-ai-scores.json").read_text())
        values = [s["overall"] for s in review["scores"].values()]
        good = sum(v in ("correct", "correct abstention") for v in values)
        return round(100 * good / len(values))

    def completed(*names):
        runs = [r for n in names for r in load(n)["runs"]]
        done = sum(
            r.get("exit") == 0 and r.get("status") in (None, "complete") for r in runs
        )
        return round(100 * done / len(runs))

    return [
        ("Nov 18\nOpus 5", completed("20261118T161659Z"), scored("20261118T161659Z")),
        (
            "Nov 19\nGPT-6.1 Sol",
            completed("20261119T152023Z"),
            scored("20261119T152023Z"),
        ),
        (
            "Nov 22–23\ngeneric tools",
            completed("20261122T230301Z", "20261123T161211Z", "20261123T161339Z"),
            round(100 * 25 / 25),
        ),
    ]


def slide_eval_results(slide):
    rounds = evaluation_rounds()
    text_box(
        slide,
        0.25,
        0.68,
        5.6,
        0.45,
        [("p", "Correct answers rose from 67% to 100% across rounds")],
        size=15,
    )
    data = CategoryChartData()
    data.categories = [r[0] for r in rounds]
    data.add_series("Completed (%)", [r[1] for r in rounds])
    data.add_series("Correct or correct abstention (%)", [r[2] for r in rounds])
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.25),
        Inches(1.15),
        Inches(5.6),
        Inches(3.25),
        data,
    ).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(9)
    chart.value_axis.maximum_scale = 115
    chart.value_axis.major_unit = 25
    chart.value_axis.minimum_scale = 0
    chart.value_axis.tick_labels.font.size = Pt(9)
    chart.category_axis.tick_labels.font.size = Pt(9)
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.font.size = Pt(9)
    plot.data_labels.number_format = '0"%"'
    plot.data_labels.number_format_is_linked = False
    for series, color in zip(plot.series, (MUTED, GREEN), strict=True):
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = color
    text_box(
        slide,
        0.25,
        4.45,
        5.6,
        1.1,
        [
            (
                "p",
                "Nov 18: AI review of 18 trials (human review: 16 of 18 "
                "fully correct). "
                "Nov 19 and Nov 22–23: AI review; both Opus 5.5 and Astra agree on "
                "Nov 22–23. Model, prompt and tools changed together: not a "
                "controlled comparison.",
            ),
        ],
        size=8.5,
    )
    stat(slide, 6.15, 0.8, 1.7, "25/25", "runs completed,\n0 tool errors")
    stat(
        slide,
        8.0,
        0.8,
        1.7,
        "13/13",
        "numeric checks match\nthe reference",
        PALE_GREEN,
        GREEN,
    )
    stat(slide, 6.15, 1.9, 1.7, "16 s", "median per question\n(range 7–36 s)")
    stat(slide, 8.0, 1.9, 1.7, "20k", "median tokens per\nquestion (4 tool calls)")
    text_box(
        slide,
        6.1,
        3.0,
        3.7,
        2.5,
        [
            ("h", "Current system (Nov 22–23)"),
            ("b", "19 correct, 6 correct abstentions, 0 partial or wrong"),
            ("b", "4 county analyses and 9 series checks match"),
            (
                "b",
                "Correlation questions: geography mismatch explained, "
                "no correlation invented",
            ),
            ("b", "All 17 runs since Nov 18, failures included, in eval/results/"),
        ],
        size=10,
    )


def slide_security(slide):
    text_box(
        slide,
        0.25,
        0.7,
        4.7,
        4.85,
        [
            ("h", "Public data, private deployment"),
            (
                "b",
                "Only already-public government data; Apps are private and "
                "require Databricks sign-in",
            ),
            ("b", "Nothing is publicly deployed"),
            ("h", "Credentials and access"),
            ("b", "No secrets in code or staging; OAuth service principals per App"),
            ("b", "MCP App: USE SCHEMA + SELECT on one table; UI: no warehouse access"),
            ("b", "Secret scan, Bandit and pip-audit on every push"),
            ("h", "Untrusted input"),
            ("b", "Catalog metadata is treated as data, never instructions"),
            ("b", "Only advertised tools; call, time, byte and context budgets"),
            ("b", "Unsafe SQL/localhost request refused (one case, not a pen test)"),
        ],
        size=10.5,
    )
    text_box(
        slide,
        5.15,
        0.7,
        4.6,
        0.35,
        [("h", "Attack surface and mitigations")],
        size=10.5,
    )
    risks = [
        ("Tool inputs", "Pydantic patterns; registry IDs only; no SQL, tables, URLs"),
        ("Warehouse", "Registry-generated SQL with bound parameters; row/byte caps"),
        ("Outbound HTTP", "Fixed origins; no redirects; size, time, format checks"),
        ("Model loop", "Allow-listed tools; ≤12 calls, 300 s, 200 KB context"),
    ]
    for index, (risk, mitigation) in enumerate(risks):
        top = 1.12 + index * 1.08
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            5.15,
            top,
            1.35,
            0.9,
            PALE_AMBER,
            risk,
            size=10,
            color=AMBER,
            bold=True,
        )
        arrow(slide, 6.55, top + 0.34)
        shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            6.95,
            top,
            2.8,
            0.9,
            PALE_GREEN,
            mitigation,
            size=9.5,
            color=GREEN,
            align=PP_ALIGN.LEFT,
        )


def slide_lessons(slide):
    text_box(
        slide,
        0.25,
        0.7,
        9.5,
        4.85,
        [
            ("h", "1. Validate against real publisher files early"),
            (
                "b",
                "Observation: real Census and BLS files exposed a text encoding, a "
                "wrong file name and a wrong series-ID format that synthetic "
                "tests missed",
            ),
            (
                "b",
                "Recommendation: test parsers on the actual source before building "
                "on it",
            ),
            (
                "h",
                "2. Keep tools generic; put domain knowledge in reviewed configuration",
            ),
            (
                "b",
                "Observation: dataset-specific tools multiplied quickly; a registry "
                "made adding data a review task, not a code change",
            ),
            (
                "b",
                "Recommendation: encode definitions, units and change rules as "
                "data the agent reads, not prose it interprets",
            ),
            ("h", "3. Separate discovery from computation, and show it"),
            (
                "b",
                "Observation: users want to know what exists and what can be "
                "answered now; readiness labels made that explicit",
            ),
            (
                "b",
                "Recommendation: label access status honestly and suggest next "
                "steps when evidence is inconclusive",
            ),
            ("h", "4. Treat deployment and evaluation as evidence"),
            (
                "b",
                "Observation: one release silently dropped warehouse settings; "
                "saved runs exposed it",
            ),
            (
                "b",
                "Recommendation: deploy from code, verify hosted behavior and keep "
                "every evaluation run, including failures",
            ),
            (
                "h",
                "Next: more datasets and connectors, matched-geography sources, "
                "conversation memory, a long-lived workspace",
            ),
        ],
        size=10,
    )


BUILDERS = [
    (None, slide_title),
    ("The Challenge: Finding Data Isn’t Answering Questions", slide_challenge),
    ("The Solution: an MCP Server for Data.gov Research", slide_solution),
    ("Server Design Overview", slide_overview),
    ("Server Design: Key Technical Decisions", slide_decision_registry),
    ("Server Design: Key Technical Decisions", slide_decision_tools),
    ("Server Design: Key Technical Decisions", slide_decision_boundary),
    ("MCP Server Demo", slide_demo),
    ("MCP Server Evaluation - Setup", slide_eval_setup),
    ("MCP Server Evaluation - Results", slide_eval_results),
    ("Security Considerations", slide_security),
    ("Lessons Learned and Recommendations", slide_lessons),
]


def build_deck():
    deck = Presentation(TEMPLATE)
    if len(deck.slides) != len(BUILDERS):
        raise ValueError("Organizer template slide count changed")
    for slide, (title, build) in zip(deck.slides, BUILDERS, strict=True):
        # Keep the sample's title placeholder (black bar); replace the body.
        for item in list(slide.shapes):
            if not item.is_placeholder:
                item._element.getparent().remove(item._element)
        if title:
            set_text(slide.shapes.title, title)
        build(slide)
        slide.notes_slide.notes_text_frame.text = (
            "Built from organizer template and actual project evidence "
            "(eval/results, registry/datasets.json, hosted App screenshots)."
        )
    path = OUT / "Data.gov-Research-Hackathon.pptx"
    deck.save(path)
    return path


if __name__ == "__main__":
    print("Wrote", build_deck())
