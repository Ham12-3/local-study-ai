from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import PrimaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.chat_bubble import ChatBubble
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.pages.base import Page
from studyvault.ui.theme import SPACING


class AskAIPage(Page):
    question_submitted = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[dict[str, object]] = []
        self.busy = False
        self.last_error: str | None = None
        self.selected_textbook_id: int | None = None

    def refresh(self, repo, ollama_status) -> None:
        self.clear()
        textbooks = repo.textbooks()
        self._add_controls(textbooks, ollama_status)
        self._add_chat_area(textbooks, ollama_status)
        self._add_composer(bool(textbooks and ollama_status.running and ollama_status.models))

    def _add_controls(self, textbooks, ollama_status) -> None:
        controls = Card(elevated=True)
        row = QHBoxLayout()
        self.selector = QComboBox()
        self.selector.addItem("Select textbook", None)
        for textbook in textbooks:
            self.selector.addItem(textbook.title, textbook.id)
        if self.selected_textbook_id is not None:
            index = self.selector.findData(self.selected_textbook_id)
            if index >= 0:
                self.selector.setCurrentIndex(index)
        self.selector.currentIndexChanged.connect(self._selection_changed)
        row.addWidget(QLabel("Textbook"))
        row.addWidget(self.selector, 1)
        if not ollama_status.running:
            row.addWidget(Badge("Ollama not running", "error"))
        elif not ollama_status.models:
            row.addWidget(Badge("No models installed", "warning"))
        else:
            row.addWidget(Badge("Ready", "success"))
        controls.layout().addLayout(row)
        self.content.addWidget(controls)

    def _add_chat_area(self, textbooks, ollama_status) -> None:
        chat = Card()
        chat.setMinimumHeight(440)
        if not textbooks:
            chat.layout().addWidget(EmptyState("No textbook selected", "Import a textbook before asking grounded questions."))
        elif not ollama_status.running:
            chat.layout().addWidget(EmptyState("Ollama is offline", "Start Ollama locally to use the AI chat interface."))
        elif not ollama_status.models:
            chat.layout().addWidget(EmptyState("No local models", "Download or install a local model before asking questions."))
        elif not self.messages:
            chat.layout().addWidget(
                ChatBubble(
                    "assistant",
                    "Choose a textbook, then ask a question. I will answer using your local model and show source chips when textbook retrieval is available.",
                    [],
                )
            )
        else:
            for message in self.messages:
                chat.layout().addWidget(
                    ChatBubble(
                        str(message["role"]),
                        str(message["content"]),
                        list(message.get("source_pages", [])),
                    ),
                    alignment=Qt.AlignmentFlag.AlignRight if message["role"] == "user" else Qt.AlignmentFlag.AlignLeft,
                )
        if self.busy:
            thinking = QLabel("Local model thinking...")
            thinking.setObjectName("Muted")
            thinking.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chat.layout().addWidget(thinking)
        if self.last_error:
            chat.layout().addWidget(Badge(self.last_error, "error"))
        self.content.addWidget(chat)

    def _add_composer(self, can_send: bool) -> None:
        composer = QWidget()
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.setSpacing(SPACING.md)
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask about concepts, pages, definitions, or summaries")
        self.input_box.returnPressed.connect(self._submit)
        self.send = PrimaryButton("Send")
        self.send.setEnabled(can_send and not self.busy)
        self.send.clicked.connect(self._submit)
        composer_layout.addWidget(self.input_box, 1)
        composer_layout.addWidget(self.send)
        self.content.addWidget(composer)

    def _selection_changed(self) -> None:
        self.selected_textbook_id = self.selector.currentData()

    def _submit(self) -> None:
        textbook_id = self.selector.currentData()
        question = self.input_box.text().strip()
        if not textbook_id:
            self.last_error = "Select a textbook first."
            return
        if not question:
            return
        self.selected_textbook_id = int(textbook_id)
        self.last_error = None
        self.messages.append({"role": "user", "content": question, "source_pages": []})
        self.input_box.clear()
        self.busy = True
        self.question_submitted.emit(int(textbook_id), question)

    def add_answer(self, answer: str, source_pages: list[int] | None = None) -> None:
        self.busy = False
        self.last_error = None
        self.messages.append({"role": "assistant", "content": answer, "source_pages": source_pages or []})

    def show_error(self, message: str) -> None:
        self.busy = False
        self.last_error = message

