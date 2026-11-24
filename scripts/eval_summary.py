"""Build a multi-page PDF summarizing every evaluation run over time.

Reads the published run files and score files in eval/results/ and writes
eval/results/EVALUATION-SUMMARY.pdf. All figures come from those files.
"""

import importlib.util
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval/results"
OUTPUT = RESULTS / "EVALUATION-SUMMARY.pdf"
SPEC = importlib.util.spec_from_file_location("report", ROOT / "scripts/eval_report.py")
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)

# Short labels for each run, from eval/results/README.md.
NOTES = {
    "20261118T154713Z": ("Core v1", "Original tools", "First live panel"),
    "20261118T161659Z": ("Core v1", "Original tools", "Summary counts added"),
    "20261119T150947Z": ("Core", "Original tools", "First run on new model"),
    "20261119T151545Z": ("Core", "Original tools", "Interrupted by App redeploy"),
    "20261119T152023Z": ("Core", "Original tools", "Final run of original tools"),
    "20261119T232056Z": ("Science", "+ science tools", "Science panel added"),
    "20261119T232423Z": ("Science", "+ science tools", "Repeat round"),
    "20261120T223428Z": ("Workflows", "+ readiness", "Relationship question failed"),
    "20261120T223552Z": ("Workflows", "+ readiness", "Retry of failed question"),
    "20261120T223719Z": ("Workflows", "+ readiness", "After prompt change"),
    "20261122T180248Z": ("Workflows", "+ exploration", "Relationship question failed"),
    "20261122T180341Z": ("Workflows", "+ exploration", "Failed retry"),
    "20261122T230301Z": ("Core", "Generic 9 tools", "Current system"),
    "20261122T230554Z": ("Workflows", "Generic 9 tools", "Network outage"),
    "20261122T232926Z": ("Science", "Generic 9 tools", "Network outage"),
    "20261123T161211Z": ("Workflows", "Generic 9 tools", "Current system"),
    "20261123T161339Z": ("Science", "Generic 9 tools", "Current system"),
}
CURRENT = ["20261122T230301Z", "20261123T161211Z", "20261123T161339Z"]
PANEL_COLORS = {
    "Core v1": "#7f8c8d",
    "Core": "#1a5fb4",
    "Science": "#1e7b3a",
    "Workflows": "#b06000",
}
GRADES = [
    "correct",
    "correct abstention",
    "partially correct",
    "wrong",
    "erroneous refusal",
    "environment-blocked",
]
GRADE_COLORS = ["#1e7b3a", "#6fbf73", "#f0ad4e", "#c0392b", "#8e44ad", "#95a5a6"]
INK, MUTED = "#1f1f1f", "#5f6368"


def load(name):
    return json.loads((RESULTS / f"{name}-eval-panel.json").read_text())


def completed(run):
    return run.get("exit") == 0 and run.get("status") in (None, "complete")


def numeric_steps(run, reference, science):
    """(passed, failed) count of data steps checked against the reference."""
    passed = failed = 0
    for step in run.get("trace", []):
        single = {"exit": 0, "status": "complete", "trace": [step]}
        levels = [
            level
            for level, message in report.check_run(single, reference, science)
            if level in ("pass", "fail") and "Model run" not in message
        ]
        if levels:
            if "fail" in levels:
                failed += 1
            else:
                passed += 1
    return passed, failed


def scores(path):
    data = json.loads(path.read_text())
    return Counter(s["overall"] for s in data["scores"].values()), data


def runs_table(reference):
    rows = []
    for name in NOTES:
        panel = load(name)
        runs = panel["runs"]
        seconds = [r["seconds"] for r in runs]
        checks = [
            numeric_steps(r, reference, panel.get("science_snapshot")) for r in runs
        ]
        rows.append(
            {
                "name": name,
                "when": datetime.strptime(name, "%Y%m%dT%H%M%SZ"),
                "panel": NOTES[name][0],
                "tools": NOTES[name][1],
                "note": NOTES[name][2],
                "model": panel.get("model_endpoint", "")
                .replace("databricks-", "")
                .replace("system.ai.", ""),
                "runs": len(runs),
                "complete": sum(completed(r) for r in runs),
                "checks_pass": sum(c[0] for c in checks),
                "checks_fail": sum(c[1] for c in checks),
                "median_s": statistics.median(seconds),
            }
        )
    return rows


