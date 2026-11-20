"""Private research interface; data/tools remain in the separate MCP App."""

import asyncio
import json
from urllib.parse import urlsplit

import plotly.graph_objects as go
import streamlit as st

from datagov_mcp.agent import AgentSettings, agent_workspace, run_agent


def safe_link(url):
    return isinstance(url, str) and urlsplit(url).scheme == "https"


def source_cards(trace):
    cards = {}
    for step in trace:
        value = step.get("result", {})
        if not isinstance(value, dict):
            continue
        for card in (
            value.get("datasets", [])
            if step.get("tool")
            in ("find_data_for_question", "assess_dataset_readiness")
            else []
        ):
            identity = (
                card.get("identifier")
                or card.get("harvest_record_id")
                or card.get("title")
            )
            previous = cards.get(identity, {})
            cards[identity] = {**previous, **card}
            if "readiness" in previous and "readiness" not in card:
                for key in ("queryable", "queryability_reason"):
                    cards[identity][key] = previous[key]
        if isinstance(value.get("dataset"), dict):
            card = value["dataset"]
            identity = (
                card.get("identifier")
                or card.get("harvest_record_id")
                or card.get("title")
            )
            previous = cards.get(identity, {})
            cards[identity] = {**previous, **card}
            for key in ("readiness", "relevance", "candidate_rank"):
                if key in previous:
                    cards[identity][key] = previous[key]
            if "readiness" in previous:
                cards[identity]["queryable"] = previous["queryable"]
                cards[identity]["queryability_reason"] = previous["queryability_reason"]
    used = {}
    for step in trace:
        value = step.get("result", {})
        if not isinstance(value, dict):
            continue
        if (
            step.get("tool") == "query_science_series"
            and value.get("status") == "complete"
        ):
            source = value["source"]
            identity = source.get("catalog_identifier") or source["url"]
            previous = cards.get(identity, {})
            used[identity] = {
                **previous,
                "identifier": identity,
                "title": previous.get("title") or value["title"],
                "publisher": source.get("publisher"),
                "description": value["method"],
                "spatial_coverage": value["geography"],
                "observation_period": (
                    f"{value['rows'][0]['year']}–{value['rows'][-1]['year']}"
                ),
                "landing_page": previous.get("landing_page") or identity,
                "source_url": source["url"],
                "used": True,
                "used_scopes": used.get(identity, {}).get("used_scopes", [])
                + [f"{value['title']} ({value['unit']})"],
            }
        if step.get("tool") in ("get_analysis_evidence", "compare_public_indicators"):
            if (
                step.get("tool") == "compare_public_indicators"
                and value.get("status") != "complete"
            ):
                continue
            evidence = value.get("evidence", value)
            if not isinstance(evidence, dict):
                continue
            manifest = evidence.get(
                "snapshot", {"sources": evidence.get("sources", [])}
            )
            if not isinstance(manifest, dict):
                continue
            for source in manifest.get("sources", []):
                identity = source.get("catalog_identifier") or source["url"]
                used[identity] = {
                    **cards.get(identity, {}),
                    "identifier": identity,
                    "title": source.get("title") or source["id"],
                    "publisher": source.get("publisher"),
                    "description": (
                        "Reviewed source used for the Maryland county comparison."
                    ),
                    "spatial_coverage": "Maryland counties and county equivalents",
                    "observation_period": "2022–2024",
                    "source_url": source["url"],
                    "used": True,
                }
    remaining = [card for key, card in cards.items() if key not in used]
    remaining.sort(
        key=lambda card: (
            -card.get("relevance", {}).get("score", -1),
            card.get("title") or "",
        )
    )
    return list(used.values()), remaining


def display_card(card, index, concise=False):
    title = card.get("title") or "Untitled dataset"
    st.markdown(f"**{index}. {title}**")
    link = card.get("landing_page")
    if not safe_link(link):
        identifier = card.get("identifier")
        link = identifier if safe_link(identifier) else None
    if not link and card.get("harvest_record_id"):
        link = "https://catalog.data.gov/harvest_record/" + card["harvest_record_id"]
    if not link:
        link = card.get("source_url")
    if safe_link(link):
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
    if card.get("used"):
        st.caption(
            "Used in this answer: "
            + "; ".join(card.get("used_scopes", ["County comparison"]))
        )
    else:
        readiness = card.get("readiness", {})
        st.caption("Availability: " + readiness.get("label", "Not assessed"))
        for blocker in readiness.get("blockers", []):
            st.caption("Requires: " + blocker)
        for scope in readiness.get("scopes", []):
            st.caption(
                "Supported scope: "
                + str(scope.get("geography", ""))
                + " · Years: "
                + ", ".join(map(str, scope.get("available_years", [])))
            )
        matches = card.get("relevance", {}).get("title_matches", [])
        if matches:
            st.caption("Topic matches: " + ", ".join(matches))
    distributions = card.get("distributions", [])
    formats = sorted({str(d["format"]) for d in distributions if d.get("format")})
    st.caption("Formats: " + (", ".join(formats) or "Not specified"))
    terms = card.get("terms", {})
    st.caption(
        "Access/use terms: "
        + (
            "; ".join(f"{key}: {value}" for key, value in terms.items())
            or "Not established; public metadata is not access permission"
        )
    )
    dictionary = card.get("data_dictionary")
    if dictionary:
        st.caption("Data dictionary: " + str(dictionary))
    else:
        st.caption("Data dictionary: not specified")


def display_result(result, concise=False):
    answer_tab, diagnostics_tab = st.tabs(
        ["Answer & sources", "Evaluation & diagnostics"]
    )
    trace = result.get("trace", [])
    with diagnostics_tab:
        st.caption(
            "Actual tool calls, metadata ranking details "
            "and source evidence for review."
        )
        st.json(trace)
        st.download_button(
            "Download answer and evidence JSON",
            json.dumps(result, indent=2),
            "research-evidence.json",
            "application/json",
        )
    with answer_tab:
        if result.get("status") != "complete":
            st.warning(
                "This response did not complete. Treat partial answers as incomplete."
            )
        st.markdown(result.get("answer") or "No answer returned.")
        used, remaining = source_cards(trace)
        for heading, cards in (
            ("Sources used in this answer", used),
            ("Other relevant datasets", remaining),
        ):
            if cards:
                st.subheader(heading)
                if heading == "Other relevant datasets":
                    st.caption(
                        "Bounded candidates, not an exhaustive inventory. "
                        "Availability is separate from relevance."
                    )
                for index, card in enumerate(cards, 1):
                    display_card(card, index, concise)
        display_charts(trace)


def display_charts(trace):
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
            st.caption(
                "Counties compared: "
                + str(value.get("summary", {}).get("counties_compared", "unknown"))
            )
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
            "What datasets are available about climate, irrigation "
            "and cover-crop practices?"
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
            "Is there a correlation between climate patterns and "
            "agricultural practices over time in Maryland "
            "and the Chesapeake Bay watershed?"
        ),
        "County comparison": (
            "Which Maryland counties gained population while "
            "unemployment fell from 2022 to 2024?"
        ),
    }
    choice = st.selectbox("Example", list(examples))
    concise = st.checkbox("Show dataset names and links only", value=False)
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
        display_result(st.session_state["result"], concise=concise)


if __name__ == "__main__":
    main()
