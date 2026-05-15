from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from studyvault.ui.theme import COLORS


class QuizOption(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)

    def set_answer_state(self, state: str | None) -> None:
        if state == "correct":
            border = COLORS.success
            bg = "rgba(52, 211, 153, 0.14)"
        elif state == "wrong":
            border = COLORS.error
            bg = "rgba(248, 113, 113, 0.14)"
        elif self.isChecked():
            border = COLORS.primary
            bg = "rgba(124, 255, 178, 0.12)"
        else:
            self.setStyleSheet("")
            return
        self.setStyleSheet(f"background:{bg}; border-color:{border};")
