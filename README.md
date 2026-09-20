# DataPrep AI

[Live Streamlit demo](https://olegzas-pro.streamlit.app/)

DataPrep AI is a data engineering career intelligence platform. It combines
retrieval-augmented generation (RAG), validated AI extraction, deterministic skill
matching, and interview coaching in one Python web application.

The project began as a class RAG assignment and is being developed into a master's
application and data engineering portfolio project. Its product goal is simple: help
data engineers turn their own résumé, target roles, and study material into a focused
preparation plan.

## What it does

### Document Q&A

- Reads TXT, Markdown, and PDF documents.
- Cleans, chunks, hashes, and deduplicates content.
- Reuses embeddings inside the private browser session.
- Ranks chunks with normalized cosine similarity and a configurable threshold.
- Produces answers with visible `[S1]`, `[S2]` source citations and chat history.
- Reports document status, cache behavior, chunk counts, and latency.

### Career Match

- Extracts schema-validated candidate and job profiles with the OpenAI Responses API.
- Normalizes skills through a controlled data engineering taxonomy.
- Calculates a transparent match score: required skills receive weight 2 and
  preferred skills receive weight 1.
- Shows résumé and job evidence for every match or gap.
- Generates a prioritized four-week learning plan.
- Includes synthetic sample documents so the public demo does not require personal data.

### Interview Lab

- Creates SQL, Python, data modeling, system design, and behavioral questions.
- Targets the selected role and supports three difficulty levels.
- Scores answers on technical accuracy, clarity, tradeoff reasoning, and production
  readiness using a deterministic 100-point total.
- Keeps progress in the browser session and exports it as JSON.

### Market Knowledge

- Uses OpenAI web search for current data engineering tools, skills, and trends.

### Engineering Metrics

- Captures privacy-safe application operations in the active browser session.
- Supports persistent local ingestion into raw date-partitioned JSONL.
- Uses DuckDB SQL staging views and analytical marts.
- Exports date-partitioned Parquet datasets for pipeline, interview, and retrieval metrics.
- Runs data-quality checks for uniqueness, valid event types, timing, and score bounds.
- Displays live session metrics and the recorded retrieval benchmark.

## Architecture

```mermaid
flowchart LR
    A["Résumé, job descriptions, notes"] --> B["Parse, clean, hash, deduplicate"]
    B --> C["Chunk and embed"]
    C --> D["Cosine search + threshold"]
    D --> E["Cited RAG answers"]
    B --> F["Validated profile extraction"]
    F --> G["Taxonomy normalization"]
    G --> H["Deterministic skill match"]
    H --> I["Learning plan + Interview Lab"]
    E --> J["Privacy-safe operational events"]
    I --> J
    J --> K["Raw partitioned JSONL"]
    K --> L["DuckDB staging + SQL marts"]
    L --> M["Partitioned Parquet + metrics dashboard"]
```

See [the architecture notes](docs/ARCHITECTURE.md) and
[the V2 roadmap](docs/V2_ROADMAP.md) for design decisions and remaining work.

## Tech stack

- Python 3.13 and Streamlit
- OpenAI Responses API, structured outputs, embeddings, and web search
- Pydantic data contracts and NumPy retrieval
- PyPDF document ingestion
- DuckDB, SQL, JSONL, and Parquet analytics
- Pytest and Streamlit AppTest
- GitHub Actions
- Docker

## Local setup

From PowerShell in the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Add your API key to `.env`; never commit that file. The model defaults in
`.env.example` can be changed without editing Python.

Run the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Expected result: five tabs named **Document Q&A**, **Career Match**,
**Interview Lab**, **Market Knowledge**, and **Engineering Metrics**. In Career Match,
leave the synthetic sample option selected and click **Analyze career match** for the
quickest demo.

## Local analytics pipeline

The public Streamlit deployment uses session analytics because its local filesystem is
temporary. To enable persistent analytics on your computer, set this in `.env`:

```text
DATAPREP_ANALYTICS_MODE=local
DATAPREP_ANALYTICS_DIR=data/analytics
```

Restart the app, use its features, then open **Engineering Metrics** and click
**Run incremental DuckDB pipeline**. The application creates:

```text
data/analytics/
├── raw/events/event_date=YYYY-MM-DD/events.jsonl
├── dataprep.duckdb
└── parquet/
    ├── pipeline_daily/event_date=YYYY-MM-DD/data.parquet
    ├── interview_progress/event_date=YYYY-MM-DD/data.parquet
    └── retrieval_quality/event_date=YYYY-MM-DD/data.parquet
```

Build a complete synthetic pipeline without calling OpenAI:

```powershell
.\.venv\Scripts\python.exe scripts\build_analytics_demo.py
```

See [the local analytics guide](docs/LOCAL_ANALYTICS.md) for tables, quality checks,
queries, and privacy boundaries.

## Docker

Build and run the same application in a container:

```powershell
docker build -t dataprep-ai .
docker run --rm -p 8501:8501 --env-file .env dataprep-ai
```

Open `http://localhost:8501`. The container defaults to session analytics. Mount a
local directory and set `DATAPREP_ANALYTICS_MODE=local` if you want persistent
container output.

## Quality checks

Run the offline automated suite (no API spending):

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run the retrieval benchmark (small embeddings API cost):

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --top-k 4 --min-score 0.25 --output evals\retrieval_quality.json
```

The current ten-case benchmark reports `Hit@4 = 1.00` and `MRR = 0.883`.
Its measured warm pass took 0.048 seconds with zero API calls, compared with
16.096 seconds for the cold pass—a 335× speedup in that run. GitHub Actions runs
the offline test suite, analytics pipeline, source compilation, and Docker build for
every push and pull request.

## Privacy and cost controls

- Uploaded content, embeddings, extracted profiles, and interview history remain in
  the current Streamlit browser session.
- The user can clear the document index and download interview history.
- Analytics contracts intentionally exclude document text, file names, answers, and
  API keys.
- Public analytics are held in the current Streamlit session. Persistent DuckDB and
  Parquet output is opt-in for local runs.
- `.env`, Streamlit secrets, caches, and virtual environments are ignored by Git.
- OpenAI requests have a configurable 60-second timeout and one retry so failures do
  not leave the interactive app waiting indefinitely.
- Public OpenAI usage should be monitored before broadly sharing the interactive URL.

## Example demo flow

1. Open Career Match and analyze the synthetic résumé and job.
2. Explain the weighted match, evidence table, and missing skills.
3. Generate the four-week plan.
4. Open Interview Lab, answer one targeted question, and show rubric feedback.
5. Open Document Q&A and ask, “How does BigQuery partitioning improve performance?”
6. Open Engineering Metrics and show the retrieval benchmark and session operations.
7. Mention the DuckDB pipeline, SQL marts, partitioned Parquet, quality checks,
   container build, and automated CI.

The complete recording outline is in [the demo script](docs/DEMO_SCRIPT.md).
