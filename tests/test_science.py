import pytest
from fastmcp import Client
from pydantic import ValidationError

from datagov_mcp.app import create_server
from datagov_mcp.evidence import EvidenceStore
from datagov_mcp.tools.science import ScienceRequest, query, snapshot


def test_science_asset_and_evidence(tmp_path):
    data = snapshot()
    assert len(data["datasets"]) == 4
    store = EvidenceStore(tmp_path)
    result = query(ScienceRequest(dataset_id="chesapeake_cover_crops"), store)
    assert result["unit"] == "square kilometres"
    assert result["rows"] == [
        {"year": 2002, "value": 481.509},
        {"year": 2012, "value": 1770.5665},
    ]
    assert result["summary"]["endpoint_difference"] == 1289.0575
    assert store.get(result["evidence_id"])["result"]["rows"] == result["rows"]
    empty = query(
        ScienceRequest(
            dataset_id="chesapeake_cover_crops", start_year=2003, end_year=2005
        ),
        store,
    )
    assert empty["status"] == "unsupported"


def test_science_input_boundaries():
    for args in [
        {"dataset_id": "arbitrary"},
        {"dataset_id": "md_temperature", "start_year": 2020},
        {"dataset_id": "md_temperature", "start_year": 2010, "end_year": 2000},
    ]:
        with pytest.raises(ValidationError):
            ScienceRequest(**args)


async def test_science_protocol(settings):
    async with Client(create_server(settings)) as client:
        caps = await client.call_tool("inspect_science_capabilities", {})
        assert len(caps.data["datasets"]) == 4
        result = await client.call_tool(
            "query_science_series", {"request": {"dataset_id": "md_temperature"}}
        )
        assert len(result.data["rows"]) == 28
        assert result.data["geography"] == "Maryland statewide"
