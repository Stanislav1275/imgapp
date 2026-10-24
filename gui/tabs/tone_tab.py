"""
Вкладка «Яркость и цвет»: яркость, контраст, гамма, насыщенность + гистограмма ДО и ПОСЛЕ.

Ползунки переводятся в числа формул функцией tone.slider_to_params
(β = 2.55 * ползунок, α = 1 + ползунок / 100, γ = ползунок / 100, k = ползунок / 100).
"""
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core import histogram, tone
from gui.tabs.base import BaseTab, make_slider
from gui.widgets import HistogramView, ImageView

CHANNEL_COLORS = {"y": (220, 70, 70), "r": (220, 40, 40), "g": (40, 170, 70), "b": (50, 90, 230)}


class ToneTab(BaseTab):
    TITLE = "Яркость и цвет"

    def __init__(self, main):
        super().__init__(main)
        self.before_view = ImageView("до")
        self.after_view = ImageView("после")
        self.hist = HistogramView()

        self.brightness = make_slider(-100, 100, 0, self.update_view)
        self.contrast = make_slider(-100, 100, 0, self.update_view)
        self.gamma = make_slider(20, 300, 100, self.update_view)
        self.saturation = make_slider(0, 200, 100, self.update_view)
        self.labels = [QLabel() for _ in range(4)]

        controls = QGroupBox("Параметры")
        grid = QGridLayout(controls)
        names = ["Яркость", "Контраст", "Гамма", "Насыщенность"]
        for row, (name, slider, label) in enumerate(zip(
                names, [self.brightness, self.contrast, self.gamma, self.saturation], self.labels)):
            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(slider, row, 1)
            grid.addWidget(label, row, 2)
        grid.setColumnStretch(1, 1)

        self.channel = QComboBox()
        for title, code in (("Яркость", "y"), ("Канал R", "r"), ("Канал G", "g"), ("Канал B", "b")):
            self.channel.addItem(title, code)
        self.channel.currentIndexChanged.connect(self.update_view)
        reset = QPushButton("Сбросить")
        reset.clicked.connect(self.reset)
        row = QHBoxLayout()
        row.addWidget(QLabel("Гистограмма:"))
        row.addWidget(self.channel)
        row.addStretch(1)
        row.addWidget(reset)

        images = QHBoxLayout()
        images.addWidget(self.before_view)
        images.addWidget(self.after_view)
        layout = QVBoxLayout(self)
        layout.addWidget(controls)
        layout.addLayout(images, 3)
        layout.addLayout(row)
        layout.addWidget(QLabel("Серая линия — гистограмма до, цветные столбики — после. "
                                "Шкала по вертикали задана гистограммой «до»."))
        layout.addWidget(self.hist, 1)
        self.update_labels()

    def reset(self):
        self.brightness.setValue(0)
        self.contrast.setValue(0)
        self.gamma.setValue(100)
        self.saturation.setValue(100)

    def params(self):
        return tone.slider_to_params(self.brightness.value(), self.contrast.value(),
                                     self.gamma.value(), self.saturation.value())

    def update_labels(self):
        beta, alpha, gamma, k = self.params()
        self.labels[0].setText("β = {:.0f}".format(beta))
        self.labels[1].setText("α = {:.2f}".format(alpha))
        self.labels[2].setText("γ = {:.2f}".format(gamma))
        self.labels[3].setText("k = {:.2f}".format(k))

    def update_view(self, *_):
        self.update_labels()
        img = self.main.image
        if img is None:
            return
        beta, alpha, gamma, k = self.params()
        result = tone.adjust_all(img, beta, alpha, gamma, k)
        self.before_view.set_image(img)
        self.after_view.set_image(result)
        code = self.channel.currentData()
        self.hist.set_data(histogram.compute_histogram(img, code),
                           histogram.compute_histogram(result, code), CHANNEL_COLORS[code])

    def on_image_changed(self):
        self.update_view()
