"""
Внешний вид приложения: две темы (светлая и тёмная) и общий стиль Qt (QSS — это «CSS для Qt»).

Цвета лежат в словарях LIGHT и DARK. Текущая тема хранится в COLORS: из неё берут цвета и
виджеты, которые рисуют себя сами (гистограмма). Чтобы поменять облик программы, достаточно
исправить цвета здесь.
"""
from string import Template

LIGHT = {
    "bg": "#f7f6f4", "panel": "#ffffff", "border": "#e6e3df", "text": "#1c1b1a", "muted": "#8a857f",
    "accent": "#4c5fd5", "accent_hover": "#3d4fc0", "on_accent": "#ffffff", "hover": "#efede9",
    "view": "#efede9", "view_text": "#a29d96",
    "hist_bg": "#ffffff", "hist_line": "#3b3835", "hist_axis": "#a29d96",
}
DARK = {
    "bg": "#121214", "panel": "#1a1a1d", "border": "#2b2b30", "text": "#ececef", "muted": "#8d8d96",
    "accent": "#8b9cff", "accent_hover": "#a5b1ff", "on_accent": "#0d0d14", "hover": "#232328",
    "view": "#0d0d0f", "view_text": "#6c6c75",
    "hist_bg": "#1a1a1d", "hist_line": "#d8d8de", "hist_axis": "#6c6c75",
}

COLORS = dict(LIGHT)        # текущая тема

# Принцип оформления: один акцентный цвет, тонкие линии вместо рамок, много воздуха, скруглённые углы.
_QSS = Template("""
* { font-family: "Inter", "Segoe UI", "SF Pro Text", "Noto Sans", "Helvetica Neue", Arial, sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: $bg; color: $text; }
QLabel { background: transparent; }
QLabel#imageView { background: $view; color: $view_text; border: 1px solid $border; border-radius: 14px; font-size: 14px; }
QLabel#imageView[empty="true"] { border: 1px dashed $view_text; }
QLabel#appTitle { font-size: 15px; font-weight: 600; letter-spacing: 0.3px; padding: 0 6px; }
QLabel#pixelInfo { color: $muted; font-family: "JetBrains Mono", "SF Mono", "Consolas", monospace; font-size: 12px; }

QToolBar { background: $bg; border: none; padding: 12px 20px 4px 20px; spacing: 6px; }
QToolBar QToolButton { background: transparent; color: $muted; border: 1px solid transparent; border-radius: 9px; padding: 7px 14px; }
QToolBar QToolButton:hover { background: $hover; color: $text; }
QToolBar QToolButton#primary { background: $accent; color: $on_accent; font-weight: 600; }
QToolBar QToolButton#primary:hover { background: $accent_hover; }
QToolButton::menu-indicator { image: none; width: 0; }

QPushButton { background: $accent; color: $on_accent; border: none; border-radius: 9px; padding: 8px 18px; font-weight: 600; }
QPushButton:hover { background: $accent_hover; }
QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
QPushButton:disabled { background: $hover; color: $muted; }

QTabWidget::pane { border: none; border-top: 1px solid $border; background: $bg; top: 0px; }
QTabBar { background: $bg; qproperty-drawBase: 0; }
QTabBar::tab { background: transparent; color: $muted; padding: 10px 14px; margin: 0 6px 0 0; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: $text; border-bottom: 2px solid $accent; font-weight: 600; }
QTabBar::tab:hover:!selected { color: $text; }

QGroupBox { background: $panel; border: 1px solid $border; border-radius: 14px; margin-top: 16px; padding: 18px 14px 12px 14px; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; color: $muted; font-size: 12px; }

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit {
    background: $panel; color: $text; border: 1px solid $border; border-radius: 9px; padding: 6px 10px;
    selection-background-color: $accent; selection-color: $on_accent; }
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover { border-color: $muted; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QPlainTextEdit:focus { border-color: $accent; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: $panel; color: $text; border: 1px solid $border; border-radius: 8px; padding: 4px;
    selection-background-color: $hover; selection-color: $text; outline: none; }
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0; border: none; }

QSlider::groove:horizontal { height: 4px; background: $border; border-radius: 2px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 2px; }
QSlider::handle:horizontal { background: $panel; border: 2px solid $accent; width: 14px; height: 14px; margin: -7px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: $accent; }

QCheckBox { spacing: 8px; background: transparent; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid $muted; border-radius: 5px; background: $panel; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; }

QTableWidget { background: $panel; border: 1px solid $border; border-radius: 14px; gridline-color: $border; outline: none; padding: 4px; }
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background: $hover; color: $text; }
QHeaderView::section { background: transparent; color: $muted; border: none; border-bottom: 1px solid $border; padding: 8px; font-size: 12px; }

QMenu { background: $panel; color: $text; border: 1px solid $border; border-radius: 12px; padding: 6px; }
QMenu::item { padding: 8px 22px; border-radius: 7px; }
QMenu::item:selected { background: $hover; color: $text; }

QStatusBar { background: $bg; color: $muted; border-top: 1px solid $border; padding: 2px 12px; }
QStatusBar::item { border: none; }
QToolTip { background: $panel; color: $text; border: 1px solid $border; border-radius: 6px; padding: 5px 8px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: $muted; }
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
