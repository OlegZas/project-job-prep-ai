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

        prompt = f"""Answer as a helpful data engineering career coach.
Use only the supplied sources. Cite factual claims with [S1], [S2], and so on.
For recommendation questions, make practical inferences from facts that are explicitly
present in the sources. For example, when asked what to prepare based on a resume,
connect its listed tools, projects, and responsibilities to likely interview topics.
Clearly phrase these as recommendations, and never invent experience or qualifications.
If the sources contain no useful evidence for the question, say exactly:
"I couldn't find enough information in these documents to answer that."
Use plain language, organize longer answers with short bullets, and be concise.

Sources:
{context}

Question: {question}"""

        response = self.client.responses.create(
            model=self.chat_model,
            input=prompt
        )

        return response.output_text
