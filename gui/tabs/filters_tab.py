"""
Вкладка «Фильтры и границы»: резкость, размытие в движении, тиснение, медиана, Canny, Робертс.
"""
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from core import edges, filters, tone
from gui.tabs.base import BaseTab
from gui.steps_dialog import StepsDialog
from gui.widgets import ImageView

# Какие параметры нужны каждому эффекту (названия — ключи в self.params).
EFFECTS = [
    ("Резкость", "sharpen", ["strength"]),
    ("Размытие в движении", "motion", ["length", "angle"]),
    ("Тиснение", "emboss", []),
    ("Медианный фильтр", "median", ["size"]),
    ("Шум «соль и перец»", "noise", []),
    ("Границы: Canny", "canny", ["low", "high", "sigma"]),
    ("Границы: оператор Робертса", "roberts", []),
]


class FiltersTab(BaseTab):
    TITLE = "Фильтры и границы"

    def __init__(self, main):
        super().__init__(main)
        self.before_view = ImageView("до")
        self.after_view = ImageView("после")

        self.effect = QComboBox()
        for title, code, _params in EFFECTS:
            self.effect.addItem(title, code)
        self.effect.currentIndexChanged.connect(self.on_effect_changed)

        self.params = {}                     # имя параметра -> (виджет-строка, поле ввода)
        row = QHBoxLayout()
        row.addWidget(QLabel("Эффект:"))
        row.addWidget(self.effect)
        self.add_param(row, "strength", "Сила", QDoubleSpinBox, 0.1, 5.0, 1.0, step=0.1)
        self.add_param(row, "length", "Длина, px", QSpinBox, 3, 101, 21)
        self.add_param(row, "angle", "Угол, °", QSpinBox, 0, 180, 0)
        self.add_param(row, "size", "Окно", QSpinBox, 3, 15, 3, step=2)
        self.add_param(row, "low", "Нижний порог", QSpinBox, 0, 255, 100)
        self.add_param(row, "high", "Верхний порог", QSpinBox, 0, 255, 200)
        self.add_param(row, "sigma", "Сглаживание σ", QDoubleSpinBox, 0.0, 5.0, 1.4, step=0.1)
        self.steps_button = QPushButton("Шаги Canny…")
        self.steps_button.setToolTip("Показать все пять шагов алгоритма Canny на текущем изображении")
        self.steps_button.clicked.connect(self.show_canny_steps)
        row.addWidget(self.steps_button)
        row.addStretch(1)

        images = QHBoxLayout()
        images.addWidget(self.before_view)
        images.addWidget(self.after_view)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(images, 1)
        self.on_effect_changed()

    def add_param(self, row, name, title, spin_class, low, high, value, step=1):
        box = QWidget()
        inner = QHBoxLayout(box)
        inner.setContentsMargins(0, 0, 0, 0)
        spin = spin_class()
        spin.setRange(low, high)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.valueChanged.connect(self.update_view)
        inner.addWidget(QLabel(title))
        inner.addWidget(spin)
        row.addWidget(box)
        self.params[name] = (box, spin)

    def on_effect_changed(self, *_):
        """Показываем только параметры выбранного эффекта."""
        needed = next(p for _t, code, p in EFFECTS if code == self.effect.currentData())
        for name, (box, _spin) in self.params.items():
            box.setVisible(name in needed)
        self.steps_button.setVisible(self.effect.currentData() == "canny")
        self.update_view()

    def value(self, name):
        return self.params[name][1].value()

    def on_image_changed(self):
        self.update_view()

    def update_view(self, *_):
        img = self.main.image
        if img is None:
            return
        source = img                                # «до» — всегда исходное изображение
        code = self.effect.currentData()
        if code == "sharpen":
            result = filters.sharpen(source, self.value("strength"))
        elif code == "motion":
            result = filters.motion_blur(source, self.value("length"), self.value("angle"))
        elif code == "emboss":
            result = filters.emboss(source)
        elif code == "median":
            result = filters.median(source, int(self.value("size")))
        elif code == "noise":
            result = filters.add_salt_pepper(source, 0.04)
        elif code == "canny":
            result = edges.canny_steps(tone.to_gray(source), int(self.value("low")), int(self.value("high")),
                                       self.value("sigma"))["edges"]
        else:
            result = edges.roberts(tone.to_gray(source), normalize=True)
        self.before_view.set_image(source)
        self.after_view.set_image(result)

    def show_canny_steps(self):
        """Кнопка «Шаги Canny…»: окно с шестью картинками — от исходной до итоговых границ."""
        if not self.has_image():
            return
        gray = tone.to_gray(self.main.image)
        steps = edges.canny_steps(gray, int(self.value("low")), int(self.value("high")), self.value("sigma"))
        hint = "Пороги: нижний {}, верхний {}, σ = {:.1f}".format(
            int(self.value("low")), int(self.value("high")), self.value("sigma"))
        self.steps_dialog = StepsDialog(self, "Canny по шагам", edges.canny_stage_images(gray, steps), hint)
        self.steps_dialog.show()
