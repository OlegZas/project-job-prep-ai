import hashlib
import io
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


class LocalFile:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.name = self.file_path.name

    def getvalue(self):
        return self.file_path.read_bytes()


class DocumentProcessor:
    supported_extensions = {".txt", ".md", ".pdf"}

    def __init__(self, chunk_size=180, overlap=30):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_local_files(self, folder_path="docs", allowed_extensions=None):
        folder = Path(folder_path)

        if not folder.exists():
            return []

        extensions = allowed_extensions or {".txt", ".md", ".pdf"}
        extensions = {extension.lower() for extension in extensions}
        files = []

        for file_path in sorted(folder.iterdir(), key=lambda path: path.name.lower()):
            if file_path.suffix.lower() in extensions:
                files.append(LocalFile(file_path))

        return files

    def read_file(self, uploaded_file, file_bytes=None):
        file_name = uploaded_file.name.lower()

        if file_bytes is None:
            file_bytes = uploaded_file.getvalue()

        if file_name.endswith(".pdf"):
            return self.read_pdf(file_bytes)

        if file_name.endswith(".txt") or file_name.endswith(".md"):
            return self.read_text(file_bytes)

        return ""

    def create_document_record(self, file):
        file_name = getattr(file, "name", "unknown")
        extension = Path(file_name).suffix.lower()

        return {
            "document_id": None,
            "file_name": file_name,
            "file_type": extension.removeprefix(".").upper() or "UNKNOWN",
            "source_type": "sample" if isinstance(file, LocalFile) else "upload",
            "file_size_bytes": 0,
            "character_count": 0,
            "word_count": 0,
            "chunk_count": 0,
            "status": "pending",
            "duplicate_of": None,
            "error": None,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    def read_text(self, file_bytes):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")

    def read_pdf(self, file_bytes):
        text = ""
        pdf = PdfReader(io.BytesIO(file_bytes))

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text

    def clean_text(self, text):
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def chunk_text(self, text, file_name, document_id=None):
        words = text.split()
        chunks = []

        if document_id is None:
            document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()

        start = 0
        chunk_number = 1

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunk_id = hashlib.sha256(
                f"{document_id}:{chunk_number}:{chunk_text}".encode("utf-8")
            ).hexdigest()

            chunks.append({
                "document_id": document_id,
                "chunk_id": chunk_id,
                "file_name": file_name,
                "chunk_number": chunk_number,
                "text": chunk_text
            })

            if end >= len(words):
                break

            start = end - self.overlap
            chunk_number += 1

        return chunks

    def process_files_with_metadata(self, files):
        documents = []
        all_chunks = []
        indexed_documents = {}

        for file in files:
            record = self.create_document_record(file)
            extension = Path(record["file_name"]).suffix.lower()

            try:
                file_bytes = file.getvalue()
                record["file_size_bytes"] = len(file_bytes)

                if extension not in self.supported_extensions:
                    record["status"] = "unsupported"
                    documents.append(record)
                    continue

                raw_text = self.read_file(file, file_bytes=file_bytes)
                clean_text = self.clean_text(raw_text)

                if not clean_text:
                    record["status"] = "empty"
                    documents.append(record)
                    continue

                document_id = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
                record["document_id"] = document_id
                record["character_count"] = len(clean_text)
                record["word_count"] = len(clean_text.split())

                if document_id in indexed_documents:
                    record["status"] = "duplicate"
                    record["duplicate_of"] = indexed_documents[document_id]
                    documents.append(record)
                    continue

                chunks = self.chunk_text(clean_text, file.name, document_id)
                record["chunk_count"] = len(chunks)
                record["status"] = "indexed"
                indexed_documents[document_id] = file.name
                all_chunks.extend(chunks)

            except Exception as error:
                record["status"] = "error"
                record["error"] = f"{type(error).__name__}: {error}"

            documents.append(record)

        return {"documents": documents, "chunks": all_chunks}

    def process_files(self, files):
        return self.process_files_with_metadata(files)["chunks"]
