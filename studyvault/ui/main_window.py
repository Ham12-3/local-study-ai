from __future__ import annotations

import os

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QStatusBar, QVBoxLayout, QWidget

from studyvault.services.local_data import LocalRepository
from studyvault.services.ollama import OllamaClient, OllamaStatus
from studyvault.services.runtime_manager import RuntimeManager, RuntimeState
from studyvault.services.workers import EmbeddingIndexWorker, ImportTextbookWorker, OllamaRefreshWorker, RagChatWorker, RuntimeSetupWorker
from studyvault.ui.components.sidebar import Sidebar
from studyvault.ui.components.topbar import Topbar
from studyvault.ui.pages.ask_ai import AskAIPage
from studyvault.ui.pages.dashboard import DashboardPage
from studyvault.ui.pages.flashcards import FlashcardsPage
from studyvault.ui.pages.notes import NotesPage
from studyvault.ui.pages.onboarding import OnboardingPage
from studyvault.ui.pages.quiz import QuizPage
from studyvault.ui.pages.settings import SettingsPage
from studyvault.ui.pages.textbooks import TextbooksPage
from studyvault.ui.pages.weak_topics import WeakTopicsPage


PAGE_TITLES = {
    "dashboard": "Dashboard",
    "textbooks": "Textbooks",
    "ask_ai": "Ask AI",
    "notes": "Notes",
    "flashcards": "Flashcards",
    "quiz": "Quiz",
    "weak_topics": "Weak Topics",
    "settings": "Settings",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StudyVault AI")
        self.resize(1280, 800)
        self.setMinimumSize(1050, 700)

        self.repo = LocalRepository()
        self.ollama = OllamaClient()
        self.runtime = RuntimeManager(self.ollama)
        self.ollama_status = OllamaStatus(False, [], "Not checked")
        self.runtime_state = RuntimeState(False, False, [], error="Not checked")
        self.runtime_busy = False
        self.pool = QThreadPool.globalInstance()
        self._active_workers = []

        root = QWidget()
        root.setObjectName("AppRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sidebar = Sidebar()
        self.topbar = Topbar()
        self.stack = QStackedWidget()

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.topbar)
        main_layout.addWidget(self.stack, 1)

        layout.addWidget(self.sidebar)
        layout.addWidget(main, 1)
        self.setCentralWidget(root)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.pages = {
            "onboarding": OnboardingPage(),
            "dashboard": DashboardPage(),
            "textbooks": TextbooksPage(),
            "ask_ai": AskAIPage(),
            "notes": NotesPage(),
            "flashcards": FlashcardsPage(),
            "quiz": QuizPage(),
            "weak_topics": WeakTopicsPage(),
            "settings": SettingsPage(),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.sidebar.page_selected.connect(self.show_page)
        self.topbar.refresh_requested.connect(self.refresh_ollama)
        self.pages["dashboard"].action_requested.connect(self.show_page)
        self.pages["textbooks"].upload_requested.connect(self.import_textbook)
        self.pages["textbooks"].rebuild_requested.connect(self.rebuild_textbook_index)
        self.pages["textbooks"].delete_requested.connect(self.delete_textbook)
        self.pages["ask_ai"].question_submitted.connect(self.ask_ai)
        self.pages["onboarding"].auto_requested.connect(lambda: self.run_runtime_operation("auto_setup"))
        self.pages["onboarding"].check_requested.connect(lambda: self.run_runtime_operation("inspect"))

        self.show_onboarding()
        if os.environ.get("STUDYVAULT_DISABLE_AUTO_SETUP") == "1":
            self.run_runtime_operation("inspect")
        else:
            self.run_runtime_operation("auto_setup")

    def show_onboarding(self) -> None:
        self.stack.setCurrentWidget(self.pages["onboarding"])
        self.topbar.set_title("Local AI Setup")
        self.pages["onboarding"].refresh(self.runtime_state, self.runtime_busy)

    def show_page(self, page: str) -> None:
        widget = self.pages[page]
        self.stack.setCurrentWidget(widget)
        if page in PAGE_TITLES:
            self.sidebar.set_active(page)
            self.topbar.set_title(PAGE_TITLES[page])
        self.refresh_page(page)

    def refresh_current_page(self) -> None:
        key = next(k for k, v in self.pages.items() if v is self.stack.currentWidget())
        self.refresh_page(key)

    def refresh_page(self, page: str) -> None:
        if page == "onboarding":
            self.pages[page].refresh(self.runtime_state, self.runtime_busy)
        elif page == "dashboard":
            self.pages[page].refresh(self.repo, self.ollama_status)
        elif page == "textbooks":
            self.pages[page].refresh(self.repo)
        elif page == "ask_ai":
            self.pages[page].refresh(self.repo, self.ollama_status)
        elif page in {"notes", "flashcards", "quiz", "weak_topics"}:
            self.pages[page].refresh(self.repo)
        elif page == "settings":
            self.pages[page].refresh(
                self.repo,
                self.ollama_status,
                self.runtime_state,
                self.runtime_busy,
                self.refresh_ollama,
                self.reset_local_cache,
                self.run_runtime_operation,
            )

    def run_runtime_operation(self, operation: str) -> None:
        self.runtime_busy = True
        self.status.showMessage("Preparing local AI setup...")
        if self.stack.currentWidget() is self.pages["onboarding"]:
            self.pages["onboarding"].refresh(self.runtime_state, True, "Working on local AI setup...")
        worker = RuntimeSetupWorker(self.runtime, operation)
        worker.signals.progress.connect(self._runtime_progress)
        worker.signals.status.connect(self._runtime_status)
        worker.signals.finished.connect(self._runtime_finished)
        worker.signals.error.connect(self._runtime_failed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        worker.signals.error.connect(lambda _message, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def _runtime_progress(self, value: int) -> None:
        if self.stack.currentWidget() is self.pages["onboarding"]:
            self.pages["onboarding"].set_progress(value)

    def _runtime_status(self, message: str) -> None:
        self.status.showMessage(message)
        if self.stack.currentWidget() is self.pages["onboarding"]:
            self.pages["onboarding"].set_status(message)
        elif self.stack.currentWidget() is self.pages["settings"]:
            self.refresh_current_page()

    def _runtime_finished(self, state: RuntimeState) -> None:
        self.runtime_busy = False
        self.runtime_state = state
        self.ollama_status = OllamaStatus(state.running, state.models, state.error)
        self.sidebar.set_ai_status(state.running, len(state.models))
        self.topbar.set_ai_status(state.running, len(state.models))
        if state.ready:
            self.status.showMessage("Local AI ready")
            if self.stack.currentWidget() is self.pages["onboarding"]:
                self.show_page("dashboard")
            else:
                self.refresh_current_page()
        else:
            self.status.showMessage("Local AI setup needs attention")
            if self.stack.currentWidget() is self.pages["onboarding"]:
                self.pages["onboarding"].refresh(state, False, state.error)
            else:
                self.refresh_current_page()

    def _runtime_failed(self, message: str) -> None:
        self.runtime_busy = False
        self.runtime_state = RuntimeState(
            installed=self.runtime_state.installed,
            running=self.runtime_state.running,
            models=self.runtime_state.models,
            executable=self.runtime_state.executable,
            error=message,
        )
        self.status.showMessage(f"Local AI setup failed: {message}")
        if self.stack.currentWidget() is self.pages["onboarding"]:
            self.pages["onboarding"].refresh(self.runtime_state, False, message)
        else:
            self.refresh_current_page()

    def refresh_ollama(self) -> None:
        self.status.showMessage("Checking Ollama local model service...")
        worker = OllamaRefreshWorker(self.ollama)
        worker.signals.finished.connect(self._ollama_refreshed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def _ollama_refreshed(self, status: OllamaStatus) -> None:
        self.ollama_status = status
        self.runtime_state = RuntimeState(
            installed=self.runtime.find_ollama_executable() is not None,
            running=status.running,
            models=status.models,
            executable=self.runtime.find_ollama_executable(),
            error=status.error,
        )
        self.sidebar.set_ai_status(status.running, len(status.models))
        self.topbar.set_ai_status(status.running, len(status.models))
        if status.running:
            self.status.showMessage(f"Ollama online - {len(status.models)} local models available")
        else:
            self.status.showMessage("Ollama offline - start Ollama to enable local AI features")
        self.refresh_current_page()

    def import_textbook(self, path: str) -> None:
        textbook_id = self.repo.add_textbook_import(path)
        self.status.showMessage("Importing textbook locally...")
        page = self.pages["textbooks"]
        page.set_import_progress(0)
        worker = ImportTextbookWorker(path, textbook_id)
        worker.signals.progress.connect(page.set_import_progress)
        worker.signals.finished.connect(self._import_finished)
        worker.signals.error.connect(self._import_failed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        worker.signals.error.connect(lambda _message, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def rebuild_textbook_index(self, textbook_id: int) -> None:
        textbook = self.repo.textbook_by_id(textbook_id)
        if textbook is None:
            self.status.showMessage("Textbook was not found.")
            return
        self.status.showMessage("Rebuilding textbook retrieval index...")
        worker = ImportTextbookWorker(textbook.file_path, textbook.id)
        if hasattr(self.pages["textbooks"], "set_import_progress"):
            worker.signals.progress.connect(self.pages["textbooks"].set_import_progress)
        worker.signals.finished.connect(self._import_finished)
        worker.signals.error.connect(self._import_failed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        worker.signals.error.connect(lambda _message, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def delete_textbook(self, textbook_id: int) -> None:
        self.repo.delete_textbook(textbook_id)
        self.status.showMessage("Textbook deleted from local library.")
        self.refresh_page("textbooks")

    def ask_ai(self, textbook_id: int, question: str) -> None:
        if not self.ollama_status.running:
            self.pages["ask_ai"].show_error("Ollama is not running.")
            self.refresh_page("ask_ai")
            return
        if not self.ollama_status.models:
            self.pages["ask_ai"].show_error("No local models are installed.")
            self.refresh_page("ask_ai")
            return
        if not self.repo.chunks_for_textbook(textbook_id):
            self.pages["ask_ai"].show_error("This textbook needs a retrieval index. Rebuilding it now; try your question again in a moment.")
            self.refresh_page("ask_ai")
            self.rebuild_textbook_index(textbook_id)
            return
        model = self.ollama_status.models[0]
        self.status.showMessage("Retrieving textbook context...")
        worker = RagChatWorker(self.ollama, self.repo.db_path, textbook_id, question, model)
        worker.signals.status.connect(self.status.showMessage)
        worker.signals.finished.connect(self._ask_ai_finished)
        worker.signals.error.connect(self._ask_ai_failed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        worker.signals.error.connect(lambda _message, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def _ask_ai_finished(self, result: dict) -> None:
        self.pages["ask_ai"].add_answer(result["answer"], result.get("source_pages", []))
        self.status.showMessage("Local AI answer ready")
        self.refresh_page("ask_ai")

    def _ask_ai_failed(self, message: str) -> None:
        self.pages["ask_ai"].show_error(message)
        self.status.showMessage(f"Ask AI failed: {message}")
        self.refresh_page("ask_ai")

    def _import_finished(self, result: dict) -> None:
        self.repo.update_textbook_import(
            result["id"],
            result["page_count"],
            result["chunk_count"],
            result["embedding_status"],
        )
        self.repo.replace_textbook_chunks(result["id"], result.get("chunks", []))
        self.status.showMessage("Textbook imported and indexed for local retrieval.")
        if self.ollama_status.running and self.ollama_status.models and result.get("chunks"):
            self._start_embedding_index(result["id"], result["chunks"])
        self.refresh_page("textbooks")

    def _start_embedding_index(self, textbook_id: int, chunks: list[dict[str, object]]) -> None:
        model = self.ollama_status.models[0]
        worker = EmbeddingIndexWorker(self.ollama, self.repo.db_path, textbook_id, chunks, model)
        worker.signals.status.connect(self.status.showMessage)
        worker.signals.finished.connect(self._embedding_finished)
        worker.signals.error.connect(self._embedding_failed)
        worker.signals.finished.connect(lambda _result, w=worker: self._release_worker(w))
        worker.signals.error.connect(lambda _message, w=worker: self._release_worker(w))
        self._active_workers.append(worker)
        self.pool.start(worker)

    def _embedding_finished(self, result: dict) -> None:
        self.status.showMessage("Textbook vector index ready")
        self.refresh_page("textbooks")

    def _embedding_failed(self, message: str) -> None:
        self.status.showMessage(f"Vector indexing skipped: {message}")
        self.refresh_page("textbooks")

    def _import_failed(self, message: str) -> None:
        self.status.showMessage(f"PDF import failed: {message}")
        self.refresh_page("textbooks")

    def reset_local_cache(self) -> None:
        self.repo.reset_cache_tables(["notes", "flashcards", "quiz_attempts", "weak_topics"])
        self.status.showMessage("Local generated cache reset")
        self.refresh_current_page()

    def _release_worker(self, worker) -> None:
        if worker in self._active_workers:
            self._active_workers.remove(worker)
