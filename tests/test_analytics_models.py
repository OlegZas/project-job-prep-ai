import pytest
from pydantic import ValidationError

from src.analytics_models import (
    InterviewMetricRecord,
    PipelineRunRecord,
    RetrievalEvaluationRecord,
)


def test_pipeline_record_is_privacy_safe_and_bigquery_ready():
    record = PipelineRunRecord(
        operation="document_index",
        status="success",
        duration_ms=125,
        input_count=3,
        output_count=18,
        cache_hits=12,
        cache_misses=6,
        model="text-embedding-3-small",
    )

    row = record.to_bigquery_row()

    assert row["run_id"]
    assert row["occurred_at"].endswith("+00:00")
    assert "document_text" not in row
    assert "file_name" not in row


def test_retrieval_metrics_are_bounded():
    with pytest.raises(ValidationError):
        RetrievalEvaluationRecord(
            evaluation_name="invalid",
            case_count=10,
            top_k=4,
            minimum_score=0.25,
            hit_rate=1.1,
            mean_reciprocal_rank=0.8,
            cold_seconds=1,
            warm_seconds=0.1,
        )


def test_interview_metric_requires_valid_rubric_scores():
    with pytest.raises(ValidationError):
        InterviewMetricRecord(
            role_family="Data Engineer",
            question_type="SQL",
            difficulty="Advanced",
            score=101,
            technical_accuracy=25,
            clarity=25,
            tradeoff_reasoning=25,
            production_readiness=25,
        )
