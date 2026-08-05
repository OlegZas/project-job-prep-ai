import hashlib
import os

import numpy as np
from src.openai_client import create_openai_client


class DocumentStore:
    def __init__(self, client=None, embedding_cache=None):
        self.client = client or create_openai_client()
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_cache = embedding_cache if embedding_cache is not None else {}
        self.items = []
        self.reset_cache_stats()

    @staticmethod
    def create_corpus_id(chunks):
        """Return a stable identifier for a set of document chunks."""
        chunk_ids = sorted(chunk["chunk_id"] for chunk in chunks)
        joined_ids = ":".join(chunk_ids)
        return hashlib.sha256(joined_ids.encode("utf-8")).hexdigest()

    def reset_cache_stats(self):
        self.cache_hits = 0
        self.cache_misses = 0

    def get_cache_stats(self):
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "cached_embeddings": len(self.embedding_cache),
        }

    def _embedding_cache_key(self, text):
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.embedding_model}:{content_hash}"

    def create_embedding(self, text):
        cache_key = self._embedding_cache_key(text)

        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[cache_key]

        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )

        embedding = response.data[0].embedding
        self.embedding_cache[cache_key] = embedding
        self.cache_misses += 1
        return embedding

    def add_chunks(self, chunks):
        self.items = []

        for chunk in chunks:
            embedding = self.create_embedding(chunk["text"])

            self.items.append({
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "file_name": chunk["file_name"],
                "chunk_number": chunk["chunk_number"],
                "text": chunk["text"],
                "embedding": embedding
            })

    def search(self, question, top_k=3, min_score=None):
        if not self.items:
            return []

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        if min_score is not None and not -1.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between -1.0 and 1.0")

        question_embedding = np.asarray(self.create_embedding(question), dtype=float)
        question_norm = np.linalg.norm(question_embedding)

        results = []

        for item in self.items:
            item_embedding = np.asarray(item["embedding"], dtype=float)
            denominator = question_norm * np.linalg.norm(item_embedding)
            score = (
                float(np.dot(question_embedding, item_embedding) / denominator)
                if denominator
                else 0.0
            )

            if min_score is not None and score < min_score:
                continue

            results.append({
                "document_id": item["document_id"],
                "chunk_id": item["chunk_id"],
                "file_name": item["file_name"],
                "chunk_number": item["chunk_number"],
                "text": item["text"],
                "score": score
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        top_results = results[:top_k]

        for rank, result in enumerate(top_results, start=1):
            result["rank"] = rank
            result["citation"] = f"S{rank}"

        return top_results
