import io
import re
from pathlib import Path

from pypdf import PdfReader


class LocalFile:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.name = self.file_path.name

    def getvalue(self):
        return self.file_path.read_bytes()


class DocumentProcessor:
    def __init__(self, chunk_size=180, overlap=30):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_local_files(self, folder_path="docs"):
        folder = Path(folder_path)

        if not folder.exists():
            return []

        files = []

        for file_path in folder.iterdir():
            if file_path.suffix.lower() in [".txt", ".md", ".pdf"]:
                files.append(LocalFile(file_path))

        return files

    def read_file(self, uploaded_file):
        file_name = uploaded_file.name.lower()
        file_bytes = uploaded_file.getvalue()

        if file_name.endswith(".pdf"):
            return self.read_pdf(file_bytes)

        if file_name.endswith(".txt") or file_name.endswith(".md"):
            return self.read_text(file_bytes)

        return ""

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

    def chunk_text(self, text, file_name):
        words = text.split()
        chunks = []

        start = 0
        chunk_number = 1

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "file_name": file_name,
                "chunk_number": chunk_number,
                "text": chunk_text
            })

            start = end - self.overlap
            chunk_number += 1

        return chunks

    def process_files(self, files):
        all_chunks = []

        for file in files:
            raw_text = self.read_file(file)
            clean_text = self.clean_text(raw_text)

            if clean_text:
                chunks = self.chunk_text(clean_text, file.name)
                all_chunks.extend(chunks)

        return all_chunks