from __future__ import annotations

import sqlite3
import re
import json
import math
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


APP_DATA_DIR = Path.home() / ".studyvault-ai"
DB_PATH = APP_DATA_DIR / "studyvault.db"


@dataclass(frozen=True)
class Textbook:
    id: int
    title: str
    file_path: str
    page_count: int
    chunk_count: int
    embedding_status: str
    last_opened_at: str | None
    imported_at: str


@dataclass(frozen=True)
class Note:
    id: int
    textbook_title: str
    title: str
    page_range: str
    body: str
    created_at: str


@dataclass(frozen=True)
class Flashcard:
    id: int
    textbook_title: str
    question: str
    answer: str
    difficulty: str
    source_page: int | None


@dataclass(frozen=True)
class WeakTopic:
    id: int
    topic: str
    textbook_title: str
    wrong_count: int
    recommended_pages: str
    progress: int


@dataclass(frozen=True)
class TextbookChunk:
    id: int
    textbook_id: int
    page_number: int
    chunk_index: int
    content: str
    embedding: str | None = None


class LocalRepository:
    """Small SQLite repository for local UI state.

    The methods intentionally return empty collections when no data exists so
    pages can show polished empty states without hardcoded study content.
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @property
    def data_dir(self) -> Path:
        return self.db_path.parent

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS textbooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    page_count INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    embedding_status TEXT DEFAULT 'Pending',
                    last_opened_at TEXT,
                    imported_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    textbook_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    page_range TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(textbook_id) REFERENCES textbooks(id)
                );

                CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    textbook_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    difficulty TEXT DEFAULT 'New',
                    source_page INTEGER,
                    FOREIGN KEY(textbook_id) REFERENCES textbooks(id)
                );

                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    textbook_id INTEGER,
                    score INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(textbook_id) REFERENCES textbooks(id)
                );

                CREATE TABLE IF NOT EXISTS weak_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    textbook_id INTEGER,
                    topic TEXT NOT NULL,
                    wrong_count INTEGER DEFAULT 0,
                    recommended_pages TEXT DEFAULT '',
                    progress INTEGER DEFAULT 0,
                    FOREIGN KEY(textbook_id) REFERENCES textbooks(id)
                );

                CREATE TABLE IF NOT EXISTS textbook_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    textbook_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    FOREIGN KEY(textbook_id) REFERENCES textbooks(id)
                );

                CREATE INDEX IF NOT EXISTS idx_textbook_chunks_textbook
                    ON textbook_chunks(textbook_id);
                """
            )

    def add_textbook_import(self, path: str) -> int:
        file_path = Path(path)
        title = file_path.stem or file_path.name
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO textbooks
                    (title, file_path, page_count, chunk_count, embedding_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, str(file_path), 0, 0, "Queued", now),
            )
            return int(cur.lastrowid)

    def update_textbook_import(
        self, textbook_id: int, page_count: int, chunk_count: int, embedding_status: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE textbooks
                SET page_count = ?, chunk_count = ?, embedding_status = ?, last_opened_at = ?
                WHERE id = ?
                """,
                (
                    page_count,
                    chunk_count,
                    embedding_status,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    textbook_id,
                ),
            )

    def replace_textbook_chunks(self, textbook_id: int, chunks: list[dict[str, object]]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM textbook_chunks WHERE textbook_id = ?", (textbook_id,))
            conn.executemany(
                """
                INSERT INTO textbook_chunks (textbook_id, page_number, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        textbook_id,
                        int(chunk["page_number"]),
                        int(chunk["chunk_index"]),
                        self._clean_text(str(chunk["content"])),
                        chunk.get("embedding"),
                    )
                    for chunk in chunks
                ],
            )

    def update_textbook_status(self, textbook_id: int, embedding_status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE textbooks SET embedding_status = ? WHERE id = ?",
                (embedding_status, textbook_id),
            )

    def delete_textbook(self, textbook_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM textbook_chunks WHERE textbook_id = ?", (textbook_id,))
            conn.execute("DELETE FROM notes WHERE textbook_id = ?", (textbook_id,))
            conn.execute("DELETE FROM flashcards WHERE textbook_id = ?", (textbook_id,))
            conn.execute("DELETE FROM quiz_attempts WHERE textbook_id = ?", (textbook_id,))
            conn.execute("DELETE FROM weak_topics WHERE textbook_id = ?", (textbook_id,))
            conn.execute("DELETE FROM textbooks WHERE id = ?", (textbook_id,))

    def textbooks(self) -> list[Textbook]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM textbooks ORDER BY imported_at DESC").fetchall()
        return [Textbook(**dict(row)) for row in rows]

    def recent_textbooks(self, limit: int = 4) -> list[Textbook]:
        return self.textbooks()[:limit]

    def textbook_by_id(self, textbook_id: int) -> Textbook | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM textbooks WHERE id = ?", (textbook_id,)).fetchone()
        return Textbook(**dict(row)) if row else None

    def chunks_for_textbook(self, textbook_id: int) -> list[TextbookChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM textbook_chunks
                WHERE textbook_id = ?
                ORDER BY page_number, chunk_index
                """,
                (textbook_id,),
            ).fetchall()
        return [TextbookChunk(**dict(row)) for row in rows]

    def search_chunks(self, textbook_id: int, query: str, limit: int = 5) -> list[TextbookChunk]:
        terms = [term for term in re.findall(r"[A-Za-z0-9']+", query.lower()) if len(term) > 2]
        chunks = self.chunks_for_textbook(textbook_id)
        if not terms:
            return chunks[:limit]

        scored: list[tuple[int, TextbookChunk]] = []
        for chunk in chunks:
            content = chunk.content.lower()
            score = sum(content.count(term) for term in terms)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _score, chunk in scored[:limit]]

    def chunks_with_embeddings(self, textbook_id: int) -> list[TextbookChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM textbook_chunks
                WHERE textbook_id = ? AND embedding IS NOT NULL
                """,
                (textbook_id,),
            ).fetchall()
        return [TextbookChunk(**dict(row)) for row in rows]

    def chunks_missing_embeddings(self, textbook_id: int) -> list[TextbookChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM textbook_chunks
                WHERE textbook_id = ? AND embedding IS NULL
                ORDER BY page_number, chunk_index
                """,
                (textbook_id,),
            ).fetchall()
        return [TextbookChunk(**dict(row)) for row in rows]

    def search_chunks_by_vector(self, textbook_id: int, query_vector: list[float], limit: int = 5) -> list[TextbookChunk]:
        scored: list[tuple[float, TextbookChunk]] = []
        for chunk in self.chunks_with_embeddings(textbook_id):
            try:
                vector = json.loads(chunk.embedding or "[]")
            except json.JSONDecodeError:
                continue
            score = self._cosine(query_vector, vector)
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _score, chunk in scored[:limit]]

    def set_chunk_embeddings(self, textbook_id: int, embedded_chunks: list[dict[str, object]]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                UPDATE textbook_chunks
                SET embedding = ?
                WHERE textbook_id = ? AND page_number = ? AND chunk_index = ?
                """,
                [
                    (
                        json.dumps(chunk["embedding"]),
                        textbook_id,
                        int(chunk["page_number"]),
                        int(chunk["chunk_index"]),
                    )
                    for chunk in embedded_chunks
                ],
            )

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        text = "".join(char for char in text if not 0xD800 <= ord(char) <= 0xDFFF)
        text = unicodedata.normalize("NFKC", text)
        return " ".join(text.split())

    def notes(self) -> list[Note]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT n.id, t.title AS textbook_title, n.title, n.page_range, n.body, n.created_at
                FROM notes n
                JOIN textbooks t ON t.id = n.textbook_id
                ORDER BY n.created_at DESC
                """
            ).fetchall()
        return [Note(**dict(row)) for row in rows]

    def flashcards(self) -> list[Flashcard]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT f.id, t.title AS textbook_title, f.question, f.answer, f.difficulty, f.source_page
                FROM flashcards f
                JOIN textbooks t ON t.id = f.textbook_id
                ORDER BY f.id DESC
                """
            ).fetchall()
        return [Flashcard(**dict(row)) for row in rows]

    def weak_topics(self) -> list[WeakTopic]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT w.id, COALESCE(t.title, 'Unknown textbook') AS textbook_title,
                       w.topic, w.wrong_count, w.recommended_pages, w.progress
                FROM weak_topics w
                LEFT JOIN textbooks t ON t.id = w.textbook_id
                ORDER BY w.wrong_count DESC
                """
            ).fetchall()
        return [WeakTopic(**dict(row)) for row in rows]

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            counts = {
                "textbooks": conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
                "notes": conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
                "flashcards": conn.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0],
                "quiz_attempts": conn.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0],
                "weak_topics": conn.execute("SELECT COUNT(*) FROM weak_topics").fetchone()[0],
            }
        return counts

    def reset_cache_tables(self, tables: Iterable[str]) -> None:
        allowed = {"notes", "flashcards", "quiz_attempts", "weak_topics"}
        selected = [table for table in tables if table in allowed]
        with self._connect() as conn:
            for table in selected:
                conn.execute(f"DELETE FROM {table}")
