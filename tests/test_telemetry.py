from src.analytics_models import InterviewMetricRecord, PipelineRunRecord
from src.telemetry import summarize_session


def test_session_summary_combines_pipeline_and_interview_metrics():
    pipeline = PipelineRunRecord(
        operation="document_search",
        status="success",
        duration_ms=100,
        cache_hits=3,
        cache_misses=1,
    )
    interview = InterviewMetricRecord(
        role_family="Data Engineer",
        question_type="SQL",
        difficulty="Intermediate",
        score=80,
        technical_accuracy=20,
        clarity=20,
        tradeoff_reasoning=20,
        production_readiness=20,
    )
    events = [
        {
            "event_type": "pipeline_run",
            "payload": pipeline.model_dump(mode="json"),
        },
        {
            "event_type": "interview_metric",
            "payload": interview.model_dump(mode="json"),
        },
    ]

    summary = summarize_session(events)

    assert summary["success_rate"] == 100.0
    assert summary["average_duration_ms"] == 100.0
    assert summary["cache_hit_percent"] == 75.0
    assert summary["average_interview_score"] == 80.0
