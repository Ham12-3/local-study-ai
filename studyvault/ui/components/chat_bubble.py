from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from studyvault.ui.components.badges import Badge
from studyvault.ui.theme import COLORS, SPACING


class ChatBubble(QFrame):
    def __init__(self, role: str, message: str, source_pages: list[int] | None = None) -> None:
        super().__init__()
        self.setObjectName("ChatBubble")
        self.setMaximumWidth(720)
        self.setStyleSheet(
            f"QFrame#ChatBubble {{ background: {'#132030' if role == 'assistant' else COLORS.surface_elevated};"
            f" border: 1px solid {COLORS.border}; border-radius: 18px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)

        if source_pages:
            chips = QHBoxLayout()
            chips.setSpacing(SPACING.xs)
            for page in source_pages:
                chips.addWidget(Badge(f"p. {page}", "primary"))
            chips.addStretch()
            layout.addLayout(chips)

