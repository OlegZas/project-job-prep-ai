"""Session-first telemetry with optional local persistence."""

import json
import os
from typing import Iterable

import streamlit as st
from pydantic import BaseModel

from src.analytics_pipeline import AnalyticsPipeline, record_to_envelope


SESSION_KEY = "analytics_events"


def analytics_mode() -> str:
    mode = os.getenv("DATAPREP_ANALYTICS_MODE", "session").strip().casefold()
    if mode not in {"session", "local"}:
        raise ValueError("DATAPREP_ANALYTICS_MODE must be 'session' or 'local'")
    return mode


def record_event(record: BaseModel) -> dict:
    envelope = record_to_envelope(record)
    events = st.session_state.setdefault(SESSION_KEY, [])
    if not any(event["event_id"] == envelope["event_id"] for event in events):
        events.append(envelope)
    if analytics_mode() == "local":
        AnalyticsPipeline().append_envelope(envelope)
    return envelope


def session_events() -> list[dict]:
    return list(st.session_state.get(SESSION_KEY, []))


def export_events(events: Iterable[dict] | None = None) -> str:
    selected = list(events) if events is not None else session_events()
    return json.dumps(selected, indent=2)


def summarize_session(events: Iterable[dict] | None = None) -> dict:
    selected = list(events) if events is not None else session_events()
    pipeline = [event["payload"] for event in selected if event["event_type"] == "pipeline_run"]
    interviews = [
        event["payload"] for event in selected if event["event_type"] == "interview_metric"
    ]
    cache_hits = sum(event.get("cache_hits", 0) for event in pipeline)
    cache_misses = sum(event.get("cache_misses", 0) for event in pipeline)
    cache_total = cache_hits + cache_misses
    return {
        "event_count": len(selected),
        "operation_count": len(pipeline),
        "success_rate": (
            round(100 * sum(event["status"] == "success" for event in pipeline) / len(pipeline), 1)
            if pipeline
            else None
        ),
        "average_duration_ms": (
            round(sum(event["duration_ms"] for event in pipeline) / len(pipeline), 1)
            if pipeline
            else None
        ),
        "cache_hit_percent": round(100 * cache_hits / cache_total, 1) if cache_total else None,
        "interview_attempts": len(interviews),
        "average_interview_score": (
            round(sum(event["score"] for event in interviews) / len(interviews), 1)
            if interviews
            else None
        ),
    }
