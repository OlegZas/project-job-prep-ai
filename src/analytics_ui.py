import json
import os
from pathlib import Path

import streamlit as st

from src.analytics_pipeline import AnalyticsPipeline
from src.telemetry import analytics_mode, export_events, session_events, summarize_session
from src.ui_components import render_section_intro


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_REPORT = PROJECT_ROOT / "evals" / "retrieval_quality.json"


def _pipeline_rows(events):
    return [
        {
            "Time": event["occurred_at"],
            "Operation": event["payload"]["operation"].replace("_", " ").title(),
            "Status": event["payload"]["status"].title(),
            "Duration (ms)": event["payload"]["duration_ms"],
            "Inputs": event["payload"]["input_count"],
            "Outputs": event["payload"]["output_count"],
            "Cache hits": event["payload"]["cache_hits"],
            "Cache misses": event["payload"]["cache_misses"],
        }
        for event in events
        if event["event_type"] == "pipeline_run"
    ]


def _render_retrieval_quality():
    if not RETRIEVAL_REPORT.exists():
        return
    report = json.loads(RETRIEVAL_REPORT.read_text(encoding="utf-8"))
    cold = report["cold_run"]
    warm = report["warm_run"]
    st.write("### Document answer quality check")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Useful source found", f"{cold['hit_rate']:.0%}")
    col2.metric("Average source rank", f"{cold['mean_reciprocal_rank']:.3f}")
    col3.metric("First run", f"{cold['duration_seconds']:.3f}s")
    col4.metric("Cached speedup", f"{report['warm_speedup']:.1f}×")
    st.caption(
        f"Tested with {cold['case_count']} prepared questions across "
        f"{report['chunk_count']} document sections. 'Useful source found' shows how "
        "often the correct source appeared. A source-rank score closer to 1 means it "
        "appeared nearer the top. Cached speedup compares repeated searches with the "
        "first run."
    )


def render_engineering_metrics():
    st.header("See how the application is performing")
    render_section_intro(
        "A transparent look behind the scenes",
        "This page shows speed, success, caching, and retrieval quality. It records "
        "operational numbers only - not your résumé text, questions, answers, or name.",
    )

    events = session_events()
    summary = summarize_session(events)
    average_duration = summary["average_duration_ms"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Actions this session",
        summary["operation_count"],
        help="Searches, answers, comparisons, plans, and interview actions recorded in this browser session.",
    )
    col2.metric(
        "Success rate",
        f"{summary['success_rate']:.1f}%" if summary["success_rate"] is not None else "—",
        help="The share of recorded actions that completed successfully.",
    )
    col3.metric(
        "Average response time",
        f"{average_duration / 1000:.1f} s"
        if average_duration is not None
        else "—",
        help="The average time taken by recorded operations. Lower is generally better.",
    )
    col4.metric(
        "Reused work",
        f"{summary['cache_hit_percent']:.1f}%"
        if summary["cache_hit_percent"] is not None
        else "—",
        help="How often cached document-search work was reused instead of created again.",
    )
    st.caption(
        "These are engineering health indicators, not a score for the user. They help "
        "show whether the app is reliable, responsive, and avoiding repeated work."
    )

    rows = _pipeline_rows(events)
    if rows:
        st.write("### Recent application actions")
        st.caption("A technical log of what ran, how long it took, and whether it succeeded.")
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("Use another tab first. Your application activity will appear here.")

    if summary["interview_attempts"]:
        interview1, interview2 = st.columns(2)
        interview1.metric("Interview attempts", summary["interview_attempts"])
        interview2.metric(
            "Average interview score", f"{summary['average_interview_score']:.1f}/100"
        )
        st.caption(
            "Interview scores summarize practice attempts from this session. A very low "
            "score usually means the submitted answer was empty or missing key detail."
        )

    st.download_button(
        "Download session performance data",
        data=export_events(events),
        file_name="dataprep_analytics_events.json",
        mime="application/json",
        disabled=not events,
    )

    _render_retrieval_quality()

    st.write("### Data engineering pipeline")
    if analytics_mode() == "local":
        st.success("Local storage is enabled for this process.")
        if st.button("Update the local analytics database"):
            try:
                with st.spinner("Ingesting events and rebuilding analytical marts..."):
                    result = AnalyticsPipeline().run()
                st.session_state.local_pipeline_result = result
            except Exception as error:
                st.error(f"Local analytics pipeline failed: {error}")

        result = st.session_state.get("local_pipeline_result")
        if result:
            p1, p2, p3 = st.columns(3)
            p1.metric("New events", result["inserted_events"])
            p2.metric("Warehouse events", result["total_events"])
            p3.metric("Parquet outputs", len(result["parquet_files"]))
            st.dataframe(result["quality_checks"], width="stretch", hide_index=True)
            st.caption(f"DuckDB: {result['database_path']}")
    else:
        st.info("The public app keeps metrics only for your current browser session. The local version can build a persistent DuckDB and Parquet analytics pipeline.")

    with st.expander("Technical details: data flow and privacy"):
        st.code(
            "Application events → partitioned JSONL → DuckDB staging views → "
            "daily analytical marts → partitioned Parquet",
            language=None,
        )
        st.write(
            "Stored fields are timestamps, operation names, statuses, counts, latency, "
            "cache metrics, model names, and aggregate interview rubric scores. Résumé "
            "text, uploaded documents, names, questions, answers, and API keys are excluded."
        )
