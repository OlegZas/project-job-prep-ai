# DataPrep AI demo script

Target length: about two minutes.

## 0:00–0:15 — Problem

“Data engineering candidates prepare from résumés, job descriptions, technical notes,
and changing tool requirements. I built DataPrep AI to turn those sources into
evidence-based preparation.”

## 0:15–0:45 — Career Match

Open **Career Match**, keep the synthetic documents selected, and analyze them. Show
the weighted score, required and preferred skill coverage, evidence table, and gaps.
Explain that AI extracts validated records while deterministic code calculates the
score.

## 0:45–1:05 — Learning and interview practice

Show the four-week plan. Open **Interview Lab**, select a question type, and show a
completed scoring example. Point out the four 25-point rubric dimensions.

## 1:05–1:25 — Cited retrieval

Open **Document Q&A** and ask a question about Kafka or BigQuery. Show the ranked
sources and citations. Mention content hashes, deduplication, cosine similarity,
thresholds, and session embedding reuse.

## 1:25–1:50 — Data engineering

Open **Engineering Metrics**. Show Hit@4, MRR, cold and warm latency, and session
operations. Then show the repository architecture diagram. Explain the path from
partitioned JSONL through incremental DuckDB staging and SQL marts to partitioned
Parquet and the dashboard.

## 1:50–2:00 — Engineering quality

“The project has 46 automated tests. GitHub Actions validates Python behavior, builds
the analytics pipeline, compiles the source, and builds the Docker image. The public
app keeps user data session-scoped, while local mode provides persistent analytics.”