def header(fig, title, subtitle=""):
    fig.text(0.05, 0.94, title, fontsize=18, weight="bold", color=INK)
    if subtitle:
        fig.text(0.05, 0.905, subtitle, fontsize=10, color=MUTED)


def page_overview(pdf, rows, current_scores):
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Data.gov Research MCP — Evaluation summary",
        "All 17 evaluation runs, November 18–23, 2026, including failed and "
        "interrupted runs. Source: eval/results/.",
    )
    total = sum(r["runs"] for r in rows if r["name"] in CURRENT)
    done = sum(r["complete"] for r in rows if r["name"] in CURRENT)
    checks = sum(r["checks_pass"] for r in rows if r["name"] in CURRENT)
    bad = sum(r["checks_fail"] for r in rows if r["name"] in CURRENT)
    opus = current_scores["Claude Opus 5.5"]
    good = opus["correct"] + opus["correct abstention"]
    cards = [
        (f"{done}/{total}", "current-system\nruns completed"),
        (f"{checks}/{checks + bad}", "numeric checks match\nthe independent reference"),
        (
            f"{good}/{sum(opus.values())}",
            "graded correct or correct\nabstention (both AI reviewers)",
        ),
        ("17", "runs published,\nfailures included"),
    ]
    for index, (value, label) in enumerate(cards):
        x = 0.05 + index * 0.235
        fig.patches.append(
            plt.Rectangle(
                (x, 0.68),
                0.21,
                0.17,
                transform=fig.transFigure,
                color="#e8f0fb",
                zorder=0,
            )
        )
        fig.text(
            x + 0.105,
            0.78,
            value,
            ha="center",
            fontsize=26,
            weight="bold",
            color="#1a5fb4",
        )
        fig.text(x + 0.105, 0.70, label, ha="center", fontsize=9.5, color=MUTED)
    lines = [
        "What was evaluated",
        "• An MCP server that searches the Data.gov catalog, reports which datasets can be "
        "queried, queries reviewed datasets and checks",
        "  whether datasets can be compared. A Databricks-hosted model answers each question "
        "using the server's tools.",
        "• Panels: Core (discovery, definitions, county analysis, unsupported requests), "
        "Science and inventory (climate and agricultural",
        "  practices, unsupported joins, unsafe SQL), and User workflows (natural questions "
        "that never name tools).",
        "",
        "How results were checked",
        "• Every run saves the question, prompt hash, model settings, source hashes and full "
        "tool trace, and runs in a fresh process.",
        "• Numbers are checked by independent arithmetic against the publisher data, not by "
        "an LLM.",
        "• Answers are graded on six criteria by AI reviewers (Claude Opus 5.5, then GPT-6 "
        "Astra as a second opinion) and, for the",
        "  first scored panel, by the project owner. Human scoring of the current runs has "
        "not been done.",
        "",
        "How to read the following pages",
        "• Page 2: every run in time order. Page 3: graded quality over time. Page 4: numeric "
        "checks and latency. Page 5: current-",
        "  system grades by question. Page 6: run-by-run table. Model, prompt and tools "
        "changed between rounds, so changes over time",
        "  reflect the whole system, not a controlled comparison.",
    ]
    y = 0.62
    for line in lines:
        bold = line and not line.startswith(("•", " "))
        fig.text(
            0.05,
            y,
            line,
            fontsize=10.5 if bold else 9.5,
            weight="bold" if bold else "normal",
            color="#1a5fb4" if bold else INK,
        )
        y -= 0.033
    pdf.savefig(fig)
    plt.close(fig)


