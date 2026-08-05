from types import SimpleNamespace

from src.rag_pipeline import RAGPipeline


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Consumer groups divide work [S1].")


def test_rag_pipeline_labels_context_and_returns_cited_answer():
    client = SimpleNamespace(responses=FakeResponses())
    pipeline = RAGPipeline(client=client)
    search_results = [
        {
            "citation": "S1",
            "file_name": "notes.txt",
            "chunk_number": 2,
            "chunk_id": "a" * 64,
            "text": "Consumers in a group share partitions.",
        }
    ]

    answer = pipeline.answer_question("What is a consumer group?", search_results)

    assert answer == "Consumer groups divide work [S1]."
    prompt = client.responses.calls[0]["input"]
    assert "[S1] notes.txt - chunk 2" in prompt
    assert "Use only the supplied sources" in prompt
