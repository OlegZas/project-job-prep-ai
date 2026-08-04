from pathlib import Path

import pytest

from src.file_loader import DocumentProcessor


class UploadedFileStub:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


def test_clean_text_normalizes_whitespace():
    processor = DocumentProcessor()

    result = processor.clean_text("  Kafka\n\nconsumer\t groups   scale.  ")

    assert result == "Kafka consumer groups scale."


def test_read_text_falls_back_to_latin_1():
    processor = DocumentProcessor()

    result = processor.read_text("café".encode("latin-1"))

    assert result == "café"


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 11)],
)
def test_invalid_chunk_configuration_is_rejected(chunk_size, overlap):
    with pytest.raises(ValueError):
        DocumentProcessor(chunk_size=chunk_size, overlap=overlap)


def test_chunk_text_preserves_overlap_without_extra_final_chunk():
    processor = DocumentProcessor(chunk_size=4, overlap=1)

    chunks = processor.chunk_text("one two three four five six seven", "notes.txt")

    assert [chunk["text"] for chunk in chunks] == [
        "one two three four",
        "four five six seven",
    ]
    assert [chunk["chunk_number"] for chunk in chunks] == [1, 2]
    assert len({chunk["document_id"] for chunk in chunks}) == 1
    assert len({chunk["chunk_id"] for chunk in chunks}) == 2


def test_process_files_ignores_unsupported_files():
    processor = DocumentProcessor(chunk_size=10, overlap=2)
    files = [
        UploadedFileStub("notes.txt", b"Kafka consumers share work in a group."),
        UploadedFileStub("data.csv", b"unsupported,content"),
    ]

    chunks = processor.process_files(files)

    assert len(chunks) == 1
    assert chunks[0]["file_name"] == "notes.txt"
    assert len(chunks[0]["document_id"]) == 64
    assert len(chunks[0]["chunk_id"]) == 64


def test_load_local_files_is_filtered_and_deterministic(tmp_path: Path):
    (tmp_path / "z-notes.md").write_text("Z", encoding="utf-8")
    (tmp_path / "a-notes.txt").write_text("A", encoding="utf-8")
    (tmp_path / "ignored.csv").write_text("ignored", encoding="utf-8")

    processor = DocumentProcessor()
    files = processor.load_local_files(tmp_path)

    assert [file.name for file in files] == ["a-notes.txt", "z-notes.md"]


def test_load_local_files_can_limit_extensions(tmp_path: Path):
    (tmp_path / "study-notes.txt").write_text("study", encoding="utf-8")
    (tmp_path / "project-roadmap.md").write_text("roadmap", encoding="utf-8")

    processor = DocumentProcessor()
    files = processor.load_local_files(tmp_path, allowed_extensions={".txt"})

    assert [file.name for file in files] == ["study-notes.txt"]


def test_content_ids_are_stable_when_a_file_is_renamed():
    processor = DocumentProcessor(chunk_size=10, overlap=2)
    content = b"Kafka consumers share work in a consumer group."

    first = processor.process_files([UploadedFileStub("first.txt", content)])
    renamed = processor.process_files([UploadedFileStub("renamed.txt", content)])

    assert first[0]["document_id"] == renamed[0]["document_id"]
    assert first[0]["chunk_id"] == renamed[0]["chunk_id"]
