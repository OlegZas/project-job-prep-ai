# DataPrep AI architecture

## Design goals

The application is intentionally small enough to understand in one review while
demonstrating production-minded boundaries: ingestion, data quality, retrieval,
validated AI output, deterministic business rules, evaluation, observability, and
privacy-aware analytics.

## Main flows

### Grounded document answers

1. `DocumentProcessor` reads supported files and isolates malformed inputs.
2. Clean content receives stable SHA-256 document and chunk identifiers.
3. Duplicate documents are recorded but not embedded twice.
4. `DocumentStore` caches embeddings by model and content hash.
5. Search uses normalized cosine similarity, a minimum score, and ranked citations.
6. `RAGPipeline` receives only the selected chunks and instructs the model to cite them.

### Career intelligence

1. OpenAI structured outputs populate Pydantic candidate and job schemas.
2. Skill aliases are normalized to a controlled data engineering taxonomy.
3. Matching is deterministic and explainable; the language model does not invent the
   score.
4. The selected job and gaps become inputs to a structured learning plan.
5. Interview feedback uses four bounded rubric values. The application recomputes the
   overall score as their sum.

## State and privacy

Streamlit session state holds indexes, extracted profiles, plans, and interview
attempts. This supports a useful demo without silently building a résumé database.
Refreshing or clearing the session removes that transient state.

Analytics records are deliberately operational and aggregate. They contain
counts, timings, model names, statuses, and rubric metrics—not source text, résumé
content, file names, questions, user answers, or secrets.

The public Streamlit deployment holds events in session state and lets a visitor
download them. Local mode appends the same event envelopes to date-partitioned JSONL.
An incremental pipeline inserts unseen event IDs into DuckDB, applies SQL staging and
mart transformations, runs quality checks, and exports date-partitioned Parquet.

## Analytics data model

| Record | Grain | Purpose |
|---|---|---|
| `raw.events` | One immutable event envelope | Incremental ingestion and lineage back to a source JSONL file |
| `staging.pipeline_runs` | One application operation | Typed reliability, latency, cache efficiency, and model usage |
| `staging.retrieval_evaluations` | One benchmark execution | Typed retrieval quality and performance results |
| `staging.interview_metrics` | One scored attempt | Typed rubric metrics without questions or answers |
| `marts.pipeline_daily` | One day and operation | Operational dashboard metrics |
| `marts.interview_progress` | One day, role family, question type, and difficulty | Aggregate practice progress |
| `marts.retrieval_quality` | One benchmark run | Retrieval quality and cache speedup |

Python contracts are in `src/analytics_models.py`, orchestration is in
`src/analytics_pipeline.py`, and transformations are in `warehouse/sql/transform.sql`.
The earlier BigQuery DDL remains as an optional future migration path.

## Deliberate limitations

- The local embedding cache is session-scoped, not shared across application replicas.
- Profile extraction and qualitative feedback require an external model and should be
  reviewed by the user.
- Skill matching checks normalized skill evidence; it is not a hiring recommendation.
- The benchmark is small and synthetic. More ambiguous, adversarial, and user-tested
  cases are needed before making broad quality claims.
- Streamlit Community Cloud does not provide durable local disk, so combined historical
  analytics are generated locally rather than collected automatically from visitors.
- Docker is validated by GitHub Actions; a local Docker engine is still required to run
  the container on a developer machine.
