"""Private research interface; data/tools remain in the separate MCP App."""

import asyncio
import json
from urllib.parse import urlsplit

import plotly.graph_objects as go
import streamlit as st
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from datagov_mcp.agent import AgentSettings, agent_workspace, run_agent
from datagov_mcp.tls import verified_context

CATALOG_TOOLS = ("find_data_for_question", "assess_dataset_readiness")
DATA_TOOLS = ("query_dataset", "analyze_change")
TABS = ["Answer", "Sources", "Data & charts", "Explore further", "Evaluation"]


def safe_link(url):
    return isinstance(url, str) and urlsplit(url).scheme == "https"


def completed(trace, tools):
    for index, step in enumerate(trace):
        value = step.get("result")
        if (
            step.get("tool") in tools
            and isinstance(value, dict)
            and value.get("status") == "complete"
        ):
            yield index, step, value


def catalog_cards(trace):
    cards = {}
    for step in trace:
        value = step.get("result")
        if not isinstance(value, dict):
            continue
        found = value.get("datasets", []) if step.get("tool") in CATALOG_TOOLS else []
        if isinstance(value.get("dataset"), dict):
            found = [value["dataset"]]
        for card in found:
            identity = (
                card.get("identifier")
                or card.get("harvest_record_id")
                or card.get("title")
            )
            previous = cards.get(identity, {})
            merged = {**previous, **card}
            # Later plain inspections must not erase an earlier readiness assessment.
            if "readiness" in previous and "readiness" not in card:
                for key in ("readiness", "relevance", "queryable"):
                    if key in previous:
                        merged[key] = previous[key]
            cards[identity] = merged
    return cards


def used_datasets(trace):
    used = {}
    for _, step, value in completed(trace, DATA_TOOLS):
        entry = used.setdefault(
            value["dataset_id"],
            {
                "dataset_id": value["dataset_id"],
                "title": value.get("title") or value["dataset_id"],
                "geography": value.get("geography", {}),
                "sources": value.get("sources", []),
                "measures": {},
                "periods": set(),
            },
        )
        for measure in value.get("measures", []):
            entry["measures"][measure["id"]] = measure
        for row in value.get("rows", []):
            if "period" in row:
                entry["periods"].add(row["period"])
        if "start_period" in value:
            entry["periods"].update({value["start_period"], value["end_period"]})
    return list(used.values())


def source_cards(trace):
    """Return (datasets used for observations, other catalog candidates)."""
    used = used_datasets(trace)
    identifiers = {s.get("catalog_identifier") for d in used for s in d["sources"]}
    cards = catalog_cards(trace)
    remaining = [c for key, c in cards.items() if key not in identifiers]
    remaining.sort(
        key=lambda c: (-c.get("relevance", {}).get("score", -1), c.get("title") or "")
    )
    return used, remaining


def card_link(card):
    for candidate in (card.get("landing_page"), card.get("identifier")):
        if safe_link(candidate):
            return candidate
    if card.get("harvest_record_id"):
        return "https://catalog.data.gov/harvest_record/" + card["harvest_record_id"]
    return None


def display_used(dataset, index):
    st.markdown(f"**{index}. {dataset['title']}**")
    geography = dataset["geography"]
    periods = sorted(dataset["periods"])
    st.caption(
        f"{geography.get('level', '').title()} · {geography.get('area', '')}"
        + (f" · {periods[0]}–{periods[-1]}" if periods else "")
    )
    for measure in dataset["measures"].values():
        st.caption(f"{measure['label']} ({measure['unit']})")
    for source in dataset["sources"]:
        label = source.get("title") or source.get("publisher") or "Publisher source"
        if safe_link(source.get("url")):
            st.link_button(label, source["url"])


def display_candidate(card, index, concise=False):
    readiness = card.get("readiness", {})
    st.markdown(
        f"**{index}. {card.get('title') or 'Untitled dataset'}** — "
        + readiness.get("label", "Availability not assessed")
    )
    link = card_link(card)
    if link:
        st.link_button("Dataset information", link)
    if concise:
        return
    st.caption("Publisher: " + (card.get("publisher") or "Not specified"))
    st.write(card.get("description") or "Description not provided.")
    st.caption(
        "Coverage: "
        + str(card.get("spatial_coverage") or "Geography not specified")
        + " · Period: "
        + str(card.get("observation_period") or "Not specified")
    )
    for blocker in readiness.get("blockers", []):
        st.caption("Requires: " + blocker)
    formats = sorted(
        {str(d["format"]) for d in card.get("distributions", []) if d.get("format")}
    )
    st.caption("Formats: " + (", ".join(formats) or "Not specified"))
    terms = card.get("terms", {})
    st.caption(
        "Access/use terms: "
        + (
            "; ".join(f"{k}: {v}" for k, v in terms.items())
            or "Not established; public metadata is not access permission"
        )
    )


