"""
Вкладка «Серое»: перевод в градации серого и линейная / нелинейная коррекция чёрно-белого.
"""
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QVBoxLayout

from core import histogram, tone
from gui.tabs.base import BaseTab
from gui.widgets import HistogramView, ImageView

CORRECTIONS = [
    ("Без коррекции", "none"),
    ("Линейная: растяжение диапазона", "stretch"),
    ("Линейная: негатив", "negative"),
    ("Нелинейная: гамма", "gamma"),
    ("Нелинейная: логарифм", "log"),
    ("Нелинейная: выравнивание гистограммы", "equalize"),
]


class GrayTab(BaseTab):
    TITLE = "Серое"

    def __init__(self, main):
        super().__init__(main)
        self.color_view = ImageView("цветное")
        self.gray_view = ImageView("серое")
        self.result_view = ImageView("после коррекции")
        self.hist = HistogramView()

        self.method = QComboBox()
        for title, code in CORRECTIONS:
            self.method.addItem(title, code)
        self.method.currentIndexChanged.connect(self.update_view)
        self.gamma = QDoubleSpinBox()
        self.gamma.setRange(0.1, 5.0)
        self.gamma.setSingleStep(0.1)
        self.gamma.setValue(0.5)
        self.gamma.valueChanged.connect(self.update_view)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Коррекция серого:"))
        controls.addWidget(self.method)
        controls.addWidget(QLabel("γ (для гаммы):"))
        controls.addWidget(self.gamma)
        controls.addStretch(1)

        images = QHBoxLayout()
        for view in (self.color_view, self.gray_view, self.result_view):
            images.addWidget(view)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(images, 3)
        layout.addWidget(QLabel("Гистограмма серого: линия — до коррекции, столбики — после."))
        layout.addWidget(self.hist, 1)

    def on_image_changed(self):
        self.update_view()

    def update_view(self, *_):
        img = self.main.image
        if img is None:
            return
        gray = tone.to_gray(img)
        code = self.method.currentData()
        if code == "stretch":
            result = tone.linear_stretch(gray)
        elif code == "negative":
            result = tone.negative(gray)
        elif code == "gamma":
            result = tone.gamma_gray(gray, self.gamma.value())
        elif code == "log":
            result = tone.log_transform(gray)
        elif code == "equalize":
            result = tone.equalize(gray)
        else:
            result = gray
        self.color_view.set_image(img)
        self.gray_view.set_image(gray)
        self.result_view.set_image(result)
        self.hist.set_data(histogram.compute_histogram(gray), histogram.compute_histogram(result))
