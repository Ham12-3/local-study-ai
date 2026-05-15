from __future__ import annotations

from pathlib import Path
import unicodedata

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from studyvault.services.local_data import LocalRepository


class WorkerSignals(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(object)
    error = Signal(str)


class ImportTextbookWorker(QRunnable):
    def __init__(self, file_path: str, textbook_id: int) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.file_path = file_path
        self.textbook_id = textbook_id
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            path = Path(self.file_path)
            if not path.exists():
                raise FileNotFoundError(str(path))
            self.signals.progress.emit(25)
            pages = self._extract_pdf_pages(path)
            self.signals.progress.emit(65)
            chunks = self._chunk_pages(pages)
            page_count = len(pages) or 1
            chunk_count = len(chunks)
            self.signals.progress.emit(100)
            self.signals.finished.emit(
                {
                    "id": self.textbook_id,
                    "page_count": page_count,
                    "chunk_count": chunk_count,
                    "embedding_status": "Text indexed",
                    "chunks": chunks,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.signals.error.emit(str(exc))

    def _extract_pdf_pages(self, path: Path) -> list[tuple[int, str]]:
        if path.suffix.lower() != ".pdf":
            return [(1, path.read_text(encoding="utf-8", errors="ignore"))]
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF import. Run pip install -r requirements.txt") from exc

        reader = PdfReader(str(path))
        pages: list[tuple[int, str]] = []
        total = max(len(reader.pages), 1)
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append((index, self._clean_text(text)))
            self.signals.progress.emit(25 + int(index * 35 / total))
        return pages

    def _chunk_pages(self, pages: list[tuple[int, str]], max_chars: int = 1500) -> list[dict[str, object]]:
        chunks: list[dict[str, object]] = []
        for page_number, text in pages:
            text = self._clean_text(text)
            if not text.strip():
                continue
            start = 0
            chunk_index = 0
            while start < len(text):
                end = min(start + max_chars, len(text))
                if end < len(text):
                    boundary = text.rfind(" ", start, end)
                    if boundary > start + 500:
                        end = boundary
                content = text[start:end].strip()
                content = self._clean_text(content)
                if content:
                    chunks.append(
                        {
                            "page_number": page_number,
                            "chunk_index": chunk_index,
                            "content": content,
                            "embedding": None,
                        }
                    )
                    chunk_index += 1
                start = end
        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        # Some PDFs emit lone UTF-16 surrogate code points for mathematical
        # symbols or damaged glyphs. SQLite cannot encode those to UTF-8.
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        text = "".join(char for char in text if not 0xD800 <= ord(char) <= 0xDFFF)
        text = unicodedata.normalize("NFKC", text)
        return " ".join(text.split())


class OllamaRefreshWorker(QRunnable):
    def __init__(self, client) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.client = client
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        self.signals.finished.emit(self.client.list_models())


class RuntimeSetupWorker(QRunnable):
    def __init__(self, manager, operation: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.manager = manager
        self.operation = operation
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            if self.operation == "inspect":
                self.signals.status.emit("Checking local AI runtime")
                result = self.manager.inspect()
            elif self.operation == "install":
                self.signals.status.emit("Downloading official Ollama installer")
                result = self.manager.install_ollama(
                    progress=self.signals.progress.emit,
                    status=self.signals.status.emit,
                )
            elif self.operation == "start":
                self.signals.status.emit("Starting local AI in the background")
                result = self.manager.start_ollama()
            elif self.operation == "pull_model":
                result = self.manager.pull_model(
                    progress=self.signals.progress.emit,
                    status=self.signals.status.emit,
                )
            elif self.operation == "auto_setup":
                result = self.manager.auto_setup(
                    progress=self.signals.progress.emit,
                    status=self.signals.status.emit,
                )
            else:
                raise ValueError(f"Unknown runtime setup operation: {self.operation}")
            self.signals.finished.emit(result)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.signals.error.emit(str(exc))


class ChatWorker(QRunnable):
    def __init__(self, client, model: str, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.client = client
        self.model = model
        self.messages = messages
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.status.emit("Local model is thinking")
            answer = self.client.chat(self.model, self.messages)
            self.signals.finished.emit(answer)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.signals.error.emit(str(exc))


class EmbeddingIndexWorker(QRunnable):
    def __init__(self, client, db_path, textbook_id: int, chunks: list[dict[str, object]], model: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.client = client
        self.db_path = db_path
        self.textbook_id = textbook_id
        self.chunks = chunks
        self.model = model
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            if not self.chunks:
                self.signals.finished.emit({"textbook_id": self.textbook_id, "status": "No text found"})
                return
            repo = LocalRepository(self.db_path)
            missing = repo.chunks_missing_embeddings(self.textbook_id)
            if not missing:
                repo.update_textbook_status(self.textbook_id, "Vector indexed")
                self.signals.progress.emit(100)
                self.signals.finished.emit({"textbook_id": self.textbook_id, "status": "Vector indexed"})
                return
            embedded: list[dict[str, object]] = []
            work = [
                {
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                }
                for chunk in missing
            ]
            total = len(work)
            batch_size = 12
            for start in range(0, total, batch_size):
                batch = work[start : start + batch_size]
                self.signals.status.emit(f"Embedding textbook chunks {start + 1}-{min(start + batch_size, total)} of {total}")
                vectors = self.client.embed(self.model, [str(chunk["content"]) for chunk in batch])
                for chunk, vector in zip(batch, vectors):
                    embedded.append(
                        {
                            "page_number": chunk["page_number"],
                            "chunk_index": chunk["chunk_index"],
                            "embedding": vector,
                        }
                    )
                repo.set_chunk_embeddings(self.textbook_id, embedded[-len(batch):])
                self.signals.progress.emit(int(min(99, (start + len(batch)) * 100 / total)))
            repo.update_textbook_status(self.textbook_id, "Vector indexed")
            self.signals.progress.emit(100)
            self.signals.finished.emit({"textbook_id": self.textbook_id, "status": "Vector indexed"})
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            LocalRepository(self.db_path).update_textbook_status(self.textbook_id, "Text indexed")
            self.signals.error.emit(str(exc))


class RagChatWorker(QRunnable):
    def __init__(self, client, db_path, textbook_id: int, question: str, model: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.client = client
        self.db_path = db_path
        self.textbook_id = textbook_id
        self.question = question
        self.model = model
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            repo = LocalRepository(self.db_path)
            textbook = repo.textbook_by_id(self.textbook_id)
            if textbook is None:
                raise RuntimeError("Selected textbook was not found.")

            chunks = []
            try:
                query_vector = self.client.embed(self.model, [self.question])[0]
                chunks = repo.search_chunks_by_vector(self.textbook_id, query_vector, limit=5)
            except Exception:
                chunks = []
            if not chunks:
                chunks = repo.search_chunks(self.textbook_id, self.question, limit=5)
            if not chunks:
                raise RuntimeError("No indexed textbook text was found. Re-import the PDF to build the local retrieval index.")

            context = "\n\n".join(f"[Page {chunk.page_number}]\n{chunk.content}" for chunk in chunks)
            source_pages = sorted({chunk.page_number for chunk in chunks})
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are StudyVault AI, a local RAG study assistant. Use only the retrieved "
                        "textbook context. If the context does not support the answer, say you cannot "
                        "find it in the indexed pages. Cite page numbers inline."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Textbook: {textbook.title}\n"
                        f"Retrieved context:\n{context}\n\n"
                        f"Question: {self.question}"
                    ),
                },
            ]
            self.signals.status.emit("Generating grounded answer")
            answer = self.client.chat(self.model, messages)
            self.signals.finished.emit({"answer": answer, "source_pages": source_pages})
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.signals.error.emit(str(exc))
