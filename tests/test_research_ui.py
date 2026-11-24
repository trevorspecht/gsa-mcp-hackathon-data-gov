import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

from datagov_mcp.research_ui import TABS, source_cards

CHANGE = {
    "tool": "analyze_change",
    "result": {
        "status": "complete",
        "dataset_id": "md_county_population_unemployment",
        "title": "County data",
        "start_period": 2022,
        "end_period": 2024,
        "geography": {"level": "county", "area": "Maryland"},
        "measures": [
            {
                "id": "population",
                "label": "Population",
                "unit": "people",
                "change_unit": "percent",
            }
        ],
        "rows": [
            {"geography_id": "24001", "geography_name": "A", "population_change": 2.0}
        ],
        "sources": [
            {
                "title": "Census",
                "url": "https://example.gov/census",
                "catalog_identifier": "census-id",
            }
        ],
    },
}
SERIES = {
    "tool": "query_dataset",
    "result": {
        "status": "complete",
        "dataset_id": "chesapeake_cover_crops",
        "title": "Cover crops",
        "geography": {"level": "watershed", "area": "Chesapeake"},
        "measures": [{"id": "cover_crop_area", "label": "Area", "unit": "km2"}],
        "rows": [
            {
                "geography_id": "w",
                "geography_name": "W",
                "period": 2002,
                "cover_crop_area": 1.0,
            },
            {
                "geography_id": "w",
                "geography_name": "W",
                "period": 2012,
                "cover_crop_area": 2.0,
            },
        ],
        "sources": [{"url": "https://example.gov/usgs"}],
    },
}


def test_ui_starts_without_network():
    app = AppTest.from_file("../src/datagov_mcp/research_ui.py").run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "Data.gov Research"
    assert len(app.text_area) == 1
    assert not app.tabs


def test_answer_tab_holds_only_the_answer():
    app = AppTest.from_string(f"""
from datagov_mcp.research_ui import display_result
display_result({{"status":"complete", "answer":"The answer.", "trace":[
 {CHANGE!r}, {SERIES!r},
 {{"tool":"assess_dataset_readiness","result":{{"datasets":[
  {{"identifier":"other","title":"Other dataset","relevance":{{"score":3}},
   "readiness":{{"label":"Promising access route — unverified","blockers":["x"]}}}}
 ]}}}}
]}})
""").run(timeout=20)
    assert not app.exception
    assert [t.label for t in app.tabs] == TABS
    answer, sources, data, _, evaluation = app.tabs
    assert [m.value for m in answer.markdown] == ["The answer."]
    assert not answer.json and not answer.dataframe
    assert sources.subheader[0].value == "Data used in this answer"
    assert sources.subheader[1].value == "Other relevant datasets"
    assert len(data.dataframe) == 2
    assert evaluation.json


def test_used_sources_exclude_catalog_duplicates():
    trace = [
        {
            "tool": "find_data_for_question",
            "result": {
                "datasets": [
                    {"identifier": "census-id", "title": "Census catalog"},
                    {"identifier": "other", "title": "Other"},
                ]
            },
        },
        CHANGE,
        {
            "tool": "list_queryable_datasets",
            "result": {"datasets": [{"dataset_id": "unused", "title": "Not used"}]},
        },
    ]
    used, other = source_cards(trace)
    assert [d["dataset_id"] for d in used] == ["md_county_population_unemployment"]
    assert [c["identifier"] for c in other] == ["other"]


def test_readiness_survives_later_inspection():
    trace = [
        {
            "tool": "assess_dataset_readiness",
            "result": {
                "datasets": [
                    {
                        "identifier": "x",
                        "title": "X",
                        "readiness": {"label": "Ready"},
                        "queryable": True,
                    }
                ]
            },
        },
        {
            "tool": "inspect_dataset",
            "result": {
                "dataset": {"identifier": "x", "title": "X", "queryable": False}
            },
        },
    ]
    _, other = source_cards(trace)
    assert other[0]["readiness"]["label"] == "Ready" and other[0]["queryable"]


def test_explore_requires_selection_and_keeps_question():
    app = AppTest.from_string("""
import streamlit as st
from datagov_mcp.research_ui import display_exploration
st.session_state['original_question'] = 'Climate and cover crops'
st.session_state['exploration_options'] = {'datasets':[
 {'dataset_id':'a', 'title':'A', 'ready':True},
 {'dataset_id':'b', 'title':'B', 'ready':False},
]}
display_exploration()
""").run(timeout=20)
    assert not app.exception
    assert app.multiselect[0].options == ["A"]
    buttons = {b.label: b for b in app.button}
    assert buttons["Explore selected data"].disabled
    assert any("Climate and cover crops" in c.value for c in app.caption)
    assert "Research this next step" in buttons


def test_preview_renders_series_and_compatibility():
    app = AppTest.from_string(f"""
import streamlit as st
from datagov_mcp.research_ui import display_exploration
st.session_state['exploration'] = {{"datasets":[{SERIES["result"]!r},
 {{"dataset_id":"b","status":"failed"}}],
 "compatibility":{{"pairs":[{{"datasets":["a","b"],"status":"not_comparable",
 "reasons":["Geography differs"]}}]}}}}
display_exploration()
""").run(timeout=20)
    assert not app.exception
    assert app.warning
    assert any("Not comparable" in m.value for m in app.markdown)
    assert len(app.dataframe) == 1


def test_concise_candidates_keep_links():
    app = AppTest.from_string("""
from datagov_mcp.research_ui import display_candidate
display_candidate({"identifier":"https://example.gov/data", "title":"Example",
 "description":"Long metadata detail"}, 1, concise=True)
""").run(timeout=20)
    assert not app.exception
    assert app.get("link_button")[0].proto.url == "https://example.gov/data"
    assert "Long metadata detail" not in str([m.value for m in app.markdown])


def test_followup_shows_in_explore_and_keeps_preview(monkeypatch):
    app = AppTest.from_string(f"""
import streamlit as st
from datagov_mcp import research_ui

async def fake_agent(prompt, settings, workspace):
    return {{"status": "complete", "answer": "Follow-up answer.", "trace": []}}

research_ui.run_agent = fake_agent
research_ui.agent_workspace = lambda settings: None
research_ui.AgentSettings = lambda: None
st.session_state['original_question'] = 'Climate and cover crops'
st.session_state.setdefault('exploration', {{"datasets": [{SERIES["result"]!r}],
 "compatibility": {{"pairs": []}}}})
st.session_state.setdefault('result', {{"status": "complete",
 "answer": "Original answer.", "trace": []}})
research_ui.display_exploration()
""").run(timeout=20)
    next(b for b in app.button if b.label == "Research this next step").click()
    app.run(timeout=20)
    assert not app.exception
    assert app.session_state["result"]["answer"] == "Original answer."
    assert app.session_state["exploration"]["datasets"]
    assert any("Follow-up answer." in m.value for m in app.markdown)
    assert any(s.value.startswith("Next step:") for s in app.subheader)
    assert len(app.dataframe) == 1
