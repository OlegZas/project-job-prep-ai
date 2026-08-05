"""Privacy-conscious analytics records for the future BigQuery pipeline.

These schemas deliberately exclude document text, resume content, answers, and file
names. The application can measure reliability and cost without copying personal
career data into an analytics warehouse.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineRunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=_utc_now)
    operation: Literal[
        "document_index",
        "document_search",
        "career_extraction",
        "learning_plan",
        "interview_generation",
        "interview_scoring",
    ]
    status: Literal["success", "no_result", "error"]
    duration_ms: int = Field(ge=0)
    input_count: int = Field(default=0, ge=0)
    output_count: int = Field(default=0, ge=0)
    cache_hits: int = Field(default=0, ge=0)
    cache_misses: int = Field(default=0, ge=0)
    model: str | None = None
    error_type: str | None = None
    app_version: str | None = None

    def to_bigquery_row(self) -> dict:
        row = self.model_dump(mode="json")
        row["occurred_at"] = self.occurred_at.isoformat()
        return row


class RetrievalEvaluationRecord(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=_utc_now)
    evaluation_name: str
    case_count: int = Field(gt=0)
    top_k: int = Field(gt=0)
    minimum_score: float = Field(ge=-1.0, le=1.0)
    hit_rate: float = Field(ge=0.0, le=1.0)
    mean_reciprocal_rank: float = Field(ge=0.0, le=1.0)
    cold_seconds: float = Field(ge=0.0)
    warm_seconds: float = Field(ge=0.0)

    def to_bigquery_row(self) -> dict:
        row = self.model_dump(mode="json")
        row["occurred_at"] = self.occurred_at.isoformat()
        return row


class InterviewMetricRecord(BaseModel):
    attempt_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=_utc_now)
    role_family: str
    question_type: Literal["SQL", "Python", "Data Modeling", "System Design", "Behavioral"]
    difficulty: Literal["Foundational", "Intermediate", "Advanced"]
    score: int = Field(ge=0, le=100)
    technical_accuracy: int = Field(ge=0, le=25)
    clarity: int = Field(ge=0, le=25)
    tradeoff_reasoning: int = Field(ge=0, le=25)
    production_readiness: int = Field(ge=0, le=25)

    def to_bigquery_row(self) -> dict:
        row = self.model_dump(mode="json")
        row["occurred_at"] = self.occurred_at.isoformat()
        return row
