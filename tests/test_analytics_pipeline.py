import json

from src.analytics_models import (
    InterviewMetricRecord,
    PipelineRunRecord,
    RetrievalEvaluationRecord,
)
from src.analytics_pipeline import AnalyticsPipeline


def records():
    return [
        PipelineRunRecord(
            operation="document_search",
            status="success",
            duration_ms=125,
            input_count=1,
            output_count=3,
            cache_hits=1,
        ),
        InterviewMetricRecord(
            role_family="Data Engineer",
            question_type="SQL",
            difficulty="Intermediate",
            score=80,
            technical_accuracy=20,
            clarity=20,
            tradeoff_reasoning=20,
            production_readiness=20,
        ),
        RetrievalEvaluationRecord(
            evaluation_name="test",
            case_count=10,
            top_k=4,
            minimum_score=0.25,
            hit_rate=1.0,
            mean_reciprocal_rank=0.88,
            cold_seconds=16.0,
            warm_seconds=0.05,
        ),
    ]


def test_pipeline_builds_incremental_duckdb_marts_and_partitioned_parquet(tmp_path):
    pipeline = AnalyticsPipeline(tmp_path)
    paths = pipeline.append_many(records())

    assert all("event_date=" in str(path) for path in paths)
    raw_event = json.loads(paths[0].read_text(encoding="utf-8").splitlines()[0])
    assert "question" not in raw_event["payload"]
    assert "answer" not in raw_event["payload"]

    first = pipeline.run()
    second = pipeline.run()

    assert first["inserted_events"] == 3
    assert first["total_events"] == 3
    assert second["inserted_events"] == 0
    assert all(check["status"] == "pass" for check in first["quality_checks"])
    assert len(first["parquet_files"]) == 3
    assert all("event_date=" in path for path in first["parquet_files"])
    assert pipeline.query("SELECT run_count FROM marts.pipeline_daily")[0]["run_count"] == 1
    assert (
        pipeline.query("SELECT average_score FROM marts.interview_progress")[0][
            "average_score"
        ]
        == 80
    )


def test_pipeline_rejects_unsupported_record(tmp_path):
    from pydantic import BaseModel

    class UnknownRecord(BaseModel):
        occurred_at: str = "2026-01-01T00:00:00+00:00"

    pipeline = AnalyticsPipeline(tmp_path)

    try:
        pipeline.append(UnknownRecord())
        raise AssertionError("Expected unsupported record error")
    except ValueError as error:
        assert "Unsupported analytics record" in str(error)
