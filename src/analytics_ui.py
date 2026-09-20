import json
import os
from pathlib import Path

import streamlit as st

from src.analytics_pipeline import AnalyticsPipeline
from src.telemetry import analytics_mode, export_events, session_events, summarize_session


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
    st.write("### Retrieval evaluation")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Hit@{report['top_k']}", f"{cold['hit_rate']:.0%}")
    col2.metric("MRR", f"{cold['mean_reciprocal_rank']:.3f}")
    col3.metric("Cold run", f"{cold['duration_seconds']:.3f}s")
    col4.metric("Warm speedup", f"{report['warm_speedup']:.1f}×")
    st.caption(
        f"{cold['case_count']} labeled cases, {report['chunk_count']} chunks, "
        f"minimum similarity {report['min_score']}. The warm run made "
        f"{warm['embedding_cache']['misses']} embedding API calls."
    )


def render_engineering_metrics():
    st.header("Engineering Metrics")
    st.write(
        "Operational events stay in this browser session on the public app. Local mode "
        "can persist the same privacy-safe records through raw JSONL, DuckDB SQL marts, "
        "and partitioned Parquet files."
    )

    events = session_events()
    summary = summarize_session(events)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Session operations", summary["operation_count"])
    col2.metric(
        "Success rate",
        f"{summary['success_rate']:.1f}%" if summary["success_rate"] is not None else "—",
    )
    col3.metric(
        "Average latency",
        f"{summary['average_duration_ms']:.0f} ms"
        if summary["average_duration_ms"] is not None
        else "—",
    )
    col4.metric(
        "Cache hit rate",
        f"{summary['cache_hit_percent']:.1f}%"
        if summary["cache_hit_percent"] is not None
        else "—",
    )

    rows = _pipeline_rows(events)
    if rows:
        st.write("### Current session pipeline runs")
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("Use another tab to create session pipeline metrics.")

    if summary["interview_attempts"]:
        interview1, interview2 = st.columns(2)
        interview1.metric("Interview attempts", summary["interview_attempts"])
        interview2.metric(
            "Average interview score", f"{summary['average_interview_score']:.1f}/100"
        )

    st.download_button(
        "Download privacy-safe session events",
        data=export_events(events),
        file_name="dataprep_analytics_events.json",
        mime="application/json",
        disabled=not events,
    )

    _render_retrieval_quality()

    st.write("### Local analytical pipeline")
    if analytics_mode() == "local":
        st.success("Local persistence is enabled for this process.")
        if st.button("Run incremental DuckDB pipeline"):
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
        st.info(
            "Public session mode is active. For persistent local analytics, set "
            "DATAPREP_ANALYTICS_MODE=local in .env and restart the app."
        )

    with st.expander("Data model and privacy boundary"):
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
