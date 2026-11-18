import importlib.util
from pathlib import Path

from datagov_mcp.ingestion import COUNTIES

spec = importlib.util.spec_from_file_location(
    "eval_report", Path(__file__).resolve().parents[1] / "scripts/eval_report.py"
)
eval_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_report)


def reference():
    rows = []
    for index, county in enumerate(sorted(COUNTIES)):
        for year, population, rate in ((2022, 100, 3.0), (2024, 100 + index, 3.1)):
            rows.append(
                {
                    "county_fips": county,
                    "county_name": county,
                    "year": year,
                    "population": population,
                    "unemployment_rate": rate,
                }
            )
    return eval_report.Reference(rows)


def compare_step(rows, summary):
    return {
        "tool": "compare_public_indicators",
        "arguments": {"request": {"population_direction": "increase"}},
        "result": {"status": "complete", "rows": rows, "summary": summary},
    }


def test_matching_comparison_passes_and_mismatch_fails():
    ref = reference()
    rows, summary = ref.expected({"population_direction": "increase"})
    assert len(rows) == 23 and summary["population"]["unchanged"] == 1
    good = {"exit": 0, "trace": [compare_step(rows, summary)]}
    assert all(level == "pass" for level, _ in eval_report.check_run(good, ref))
    altered = [dict(rows[0], population_change=99.0)] + rows[1:]
    bad = {"exit": 0, "trace": [compare_step(altered, summary)]}
    assert ("fail", f"Values differ: {rows[0]['county_fips']}") in (
        eval_report.check_run(bad, ref)
    )


def test_answer_markdown_cannot_inject_html():
    rendered = eval_report.markdown.render("<script>alert(1)</script>")
    assert "<script>" not in rendered
