"""
Вкладка «Морфология»: эрозия, дилатация, открытие, закрытие, градиент.

Морфологические операции работают с бинарным изображением, поэтому сначала
серое изображение превращается в чёрно-белое (порогом или методом Оцу).
"""
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout)

from core import binarize, morphology, tone
from gui.tabs.base import BaseTab, make_slider
from gui.widgets import ImageView


class MorphTab(BaseTab):
    TITLE = "Морфология"

    def __init__(self, main):
        super().__init__(main)
        self.before_view = ImageView("бинарное изображение")
        self.after_view = ImageView("результат")

        self.operation = QComboBox()
        for title, code in morphology.OPERATIONS.items():
            self.operation.addItem(title, code)
        self.shape = QComboBox()
        for title, code in morphology.KERNEL_SHAPES.items():
            self.shape.addItem(title, code)
        self.size = QSpinBox()
        self.size.setRange(1, 31)
        self.size.setSingleStep(2)
        self.size.setValue(5)
        self.iterations = QSpinBox()
        self.iterations.setRange(1, 10)
        self.otsu = QCheckBox("Порог по Оцу (авто)")
        self.otsu.setToolTip("Включено: порог подбирается сам. Подвиньте ползунок — включится ручной порог.")
        self.otsu.setChecked(True)
        self.threshold = make_slider(0, 255, 128, self.on_slider)
        self.threshold_label = QLabel("T = 128")
        self.invert = QCheckBox("Инвертировать (объекты — тёмные)")

        for widget in (self.operation, self.shape):
            widget.currentIndexChanged.connect(self.update_view)
        for widget in (self.size, self.iterations):
            widget.valueChanged.connect(self.update_view)
        self.otsu.toggled.connect(self.update_view)
        self.invert.toggled.connect(self.update_view)

        row1 = QHBoxLayout()
        for text, widget in (("Операция:", self.operation), ("Ядро:", self.shape),
                             ("Размер:", self.size), ("Повторов:", self.iterations)):
            row1.addWidget(QLabel(text))
            row1.addWidget(widget)
        row1.addStretch(1)
        row2 = QHBoxLayout()
        row2.addWidget(self.otsu)
        row2.addWidget(self.threshold, 1)
        row2.addWidget(self.threshold_label)
        row2.addWidget(self.invert)

        images = QHBoxLayout()
        images.addWidget(self.before_view)
        images.addWidget(self.after_view)
        self.note = QLabel()
        layout = QVBoxLayout(self)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(images, 1)
        layout.addWidget(self.note)

    def on_slider(self, *_):
        """Пользователь двигает ползунок руками: значит, нужен ручной порог, и «Порог по Оцу» выключаем."""
        if self.otsu.isChecked():
            self.otsu.blockSignals(True)
            self.otsu.setChecked(False)
            self.otsu.blockSignals(False)
        self.update_view()

    def on_image_changed(self):
        self.update_view()

    def update_view(self, *_):
        img = self.main.image
        if img is None:
            return
        gray = tone.to_gray(img)
        if self.otsu.isChecked():
            binary, T = binarize.otsu(gray)
            self.threshold.blockSignals(True)       # показать найденный порог на ползунке, не вызывая пересчёт
            self.threshold.setValue(T)
            self.threshold.blockSignals(False)
        else:
            T = self.threshold.value()
            binary = binarize.threshold(gray, T)
        self.threshold_label.setText("T = {}".format(T))
        if self.invert.isChecked():
            binary = 255 - binary
        kernel = morphology.make_kernel(self.shape.currentData(), self.size.value())
        result = morphology.apply(self.operation.currentData(), binary, kernel, self.iterations.value())
        self.before_view.set_image(binary)
        self.after_view.set_image(result)
        self.note.setText("Белых пикселей: до — {}, после — {}".format(int((binary == 255).sum()),
                                                                       int((result == 255).sum())))
