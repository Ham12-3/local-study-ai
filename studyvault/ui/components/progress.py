from PySide6.QtWidgets import QProgressBar


class SlimProgress(QProgressBar):
    def __init__(self, value: int = 0) -> None:
        super().__init__()
        self.setRange(0, 100)
        self.setValue(value)
        self.setTextVisible(False)

