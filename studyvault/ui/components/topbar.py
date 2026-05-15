from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import SecondaryButton
from studyvault.ui.theme import SPACING


class Topbar(QFrame):
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Topbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        layout.setSpacing(SPACING.md)

        self.title = QLabel("Dashboard")
        self.title.setObjectName("PageTitle")
        self.status = Badge("Checking Ollama", "neutral")
        self.refresh = SecondaryButton("Refresh models")
        self.refresh.clicked.connect(self.refresh_requested.emit)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.status)
        layout.addWidget(self.refresh)

    def set_title(self, title: str) -> None:
        self.title.setText(title)

    def set_ai_status(self, running: bool, count: int = 0) -> None:
        self.status.setText(f"Ollama online · {count} models" if running else "Ollama offline")
        self.status.set_style("success" if running else "error")