def page_timeline(pdf, rows):
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Every run in time order",
        "Bar height = share of questions that completed. Labels give questions per run. "
        "Shaded bands mark tool versions.",
    )
    ax = fig.add_axes([0.07, 0.30, 0.88, 0.55])
    xs = range(len(rows))
    pct = [100 * r["complete"] / r["runs"] for r in rows]
    ax.bar(xs, pct, color=[PANEL_COLORS[r["panel"]] for r in rows], width=0.7)
    for x, r, p in zip(xs, rows, pct, strict=True):
        ax.text(x, p + 2, f"{r['complete']}/{r['runs']}", ha="center", fontsize=8.5)
    bands, start = [], 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i]["tools"] != rows[start]["tools"]:
            bands.append((start, i - 1, rows[start]["tools"]))
            start = i
    for index, (a, b, label) in enumerate(bands):
        if index % 2 == 0:
            ax.axvspan(a - 0.5, b + 0.5, color="#f1f3f4", zorder=0)
        ax.text((a + b) / 2, 118, label, ha="center", fontsize=8.5, color=MUTED)
    ax.set_ylim(0, 125)
    ax.set_xlim(-0.6, len(rows) - 0.4)
    ax.set_ylabel("Questions completed (%)")
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xticks(list(xs))
    ax.set_xticklabels([r["when"].strftime("%b %d\n%H:%M") for r in rows], fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in PANEL_COLORS.values()]
    ax.legend(
        handles,
        list(PANEL_COLORS),
        ncol=4,
        loc="lower left",
        fontsize=8.5,
        frameon=False,
        bbox_to_anchor=(0, -0.28),
    )
    notes = [
        "Incomplete runs: one interrupted by a concurrent App redeploy (Nov 19), two "
        "relationship-question failures that led to prompt and UI",
        "changes (Nov 20 and 22), and runs cut off by a network outage on this machine "
        "(Nov 22, evening). All are kept in eval/results/.",
        "The three rightmost runs are the current system (nine dataset-agnostic tools): "
        "25 of 25 questions completed.",
    ]
    for index, line in enumerate(notes):
        fig.text(0.07, 0.12 - index * 0.03, line, fontsize=9, color=INK)
    pdf.savefig(fig)
    plt.close(fig)


def page_quality(pdf, scored):
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Graded answer quality over time",
        "Overall grade per question on the six-criterion rubric. Each bar is one "
        "review of one panel.",
    )
    ax = fig.add_axes([0.20, 0.28, 0.50, 0.57])
    labels = [s[0] for s in scored]
    left = [0] * len(scored)
    for grade, color in zip(GRADES, GRADE_COLORS, strict=True):
        values = [100 * s[1][grade] / sum(s[1].values()) for s in scored]
        if not any(values):
            continue
        ax.barh(labels, values, left=left, color=color, label=grade)
        for y, (v, l0, s) in enumerate(zip(values, left, scored, strict=True)):
            if v >= 6:
                ax.text(
                    l0 + v / 2,
                    y,
                    str(s[1][grade]),
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white",
                    weight="bold",
                )
        left = [a + b for a, b in zip(left, values, strict=True)]
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of questions (%)")
    ax.tick_params(axis="y", labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(
        loc="lower left", bbox_to_anchor=(0, -0.22), ncol=4, fontsize=8.5, frameon=False
    )
    side = [
        "Reading the chart",
        "Green = fully correct or a correct",
        "refusal of an unsupported request.",
        "Amber = partially correct.",
        "",
        "Nov 18: six partial answers in the",
        "AI review (miscounted counties,",
        "unfinished answers, vintage and",
        "metadata confusion). Fixes: summary",
        "counts, completion checks, prompt.",
        "The owner's human review of the",
        "same panel: 16 correct, 2 partial.",
        "",
        "Nov 19 and the current system: no",
        "partial or wrong answers.",
        "",
        "Current system: Claude Opus 5.5 and",
        "GPT-6 Astra agree on every overall",
        "grade; 5 of 150 criterion grades",
        "differ. Astra saw the Opus scores.",
    ]
    for index, line in enumerate(side):
        fig.text(
            0.73,
            0.83 - index * 0.028,
            line,
            fontsize=9,
            weight="bold" if index == 0 else "normal",
            color="#1a5fb4" if index == 0 else INK,
        )
    pdf.savefig(fig)
    plt.close(fig)


def page_checks(pdf, rows):
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Numeric accuracy and response time",
        "Data steps checked by independent arithmetic, and median seconds per "
        "question, for every run.",
    )
    checked = [r for r in rows if r["checks_pass"] + r["checks_fail"]]
    ax = fig.add_axes([0.07, 0.56, 0.88, 0.28])
    xs = range(len(checked))
    ax.bar(xs, [r["checks_pass"] for r in checked], color="#1e7b3a", label="match")
    ax.bar(
        xs,
        [r["checks_fail"] for r in checked],
        bottom=[r["checks_pass"] for r in checked],
        color="#c0392b",
        label="mismatch",
    )
    for x, r in zip(xs, checked, strict=True):
        ax.text(
            x,
            r["checks_pass"] + r["checks_fail"] + 0.3,
            f"{r['checks_pass']}/{r['checks_pass'] + r['checks_fail']}",
            ha="center",
            fontsize=8.5,
        )
    ax.set_xticks(list(xs))
    ax.set_xticklabels(
        [f"{r['when']:%b %d}\n{r['when']:%H:%M}\n{r['panel']}" for r in checked],
        fontsize=7,
    )
    ax.set_ylabel("Checked data steps")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax2 = fig.add_axes([0.07, 0.08, 0.88, 0.28])
    xs2 = range(len(rows))
    capped = [min(r["median_s"], 58) for r in rows]
    ax2.plot(list(xs2), capped, marker="o", color="#1a5fb4")
    for x, r, y in zip(xs2, rows, capped, strict=True):
        label = f"{r['median_s']:.0f}" + ("↑" if r["median_s"] > 58 else "")
        ax2.text(x, y + 2, label, ha="center", fontsize=8)
    ax2.set_xticks(list(xs2))
    ax2.set_xticklabels([r["when"].strftime("%b %d\n%H:%M") for r in rows], fontsize=7)
    ax2.set_ylabel("Median seconds per question")
    ax2.set_ylim(0, 66)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.07,
        0.425,
        "No checked data step has ever mismatched the reference. Runs with no "
        "checked steps (discovery-only or failed)\nare omitted from the top chart. "
        "Times include all model and tool calls. The axis is capped at 60 s; the "
        "Nov 22 23:29 outage\nrun's median was 400 s (timeouts). Small sample: not "
        "a service-level guarantee.",
        fontsize=8.5,
        color=MUTED,
    )
    pdf.savefig(fig)
    plt.close(fig)


