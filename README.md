# DataPrep AI

**Data engineering interview preparation with evidence from your own documents.**

[Open the live app](https://jobprep-oz.streamlit.app/)

![DataPrep AI landing page](assets/dataprep-career-hero.webp)

## What it does

DataPrep AI helps data engineering candidates prepare for job applications and interviews.

- Ask questions about a résumé, job posting, or study notes and review the supporting passages.
- Compare a résumé with a job and see which skills are supported by evidence.
- Find important skill gaps and generate a focused four-week learning plan.
- Practice role-specific interview questions and receive structured feedback.
- Ask current questions about data engineering tools, skills, and hiring trends.
- Review application speed, retrieval quality, and privacy-safe operational metrics.

The application accepts Word, PDF, TXT, and Markdown files.

## How it works

The document assistant uses retrieval-augmented generation (RAG):

1. Files are read, cleaned, checked for duplicates, and divided into smaller sections.
2. OpenAI embeddings convert the sections and the user's question into numeric representations.
3. The most relevant sections are selected with cosine similarity.
4. The language model answers from that evidence and displays the sources.

The résumé and job comparison uses structured AI extraction followed by deterministic Python rules. Required skills receive more weight than preferred skills, and a match must include résumé evidence.

## Technology

- Python and Streamlit
- OpenAI Responses API, embeddings, and web search
- Pydantic and NumPy
- PyPDF and python-docx
- DuckDB, SQL, JSONL, and Parquet

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Add your OpenAI API key to `.env` before starting the application:

```text
OPENAI_API_KEY=your-key-here
```

Never commit `.env` or an API key.

## Local analytics

The public app keeps operational metrics only for the current browser session. Local mode can write privacy-safe events to JSONL, load them into DuckDB, build SQL analytical tables, and export partitioned Parquet files.

To enable it, add this to `.env`:

```text
DATAPREP_ANALYTICS_MODE=local
DATAPREP_ANALYTICS_DIR=data/analytics
```

Résumé text, uploaded documents, questions, answers, names, and API keys are excluded from analytics events.

## AI-assisted development

AI coding assistants were used for brainstorming, initial code generation, debugging, and interface iteration. I reviewed the changes and remained responsible for the requirements, architecture, testing, and final implementation decisions.
