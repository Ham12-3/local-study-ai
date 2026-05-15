from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout

from studyvault.ui.components.buttons import PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.components.quiz_option import QuizOption
from studyvault.ui.pages.base import Page


class QuizPage(Page):
    def refresh(self, repo) -> None:
        self.clear()
        setup = Card(elevated=True)
        title = QLabel("Quiz setup")
        title.setObjectName("SectionTitle")
        row = QHBoxLayout()
        selector = QComboBox()
        selector.addItem("Select textbook")
        for textbook in repo.textbooks():
            selector.addItem(textbook.title, textbook.id)
        count = QSpinBox()
        count.setRange(3, 50)
        count.setValue(10)
        count.setPrefix("Questions ")
        start = PrimaryButton("Start quiz")
        start.setEnabled(bool(repo.textbooks()))
        row.addWidget(selector, 1)
        row.addWidget(count)
        row.addWidget(start)
        setup.layout().addWidget(title)
        setup.layout().addLayout(row)
        self.content.addWidget(setup)

        if not repo.textbooks():
            self.content.addWidget(EmptyState("No quiz source", "Import a textbook before generating a grounded quiz."))
            return

        question = Card()
        qtitle = QLabel("Question card")
        qtitle.setObjectName("SectionTitle")
        muted = QLabel("Generated questions from the selected textbook will appear here.")
        muted.setObjectName("Muted")
        muted.setWordWrap(True)
        options = QVBoxLayout()
        for label in ["Option A", "Option B", "Option C", "Option D"]:
            option = QuizOption(label)
            option.setEnabled(False)
            options.addWidget(option)
        explanation = Card(elevated=True)
        explanation.layout().addWidget(QLabel("Explanation panel"))
        message = QLabel("After answering, explanations and weak topic updates appear here.")
        message.setObjectName("Muted")
        message.setWordWrap(True)
        explanation.layout().addWidget(message)
        question.layout().addWidget(qtitle)
        question.layout().addWidget(muted)
        question.layout().addLayout(options)
        question.layout().addWidget(SecondaryButton("Next"))
        question.layout().addWidget(explanation)
        self.content.addWidget(question)
