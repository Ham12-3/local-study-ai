from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from studyvault.ui.theme import SPACING


class Sidebar(QFrame):
    page_selected = Signal(str)

    PAGES = [
        ("dashboard", "◈", "Dashboard"),
        ("textbooks", "▣", "Textbooks"),
        ("ask_ai", "✦", "Ask AI"),
        ("notes", "□", "Notes"),
        ("flashcards", "◇", "Flashcards"),
        ("quiz", "◎", "Quiz"),
        ("weak_topics", "△", "Weak Topics"),
        ("settings", "⚙", "Settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(248)
        self.buttons: dict[str, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.sm)

        brand = QLabel("StudyVault AI")
        brand.setObjectName("AppName")
        layout.addWidget(brand)

        sub = QLabel("Local study intelligence")
        sub.setObjectName("SmallMuted")
        layout.addWidget(sub)
        layout.addSpacing(SPACING.lg)

        for key, icon, label in self.PAGES:
            button = QPushButton(f"{icon}  {label}")
            button.setObjectName("SidebarButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=key: self.page_selected.emit(page))
            self.buttons[key] = button
            layout.addWidget(button)

        layout.addStretch()
        self.status = QLabel("● Local AI checking")
        self.status.setObjectName("SmallMuted")
        layout.addWidget(self.status)

    def set_active(self, page: str) -> None:
        for key, button in self.buttons.items():
            button.setProperty("active", key == page)
            button.style().unpolish(button)
            button.style().polish(button)

    def set_ai_status(self, running: bool, model_count: int = 0) -> None:
        if running:
            self.status.setText(f"● Local AI online · {model_count} models")
            self.status.setStyleSheet("color:#34D399;")
        else:
            self.status.setText("● Local AI offline")
            self.status.setStyleSheet("color:#F87171;")
