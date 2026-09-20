"""Local analytics pipeline: JSONL -> DuckDB -> analytical Parquet marts."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import duckdb
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANALYTICS_DIR = PROJECT_ROOT / "data" / "analytics"


def analytics_root() -> Path:
    configured = os.getenv("DATAPREP_ANALYTICS_DIR")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_ANALYTICS_DIR


def record_to_envelope(record: BaseModel) -> dict:
    payload = record.model_dump(mode="json")
    if "run_id" in payload:
        event_type = "pipeline_run"
        event_id = payload["run_id"]
    elif "attempt_id" in payload:
        event_type = "interview_metric"
        event_id = payload["attempt_id"]
    elif "evaluation_id" in payload:
        event_type = "retrieval_evaluation"
        event_id = payload["evaluation_id"]
    else:
        raise ValueError(f"Unsupported analytics record: {type(record).__name__}")

    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": payload["occurred_at"],
        "payload": payload,
    }


class AnalyticsPipeline:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root).resolve() if root else analytics_root()
        self.raw_dir = self.root / "raw" / "events"
        self.parquet_dir = self.root / "parquet"
        self.database_path = self.root / "dataprep.duckdb"

    def append(self, record: BaseModel) -> Path:
        return self.append_envelope(record_to_envelope(record))

    def append_envelope(self, envelope: dict) -> Path:
        occurred_at = datetime.fromisoformat(envelope["occurred_at"])
        partition = self.raw_dir / f"event_date={occurred_at.date().isoformat()}"
        partition.mkdir(parents=True, exist_ok=True)
        destination = partition / "events.jsonl"
        with destination.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        return destination

    def _connect(self):
        self.root.mkdir(parents=True, exist_ok=True)
        connection = duckdb.connect(str(self.database_path))
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        connection.execute("CREATE SCHEMA IF NOT EXISTS staging")
        connection.execute("CREATE SCHEMA IF NOT EXISTS marts")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.events (
                event_id VARCHAR PRIMARY KEY,
                event_type VARCHAR NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL,
                payload JSON NOT NULL,
                source_file VARCHAR NOT NULL,
                ingested_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        return connection

    def ingest(self, connection=None) -> int:
        owns_connection = connection is None
        connection = connection or self._connect()
        inserted = 0
        try:
            for source in sorted(self.raw_dir.glob("event_date=*/events.jsonl")):
                with source.open(encoding="utf-8") as stream:
                    for line in stream:
                        if not line.strip():
                            continue
                        envelope = json.loads(line)
                        before = connection.execute(
                            "SELECT count(*) FROM raw.events"
                        ).fetchone()[0]
                        connection.execute(
                            """
                            INSERT OR IGNORE INTO raw.events
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            [
                                envelope["event_id"],
                                envelope["event_type"],
                                envelope["occurred_at"],
                                json.dumps(envelope["payload"]),
                                str(source.relative_to(self.root)),
                                datetime.now(timezone.utc).isoformat(),
                            ],
                        )
                        after = connection.execute(
                            "SELECT count(*) FROM raw.events"
                        ).fetchone()[0]
                        inserted += after - before
            return inserted
        finally:
            if owns_connection:
                connection.close()

    def transform(self, connection=None) -> None:
        owns_connection = connection is None
        connection = connection or self._connect()
        try:
            sql_path = PROJECT_ROOT / "warehouse" / "sql" / "transform.sql"
            connection.execute(sql_path.read_text(encoding="utf-8"))
        finally:
            if owns_connection:
                connection.close()

    def quality_checks(self, connection=None) -> list[dict]:
        owns_connection = connection is None
        connection = connection or self._connect()
        checks = [
            (
                "unique_event_ids",
                "SELECT count(*) - count(DISTINCT event_id) FROM raw.events",
            ),
            (
                "valid_event_types",
                """SELECT count(*) FROM raw.events
                   WHERE event_type NOT IN
                   ('pipeline_run', 'interview_metric', 'retrieval_evaluation')""",
            ),
            (
                "nonnegative_pipeline_duration",
                "SELECT count(*) FROM staging.pipeline_runs WHERE duration_ms < 0",
            ),
            (
                "bounded_interview_scores",
                "SELECT count(*) FROM staging.interview_metrics WHERE score NOT BETWEEN 0 AND 100",
            ),
            (
                "bounded_retrieval_metrics",
                """SELECT count(*) FROM staging.retrieval_evaluations
                   WHERE hit_rate NOT BETWEEN 0 AND 1
                      OR mean_reciprocal_rank NOT BETWEEN 0 AND 1""",
            ),
        ]
        try:
            results = []
            for name, query in checks:
                failed_rows = connection.execute(query).fetchone()[0]
                results.append(
                    {
                        "check": name,
                        "failed_rows": failed_rows,
                        "status": "pass" if failed_rows == 0 else "fail",
                    }
                )
            return results
        finally:
            if owns_connection:
                connection.close()

    def export_parquet(self, connection=None) -> list[Path]:
        owns_connection = connection is None
        connection = connection or self._connect()
        exports = []
        try:
            for table in (
                "pipeline_daily",
                "interview_progress",
                "retrieval_quality",
            ):
                dates = connection.execute(
                    f"SELECT DISTINCT event_date FROM marts.{table} ORDER BY event_date"
                ).fetchall()
                for (event_date,) in dates:
                    date_text = event_date.isoformat()
                    folder = self.parquet_dir / table / f"event_date={date_text}"
                    folder.mkdir(parents=True, exist_ok=True)
                    destination = folder / "data.parquet"
                    safe_path = str(destination).replace("'", "''")
                    connection.execute(
                        f"""COPY (
                            SELECT * EXCLUDE (event_date)
                            FROM marts.{table}
                            WHERE event_date = DATE '{date_text}'
                        ) TO '{safe_path}' (FORMAT PARQUET)"""
                    )
                    exports.append(destination)
            return exports
        finally:
            if owns_connection:
                connection.close()

    def run(self) -> dict:
        connection = self._connect()
        try:
            inserted = self.ingest(connection)
            self.transform(connection)
            checks = self.quality_checks(connection)
            exports = self.export_parquet(connection)
            if any(check["status"] == "fail" for check in checks):
                raise RuntimeError("Analytics data-quality checks failed")
            return {
                "inserted_events": inserted,
                "total_events": connection.execute(
                    "SELECT count(*) FROM raw.events"
                ).fetchone()[0],
                "quality_checks": checks,
                "parquet_files": [str(path) for path in exports],
                "database_path": str(self.database_path),
            }
        finally:
            connection.close()

    def query(self, sql: str) -> list[dict]:
        connection = self._connect()
        try:
            cursor = connection.execute(sql)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            connection.close()

    def append_many(self, records: Iterable[BaseModel]) -> list[Path]:
        return [self.append(record) for record in records]