def measure_fields(value):
    if "start_period" in value:
        return [
            (m["id"] + "_change", m["label"] + " change", m["change_unit"])
            for m in value["measures"]
        ]
    return [(m["id"], m["label"], m["unit"]) for m in value["measures"]]


def display_data(value, key, show_table=True):
    """Generic chart: change → bars by geography; observations → series by period."""
    rows = value.get("rows", [])
    if not rows:
        return
    st.subheader(value.get("title") or value["dataset_id"])
    geographies = {r["geography_id"] for r in rows}
    for field, label, unit in measure_fields(value):
        points = [r for r in rows if r.get(field) is not None]
        if not points:
            continue
        if "start_period" in value:
            ordered = sorted(points, key=lambda r: r[field])
            figure = go.Figure(
                go.Bar(
                    x=[r[field] for r in ordered],
                    y=[r["geography_name"] for r in ordered],
                    orientation="h",
                )
            )
            figure.update_layout(height=max(260, 24 * len(ordered)))
            title = f"{label}, {value['start_period']}–{value['end_period']}"
            figure.update_layout(title=title, xaxis_title=unit)
        else:
            figure = go.Figure()
            for geography in sorted(geographies):
                series = sorted(
                    (r for r in points if r["geography_id"] == geography),
                    key=lambda r: r["period"],
                )
                periods = [r["period"] for r in series]
                gaps = any(b - a > 1 for a, b in zip(periods, periods[1:]))
                # Sparse observation years are shown as unconnected points.
                figure.add_trace(
                    go.Scatter(
                        x=periods,
                        y=[r[field] for r in series],
                        mode="markers" if gaps else "lines+markers",
                        name=series[0]["geography_name"],
                    )
                )
            figure.update_layout(
                title=label,
                xaxis_title="Observation period",
                yaxis_title=unit,
                showlegend=len(geographies) > 1,
            )
        st.plotly_chart(figure, key=f"{key}-{field}")
    if show_table:
        st.dataframe(rows)
    for caveat in value.get("caveats", []):
        st.caption(caveat)


def display_result(result, concise=False):
    trace = result.get("trace", [])
    used, candidates = source_cards(trace)
    answer, sources, data, explore, evaluation = st.tabs(TABS)
    with answer:
        if result.get("status") != "complete":
            st.warning("This response did not complete. Treat it as incomplete.")
        st.markdown(result.get("answer") or "No answer returned.")
    with sources:
        if used:
            st.subheader("Data used in this answer")
            for index, dataset in enumerate(used, 1):
                display_used(dataset, index)
        if candidates:
            st.subheader("Other relevant datasets")
            st.caption(
                "Bounded catalog candidates, not an exhaustive inventory. "
                "Availability is separate from relevance."
            )
            for index, card in enumerate(candidates, 1):
                display_candidate(card, index, concise)
        if not used and not candidates:
            st.write("No datasets were consulted for this answer.")
    with data:
        shown = False
        for index, step, value in completed(trace, DATA_TOOLS):
            display_data(value, f"trace-{index}")
            shown = True
        if not shown:
            st.write("No observations were retrieved for this answer.")
    with explore:
        display_exploration(used)
    with evaluation:
        st.caption("Actual tool calls and source evidence, for review and judging.")
        st.json(trace, expanded=False)
        st.download_button(
            "Download answer and evidence JSON",
            json.dumps(result, indent=2),
            "research-evidence.json",
            "application/json",
        )


async def mcp_tool(name, arguments=None):
    settings = AgentSettings()
    workspace = agent_workspace(settings)
    headers = await asyncio.to_thread(workspace.config.authenticate)
    async with Client(
        StreamableHttpTransport(
            settings.databricks_mcp_url, headers=headers, verify=verified_context()
        ),
        timeout=120,
    ) as client:
        return (await client.call_tool(name, arguments or {})).data


