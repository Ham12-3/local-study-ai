from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame

from studyvault.ui.theme import SPACING


class EmptyState(QFrame):
    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message_label = QLabel(message)
        message_label.setObjectName("Muted")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(message_label)

