from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.pages.base import Page
from studyvault.ui.theme import SPACING


class DashboardPage(Page):
    action_requested = Signal(str)

    def refresh(self, repo, ollama_status) -> None:
        self.clear()
        stats = repo.stats()
        grid = QGridLayout()
        grid.setSpacing(SPACING.md)
        cards = [
            ("Uploaded textbooks", stats["textbooks"]),
            ("Notes generated", stats["notes"]),
            ("Flashcards created", stats["flashcards"]),
            ("Quiz attempts", stats["quiz_attempts"]),
            ("Weak topics", stats["weak_topics"]),
            ("Local AI status", "Online" if ollama_status.running else "Offline"),
        ]
        for i, (label, value) in enumerate(cards):
            card = Card(elevated=i == 5)
            number = QLabel(str(value))
            number.setObjectName("PageTitle")
            caption = QLabel(label)
            caption.setObjectName("Muted")
            card.layout().addWidget(number)
            card.layout().addWidget(caption)
            grid.addWidget(card, i // 3, i % 3)
        self.content.addLayout(grid)

        quick = Card(elevated=True)
        title = QLabel("Quick actions")
        title.setObjectName("SectionTitle")
        row = QHBoxLayout()
        for label, page in [
            ("Upload textbook", "textbooks"),
            ("Ask AI", "ask_ai"),
            ("Generate flashcards", "flashcards"),
            ("Start quiz", "quiz"),
        ]:
            button = PrimaryButton(label) if page == "textbooks" else SecondaryButton(label)
            button.clicked.connect(lambda checked=False, p=page: self.action_requested.emit(p))
            row.addWidget(button)
        quick.layout().addWidget(title)
        quick.layout().addLayout(row)
        self.content.addWidget(quick)

        split = QHBoxLayout()
        split.setSpacing(SPACING.lg)
        split.addWidget(self._recent(repo))
        split.addWidget(self._continue(repo, ollama_status))
        self.content.addLayout(split)

    def _recent(self, repo) -> QWidget:
        card = Card()
        title = QLabel("Recent textbooks")
        title.setObjectName("SectionTitle")
        card.layout().addWidget(title)
        textbooks = repo.recent_textbooks()
        if not textbooks:
            card.layout().addWidget(EmptyState("No textbooks yet", "Import a PDF to begin building your local study vault."))
            return card
        for textbook in textbooks:
            row = QLabel(f"{textbook.title}\n{max(textbook.page_count, 0)} pages · {textbook.embedding_status}")
            row.setObjectName("Muted")
            card.layout().addWidget(row)
        return card

    def _continue(self, repo, ollama_status) -> QWidget:
        card = Card()
        title = QLabel("Continue studying")
        title.setObjectName("SectionTitle")
        card.layout().addWidget(title)
        if not repo.textbooks():
            card.layout().addWidget(EmptyState("Nothing queued", "Your next study session will appear here once textbooks are imported."))
        elif not ollama_status.running:
            card.layout().addWidget(Badge("Ollama is not running", "error"))
            note = QLabel("Start Ollama locally to ask questions, generate notes, and build quizzes.")
            note.setObjectName("Muted")
            note.setWordWrap(True)
            card.layout().addWidget(note)
        else:
            card.layout().addWidget(Badge("Ready", "success"))
            card.layout().addWidget(QLabel("Pick up from your most recent textbook, notes, or review queue."))
        return card