def display_exploration(used=()):
    original = st.session_state.get("original_question", "")
    if original:
        st.caption("Exploring: " + original)
    st.write(
        "Select queryable datasets to preview actual observations and check whether "
        "their geography and periods align. Catalog datasets without a reviewed "
        "connector cannot be retrieved here."
    )
    if st.button("Show queryable datasets"):
        try:
            st.session_state["exploration_options"] = asyncio.run(
                mcp_tool("list_queryable_datasets")
            )
        except Exception:
            st.error("Could not load datasets. Your answer is preserved.")
    options = [
        d
        for d in st.session_state.get("exploration_options", {}).get("datasets", [])
        if d.get("ready")
    ]
    if options:
        lookup = {d["dataset_id"]: d for d in options}
        selected = st.multiselect(
            "Select datasets to explore",
            list(lookup),
            default=[d["dataset_id"] for d in used if d["dataset_id"] in lookup],
            format_func=lambda i: lookup[i]["title"],
        )
        live = st.checkbox(
            "Refresh from publisher where a live route is registered",
            help="Bounded fixed-route requests; otherwise reviewed snapshots.",
        )
        if st.button("Explore selected data", disabled=not selected):
            with st.spinner("Retrieving and validating selected observations…"):
                st.session_state["exploration"] = asyncio.run(
                    explore_selection(selected, live)
                )
    preview = st.session_state.get("exploration")
    if preview:
        for index, value in enumerate(preview["datasets"]):
            if value.get("status") != "complete":
                reason = value.get("reason") or value.get("error", {}).get("message")
                st.warning(f"{value.get('dataset_id')}: {reason or 'Not retrieved'}")
                continue
            display_data(value, f"preview-{index}")
            st.caption(
                "Retrieved from: " + value.get("provenance", {}).get("storage", "")
            )
        pairs = preview.get("compatibility", {}).get("pairs", [])
        if pairs:
            st.subheader("Can these datasets be compared?")
            for pair in pairs:
                verdict = (
                    "Side-by-side description possible"
                    if pair["status"] == "descriptive_alignment_possible"
                    else "Not comparable"
                )
                st.markdown(f"**{' + '.join(pair['datasets'])}: {verdict}**")
                for reason in pair["reasons"]:
                    st.caption(reason)
        st.download_button(
            "Download preview and provenance",
            json.dumps(preview, indent=2),
            "selected-data-preview.json",
            "application/json",
        )
    followups = {
        "Find datasets with matching geography and periods": (
            "Which datasets provide repeated observations for the same places and "
            "periods so the measures in my question could be compared? "
            "Explain access and gaps."
        ),
        "Narrow to one measurable relationship": (
            "Suggest one measurable relationship from my question that available "
            "data can describe, and show the supporting observations."
        ),
    }
    followup = st.selectbox("Suggested next step", list(followups))
    if st.button("Research this next step"):
        settings = AgentSettings()
        prompt = (
            "Original research question: "
            + original
            + "\nNext step: "
            + followups[followup]
        )
        with st.spinner("Following up on the original question…"):
            try:
                st.session_state["result"] = asyncio.run(
                    run_agent(prompt, settings, agent_workspace(settings))
                )
                for key in ("exploration", "exploration_options"):
                    st.session_state.pop(key, None)
                st.rerun()
            except Exception:
                st.error("Follow-up failed; the previous answer is preserved.")


async def explore_selection(dataset_ids, live):
    results = []
    for dataset_id in dataset_ids:
        try:
            results.append(
                await mcp_tool(
                    "query_dataset",
                    {"request": {"dataset_id": dataset_id}, "live": live},
                )
            )
        except Exception:
            results.append({"dataset_id": dataset_id, "status": "failed"})
    compatibility = {}
    if len(dataset_ids) > 1:
        try:
            compatibility = await mcp_tool(
                "assess_compatibility",
                {"request": {"datasets": [{"dataset_id": i} for i in dataset_ids]}},
            )
        except Exception:
            compatibility = {}
    return {"datasets": results, "compatibility": compatibility}


EXAMPLES = {
    "Dataset landscape": (
        "What datasets are available about climate, irrigation and cover-crop "
        "practices?"
    ),
    "Climate and agriculture": (
        "Is there a correlation between climate patterns and agricultural "
        "practices over time in Maryland and the Chesapeake Bay watershed?"
    ),
    "Change over time": (
        "How did estimated cover-crop implementation in the Chesapeake Bay "
        "watershed change between 2002 and 2012?"
    ),
    "County comparison": (
        "Which Maryland counties gained population while unemployment fell from "
        "2022 to 2024?"
    ),
}


def main():
    st.set_page_config(page_title="Data.gov Research", layout="wide")
    st.title("Data.gov Research")
    st.caption(
        "Ask a question about public data. Private hackathon prototype; each question "
        "starts fresh. Do not enter private or sensitive information."
    )
    choice = st.selectbox("Example", list(EXAMPLES))
    with st.form("question"):
        question = st.text_area(
            "Question", value=EXAMPLES[choice], max_chars=2000, height=100
        )
        submitted = st.form_submit_button("Research")
    concise = st.toggle("Show dataset names and links only", value=False)
    if submitted and question.strip():
        with st.spinner("Researching…"):
            try:
                settings = AgentSettings()
                st.session_state["result"] = asyncio.run(
                    run_agent(question, settings, agent_workspace(settings))
                )
                st.session_state["original_question"] = question
                for key in ("exploration", "exploration_options"):
                    st.session_state.pop(key, None)
            except Exception:
                st.error(
                    "Research request failed. Check App access and model "
                    "configuration; no result was verified."
                )
                st.session_state.pop("result", None)
    if "result" in st.session_state:
        answered = st.session_state.get("original_question")
        if answered:
            st.markdown("**Answering:** " + answered)
        display_result(st.session_state["result"], concise=concise)


if __name__ == "__main__":
    main()
