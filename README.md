# Streamlit link : https://olegzas-pro.streamlit.app/

# DataPrep AI

DataPrep AI is a Python web app that helps users prepare for data engineering interviews.

> V2 is being developed as a Data Engineering Career Intelligence Platform. See the [V2 roadmap](docs/V2_ROADMAP.md).

The app lets users upload interview notes, resumes, job descriptions, SQL notes, Kafka notes, or cloud study guides. It reads the documents, splits them into smaller chunks, creates embeddings, searches for the most useful chunks, and sends that context to OpenAI to generate an interview-focused answer.

## Business Use Case

Data engineering candidates often study from many different files and notes. This app helps organize that information in one place. A user can ask questions and get answers based on their own documents.

The target user is someone preparing for a data engineering interview.

## Main Features

* Upload TXT, MD, or PDF files
* Use sample interview notes
* Ask questions about uploaded documents
* Retrieve the most relevant document chunks
* Generate answers using OpenAI
* Show references used for the answer
* Ask live market knowledge questions about data engineering topics
* Reuse unchanged embeddings within a private browser session
* Assign stable content-based IDs to documents and chunks
* Display indexing and retrieval timing
* Catalog document metadata and per-file processing status
* Skip duplicate content before chunking or embedding
* Isolate malformed files so one failure does not stop the corpus

## Tech Stack

* Python
* Streamlit
* OpenAI API
* OpenAI embeddings
* NumPy
* PyPDF
* python-dotenv
* GitHub
* Streamlit Community Cloud

## Local Setup

The verified local runtime is Python 3.13.

From PowerShell in the repository root, create the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

If `python` is not on `PATH`, replace it with the full path to a Python 3.13 executable.

Create a local `.env` file containing your API key. Do not commit this file:

```text
OPENAI_API_KEY=your-key-here
```

Start the application:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Automated Checks

Run all unit and application smoke tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The smoke test renders the Streamlit page without calling OpenAI. Tests that use the API are kept separate so routine checks do not spend API credit.

## Retrieval Evaluation

The repository includes a small benchmark that checks whether each question retrieves its expected source document. It reports hit rate at `k` and mean reciprocal rank.

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --top-k 3
```

To save a baseline report:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --top-k 3 --output evals\baseline.json
```

This command uses the OpenAI embeddings API and therefore has a small API cost. Routine unit tests do not run it.

The initial [retrieval baseline](evals/baseline.json) contains six document-level cases. All six expected documents ranked first (`Hit@3 = 1.0`, `MRR = 1.0`), and the uncached run took 19.081 seconds for 45 chunks. Future benchmarks will add harder chunk-level and ambiguous questions.

The Day 3 [cached retrieval baseline](evals/cached_baseline.json) runs the same corpus and questions twice in one process:

* Cold pass: 18.512 seconds, 51 embedding API calls
* Warm pass: 0.078 seconds, 51 cache hits, 0 embedding API calls
* Measured warm-cache speedup: 237.33x

## Session Cache and Privacy

Document metadata, document-derived embeddings, and question embeddings are retained only in the current Streamlit browser session. They are not written to a shared database or committed to Git. This allows repeated questions to reuse unchanged work without retaining resume-derived data across users.

Changing an uploaded document changes its content ID and refreshes the affected index. The **Clear session document index** button immediately removes the in-session index and cached embeddings.

The document catalog uses content hashes to identify duplicates even when two files have different names. Duplicate files remain visible in the catalog for transparency but do not create repeated chunks or embedding API calls.


## Example Questions

```text
What is a Kafka consumer group?
What are SQL window functions?
What is BigQuery partitioning?
Based on my notes, what interview topics should I study?
What skills are important for data engineers?
```

## Future Improvements

In the future, I would like to add saved chat history, better document storage, BigQuery logging, Docker, Cloud Run deployment, and interview quiz scoring.
