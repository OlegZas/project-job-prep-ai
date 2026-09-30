# DataPrep AI demo script

Target length: about five minutes. Use synthetic or redacted documents.

## 0:00-1:02 - What I built, stack, and purpose

Show the redesigned landing page, then the README and repository folders.

> Hi, this is DataPrep AI. I built it to help data engineering candidates turn
> resumes, job postings, and study notes into focused interview preparation.

Mention Python, Streamlit, the OpenAI Responses API, Pydantic, NumPy, PyPDF,
python-docx, DuckDB, SQL, Parquet, Pytest, GitHub Actions, and Docker. Explain that an
AI coding assistant helped with brainstorming, code generation, debugging, tests, and
UI iteration, while you reviewed the work and verified it with automated tests.

Point across the five tabs and give one sentence about each.

## 1:02-2:00 - Upload documents and ask questions

Open **Ask My Documents** and upload safe Word, PDF, or TXT files. Ask:

> Based on my resume, what interview topics should I prepare?

Show the answer and supporting passages. Explain that files are cleaned, hashed,
deduplicated, divided into sections, and embedded. The query embedding is compared
with the sections using cosine similarity, top results are retrieved, and the model
answers from cited context.

Briefly show `read_docx()` in `src/file_loader.py`, `search()` in
`src/document_store.py`, and `answer_question()` in `src/rag_pipeline.py`.

## 2:00-3:05 - Resume and job match plus learning plan

Open **Resume & Job Match** and compare the resume with the target job. Show the match
score, required and preferred coverage, one supported skill, and one skill not shown.

Explain that the API returns validated Pydantic profiles with atomic skills. Python
normalizes aliases and matches exact tools, named alternatives, and broader
capabilities to resume evidence. Required skills count twice as much as preferred
skills, and Python calculates the final score.

Show `extract_job()` in `src/career_intelligence.py`, `normalize_skill_name()` in
`src/skill_taxonomy.py`, and `build_skill_match()` in `src/matching.py`.

Generate the four-week plan. Open two weeks and explain that each week is intentionally
limited to a short focus, one practical task, and no more than three questions.

## 3:05-4:00 - Practice Interview and Current Trends

Open **Practice Interview**. Explain that the question is personalized from the target
job responsibilities, demonstrated candidate skills, selected topic, and difficulty.
Show the compact criteria and scored feedback across accuracy, clarity, tradeoff
reasoning, and production readiness.

Open **Current Trends** and ask:

> How is AI affecting data engineering careers and job searches?

Explain that this tool uses web search for information that may change over time and
requests a concise, practical answer.

## 4:00-5:22 - Project Metrics and closing

Open **Project Metrics**. Explain that this is an engineering-health dashboard, not a
score for the user.

- Actions this session: recorded searches, comparisons, generations, and scoring runs.
- Success rate: the percentage of recorded operations that completed successfully.
- Average response time: average duration of those operations.
- Reused work: how much cached document-search work was reused.
- Interview score: the quality of the submitted practice answer, not app health.
- Useful source found: how often the expected source appeared in the retrieval test.
- Average source rank: closer to 1 means the expected source appeared nearer the top.
- First run: a cold run that created embeddings.
- Cached speedup: how much faster the repeated run was with existing embeddings.

Expand the data-flow section. Explain that the public app keeps metrics only in the
browser session. Local mode writes privacy-safe operational events to partitioned
JSONL, incrementally loads DuckDB, builds SQL marts, runs quality checks, and exports
partitioned Parquet. Resume text, names, questions, answers, and API keys are excluded.

Finish on the landing page:

> DataPrep AI combines a useful career product with structured AI, deterministic
> scoring, cited retrieval, automated tests, and a practical data-engineering pipeline.
> The live application and source code are linked with this demo. Thanks for watching.
