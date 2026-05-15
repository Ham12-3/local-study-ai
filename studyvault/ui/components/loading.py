from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class LoadingState(QWidget):
    def __init__(self, text: str = "Loading") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(text)
        label.setObjectName("Muted")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setFixedWidth(220)
        layout.addWidget(label)
        layout.addWidget(bar)

