"""
Внешний вид приложения: две темы (светлая и тёмная) и общий стиль Qt (QSS — это «CSS для Qt»).

Цвета лежат в словарях LIGHT и DARK. Текущая тема хранится в COLORS: из неё берут цвета и
виджеты, которые рисуют себя сами (гистограмма). Чтобы поменять облик программы, достаточно
исправить цвета здесь.
"""
from string import Template

LIGHT = {
    "bg": "#f3f5f9", "panel": "#ffffff", "border": "#d8dde8", "text": "#1d2330", "muted": "#677086",
    "accent": "#3b6fe0", "accent_hover": "#2f5bc2", "on_accent": "#ffffff", "hover": "#e9effc",
    "view": "#1d2025", "view_text": "#9aa3b2",
    "hist_bg": "#ffffff", "hist_line": "#4b5262", "hist_axis": "#8a93a3",
}
DARK = {
    "bg": "#151820", "panel": "#1e222b", "border": "#333a47", "text": "#e5e8ee", "muted": "#9aa3b2",
    "accent": "#6c94f2", "accent_hover": "#88a8f6", "on_accent": "#0b0d12", "hover": "#283044",
    "view": "#0e1014", "view_text": "#7d8697",
    "hist_bg": "#1e222b", "hist_line": "#cfd4de", "hist_axis": "#7d8697",
}

COLORS = dict(LIGHT)        # текущая тема

_QSS = Template("""
* { font-family: "Segoe UI", "SF Pro Text", "Noto Sans", "Helvetica Neue", Arial, sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: $bg; color: $text; }
QLabel { background: transparent; }
QLabel#imageView { background: $view; color: $view_text; border: 1px solid $border; border-radius: 10px; font-size: 14px; }

QToolBar { background: $panel; border: none; border-bottom: 1px solid $border; padding: 6px 10px; spacing: 8px; }
QToolButton { background: $panel; color: $text; border: 1px solid $border; border-radius: 7px; padding: 6px 14px; }
QToolButton:hover { background: $hover; border-color: $accent; }
QToolButton::menu-indicator { subcontrol-position: right center; right: 6px; }

QPushButton { background: $accent; color: $on_accent; border: none; border-radius: 7px; padding: 7px 16px; font-weight: 600; }
QPushButton:hover { background: $accent_hover; }
QPushButton:disabled { background: $border; color: $muted; }

QTabWidget::pane { border: 1px solid $border; border-radius: 10px; background: $bg; top: -1px; }
QTabBar::tab { background: transparent; color: $muted; padding: 10px 16px; margin-right: 2px; border-bottom: 3px solid transparent; }
QTabBar::tab:selected { color: $accent; border-bottom: 3px solid $accent; font-weight: 600; }
QTabBar::tab:hover:!selected { color: $text; }

QGroupBox { background: $panel; border: 1px solid $border; border-radius: 10px; margin-top: 14px; padding: 14px 10px 8px 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: $muted; }

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit {
    background: $panel; color: $text; border: 1px solid $border; border-radius: 7px; padding: 5px 9px;
    selection-background-color: $accent; selection-color: $on_accent; }
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover { border-color: $accent; }
QComboBox QAbstractItemView { background: $panel; color: $text; border: 1px solid $border; selection-background-color: $accent; selection-color: $on_accent; }

QSlider::groove:horizontal { height: 6px; background: $border; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 3px; }
QSlider::handle:horizontal { background: $panel; border: 2px solid $accent; width: 14px; height: 14px; margin: -6px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: $hover; }

QCheckBox { spacing: 8px; background: transparent; }

QTableWidget { background: $panel; border: 1px solid $border; border-radius: 10px; gridline-color: $border; }
QHeaderView::section { background: $bg; color: $muted; border: none; border-bottom: 1px solid $border; padding: 7px; }

QMenu { background: $panel; color: $text; border: 1px solid $border; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 22px; border-radius: 5px; }
QMenu::item:selected { background: $accent; color: $on_accent; }

QStatusBar { background: $panel; color: $muted; border-top: 1px solid $border; }
QToolTip { background: $panel; color: $text; border: 1px solid $border; padding: 4px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""")


def stylesheet(colors):
    """Готовый текст стиля для заданной темы."""
    return _QSS.substitute(colors)


def apply(app, dark=False):
    """Включить тему: запомнить цвета и применить стиль ко всему приложению."""
    COLORS.clear()
    COLORS.update(DARK if dark else LIGHT)
    app.setStyleSheet(stylesheet(COLORS))
