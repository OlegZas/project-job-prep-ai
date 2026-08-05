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

Future BigQuery records are deliberately operational and aggregate. They contain
counts, timings, model names, statuses, and rubric metrics—not source text, résumé
content, file names, questions, user answers, or secrets.

## Analytics data model

| Record | Grain | Purpose |
|---|---|---|
| `pipeline_runs` | One application operation | Reliability, latency, cache efficiency, model usage |
| `retrieval_evaluations` | One benchmark execution | Retrieval quality and performance regression tracking |
| `interview_metrics` | One scored attempt | Aggregate learning progress by role family and question type |

Python contracts are in `src/analytics_models.py`; partitioned and clustered BigQuery
DDL is in `warehouse/bigquery_schema.sql`.

## Deliberate limitations

- The local embedding cache is session-scoped, not shared across application replicas.
- Profile extraction and qualitative feedback require an external model and should be
  reviewed by the user.
- Skill matching checks normalized skill evidence; it is not a hiring recommendation.
- The benchmark is small and synthetic. More ambiguous, adversarial, and user-tested
  cases are needed before making broad quality claims.
- Authentication, public rate limits, warehouse writes, and cloud monitoring are not
  enabled yet.
