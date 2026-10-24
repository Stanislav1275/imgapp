"""
Вкладка «Цвет»: перевод цвета ОДНОГО пикселя из одной модели в другие.

Как пользоваться: выберите исходную модель, введите числа (или щёлкните по изображению —
тогда подставится цвет этого пикселя как RGB) и посмотрите результат во всех моделях.
"""
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from core import colorspaces
from gui.tabs.base import BaseTab
from gui.widgets import ImageView

# Для каждой модели: список полей (подпись, минимум, максимум, множитель для показа).
# Множитель 100 означает, что внутри программы число — доля 0..1, а на экране — проценты.
SPECS = {
    "RGB":   [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)],
    "CMYK":  [("C, %", 0, 100, 100), ("M, %", 0, 100, 100), ("Y, %", 0, 100, 100), ("K, %", 0, 100, 100)],
    "HSV":   [("H, °", 0, 360, 1), ("S, %", 0, 100, 100), ("V, %", 0, 100, 100)],
    "HSL":   [("H, °", 0, 360, 1), ("S, %", 0, 100, 100), ("L, %", 0, 100, 100)],
    "YCbCr": [("Y", 0, 255, 1), ("Cb", 0, 255, 1), ("Cr", 0, 255, 1)],
    "LAB":   [("L", 0, 100, 1), ("a", -128, 127, 1), ("b", -128, 127, 1)],
}


class ColorTab(BaseTab):
    TITLE = "Цвет пикселя"

    def __init__(self, main):
        super().__init__(main)
        self.view = ImageView("Щёлкните по изображению, чтобы взять цвет пикселя")
        self.view.clicked.connect(self.pick_pixel)

        # --- ввод ---
        self.model_box = QComboBox()
        self.model_box.addItems(colorspaces.MODELS)
        self.model_box.currentTextChanged.connect(self.rebuild_fields)
        self.fields = []
        self.fields_box = QGroupBox("Значения")
        self.fields_layout = QVBoxLayout(self.fields_box)
        self.hex_edit = QLineEdit()
        self.hex_edit.setPlaceholderText("#FF8000")
        hex_button = QPushButton("Взять из HEX")
        hex_button.clicked.connect(self.from_hex)
        convert_button = QPushButton("Перевести")
        convert_button.clicked.connect(self.convert)

        self.swatch = QLabel()
        self.swatch.setFixedHeight(40)
        self.swatch.setStyleSheet("background: #888; border: 1px solid #555;")

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Модель", "Значения"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.pixel_label = QLabel("Пиксель: не выбран")

        side = QVBoxLayout()
        side.addWidget(QLabel("Исходная модель:"))
        side.addWidget(self.model_box)
        side.addWidget(self.fields_box)
        row = QHBoxLayout()
        row.addWidget(self.hex_edit)
        row.addWidget(hex_button)
        side.addLayout(row)
        side.addWidget(convert_button)
        side.addWidget(self.swatch)
        side.addWidget(self.pixel_label)
        side.addWidget(self.table, 1)

        layout = QHBoxLayout(self)
        layout.addWidget(self.view, 3)
        layout.addLayout(side, 2)

        self.rebuild_fields("RGB")
        self.set_values("RGB", (255, 128, 0))
        self.convert()

    # ---- поля ввода ----
    def rebuild_fields(self, model):
        """Пересоздать поля ввода под выбранную модель (у CMYK их четыре, у остальных три)."""
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.fields = []
        for label, low, high, _scale in SPECS[model]:
            spin = QDoubleSpinBox()
            spin.setRange(low, high)
            spin.setDecimals(3)
            holder = QWidget()
            row = QHBoxLayout(holder)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(label))
            row.addWidget(spin, 1)
            self.fields_layout.addWidget(holder)
            self.fields.append(spin)

    def set_values(self, model, values):
        """Записать значения модели (во внутренних единицах) в поля ввода."""
        if self.model_box.currentText() != model:
            self.model_box.setCurrentText(model)          # это вызовет rebuild_fields
        for spin, (_l, _lo, _hi, scale), value in zip(self.fields, SPECS[model], values):
            spin.setValue(value * scale)

    def read_values(self):
        """Прочитать поля ввода и вернуть значения во внутренних единицах."""
        model = self.model_box.currentText()
        return model, tuple(spin.value() / scale for spin, (_l, _lo, _hi, scale) in zip(self.fields, SPECS[model]))

    # ---- действия ----
    def pick_pixel(self, x, y):
        img = self.main.image
        if img is None:
            return
        R, G, B = (int(v) for v in img[y, x][:3])
        self.pixel_label.setText("Пиксель ({}, {}): RGB = ({}, {}, {})".format(x, y, R, G, B))
        self.set_values("RGB", (R, G, B))
        self.convert()

    def from_hex(self):
        try:
            self.set_values("RGB", colorspaces.hex_to_rgb(self.hex_edit.text()))
        except ValueError as error:
            self.pixel_label.setText("Ошибка HEX: {}".format(error))
            return
        self.convert()

    def convert(self):
        model, values = self.read_values()
        R, G, B = colorspaces.convert(values, model, "RGB")
        self.swatch.setStyleSheet("background: rgb({}, {}, {}); border: 1px solid #555;".format(R, G, B))
        self.table.setRowCount(0)
        rows = [("HEX", colorspaces.rgb_to_hex(R, G, B))]
        for target in colorspaces.MODELS:
            result = colorspaces.convert((R, G, B), "RGB", target)
            parts = ["{} = {:.2f}".format(label.split(",")[0], value * scale)
                     for (label, _lo, _hi, scale), value in zip(SPECS[target], result)]
            rows.append((target, ",  ".join(parts)))
        self.table.setRowCount(len(rows))
        for r, (name, text) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(text))

    def on_image_changed(self):
        self.view.set_image(self.main.image)
