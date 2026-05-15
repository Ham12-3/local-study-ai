from PySide6.QtWidgets import QLabel

from studyvault.ui.theme import COLORS


class Badge(QLabel):
    def __init__(self, text: str, tone: str = "neutral") -> None:
        super().__init__(text)
        self.set_style(tone)

    def set_style(self, tone: str) -> None:
        colors = {
            "success": (COLORS.success, "rgba(52, 211, 153, 0.13)"),
            "warning": (COLORS.warning, "rgba(251, 191, 36, 0.13)"),
            "error": (COLORS.error, "rgba(248, 113, 113, 0.13)"),
            "primary": (COLORS.primary, "rgba(124, 255, 178, 0.13)"),
            "neutral": (COLORS.text_muted, "rgba(148, 163, 184, 0.10)"),
        }
        fg, bg = colors.get(tone, colors["neutral"])
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border:1px solid {fg}; "
            "border-radius:10px; padding:4px 8px; font-size:12px; font-weight:700;"
        )

