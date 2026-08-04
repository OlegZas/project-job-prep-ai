import hashlib
import os

import numpy as np
from openai import OpenAI


class DocumentStore:
    def __init__(self, client=None, embedding_cache=None):
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

    def search(self, question, top_k=3):
        if not self.items:
            return []

        question_embedding = self.create_embedding(question)

        results = []

        for item in self.items:
            score = np.dot(question_embedding, item["embedding"])

            results.append({
                "document_id": item["document_id"],
                "chunk_id": item["chunk_id"],
                "file_name": item["file_name"],
                "chunk_number": item["chunk_number"],
                "text": item["text"],
                "score": float(score)
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]
