"""Private research interface; data/tools remain in the separate MCP App."""

import asyncio
import json
from urllib.parse import urlsplit

import plotly.graph_objects as go
import streamlit as st

from datagov_mcp.agent import AgentSettings, agent_workspace, run_agent


def safe_link(url):
    return isinstance(url, str) and urlsplit(url).scheme == "https"


def display_result(result):
    if result.get("status") != "complete":
        st.warning(
            "This response did not complete. Treat any partial answer as incomplete."
        )
    st.markdown(result.get("answer") or "No answer returned.")
    trace = result.get("trace", [])
    cards = {}
    for step in trace:
        value = step.get("result", {})
        if not isinstance(value, dict):
            continue
        for card in (
            value.get("datasets", [])
            if step.get("tool") == "find_data_for_question"
            else []
        ):
            cards[
                card.get("identifier")
                or card.get("harvest_record_id")
                or card.get("title")
            ] = card
        if isinstance(value.get("dataset"), dict):
            card = value["dataset"]
            cards[
                card.get("identifier")
                or card.get("harvest_record_id")
                or card.get("title")
            ] = card
    if cards:
        st.subheader(f"Dataset inventory — {len(cards)} distinct returned records")
        st.caption(
            (
                "Bounded search results, not an exhaustive "
                "inventory. Metadata is not verified "
                "observations."
            )
        )
        for card in cards.values():
            with st.expander(card.get("title") or "Untitled dataset"):
                st.write(
                    {
                        k: card.get(k)
                        for k in (
                            "publisher",
                            "identifier",
                            "observation_period",
                            "access_status",
                            "queryable",
                        )
                    }
                )
                st.write(card.get("description", ""))
                url = card.get("landing_page")
                if safe_link(url):
                    st.link_button("Publisher landing page", url)
                st.json(
                    {
                        k: card.get(k)
                        for k in (
                            "terms",
                            "data_dictionary",
                            "distributions",
                            "metadata_note",
                        )
                    }
                )
    for index, step in enumerate(trace):
        value = step.get("result", {})
        if not isinstance(value, dict) or value.get("status") != "complete":
            continue
        rows = value.get("rows", [])
        if step["tool"] == "compare_public_indicators" and rows:
            st.subheader("County comparison")
            st.caption(
                (
                    "Population: percent change. Unemployment: "
                    "percentage-point change. Separate axes; no "
                    "causal inference."
                )
            )
            st.json(value.get("summary", {}), expanded=False)
            for field, title in [
                ("population_change", "Population change (%)"),
                ("unemployment_change", "Unemployment rate change (percentage points)"),
            ]:
                ordered = sorted(rows, key=lambda r: r[field])
                fig = go.Figure(
                    go.Bar(
                        x=[r[field] for r in ordered],
                        y=[r["county_name"] for r in ordered],
                        orientation="h",
                    )
                )
                fig.update_layout(
                    title=title, xaxis_title=title, height=max(300, len(rows) * 24)
                )
                st.plotly_chart(fig, key=f"county-{index}-{field}")
            st.dataframe(rows)
        elif step["tool"] == "query_science_series" and rows:
            st.subheader(value["title"])
            st.caption(f"{value['geography']} · {value['unit']} · {value['method']}")
            fig = go.Figure()
            # Sparse practice observations remain unconnected.
            mode = (
                "lines+markers" if value["dataset_id"].startswith("md_") else "markers"
            )
            fig.add_trace(
                go.Scatter(
                    x=[r["year"] for r in rows], y=[r["value"] for r in rows], mode=mode
                )
            )
            fig.update_layout(xaxis_title="Observation year", yaxis_title=value["unit"])
            st.plotly_chart(fig, key=f"science-{index}")
            st.dataframe(rows)
            for caveat in value.get("caveats", []):
                st.caption(caveat)
        if value.get("evidence_id"):
            st.caption("Evidence ID: " + value["evidence_id"])
    with st.expander("Full tool trace and source evidence"):
        st.json(trace)
    st.download_button(
        "Download answer and evidence JSON",
        json.dumps(result, indent=2),
        "research-evidence.json",
        "application/json",
    )


def main():
    st.set_page_config(page_title="Data.gov Research", layout="wide")
    st.title("Data.gov Research")
    st.write(
        (
            "Ask a research question. Discover public "
            "datasets, inspect their metadata, and query "
            "reviewed data where supported."
        )
    )
    st.info(
        (
            "Private hackathon prototype. Each question "
            "starts fresh; conversation memory is not "
            "implemented. Do not enter private or sensitive "
            "information."
        )
    )
    examples = {
        "Dataset landscape": (
            "Find climate and agriculture datasets relevant "
            "to changing irrigation and cover-crop practices. "
            "Inspect several promising records and describe "
            "periods, geography, formats, access, "
            "dictionaries and what remains unknown."
        ),
        "Climate observations": (
            "Show Maryland annual temperature and "
            "precipitation observations from 1985 to 2012. "
            "Explain units and why endpoint differences are "
            "not climate attribution."
        ),
        "Agricultural practices": (
            "How did estimated Chesapeake Bay watershed "
            "cover-crop and conservation-tillage "
            "implementation change in the available years? "
            "Show both series with sources."
        ),
        "Research limitations": (
            "Do Maryland climate observations prove climate "
            "change caused adoption of cover crops in the "
            "Chesapeake Bay watershed? Check what the "
            "registered data can support."
        ),
        "County comparison": (
            "Which Maryland counties gained population while "
            "unemployment fell from 2022 to 2024?"
        ),
    }
    choice = st.selectbox("Example", list(examples))
    with st.form("question"):
        question = st.text_area(
            "Question", value=examples[choice], max_chars=2000, height=110
        )
        submitted = st.form_submit_button("Research")
    if submitted and question.strip():
        with st.spinner("Researching through the MCP server…"):
            try:
                settings = AgentSettings()
                result = asyncio.run(
                    run_agent(question, settings, agent_workspace(settings))
                )
                st.session_state["result"] = result
            except Exception:
                st.error(
                    (
                        "Research request failed. Check App access and "
                        "model configuration; no result was verified."
                    )
                )
                st.session_state.pop("result", None)
    if "result" in st.session_state:
        display_result(st.session_state["result"])


if __name__ == "__main__":
    main()
