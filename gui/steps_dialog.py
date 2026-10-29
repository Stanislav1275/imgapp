"""Окно с несколькими картинками подряд — например, шаги алгоритма Canny (3 столбца)."""
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout

from gui.widgets import ImageView


class StepsDialog(QDialog):
    def __init__(self, parent, title, pictures, hint=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1100, 720)
        grid = QGridLayout()
        for k, (caption, picture) in enumerate(pictures):
            view = ImageView(caption)
            view.set_image(picture)
            grid.addWidget(view, (k // 3) * 2, k % 3)
            grid.addWidget(QLabel(caption), (k // 3) * 2 + 1, k % 3)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)
        layout = QVBoxLayout(self)
        if hint:
            layout.addWidget(QLabel(hint))
        layout.addLayout(grid, 1)
        layout.addWidget(close_button)
