# DataPrep AI V2 Roadmap

## Product direction

DataPrep AI V2 will be a career intelligence platform for data engineers. It will turn resumes and job descriptions into structured skill data, evidence-based gap analysis, personalized interview preparation, and job-market analytics.

The project should demonstrate two things clearly:

1. A useful product for data engineering candidates.
2. Production-minded data engineering: repeatable ingestion, persistent data, quality checks, observability, analytics, testing, and controlled cloud costs.

## V2 minimum viable product

A user can:

- Upload a resume and one or more job descriptions.
- Review extracted skills and the source text supporting each skill.
- Compare resume skills with job requirements in a visual matrix.
- Ask grounded questions and inspect citations.
- Generate a prioritized study plan and role-specific interview questions.
- See basic pipeline metrics such as documents processed, chunks created, failures, latency, and estimated API usage.

## Scope rules

- Build a reliable local version before adding Google Cloud services.
- Keep Streamlit for the first V2 release.
- Do not scrape job sites without an authorized API or explicit permission.
- Do not add a service solely to make the architecture look larger.
- Keep every public AI operation rate-limited and budget-controlled.
- Never store an uploaded resume longer than the UI tells the user.

## Delivery phases

### Phase 0: Preserve and verify the class project

- Create a Git checkpoint for the completed class-project version.
- Pin a supported Python version and dependency versions.
- Create a local virtual environment.
- Confirm the current app starts.
- Add a small smoke-test suite.

Definition of done: a new developer can clone the repository, install it, and start the existing application by following the README.

### Phase 1: Reliable RAG foundation

- Assign stable IDs to documents and chunks.
- Cache or persist embeddings instead of recreating them for every question.
- Store metadata and page or section references.
- Add document deduplication.
- Add retrieval configuration and normalized cosine similarity.
- Add chat history and clearer failure states.
- Create a small retrieval evaluation set.

Definition of done: repeated questions do not re-embed unchanged documents, citations identify their source, and automated retrieval checks can be run locally.

### Phase 2: Career intelligence features

- Parse resumes and job descriptions into validated structured records.
- Create a controlled data-engineering skill taxonomy.
- Show an evidence-based resume-to-job skill matrix.
- Generate a prioritized learning plan.
- Add technical, SQL, system-design, and behavioral interview modes.
- Save interview scores and progress locally.

Definition of done: a user can upload one resume and two job descriptions, compare them, and complete a role-specific interview session.

### Phase 3: Data engineering and analytics layer

- Define raw, cleaned, and analytical datasets.
- Add BigQuery tables for documents, skills, matches, pipeline runs, and evaluations.
- Add SQL or dbt transformations and tests.
- Add pipeline-run, data-quality, latency, and estimated-cost dashboards.
- Add a curated, legally usable sample job dataset.

Definition of done: the application includes a reproducible analytical pipeline and a visible data-quality/observability story.

### Phase 4: Cloud and portfolio release

- Add Docker packaging.
- Add automated tests in GitHub Actions.
- Deploy a stable public demo to Streamlit Community Cloud or Cloud Run.
- Add rate limits, budget alerts, privacy messaging, and a sample/demo mode.
- Rewrite the README as a technical case study.
- Add screenshots, an architecture diagram, evaluation results, and a short demo script.

Definition of done: a reviewer can understand the business value, architecture, engineering decisions, measured results, and limitations in less than five minutes.

## Suggested daily sessions

Each session should produce one small, testable result.

| Day | Outcome |
|---:|---|
| 1 | Preserve the class project, document V2 scope, and verify the runtime |
| 2 | Create the Python environment, pin dependencies, and add smoke tests |
| 3 | Refactor app state and stop unnecessary embedding recomputation |
| 4 | Add persistent document/chunk metadata and deduplication |
| 5 | Improve citations, retrieval scoring, and retrieval tests |
| 6 | Define the skill taxonomy and structured extraction schemas |
| 7 | Implement resume and job-description extraction |
| 8 | Build the evidence-based skill comparison view |
| 9 | Add the learning plan and interview-question generator |
| 10 | Add interview scoring and progress history |
| 11 | Design the analytical data model and pipeline-run records |
| 12 | Add BigQuery integration and transformations |
| 13 | Add data-quality, latency, and cost dashboards |
| 14 | Polish visual design and accessibility |
| 15 | Add Docker, CI, deployment documentation, and the public release |

The schedule is a guide, not a deadline. A day can be repeated when a feature needs more testing.

## Day 1 checklist

- [x] Inspect the repository and existing architecture.
- [x] Check tracked files for obvious API secrets.
- [x] Confirm that earlier Git recovery points exist.
- [x] Write the V2 product scope and phased roadmap.
- [x] Create a named Git checkpoint for the completed class project (`f39bf22`).
- [x] Install or select a supported Python runtime.
- [x] Start the current Streamlit app locally and record baseline behavior.

## Initial success measures

These targets should be refined after the baseline evaluation exists:

- Unchanged documents are embedded only once.
- Every grounded answer displays usable source evidence.
- Skill extraction produces validated structured output.
- The public demo has a hard API usage limit.
- Core parsing, retrieval, and scoring logic has automated tests.
- The repository contains a reproducible setup and deployment path.

## Working log

### 2026-07-31

- Audited the existing Streamlit, ingestion, retrieval, RAG, and web-search code.
- Found no obvious tracked OpenAI or Google API key pattern.
- Found three earlier commits, so the project has historical recovery points.
- Found that the completed class-project changes are not yet committed.
- Found a Windows Python launcher but no installed Python runtime available through it.
- Located Anaconda Python 3.13 and created an isolated `.venv` for the project.
- Reinstalled compiled dependencies with Python 3.13-compatible wheels.
- Confirmed all direct dependencies import and the Streamlit health endpoint returns HTTP 200.
- Selected the Career Intelligence Platform direction for V2.
