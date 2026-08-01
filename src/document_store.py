import os

import numpy as np
from openai import OpenAI


class DocumentStore:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.items = []

    def create_embedding(self, text):
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )

        return response.data[0].embedding

    def add_chunks(self, chunks):
        self.items = []

        for chunk in chunks:
            embedding = self.create_embedding(chunk["text"])

            self.items.append({
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
                "file_name": item["file_name"],
                "chunk_number": item["chunk_number"],
                "text": item["text"],
                "score": float(score)
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]