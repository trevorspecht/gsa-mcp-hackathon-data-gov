"""Build a self-contained HTML review page for an evaluation panel run.

The page shows each question, expected behavior, the agent's answer, the actual
tool trace, and automated checks against an independent reference computed from
the reviewed snapshot. Reviewers score in the page and export scores as JSON.
"""

import argparse
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = [
    "tool_selection",
    "parameters",
    "returned_data",
    "interpretation",
    "citations",
    "limitations",
]
OVERALL = [
    "correct",
    "partially correct",
    "wrong",
    "correct abstention",
    "erroneous refusal",
    "environment-blocked",
]
TOLERANCE = 1e-6
markdown = MarkdownIt("commonmark", {"html": False}).enable("table")


def load_review(path: Path | None, panel_path: Path, panel: dict):
    if path is None:
        return None
    review = json.loads(path.read_text())
    if (
        review.get("panel") != panel_path.name
        or review.get("panel_sha256")
        != hashlib.sha256(panel_path.read_bytes()).hexdigest()
        or review.get("snapshot_id") != panel.get("snapshot_id")
    ):
        raise ValueError("AI review does not match this exact panel and snapshot")
    expected = {f"{r['id']}#{r['repeat']}" for r in panel["runs"]}
    if set(review["scores"]) != expected:
        raise ValueError("AI review must score every panel run exactly once")
    for score in review["scores"].values():
        if score["overall"] not in OVERALL:
            raise ValueError("Invalid AI overall score")
        for key in RUBRIC:
            if score[key] not in {"pass", "partial", "fail", "n/a"}:
                raise ValueError("Invalid AI rubric score")
            if not score["reasons"].get(key):
                raise ValueError("AI rubric scores require explanations")
    return review


def review_card(review, key):
    if review is None:
        return ""
    score = review["scores"][key]
    rows = "".join(
        "<tr>"
        f"<th>{html.escape(k.replace('_', ' '))}</th>"
        f"<td>{html.escape(score[k])}</td>"
        f"<td>{html.escape(score['reasons'][k])}</td></tr>"
        for k in RUBRIC
    )
    return (
        '<section class="ai-review"><h3>AI reviewer assessment — '
        f"{html.escape(review['reviewer'])}</h3>"
        f"<p><b>Overall: {html.escape(score['overall'])}</b></p>"
        f"<p>{html.escape(score['notes'])}</p>"
        "<details><summary>All six rubric scores and reasons</summary>"
        "<table><thead><tr><th>Criterion</th><th>AI score</th>"
        f"<th>Reason</th></tr></thead><tbody>{rows}</tbody></table>"
        "</details><p>Advisory AI assessment, not a human score. "
        "Your scoring fields below are independent.</p></section>"
    )


def review_summary(review, runs):
    if review is None:
        return ""
    counts = Counter(s["overall"] for s in review["scores"].values())
    totals = "; ".join(f"{n} {label}" for label, n in sorted(counts.items()))
    links = " ".join(
        f'<a href="#run-{i}">{html.escape(r["id"])}·{r["repeat"]}</a>'
        for i, r in enumerate(runs)
        if review["scores"][f"{r['id']}#{r['repeat']}"]["overall"]
        not in {"correct", "correct abstention"}
    )
    return (
        '<section class="ref ai-overview"><h2>Separate AI review</h2>'
        f"<p><b>{html.escape(review['reviewer'])}</b> · "
        f"{html.escape(review['reviewed_at'])} · {len(runs)} runs scored.</p>"
        f"<p>{html.escape(totals)}</p>"
        f"<p>{html.escape(review['method'])}</p>"
        f"<p><b>Start with flagged AI assessments:</b> {links}</p>"
        "<p>Original answers and traces are unchanged. AI scores are read-only "
        "and do not populate, replace or export as your human scores. "
        "The automatic-check filter does not filter these AI assessments.</p>"
        "</section>"
    )


def text_of(answer):
    if isinstance(answer, list):
        return "\n".join(
            p.get("text", "")
            for p in answer
            if isinstance(p, dict) and p.get("type") == "text"
        )
    return answer or ""


