from types import SimpleNamespace

from src.document_store import DocumentStore
from src.file_loader import DocumentProcessor


class FakeEmbeddings:
    def __init__(self):
        self.calls = []

    def create(self, model, input):
        self.calls.append({"model": model, "input": input})
        embedding = [1.0, 0.0] if "Kafka" in input else [0.0, 1.0]
        return SimpleNamespace(data=[SimpleNamespace(embedding=embedding)])


class FakeOpenAIClient:
    def __init__(self):
        self.embeddings = FakeEmbeddings()


def make_chunks():
    processor = DocumentProcessor(chunk_size=20, overlap=2)
    return processor.chunk_text(
        "Kafka consumer groups distribute partition work across consumers.",
        "kafka.txt",
    )


def test_embedding_cache_avoids_duplicate_api_calls():
    client = FakeOpenAIClient()
    store = DocumentStore(client=client)

    first = store.create_embedding("Kafka")
    second = store.create_embedding("Kafka")

    assert first == second
    assert len(client.embeddings.calls) == 1
    assert store.get_cache_stats() == {
        "hits": 1,
        "misses": 1,
        "cached_embeddings": 1,
    }


def test_reindexing_unchanged_chunks_uses_cached_embeddings():
    client = FakeOpenAIClient()
    store = DocumentStore(client=client)
    chunks = make_chunks()

    store.add_chunks(chunks)
    store.reset_cache_stats()
    store.add_chunks(chunks)

    assert len(client.embeddings.calls) == len(chunks)
    assert store.get_cache_stats()["hits"] == len(chunks)
    assert store.get_cache_stats()["misses"] == 0


def test_search_results_preserve_stable_ids():
    client = FakeOpenAIClient()
    store = DocumentStore(client=client)
    chunks = make_chunks()
    store.add_chunks(chunks)

    result = store.search("Kafka", top_k=1)[0]

    assert result["document_id"] == chunks[0]["document_id"]
    assert result["chunk_id"] == chunks[0]["chunk_id"]
    assert result["citation"] == "S1"
    assert result["rank"] == 1
    assert result["score"] == 1.0


def test_search_applies_minimum_cosine_similarity():
    client = FakeOpenAIClient()
    store = DocumentStore(client=client)
    store.add_chunks(make_chunks())

    assert store.search("unrelated question", top_k=3, min_score=0.25) == []


def test_search_validates_configuration():
    client = FakeOpenAIClient()
    store = DocumentStore(client=client)
    store.add_chunks(make_chunks())

    try:
        store.search("Kafka", top_k=0)
        raise AssertionError("Expected top_k validation")
    except ValueError as error:
        assert "top_k" in str(error)

    try:
        store.search("Kafka", min_score=2.0)
        raise AssertionError("Expected min_score validation")
    except ValueError as error:
        assert "min_score" in str(error)


def test_corpus_id_is_independent_of_chunk_order():
    chunks = DocumentProcessor(chunk_size=4, overlap=1).chunk_text(
        "one two three four five six seven",
        "notes.txt",
    )

    assert DocumentStore.create_corpus_id(chunks) == DocumentStore.create_corpus_id(
        list(reversed(chunks))
    )
