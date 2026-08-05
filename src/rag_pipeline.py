import os

from src.openai_client import create_openai_client


class RAGPipeline:
    def __init__(self, client=None):
        self.client = client or create_openai_client()
        self.chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.6-luna")

    def build_context(self, search_results):
        context_parts = []

        for result in search_results:
            citation = result.get("citation", f"S{len(context_parts) + 1}")
            source = (
                f"[{citation}] {result['file_name']} - chunk {result['chunk_number']} "
                f"[{result['chunk_id'][:12]}]"
            )
            text = result["text"]

            context_parts.append(f"Source: {source}\n{text}")

        return "\n\n---\n\n".join(context_parts)

    def answer_question(self, question, search_results):
        context = self.build_context(search_results)

        prompt = f"""Answer as a data engineering interview coach.
Use only the supplied sources. Cite factual claims with [S1], [S2], and so on.
If the sources do not answer the question, say exactly: "I don't know based on the uploaded documents."
Be practical and concise.

Sources:
{context}

Question: {question}"""

        response = self.client.responses.create(
            model=self.chat_model,
            input=prompt
        )

        return response.output_text
