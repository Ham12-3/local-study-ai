from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.components.loading import LoadingState
from studyvault.ui.theme import SPACING


class Page(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.container = QWidget()
        self.content = QVBoxLayout(self.container)
        self.content.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        self.content.setSpacing(SPACING.lg)
        self.content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.container)

    def clear(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_loading(self, message: str = "Loading local data") -> None:
        self.clear()
        self.content.addWidget(LoadingState(message))

    def show_empty(self, title: str, message: str) -> None:
        self.clear()
        self.content.addWidget(EmptyState(title, message))

    def show_error(self, title: str, message: str) -> None:
        self.clear()
        state = EmptyState(title, message)
        state.setStyleSheet("border-color:#F87171;")
        self.content.addWidget(state)

    def show_success(self, title: str, message: str) -> None:
        self.clear()
        state = EmptyState(title, message)
        state.setStyleSheet("border-color:#34D399;")
        self.content.addWidget(state)
