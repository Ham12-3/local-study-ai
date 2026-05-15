from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout
from PySide6.QtGui import QColor

from studyvault.ui.theme import COLORS, SPACING


class Card(QFrame):
    def __init__(self, elevated: bool = False, shadow: bool = True) -> None:
        super().__init__()
        self.setObjectName("ElevatedCard" if elevated else "Card")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)
        if shadow:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(28)
            effect.setOffset(0, 12)
            effect.setColor(QColor(COLORS.shadow))
            self.setGraphicsEffect(effect)
