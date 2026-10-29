"""
Вкладка «Морфология»: эрозия, дилатация, открытие, закрытие, градиент.

Морфологические операции работают с бинарным изображением, поэтому цепочка из трёх картинок:
    1) оригинал  ->  2) чёрно-белое (порог со вкладки «Серое и бинаризация»)  ->  3) результат операции.
"""
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout)

from core import morphology
from gui.tabs.base import BaseTab
from gui.widgets import ImageView


class MorphTab(BaseTab):
    TITLE = "Морфология"

    def __init__(self, main):
        super().__init__(main)
        self.original_view = ImageView("оригинал")
        self.before_view = ImageView("чёрно-белое")
        self.after_view = ImageView("результат")

        self.operation = QComboBox()
        for title, code in morphology.OPERATIONS.items():
            self.operation.addItem(title, code)
        self.size = QSpinBox()
        self.size.setRange(1, 31)
        self.size.setSingleStep(2)
        self.size.setValue(5)

        self.operation.currentIndexChanged.connect(self.update_view)
        self.size.valueChanged.connect(self.update_view)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Операция:"))
        row1.addWidget(self.operation)
        row1.addWidget(QLabel("Размер ядра:"))
        row1.addWidget(self.size)
        row1.addStretch(1)
        images = QHBoxLayout()
        for title, view in (("1. Оригинал", self.original_view),
                            ("2. Чёрно-белое (из вкладки «Серое и бинаризация»)", self.before_view),
                            ("3. Результат операции", self.after_view)):
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            column.addWidget(view, 1)
            images.addLayout(column)
        self.note = QLabel()
        layout = QVBoxLayout(self)
        layout.addLayout(row1)
        layout.addLayout(images, 1)
        layout.addWidget(self.note)

    def on_image_changed(self):
        self.update_view()

    def showEvent(self, event):
        """При переходе на вкладку берём свежую бинаризацию (её могли поменять на соседней вкладке)."""
        super().showEvent(event)
        self.update_view()

    def update_view(self, *_):
        img = self.main.image
        if img is None:
            return
        binary, _ = self.main.tab_list[3].current_binary()      # бинаризация настраивается на вкладке «Серое и бинаризация»
        kernel = morphology.make_kernel(morphology.KERNEL_SHAPES["Прямоугольник"], self.size.value())
        result = morphology.apply(self.operation.currentData(), binary, kernel)
        self.original_view.set_image(img)
        self.before_view.set_image(binary)
        self.after_view.set_image(result)
        self.note.setText("Белых пикселей: в чёрно-белом — {}, после операции — {}".format(
            int((binary == 255).sum()), int((result == 255).sum())))
