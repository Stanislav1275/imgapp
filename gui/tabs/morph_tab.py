"""
Вкладка «Морфология»: эрозия, дилатация, открытие, закрытие, градиент.

Морфологические операции работают с чёрно-белым изображением, поэтому перед операцией
картинка автоматически бинаризуется методом Оцу. Вкладка показывает только две картинки:
исходное и результат.
"""
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout

from core import binarize, morphology, tone
from gui.tabs.base import BaseTab
from gui.widgets import ImageView


class MorphTab(BaseTab):
    TITLE = "Морфология"

    def __init__(self, main):
        super().__init__(main)
        self.original_view = ImageView("исходное")
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

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Операция:"))
        controls.addWidget(self.operation)
        controls.addWidget(QLabel("Размер ядра:"))
        controls.addWidget(self.size)
        controls.addStretch(1)

        images = QHBoxLayout()
        images.addWidget(self.original_view)
        images.addWidget(self.after_view)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(images, 1)
        layout.addWidget(QLabel("Перед операцией изображение переводится в чёрно-белое (порог по Оцу)."))

    def on_image_changed(self):
        self.update_view()

    def update_view(self, *_):
        img = self.main.image
        if img is None:
            return
        binary, _ = binarize.otsu(tone.to_gray(img))
        kernel = morphology.make_kernel(morphology.KERNEL_SHAPES["Прямоугольник"], self.size.value())
        self.original_view.set_image(img)
        self.after_view.set_image(morphology.apply(self.operation.currentData(), binary, kernel))
