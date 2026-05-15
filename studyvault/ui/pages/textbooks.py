from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QVBoxLayout

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.components.progress import SlimProgress
from studyvault.ui.pages.base import Page
from studyvault.ui.theme import SPACING


class DropZone(QFrame):
    clicked = Signal()
    file_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("UploadDropzone")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Drop a textbook PDF here")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("or browse your local files")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button = PrimaryButton("Choose PDF")
        button.clicked.connect(self.clicked.emit)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(220)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.file_dropped.emit(path)


class TextbooksPage(Page):
    upload_requested = Signal(str)
    rebuild_requested = Signal(int)
    delete_requested = Signal(int)

    def refresh(self, repo) -> None:
        self.clear()
        upload = Card(elevated=True)
        title = QLabel("Import textbooks")
        title.setObjectName("SectionTitle")
        drop = DropZone()
        drop.clicked.connect(self._choose_file)
        drop.file_dropped.connect(self.upload_requested.emit)
        self.import_progress = SlimProgress()
        upload.layout().addWidget(title)
        upload.layout().addWidget(drop)
        upload.layout().addWidget(self.import_progress)
        self.content.addWidget(upload)

        section = QLabel("Textbook library")
        section.setObjectName("SectionTitle")
        self.content.addWidget(section)

        textbooks = repo.textbooks()
        if not textbooks:
            self.content.addWidget(EmptyState("No textbooks yet", "Uploaded textbooks will appear as clean cards with import and embedding status."))
            return
        for textbook in textbooks:
            self.content.addWidget(self._textbook_card(textbook))

    def _textbook_card(self, textbook):
        card = Card()
        header = QHBoxLayout()
        title = QLabel(textbook.title)
        title.setObjectName("SectionTitle")
        status = Badge(textbook.embedding_status, "success" if "indexed" in textbook.embedding_status.lower() else "warning")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(status)
        card.layout().addLayout(header)
        meta = QLabel(
            f"{textbook.page_count} pages - {textbook.chunk_count} chunks - Last opened: "
            f"{textbook.last_opened_at or 'Never'}"
        )
        meta.setObjectName("Muted")
        meta.setWordWrap(True)
        path = QLabel(str(Path(textbook.file_path)))
        path.setObjectName("SmallMuted")
        path.setWordWrap(True)
        actions = QHBoxLayout()
        actions.addWidget(SecondaryButton("Open"))
        rebuild = SecondaryButton("Rebuild index")
        rebuild.clicked.connect(lambda checked=False, textbook_id=textbook.id: self.rebuild_requested.emit(textbook_id))
        actions.addWidget(rebuild)
        delete = DangerButton("Delete")
        delete.clicked.connect(lambda checked=False, textbook_id=textbook.id, title=textbook.title: self._confirm_delete(textbook_id, title))
        actions.addWidget(delete)
        actions.addStretch()
        card.layout().addWidget(meta)
        card.layout().addWidget(path)
        card.layout().addLayout(actions)
        return card

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import textbook", "", "PDF files (*.pdf);;All files (*.*)")
        if path:
            self.upload_requested.emit(path)

    def set_import_progress(self, value: int) -> None:
        self.import_progress.setValue(value)

    def _confirm_delete(self, textbook_id: int, title: str) -> None:
        result = QMessageBox.question(
            self,
            "Delete textbook",
            f"Delete '{title}' and its local notes, flashcards, quiz attempts, weak topics, and retrieval index?",
        )
        if result == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(textbook_id)
