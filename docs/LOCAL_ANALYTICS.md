# Local analytics pipeline

## Purpose

The local pipeline demonstrates a complete data engineering path without a cloud
account. It uses immutable JSONL events as the raw layer, DuckDB for incremental
ingestion and SQL transformations, and Parquet for portable analytical outputs.

The public Streamlit app uses session mode. This avoids treating temporary hosted disk
as durable storage and prevents one visitor from seeing another visitor's activity.

## Run it

Generate a synthetic dataset without OpenAI calls:

```powershell
.\.venv\Scripts\python.exe scripts\build_analytics_demo.py
```

Or enable persistent capture while running the app locally:

```text
DATAPREP_ANALYTICS_MODE=local
DATAPREP_ANALYTICS_DIR=data/analytics
```

After using the app, open **Engineering Metrics** and click **Run incremental DuckDB
pipeline**.

## Layers

| Layer | Location | Responsibility |
|---|---|---|
| Raw | `raw/events/event_date=*/events.jsonl` | Immutable event envelopes partitioned by event date |
| Warehouse | `dataprep.duckdb` | Incremental deduplication, typed staging views, and marts |
| Serving | `parquet/*/event_date=*/data.parquet` | Portable, date-partitioned analytical output |
| Presentation | Streamlit Engineering Metrics | Session operations, interview progress, and retrieval quality |

Incremental ingestion uses `event_id` as the primary key. Re-running the pipeline reads
the source files again but inserts only unseen events, making the run idempotent.

## Useful DuckDB queries

Start DuckDB with the generated database and run:

```sql
SELECT * FROM marts.pipeline_daily ORDER BY event_date DESC, operation;

SELECT * FROM marts.interview_progress
ORDER BY event_date DESC, question_type, difficulty;

SELECT * FROM marts.retrieval_quality ORDER BY event_date DESC;
```

## Data-quality checks

Every run checks:

- Event IDs are unique.
- Event types are recognized.
- Pipeline durations are nonnegative.
- Interview scores remain between 0 and 100.
- Hit rate and mean reciprocal rank remain between 0 and 1.

A failing check stops the pipeline before a successful result is reported.

## Privacy boundary

The analytics layer permits timestamps, operation names, status, latency, counts,
cache metrics, model names, coarse role families, question types, difficulty, and
rubric scores. It excludes names, filenames, résumé content, uploaded text, questions,
answers, generated responses, and secrets.
