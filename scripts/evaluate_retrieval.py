import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.document_store import DocumentStore  # noqa: E402
from src.file_loader import DocumentProcessor  # noqa: E402


DEFAULT_CASES = PROJECT_ROOT / "evals" / "retrieval_cases.json"
DEFAULT_DOCS = PROJECT_ROOT / "docs"


def load_cases(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        cases = json.load(file)

    if not cases:
        raise ValueError("The evaluation file does not contain any cases")

    return cases


def score_cases(
    store: DocumentStore, cases: list[dict], top_k: int, min_score: float
) -> dict:
    results = []
    reciprocal_rank_total = 0.0

    for case in cases:
        matches = store.search(
            case["question"], top_k=top_k, min_score=min_score
        )
        ranked_files = [match["file_name"] for match in matches]
        expected_terms = [term.casefold() for term in case.get("expected_terms", [])]

        rank = next(
            (
                index
                for index, match in enumerate(matches, start=1)
                if match["file_name"] == case["expected_file"]
                and all(term in match["text"].casefold() for term in expected_terms)
            ),
            None,
        )
        reciprocal_rank = 1.0 / rank if rank else 0.0

        reciprocal_rank_total += reciprocal_rank
        results.append(
            {
                "id": case["id"],
                "expected_file": case["expected_file"],
                "rank": rank,
                "top_files": ranked_files,
                "expected_terms": case.get("expected_terms", []),
                "hit": rank is not None,
            }
        )

    case_count = len(results)
    return {
        "case_count": case_count,
        "hit_rate": sum(result["hit"] for result in results) / case_count,
        "mean_reciprocal_rank": reciprocal_rank_total / case_count,
        "results": results,
    }


def run_pass(
    store: DocumentStore,
    chunks: list[dict],
    cases: list[dict],
    top_k: int,
    min_score: float,
) -> dict:
    store.reset_cache_stats()
    started_at = time.perf_counter()
    store.add_chunks(chunks)
    metrics = score_cases(store, cases, top_k, min_score)
    metrics["duration_seconds"] = round(time.perf_counter() - started_at, 3)
    metrics["embedding_cache"] = store.get_cache_stats()
    return metrics


def evaluate(cases: list[dict], top_k: int, min_score: float) -> dict:
    processor = DocumentProcessor(chunk_size=180, overlap=30)
    files = processor.load_local_files(DEFAULT_DOCS, allowed_extensions={".txt"})
    chunks = processor.process_files(files)
    store = DocumentStore()

    cold_run = run_pass(store, chunks, cases, top_k, min_score)
    warm_run = run_pass(store, chunks, cases, top_k, min_score)
    warm_seconds = warm_run["duration_seconds"]
    speedup = cold_run["duration_seconds"] / warm_seconds if warm_seconds else None

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": store.embedding_model,
        "document_count": len(files),
        "chunk_count": len(chunks),
        "chunk_size": processor.chunk_size,
        "chunk_overlap": processor.overlap,
        "top_k": top_k,
        "min_score": min_score,
        "cold_run": cold_run,
        "warm_run": warm_run,
        "warm_speedup": round(speedup, 2) if speedup is not None else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure whether document retrieval finds the expected source file."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.25)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()

    if args.top_k <= 0:
        raise ValueError("--top-k must be greater than zero")

    if not 0 <= args.min_score <= 1:
        raise ValueError("--min-score must be between zero and one")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to run the retrieval evaluation")

    report = evaluate(load_cases(args.cases), args.top_k, args.min_score)
    output = json.dumps(report, indent=2)
    print(output)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
