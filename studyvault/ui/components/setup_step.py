from PySide6.QtWidgets import QHBoxLayout, QLabel, QFrame

from studyvault.ui.components.badges import Badge
from studyvault.ui.theme import SPACING


class SetupStep(QFrame):
    def __init__(self, title: str, detail: str, state: str = "pending") -> None:
        super().__init__()
        self.setObjectName("Card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.md)
        text = QLabel(f"{title}\n{detail}")
        text.setObjectName("Muted")
        text.setWordWrap(True)
        self.badge = Badge(self._label(state), self._tone(state))
        layout.addWidget(text, 1)
        layout.addWidget(self.badge)

    def set_state(self, state: str) -> None:
        self.badge.setText(self._label(state))
        self.badge.set_style(self._tone(state))

    @staticmethod
    def _label(state: str) -> str:
        return {
            "done": "Done",
            "active": "Working",
            "error": "Needs attention",
            "pending": "Pending",
        }.get(state, "Pending")

    @staticmethod
    def _tone(state: str) -> str:
        return {
            "done": "success",
            "active": "primary",
            "error": "error",
            "pending": "neutral",
        }.get(state, "neutral")
