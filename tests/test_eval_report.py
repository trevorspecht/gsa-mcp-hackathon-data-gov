import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

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


def test_ai_review_is_bound_to_panel_and_requires_every_reason(tmp_path):
    panel = {"snapshot_id": "s", "runs": [{"id": "D1", "repeat": 1}]}
    path = tmp_path / "panel.json"
    path.write_text(json.dumps(panel))
    score = {
        **dict.fromkeys(eval_report.RUBRIC, "pass"),
        "overall": "correct",
        "notes": "Checked",
        "reasons": dict.fromkeys(eval_report.RUBRIC, "Supported by the trace"),
    }
    review = {
        "panel": path.name,
        "panel_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "snapshot_id": "s",
        "reviewer": "Test AI",
        "scores": {"D1#1": score},
    }
    ai = tmp_path / "ai.json"
    ai.write_text(json.dumps(review))
    assert eval_report.load_review(ai, path, panel) == review
    assert eval_report.load_review(None, path, panel) is None
    del score["reasons"]["limitations"]
    ai.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="explanations"):
        eval_report.load_review(ai, path, panel)
    path.write_text(json.dumps(panel) + "\n")
    with pytest.raises(ValueError, match="exact panel"):
        eval_report.load_review(ai, path, panel)


def test_ai_card_is_escaped_and_separate_from_human_inputs():
    score = {
        **dict.fromkeys(eval_report.RUBRIC, "partial"),
        "overall": "partially correct",
        "notes": "<script>alert(1)</script>",
        "reasons": dict.fromkeys(eval_report.RUBRIC, "<b>reason</b>"),
    }
    review = {"reviewer": "Test AI", "scores": {"D1#1": score}}
    card = eval_report.review_card(review, "D1#1")
    assert "<script>" not in card and "&lt;script&gt;" in card
    assert "data-key" not in card and "<select" not in card
    assert "AI reviewer assessment" in card
    assert eval_report.review_card(None, "D1#1") == ""


def test_panel_questions_preserve_old_wording_and_prefer_embedded():
    assert "same comparison" in eval_report.panel_questions({})["U2"]["question"]
    panel = {"questions": [{"id": "U2", "question": "Frozen exact question"}]}
    assert (
        eval_report.panel_questions(panel)["U2"]["question"] == "Frozen exact question"
    )


def test_incomplete_answer_flagged_even_if_exit_was_zero():
    checks = eval_report.check_run(
        {"exit": 0, "status": "incomplete", "trace": []}, reference()
    )
    assert ("fail", "Model run status: incomplete") in checks
