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
    assert app.expander[0].label.startswith("1. Water quality")
    assert "unverified" in app.expander[0].label
    assert app.expander[1].label.startswith("2. Climate")
    assert "Ready within reviewed scope" in app.expander[1].label
    assert app.subheader[0].value.endswith("2 distinct returned records")