def sign(value, labels):
    value = round(value, 6)
    return labels[0] if value > 0 else labels[1] if value < 0 else labels[2]


class Reference:
    """Independent arithmetic over indicators.json; shares no code with the server."""

    def __init__(self, rows):
        self.rows = {(r["county_fips"], r["year"]): r for r in rows}
        self.counties = sorted({c for c, _ in self.rows})

    def changes(self, start, end, counties=None):
        result = []
        for county in counties or self.counties:
            a, b = self.rows.get((county, start)), self.rows.get((county, end))
            if not a or not b:
                continue
            result.append(
                {
                    "county_fips": county,
                    "county_name": a["county_name"],
                    "population_start": a["population"],
                    "population_end": b["population"],
                    "population_change": 100
                    * (b["population"] - a["population"])
                    / a["population"],
                    "unemployment_start": a["unemployment_rate"],
                    "unemployment_end": b["unemployment_rate"],
                    "unemployment_change": b["unemployment_rate"]
                    - a["unemployment_rate"],
                }
            )
        return result

    def expected(self, request):
        rows = self.changes(
            request.get("start_year", 2022),
            request.get("end_year", 2024),
            request.get("county_fips") or None,
        )
        complete = list(rows)
        for field, key in (
            ("population_change", "population_direction"),
            ("unemployment_change", "unemployment_direction"),
        ):
            direction = request.get(key, "any")
            if direction == "increase":
                rows = [r for r in rows if round(r[field], 6) > 0]
            elif direction == "decrease":
                rows = [r for r in rows if round(r[field], 6) < 0]
        sort = request.get("sort_by", "county")
        if sort == "county":
            rows.sort(key=lambda r: r["county_fips"])
        else:
            rows.sort(key=lambda r: (r[sort], r["county_fips"]), reverse=True)
        pop = ("increased", "decreased", "unchanged")
        rate = ("rose", "fell", "unchanged")
        summary = {
            "population": dict.fromkeys(pop, 0),
            "unemployment_rate": dict.fromkeys(rate, 0),
        }
        for r in complete:
            summary["population"][sign(r["population_change"], pop)] += 1
            summary["unemployment_rate"][sign(r["unemployment_change"], rate)] += 1
        summary["counties_compared"] = len(complete)
        return rows[: request.get("limit", 24)], summary


def check_run(run, reference, science=None):
    checks = []
    trace = run.get("trace", [])
    if run.get("status") not in (None, "complete"):
        checks.append(("fail", f"Model run status: {run['status']}"))
    if run.get("exit") != 0:
        checks.append(("fail", f"Agent exited {run.get('exit')}"))
    for step in trace:
        result = step.get("result")
        if isinstance(result, dict) and (result.get("error") or result.get("is_error")):
            checks.append(("warn", f"{step['tool']} returned an error"))
        if step["tool"] == "query_science_series" and isinstance(result, dict):
            if science and result.get("status") == "complete":
                request = step["arguments"]["request"]
                dataset = next(
                    d for d in science["datasets"] if d["id"] == request["dataset_id"]
                )
                expected = [
                    r
                    for r in dataset["observations"]
                    if request.get("start_year", 1985)
                    <= r["year"]
                    <= request.get("end_year", 2012)
                ]
                matches = (
                    result.get("rows") == expected
                    and result.get("unit") == dataset["unit"]
                    and result.get("snapshot_id") == science["snapshot_id"]
                )
                checks.append(
                    (
                        "pass" if matches else "fail",
                        "Science rows, units and snapshot match frozen reference"
                        if matches
                        else "Science reference mismatch",
                    )
                )
            else:
                checks.append(
                    ("info", "Science query: inspect available years and evidence")
                )
        if step["tool"] != "compare_public_indicators" or not isinstance(result, dict):
            continue
        if result.get("status") != "complete":
            checks.append(("info", f"compare status: {result.get('status')}"))
            continue
        request = step["arguments"].get("request", {})
        rows, summary = reference.expected(request)
        got = result.get("rows", [])
        if [r["county_fips"] for r in got] == [r["county_fips"] for r in rows]:
            checks.append(
                ("pass", f"Row set and order match reference ({len(rows)} rows)")
            )
        else:
            checks.append(("fail", "Row set or order differs from reference"))
        bad = [
            g["county_fips"]
            for g, e in zip(got, rows, strict=False)
            if any(
                abs(float(g[k]) - float(e[k])) > TOLERANCE
                for k in e
                if k not in ("county_fips", "county_name")
            )
        ]
        checks.append(
            ("fail", f"Values differ: {', '.join(bad)}")
            if bad
            else ("pass", f"All values within {TOLERANCE}")
        )
        server = result.get("summary")
        if server is None:
            checks.append(("info", "No summary counts (run predates the feature)"))
        elif all(server.get(k) == summary[k] for k in summary):
            checks.append(("pass", "Summary counts match reference"))
        else:
            checks.append(("fail", "Summary counts differ from reference"))
    if not trace:
        checks.append(("warn", "No tool calls; answer is not MCP-backed"))
    elif not any(step["tool"] == "compare_public_indicators" for step in trace):
        checks.append(("info", "No comparison executed; judge the answer manually"))
    return checks


