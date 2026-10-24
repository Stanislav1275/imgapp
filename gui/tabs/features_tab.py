"""
Вкладка «Ключевые точки»: детекторы Харриса, SIFT и FAST.
(SURF из четырёх возможных не делаем: по заданию достаточно любых трёх.)
"""
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QVBoxLayout)

from core import features
from gui.tabs.base import BaseTab
from gui.widgets import ImageView, busy


class FeaturesTab(BaseTab):
    TITLE = "Ключевые точки"

    def __init__(self, main):
        super().__init__(main)
        self.before_view = ImageView("изображение")
        self.after_view = ImageView("ключевые точки")

        self.detector = QComboBox()
        self.detector.addItems(features.DETECTORS)
        self.detector.currentIndexChanged.connect(self.on_detector_changed)
        self.harris_ratio = QDoubleSpinBox()
        self.harris_ratio.setDecimals(3)
        self.harris_ratio.setRange(0.001, 0.5)
        self.harris_ratio.setSingleStep(0.005)
        self.harris_ratio.setValue(0.01)
        self.fast_threshold = QSpinBox()
        self.fast_threshold.setRange(1, 100)
        self.fast_threshold.setValue(20)
        self.sift_points = QSpinBox()
        self.sift_points.setRange(0, 2000)
        self.sift_points.setValue(0)
        self.sift_points.setSpecialValueText("все")
        run = QPushButton("Найти точки")
        run.setToolTip("Запустить выбранный детектор на текущем изображении")
        run.clicked.connect(self.run)

        self.harris_label = QLabel("Порог (доля от максимума):")
        self.fast_label = QLabel("Порог яркости:")
        self.sift_label = QLabel("Макс. точек:")
        self.status = QLabel()

        row = QHBoxLayout()
        row.addWidget(QLabel("Детектор:"))
        row.addWidget(self.detector)
        for label, spin in ((self.harris_label, self.harris_ratio), (self.fast_label, self.fast_threshold),
                            (self.sift_label, self.sift_points)):
            row.addWidget(label)
            row.addWidget(spin)
        row.addWidget(run)
        row.addStretch(1)

        images = QHBoxLayout()
        images.addWidget(self.before_view)
        images.addWidget(self.after_view)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(images, 1)
        layout.addWidget(self.status)
        self.on_detector_changed()

    def on_detector_changed(self, *_):
        """Показываем только параметр выбранного детектора."""
        name = self.detector.currentText()
        for label, spin, owner in ((self.harris_label, self.harris_ratio, "Харрис"),
                                   (self.fast_label, self.fast_threshold, "FAST"),
                                   (self.sift_label, self.sift_points, "SIFT")):
            label.setVisible(name == owner)
            spin.setVisible(name == owner)

    def on_image_changed(self):
        self.before_view.set_image(self.main.image)
        self.after_view.set_image(None)
        self.status.setText("")

    def run(self):
        if not self.has_image():
            return
        name = self.detector.currentText()
        with busy():                                  # SIFT на большой картинке может думать секунду-другую
            if name == "Харрис":
                points = features.detect(name, self.main.image, ratio=self.harris_ratio.value())
            elif name == "FAST":
                points = features.detect(name, self.main.image, threshold=self.fast_threshold.value())
            else:
                points = features.detect(name, self.main.image, max_points=self.sift_points.value())
        self.after_view.set_image(features.draw_points(self.main.image, points))
        self.status.setText("{}: найдено точек — {}".format(name, len(points)))
