"""
Вкладка «Серое»: перевод в градации серого, линейная / нелинейная коррекция и бинаризация
(порог вручную или по Оцу). Бинарное изображение отсюда берёт вкладка «Морфология».
"""
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core import binarize, histogram, tone
from gui.tabs.base import BaseTab, make_slider
from gui.widgets import HistogramView, ImageView

CORRECTIONS = [
    ("Без коррекции", "none"),
    ("Линейная: растяжение диапазона", "stretch"),
    ("Линейная: негатив", "negative"),
    ("Нелинейная: гамма", "gamma"),
    ("Нелинейная: логарифм", "log"),
    ("Нелинейная: выравнивание гистограммы", "equalize"),
    ("Бинаризация: порог или Оцу", "binary"),
]


class GrayTab(BaseTab):
    TITLE = "Серое и бинаризация"

    def __init__(self, main):
        super().__init__(main)
        self.color_view = ImageView("исходное")
        self.result_view = ImageView("результат")
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
        controls.addWidget(QLabel("Преобразование серого:"))
        controls.addWidget(self.method)
        self.gamma_label = QLabel("γ:")
        controls.addWidget(self.gamma_label)
        controls.addWidget(self.gamma)
        controls.addStretch(1)

        self.otsu = QCheckBox("Порог подобрать само (Оцу)")
        self.otsu.setChecked(True)
        self.otsu.toggled.connect(self.update_view)
        self.threshold = make_slider(0, 255, 128, self.on_slider)
        self.threshold_label = QLabel("T = 128")
        binarization = QHBoxLayout()                  # эта строка видна только при методе «Бинаризация»
        binarization.addWidget(self.otsu)
        binarization.addWidget(self.threshold, 1)
        binarization.addWidget(self.threshold_label)
        self.binarization_row = QWidget()
        self.binarization_row.setLayout(binarization)
        binarization.setContentsMargins(0, 0, 0, 0)

        images = QHBoxLayout()
        for view in (self.color_view, self.result_view):
            images.addWidget(view)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.binarization_row)
        layout.addLayout(images, 3)
        layout.addWidget(QLabel("Гистограмма серого: линия — до коррекции, столбики — после."))
        layout.addWidget(self.hist, 1)

    def on_slider(self, *_):
        """Ползунок двигают руками: порог ручной, галочку «Оцу» снимаем."""
        if self.otsu.isChecked():
            self.otsu.blockSignals(True)
            self.otsu.setChecked(False)
            self.otsu.blockSignals(False)
        self.update_view()

    def current_binary(self):
        """Чёрно-белое изображение (0/255) и порог T по текущим настройкам. Нет картинки -> (None, None)."""
        if self.main.image is None:
            return None, None
        gray = tone.to_gray(self.main.image)
        if self.otsu.isChecked():
            return binarize.otsu(gray)
        T = self.threshold.value()
        return binarize.threshold(gray, T), T

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
        elif code == "binary":
            result = self.current_binary()[0]
        else:
            result = gray
        self.binarization_row.setVisible(code == "binary")       # у каждого метода показываем только его настройки
        self.gamma_label.setVisible(code == "gamma")
        self.gamma.setVisible(code == "gamma")
        self.color_view.set_image(img)
        self.result_view.set_image(result)
        if self.otsu.isChecked():                   # показать найденный порог на ползунке
            T = self.current_binary()[1]
            self.threshold.blockSignals(True)
            self.threshold.setValue(T)
            self.threshold.blockSignals(False)
            self.threshold_label.setText("T = {}".format(T))
        else:
            self.threshold_label.setText("T = {}".format(self.threshold.value()))
        self.hist.set_data(histogram.compute_histogram(gray), histogram.compute_histogram(result))
