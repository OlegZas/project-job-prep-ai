import os

from openai import OpenAI


class RAGPipeline:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    def build_context(self, search_results):
        context_parts = []

        for result in search_results:
            source = f"{result['file_name']} - chunk {result['chunk_number']}"
            text = result["text"]

            context_parts.append(f"Source: {source}\n{text}")

        return "\n\n---\n\n".join(context_parts)

    def answer_question(self, question, search_results):
        context = self.build_context(search_results)

        prompt = f"""
You are DataPrep AI, a data engineering interview prep assistant.

Use only the context below to answer the user's question.
If the answer is not found in the context, say:
"I don't know based on the uploaded documents."

Keep the answer clear, practical, and interview-focused.

Context:
{context}

Question:
{question}

Answer:
"""

        response = self.client.responses.create(
            model=self.chat_model,
            input=prompt
        )

        return response.output_text