def page_current(pdf):
    opus, astra = {}, {}
    questions = {}
    for name in CURRENT:
        panel = load(name)
        questions.update({q["id"]: q for q in panel["questions"]})
        opus.update(
            json.loads((RESULTS / f"{name}-eval-ai-scores.json").read_text())["scores"]
        )
        astra.update(
            json.loads((RESULTS / f"{name}-eval-ai-scores-astra.json").read_text())[
                "scores"
            ]
        )
    keys = list(opus)
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Current system: grades by question",
        "25 questions, nine dataset-agnostic tools. Cell = criterion grade; "
        "outlined cells are where the two reviewers differ.",
    )
    fig.texts[-1].set_position((0.05, 0.915))
    fig.texts[-2].set_position((0.05, 0.945))
    criteria = [
        "tool_selection",
        "parameters",
        "returned_data",
        "interpretation",
        "citations",
        "limitations",
    ]
    colors = {
        "pass": "#6fbf73",
        "partial": "#f0ad4e",
        "fail": "#c0392b",
        "n/a": "#dfe3e6",
    }
    ax = fig.add_axes([0.22, 0.08, 0.5, 0.76])
    for y, key in enumerate(keys):
        for x, criterion in enumerate(criteria):
            grade = astra[key][criterion]
            ax.add_patch(plt.Rectangle((x, y), 0.95, 0.9, color=colors[grade]))
            if opus[key][criterion] != grade:
                ax.add_patch(
                    plt.Rectangle((x, y), 0.95, 0.9, fill=False, lw=1.6, ec=INK)
                )
                ax.text(
                    x + 0.47,
                    y + 0.45,
                    f"{opus[key][criterion][:4]}→{grade[:4]}",
                    ha="center",
                    va="center",
                    fontsize=6,
                )
    ax.set_xlim(0, len(criteria))
    ax.set_ylim(len(keys), 0)
    ax.set_xticks([x + 0.47 for x in range(len(criteria))])
    ax.set_xticklabels([c.replace("_", "\n") for c in criteria], fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks([y + 0.45 for y in range(len(keys))])
    ax.set_yticklabels([k.split("#")[0] for k in keys], fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    for y, key in enumerate(keys):
        qid = key.split("#")[0]
        text = questions[qid]["question"]
        fig.text(
            0.02,
            0.84 - y * (0.76 / len(keys)) - 0.006,
            (text[:28] + "…") if len(text) > 29 else text,
            fontsize=6.5,
            color=MUTED,
            va="top",
        )
        fig.text(
            0.735,
            0.84 - y * (0.76 / len(keys)) - 0.006,
            astra[key]["overall"],
            fontsize=8,
            va="top",
            color="#1e7b3a"
            if astra[key]["overall"].startswith("correct")
            else "#c0392b",
        )
    fig.text(0.735, 0.865, "Overall (both)", fontsize=8.5, weight="bold")
    legend = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    fig.legend(
        legend,
        list(colors),
        loc="lower right",
        ncol=4,
        fontsize=8,
        frameon=False,
        bbox_to_anchor=(0.98, 0.02),
    )
    fig.text(
        0.86,
        0.84,
        "Panels: D/M/A/U core;\nL/Q user workflows;\nR/S science "
        "and inventory.\n\nCell colors show GPT-6\nAstra's grades; outlined\n"
        "cells show Opus→Astra\nchanges. Details:\nSECOND-OPINION-\nREVIEW.md",
        fontsize=8,
        color=MUTED,
        va="top",
    )
    pdf.savefig(fig)
    plt.close(fig)


def page_table(pdf, rows):
    fig = plt.figure(figsize=(11, 8.5))
    header(
        fig,
        "Run-by-run record",
        "Every published run. Files: eval/results/<run>-eval-panel.json and "
        "-eval-review.html (open in a browser).",
    )
    ax = fig.add_axes([0.03, 0.05, 0.94, 0.82])
    ax.axis("off")
    columns = [
        "Run (UTC)",
        "Panel",
        "Tools",
        "Answer model",
        "Completed",
        "Checks",
        "Median s",
        "Note",
    ]
    cells = [
        [
            r["when"].strftime("%b %d %H:%M"),
            r["panel"],
            r["tools"],
            r["model"],
            f"{r['complete']}/{r['runs']}",
            f"{r['checks_pass']}/{r['checks_pass'] + r['checks_fail']}"
            if r["checks_pass"] + r["checks_fail"]
            else "—",
            f"{r['median_s']:.1f}",
            r["note"],
        ]
        for r in rows
    ]
    table = ax.table(
        cellText=cells,
        colLabels=columns,
        loc="upper center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.10, 0.08, 0.12, 0.12, 0.08, 0.06, 0.07, 0.27],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.55)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#dfe3e6")
        if row == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#1a5fb4")
        elif rows[row - 1]["name"] in CURRENT:
            cell.set_facecolor("#e6f4ea")
    pdf.savefig(fig)
    plt.close(fig)


def main():
    reference = report.Reference(
        json.loads((ROOT / "data/reviewed/indicators.json").read_text())
    )
    rows = runs_table(reference)
    human, _ = scores(RESULTS / "20261118T161659Z-eval-human-scores.json")
    nov18, _ = scores(RESULTS / "20261118T161659Z-eval-ai-scores.json")
    nov19, _ = scores(RESULTS / "20261119T152023Z-eval-ai-scores.json")
    current = {"Claude Opus 5.5": Counter(), "GPT-6 Astra": Counter()}
    for name in CURRENT:
        current["Claude Opus 5.5"] += scores(RESULTS / f"{name}-eval-ai-scores.json")[0]
        current["GPT-6 Astra"] += scores(RESULTS / f"{name}-eval-ai-scores-astra.json")[
            0
        ]
    scored = [
        ("Nov 18 · core (18)\nAI review (GPT-6 Astra)", nov18),
        ("Nov 18 · core (18)\nhuman review (owner)", human),
        ("Nov 19 · core (18)\nAI review (GPT-6 Astra)", nov19),
        (
            "Nov 22–23 · current (25)\nAI review (Claude Opus 5.5)",
            current["Claude Opus 5.5"],
        ),
        (
            "Nov 22–23 · current (25)\nsecond opinion (GPT-6 Astra)",
            current["GPT-6 Astra"],
        ),
    ]
    with PdfPages(OUTPUT) as pdf:
        page_overview(pdf, rows, current)
        page_timeline(pdf, rows)
        page_quality(pdf, scored)
        page_checks(pdf, rows)
        page_current(pdf)
        page_table(pdf, rows)
        info = pdf.infodict()
        info["Title"] = "Data.gov Research MCP — Evaluation summary"
    print("Wrote", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
