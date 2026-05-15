from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SecondaryButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class DangerButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("DangerButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
