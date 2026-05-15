from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    background: str = "#0B0F14"
    surface: str = "#111827"
    surface_elevated: str = "#162033"
    surface_hover: str = "#1B2940"
    border: str = "#243044"
    border_focus: str = "#7CFFB2"
    primary: str = "#7CFFB2"
    primary_muted: str = "#1F8A5B"
    text_main: str = "#F8FAFC"
    text_muted: str = "#94A3B8"
    text_dim: str = "#64748B"
    warning: str = "#FBBF24"
    error: str = "#F87171"
    success: str = "#34D399"
    shadow: str = "#05080C"


@dataclass(frozen=True)
class Spacing:
    xs: int = 6
    sm: int = 10
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 44


@dataclass(frozen=True)
class Radius:
    sm: int = 8
    md: int = 12
    lg: int = 18
    xl: int = 24


@dataclass(frozen=True)
class Typography:
    family: str = "Segoe UI"
    page_title: int = 24
    section_title: int = 18
    body: int = 14
    small: int = 12


COLORS = Colors()
SPACING = Spacing()
RADIUS = Radius()
TYPOGRAPHY = Typography()


def build_stylesheet() -> str:
    c = COLORS
    r = RADIUS
    t = TYPOGRAPHY
    return f"""
    * {{
        font-family: "{t.family}";
        font-size: {t.body}px;
        color: {c.text_main};
        outline: none;
    }}

    QMainWindow, QWidget#AppRoot {{
        background: {c.background};
    }}

    QFrame#Sidebar {{
        background: {c.surface};
        border-right: 1px solid {c.border};
    }}

    QLabel#AppName {{
        font-size: 19px;
        font-weight: 700;
        color: {c.text_main};
    }}

    QLabel#PageTitle {{
        font-size: {t.page_title}px;
        font-weight: 700;
        color: {c.text_main};
    }}

    QLabel#SectionTitle {{
        font-size: {t.section_title}px;
        font-weight: 650;
        color: {c.text_main};
    }}

    QLabel#Muted, QLabel#SmallMuted {{
        color: {c.text_muted};
    }}

    QLabel#SmallMuted {{
        font-size: {t.small}px;
    }}

    QFrame#Topbar {{
        background: {c.background};
        border-bottom: 1px solid {c.border};
    }}

    QFrame#Card, QFrame#UploadCard, QFrame#ChatBubble, QFrame#EmptyState {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: {r.lg}px;
    }}

    QFrame#ElevatedCard {{
        background: {c.surface_elevated};
        border: 1px solid {c.border};
        border-radius: {r.lg}px;
    }}

    QFrame#UploadDropzone {{
        background: {c.surface_elevated};
        border: 1px dashed {c.primary_muted};
        border-radius: {r.xl}px;
    }}

    QPushButton {{
        background: {c.surface_elevated};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 10px 14px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {c.surface_hover};
        border-color: {c.primary_muted};
    }}

    QPushButton:pressed {{
        background: {c.primary_muted};
    }}

    QPushButton:disabled {{
        color: {c.text_dim};
        background: #0E1522;
        border-color: #172033;
    }}

    QPushButton#PrimaryButton {{
        background: {c.primary};
        color: #07100B;
        border-color: {c.primary};
    }}

    QPushButton#PrimaryButton:hover {{
        background: #A4FFC8;
    }}

    QPushButton#DangerButton {{
        color: {c.error};
        border-color: rgba(248, 113, 113, 0.45);
    }}

    QPushButton#SidebarButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: {r.md}px;
        padding: 11px 12px;
        text-align: left;
        color: {c.text_muted};
        font-weight: 600;
    }}

    QPushButton#SidebarButton:hover {{
        background: {c.surface_elevated};
        color: {c.text_main};
    }}

    QPushButton#SidebarButton[active="true"] {{
        background: rgba(124, 255, 178, 0.12);
        border-color: rgba(124, 255, 178, 0.34);
        color: {c.primary};
    }}

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 9px 11px;
        selection-background-color: {c.primary_muted};
    }}

    QTextEdit, QPlainTextEdit {{
        padding: 12px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {c.border_focus};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}

    QListWidget {{
        background: transparent;
        border: none;
    }}

    QListWidget::item {{
        background: {c.surface};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        margin: 5px 0;
        padding: 10px;
    }}

    QListWidget::item:selected {{
        background: {c.surface_elevated};
        border-color: {c.primary_muted};
    }}

    QScrollArea, QScrollArea QWidget, QScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}

    QScrollArea > QWidget {{
        background: {c.background};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {c.border};
        border-radius: 5px;
        min-height: 36px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c.text_dim};
    }}

    QProgressBar {{
        background: #0E1522;
        border: 1px solid {c.border};
        border-radius: 7px;
        height: 12px;
        text-align: center;
        color: transparent;
    }}

    QProgressBar::chunk {{
        background: {c.primary};
        border-radius: 6px;
    }}

    QStatusBar {{
        background: {c.surface};
        border-top: 1px solid {c.border};
    }}

    QMessageBox {{
        background: {c.surface};
    }}
    """
