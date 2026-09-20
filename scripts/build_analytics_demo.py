import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics_models import (  # noqa: E402
    InterviewMetricRecord,
    PipelineRunRecord,
    RetrievalEvaluationRecord,
)
from src.analytics_pipeline import AnalyticsPipeline  # noqa: E402


def sample_records() -> list:
    occurred_at = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
    report = json.loads(
        (PROJECT_ROOT / "evals" / "retrieval_quality.json").read_text(encoding="utf-8")
    )
    return [
        PipelineRunRecord(
            occurred_at=occurred_at,
            operation="document_index",
            status="success",
            duration_ms=16_096,
            input_count=45,
            output_count=45,
            cache_misses=45,
            model="text-embedding-3-small",
            app_version="portfolio-demo",
        ),
        PipelineRunRecord(
            occurred_at=occurred_at,
            operation="document_index",
            status="success",
            duration_ms=48,
            input_count=45,
            output_count=45,
            cache_hits=45,
            model="text-embedding-3-small",
            app_version="portfolio-demo",
        ),
        PipelineRunRecord(
            occurred_at=occurred_at,
            operation="document_search",
            status="success",
            duration_ms=92,
            input_count=1,
            output_count=4,
            cache_misses=1,
            model="text-embedding-3-small",
            app_version="portfolio-demo",
        ),
        InterviewMetricRecord(
            occurred_at=occurred_at,
            role_family="Data Engineer",
            question_type="SQL",
            difficulty="Intermediate",
            score=74,
            technical_accuracy=20,
            clarity=19,
            tradeoff_reasoning=18,
            production_readiness=17,
        ),
        InterviewMetricRecord(
            occurred_at=occurred_at,
            role_family="Data Engineer",
            question_type="System Design",
            difficulty="Advanced",
            score=82,
            technical_accuracy=22,
            clarity=20,
            tradeoff_reasoning=21,
            production_readiness=19,
        ),
        RetrievalEvaluationRecord(
            occurred_at=occurred_at,
            evaluation_name="ten_case_retrieval_quality",
            case_count=report["cold_run"]["case_count"],
            top_k=report["top_k"],
            minimum_score=report["min_score"],
            hit_rate=report["cold_run"]["hit_rate"],
            mean_reciprocal_rank=report["cold_run"]["mean_reciprocal_rank"],
            cold_seconds=report["cold_run"]["duration_seconds"],
            warm_seconds=report["warm_run"]["duration_seconds"],
        ),
    ]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a local DuckDB and Parquet analytics demo from synthetic events."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "analytics",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline = AnalyticsPipeline(args.output)
    pipeline.append_many(sample_records())
    result = pipeline.run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
