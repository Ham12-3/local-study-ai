from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.card import Card
from studyvault.ui.theme import SPACING


class FlashcardWidget(Card):
    def __init__(self) -> None:
        super().__init__(elevated=True)
        self.question = QLabel("No flashcard selected")
        self.question.setObjectName("SectionTitle")
        self.question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question.setWordWrap(True)
        self.answer = QLabel("")
        self.answer.setObjectName("Muted")
        self.answer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer.setWordWrap(True)
        self.badge = Badge("New", "neutral")
        self.layout().addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.question)
        self.layout().addWidget(self.answer)
        self.setMinimumHeight(260)

    def set_card(self, question: str, answer: str, difficulty: str, revealed: bool) -> None:
        self.question.setText(question)
        self.answer.setText(answer if revealed else "")
        self.badge.setText(difficulty)
        self.badge.set_style("warning" if difficulty.lower() == "hard" else "primary")
        self.layout().setSpacing(SPACING.lg if revealed else SPACING.md)

