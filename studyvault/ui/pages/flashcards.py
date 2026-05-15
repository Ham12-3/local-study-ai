from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import PrimaryButton, SecondaryButton
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.components.flashcard_widget import FlashcardWidget
from studyvault.ui.pages.base import Page


class FlashcardsPage(Page):
    def __init__(self) -> None:
        super().__init__()
        self.index = 0
        self.revealed = False

    def refresh(self, repo) -> None:
        self.clear()
        cards = repo.flashcards()
        if not cards:
            self.content.addWidget(EmptyState("No flashcards yet", "Generate flashcards from an imported textbook to start review."))
            return

        current = cards[self.index % len(cards)]
        progress = QLabel(f"{self.index + 1} / {len(cards)}")
        progress.setObjectName("Muted")
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget = FlashcardWidget()
        widget.set_card(current.question, current.answer, current.difficulty, self.revealed)
        self.content.addWidget(progress)
        self.content.addWidget(widget)
        if current.source_page:
            self.content.addWidget(Badge(f"Source p. {current.source_page}", "primary"), alignment=Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        reveal = PrimaryButton("Reveal answer")
        correct = SecondaryButton("Correct")
        incorrect = SecondaryButton("Incorrect")
        correct.setEnabled(self.revealed)
        incorrect.setEnabled(self.revealed)
        reveal.clicked.connect(lambda: self._reveal(repo))
        correct.clicked.connect(lambda: self._advance(repo))
        incorrect.clicked.connect(lambda: self._advance(repo))
        row.addStretch()
        row.addWidget(reveal)
        row.addWidget(incorrect)
        row.addWidget(correct)
        row.addStretch()
        self.content.addLayout(row)

    def _reveal(self, repo) -> None:
        self.revealed = True
        self.refresh(repo)

    def _advance(self, repo) -> None:
        self.index += 1
        self.revealed = False
        self.refresh(repo)

