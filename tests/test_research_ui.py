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
