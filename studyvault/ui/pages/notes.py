from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QSpinBox

from studyvault.ui.components.buttons import PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.pages.base import Page


class NotesPage(Page):
    def refresh(self, repo) -> None:
        self.clear()
        setup = Card(elevated=True)
        row = QHBoxLayout()
        selector = QComboBox()
        selector.addItem("Select textbook")
        for textbook in repo.textbooks():
            selector.addItem(textbook.title, textbook.id)
        start = QSpinBox()
        start.setPrefix("From page ")
        start.setRange(1, 9999)
        end = QSpinBox()
        end.setPrefix("To page ")
        end.setRange(1, 9999)
        generate = PrimaryButton("Generate notes")
        generate.setEnabled(bool(repo.textbooks()))
        row.addWidget(selector, 1)
        row.addWidget(start)
        row.addWidget(end)
        row.addWidget(generate)
        setup.layout().addWidget(QLabel("Create notes"))
        setup.layout().addLayout(row)
        self.content.addWidget(setup)

        notes = repo.notes()
        if not notes:
            self.content.addWidget(EmptyState("No notes generated yet", "Generated notes from your textbooks will appear here."))
            return

        body = QHBoxLayout()
        list_card = Card()
        note_list = QListWidget()
        for note in notes:
            note_list.addItem(f"{note.title}\n{note.textbook_title} · {note.page_range}")
        list_card.layout().addWidget(QLabel("Notes"))
        list_card.layout().addWidget(note_list)
        viewer = Card(elevated=True)
        text = QPlainTextEdit(notes[0].body)
        text.setReadOnly(True)
        viewer.layout().addWidget(QLabel(notes[0].title))
        viewer.layout().addWidget(text)
        viewer.layout().addWidget(SecondaryButton("Export"))
        body.addWidget(list_card, 1)
        body.addWidget(viewer, 2)
        self.content.addLayout(body)