def table(rows, columns):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in columns)
    body = "".join(
        "<tr>"
        + "".join(f"<td>{html.escape(fmt(r.get(c)))}</td>" for c in columns)
        + "</tr>"
        for r in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def fmt(value):
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return "" if value is None else str(value)


def run_card(index, run, question, reference, ai_review=None, science=None):
    checks = check_run(run, reference, science)
    badges = "".join(
        f'<li class="{level}">{html.escape(level.upper())}: {html.escape(msg)}</li>'
        for level, msg in checks
    )
    steps = []
    for n, step in enumerate(run.get("trace", []), 1):
        result = step.get("result")
        summary = result.get("summary") if isinstance(result, dict) else None
        rows = result.get("rows") if isinstance(result, dict) else None
        extra = ""
        if summary:
            extra += (
                "<h5>Summary counts</h5><pre>"
                + html.escape(json.dumps(summary, indent=1))
                + "</pre>"
            )
        if rows:
            extra += "<h5>Returned rows</h5>" + table(rows, list(rows[0].keys()))
        tool = html.escape(step["tool"])
        arguments = html.escape(json.dumps(step.get("arguments"), indent=1))
        full = html.escape(json.dumps(result, indent=1)[:60000])
        steps.append(
            f"<details><summary>{n}. <code>{tool}</code></summary>"
            f"<h5>Arguments</h5><pre>{arguments}</pre>{extra}"
            f"<details><summary>Full result JSON</summary><pre>{full}</pre>"
            "</details></details>"
        )
    rubric = "".join(
        f'<label>{html.escape(r.replace("_", " "))}<select data-key="{r}">'
        '<option value="">—</option><option>pass</option><option>partial</option>'
        "<option>fail</option><option>n/a</option></select></label>"
        for r in RUBRIC
    )
    overall = "".join(f"<option>{html.escape(o)}</option>" for o in OVERALL)
    key = f"{run['id']}#{run['repeat']}"
    status = (
        "fail"
        if any(c[0] == "fail" for c in checks)
        else "warn"
        if any(c[0] == "warn" for c in checks)
        else "pass"
    )
    answer = markdown.render(text_of(run.get("answer")) or run.get("error_output", ""))
    calls = len(run.get("trace", []))
    heading = (
        f"{html.escape(run['id'])} <small>run {run['repeat']} · "
        f"{run.get('seconds', '?')} s · {html.escape(question['category'])}</small>"
    )
    return f"""
<section class="run" id="run-{index}" data-run="{html.escape(key)}"
 data-auto="{status}">
  <header><h2>{heading}</h2><span class="auto {status}">auto: {status}</span></header>
  <p class="q"><b>Question:</b> {html.escape(question["question"])}</p>
  <p class="exp"><b>Expected:</b> {html.escape(question["expected"])}</p>
  <div class="cols">
    <div class="answer"><h3>Agent answer</h3>{answer}</div>
    <div class="side">
      {review_card(ai_review, key)}
      <details><summary>Model completion metadata</summary>
      <pre>{html.escape(json.dumps(run.get("model_turns", []), indent=1))}</pre>
      </details>
      <h3>Automated checks</h3><ul class="checks">{badges}</ul>
      <h3>Tool trace ({calls} calls)</h3>{"".join(steps)}
      <h3>Your score</h3><div class="score">{rubric}
      <label>overall<select data-key="overall"><option value="">—</option>
      {overall}</select></label>
      <label class="notes">notes<textarea data-key="notes" rows="3"></textarea>
      </label></div>
    </div>
  </div>
</section>"""


def render(template, **values):
    for key, value in values.items():
        template = template.replace(f"@@{key.upper()}@@", value)
    return template


def panel_questions(panel):
    if "questions" in panel:
        return {q["id"]: q for q in panel["questions"]}
    return {
        q["id"]: q for q in json.loads((ROOT / "eval/questions-v1.json").read_text())
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", type=Path, help="*-eval-panel.json file")
    parser.add_argument("--data", type=Path, default=ROOT / ".local/data")
    parser.add_argument("--ai-review", type=Path, help="Separate AI score JSON")
    args = parser.parse_args()
    panel = json.loads(args.panel.read_text())
    ai_path = args.ai_review or args.panel.with_name(
        args.panel.stem.replace("-eval-panel", "-eval-ai-scores") + ".json"
    )
    ai_review = load_review(
        ai_path if args.ai_review or ai_path.exists() else None, args.panel, panel
    )
    questions = panel_questions(panel)
    manifest = json.loads((args.data / "manifest.json").read_text())
    reference = Reference(json.loads((args.data / "indicators.json").read_text()))
    if manifest["snapshot_id"] != panel.get("snapshot_id"):
        raise SystemExit("Panel snapshot does not match the reference snapshot")
    runs = sorted(
        panel["runs"], key=lambda r: (list(questions).index(r["id"]), r["repeat"])
    )
    cards = "".join(
        run_card(
            i,
            r,
            questions[r["id"]],
            reference,
            ai_review,
            panel.get("science_snapshot"),
        )
        for i, r in enumerate(runs)
    )
    nav = "".join(
        f'<a href="#run-{i}" data-nav="{html.escape(r["id"])}#{r["repeat"]}">'
        f"{html.escape(r['id'])}{'' if r['repeat'] == 1 else '·' + str(r['repeat'])}"
        "</a>"
        for i, r in enumerate(runs)
    )
    ref_cols = [
        "county_fips",
        "county_name",
        "population_start",
        "population_end",
        "population_change",
        "unemployment_start",
        "unemployment_end",
        "unemployment_change",
    ]
    ref_sections = ""
    for start, end in ((2022, 2024), (2023, 2024), (2022, 2023)):
        rows, summary = reference.expected({"start_year": start, "end_year": end})
        ref_sections += (
            f"<details><summary>{start} → {end}: population "
            f"{html.escape(json.dumps(summary['population']))}; unemployment "
            f"{html.escape(json.dumps(summary['unemployment_rate']))}</summary>"
            f"{table(rows, ref_cols)}</details>"
        )
    sources = table(
        manifest["sources"],
        ["publisher", "title", "url", "catalog_identifier", "sha256"],
    )
    storage_key = "datagov-eval-" + panel["started_at"]
    page = render(
        (ROOT / "eval/review_template.html").read_text(),
        title=html.escape(f"Evaluation review · {panel['started_at']}"),
        meta=html.escape(
            f"{len(runs)} runs · model {panel.get('model_endpoint')} · "
            f"snapshot {panel['snapshot_id']}"
        ),
        nav=nav,
        cards=cards,
        ai_summary=review_summary(ai_review, runs),
        reference=ref_sections,
        sources=sources,
        storage_key=json.dumps(storage_key),
        panel_name=json.dumps(args.panel.name),
    )
    out = args.panel.with_name(
        args.panel.name.replace("-eval-panel.json", "-eval-review.html")
    )
    out.write_text(page)
    print(f"Wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")


if __name__ == "__main__":
    main()
