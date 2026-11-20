import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest


def test_ui_starts_without_network():
    app = AppTest.from_file("../src/datagov_mcp/research_ui.py").run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "Data.gov Research"
    assert len(app.text_area) == 1


def test_science_capabilities_are_not_catalog_cards():
    app = AppTest.from_string("""
from datagov_mcp.research_ui import display_result
display_result({"status":"complete", "answer":"Example", "trace":[
 {"tool":"inspect_science_capabilities",
  "result":{"datasets":[{"id":"md_temperature", "title":"Climate"}]}}
]})
""").run(timeout=20)
    assert not app.exception
    assert not app.subheader


def test_ranked_cards_keep_readiness_after_later_inspection():
    app = AppTest.from_string("""
from datagov_mcp.research_ui import display_result
ready = {"identifier":"climate", "title":"Climate", "queryable":True,
 "queryability_reason":"Reviewed scope", "relevance":{"score":1},
 "readiness":{"label":"Ready within reviewed scope", "blockers":[],
 "scopes":[], "question_compatibility":"Check scope", "wait_note":"No estimate"}}
water = {"identifier":"water", "title":"Water quality", "queryable":False,
 "relevance":{"score":9}, "readiness":{"label":"Promising access route — unverified",
 "blockers":["No connector"], "scopes":[], "question_compatibility":"Unknown",
 "wait_note":"No estimate"}}
display_result({"status":"complete", "answer":"Example", "trace":[
 {"tool":"assess_dataset_readiness", "result":{"datasets":[ready,water]}},
 {"tool":"inspect_dataset", "result":{"dataset":{
 "identifier":"climate", "title":"Climate", "queryable":False}}},
 {"tool":"find_data_for_question", "result":{"datasets":[{
 "identifier":"climate", "title":"Climate", "queryable":False}]}}
]})
""").run(timeout=20)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Answer & sources",
        "Evaluation & diagnostics",
    ]
    assert app.subheader[0].value == "Other relevant datasets"
    text = [item.value for item in app.markdown]
    assert text.index("**1. Water quality**") < text.index("**2. Climate**")
    assert any("Ready within reviewed scope" in item.value for item in app.caption)
    assert not app.tabs[0].json
    assert app.tabs[1].json


def test_used_sources_precede_candidates_and_capabilities_are_not_usage():
    from datagov_mcp.research_ui import source_cards

    trace = [
        {
            "tool": "inspect_science_capabilities",
            "result": {"datasets": [{"id": "unused", "title": "Not used"}]},
        },
        {
            "tool": "query_science_series",
            "result": {
                "status": "complete",
                "title": "Temperature",
                "unit": "F",
                "method": "Annual observations",
                "geography": "Maryland",
                "source": {
                    "url": "https://example.gov/file.csv",
                    "publisher": "NOAA",
                    "catalog_identifier": "https://example.gov/catalog",
                },
                "rows": [{"year": 1985, "value": 1}, {"year": 2012, "value": 2}],
            },
        },
        {
            "tool": "find_data_for_question",
            "result": {
                "datasets": [
                    {"identifier": "other", "title": "Other climate dataset"},
                    {
                        "identifier": "https://example.gov/catalog",
                        "title": "Climate parent",
                    },
                ]
            },
        },
    ]
    used, other = source_cards(trace)
    assert len(used) == 1 and used[0]["title"] == "Climate parent"
    assert used[0]["used"]
    assert [card["identifier"] for card in other] == ["other"]


def test_concise_cards_keep_links_and_hide_metadata():
    app = AppTest.from_string("""
from datagov_mcp.research_ui import display_result
display_result({"status":"complete", "answer":"Dataset list", "trace":[
 {"tool":"find_data_for_question", "result":{"datasets":[{
 "identifier":"https://example.gov/data", "title":"Example dataset",
 "publisher":"Publisher detail", "description":"Long metadata detail"}]}}
]}, concise=True)
""").run(timeout=20)
    assert not app.exception
    assert not app.tabs[0].json
    assert "Long metadata detail" not in str([m.value for m in app.markdown])
    assert app.get("link_button")[0].proto.label == "Dataset information"
    assert app.get("link_button")[0].proto.url == "https://example.gov/data"
