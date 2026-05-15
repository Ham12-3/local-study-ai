import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThreadPool

from studyvault.ui.main_window import MainWindow
from studyvault.ui.theme import build_stylesheet


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StudyVault AI")
    app.setOrganizationName("StudyVault")
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
    app.aboutToQuit.connect(lambda: QThreadPool.globalInstance().waitForDone(3000))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
