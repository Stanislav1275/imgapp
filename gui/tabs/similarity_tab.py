"""
Вкладка «Сходство»: загрузить от 3 до 10 изображений и показать два самых похожих.
Эта вкладка не использует «текущее изображение»: у неё свой набор файлов.
"""
import os

from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from core import imageio, similarity
from gui.tabs.base import BaseTab
from gui.widgets import ImageView, busy

MIN_IMAGES, MAX_IMAGES = 3, 10


class SimilarityTab(BaseTab):
    TITLE = "Сходство"

    def __init__(self, main):
        super().__init__(main)
        self.paths = []
        self.first_view = ImageView("первое из похожих")
        self.second_view = ImageView("второе из похожих")
        self.first_caption = QLabel()
        self.second_caption = QLabel()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(170)
        self.method = QComboBox()
        self.method.addItem("По ключевым точкам SIFT", "sift")
        self.method.addItem("По цветовым гистограммам", "hist")
        self.method.currentIndexChanged.connect(lambda *_: self.paths and self.compare())   # пересчёт при смене метода

        choose = QPushButton("Выбрать {}–{} изображений…".format(MIN_IMAGES, MAX_IMAGES))
        choose.clicked.connect(self.choose_files)
        row = QHBoxLayout()
        row.addWidget(choose)
        row.addWidget(QLabel("Метод:"))
        row.addWidget(self.method)
        row.addStretch(1)

        views = QHBoxLayout()
        for view, caption in ((self.first_view, self.first_caption), (self.second_view, self.second_caption)):
            column = QVBoxLayout()
            column.addWidget(view, 1)
            column.addWidget(caption)
            views.addLayout(column)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(views, 1)
        layout.addWidget(self.log)

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите изображения", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)")
        if not paths:
            return
        if not MIN_IMAGES <= len(paths) <= MAX_IMAGES:
            QMessageBox.warning(self, "Неверное число файлов",
                                "Нужно выбрать от {} до {} изображений, выбрано {}.".format(
                                    MIN_IMAGES, MAX_IMAGES, len(paths)))
            return
        self.paths = paths
        self.compare()

    def compare(self):
        try:
            images = [imageio.load_image(p) for p in self.paths]
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка чтения", str(error))
            return
        with busy():
            i, j, score, matrix = similarity.most_similar_pair(images, self.method.currentData())
        self.first_view.set_image(images[i])
        self.second_view.set_image(images[j])
        self.first_caption.setText(os.path.basename(self.paths[i]))
        self.second_caption.setText(os.path.basename(self.paths[j]))
        names = [os.path.basename(p) for p in self.paths]
        lines = ["Самые похожие: «{}» и «{}», оценка = {:.3f}".format(names[i], names[j], score), "",
                 "Матрица оценок (чем больше, тем более похожи):"]
        for a in range(len(names)):
            lines.append("{:<22}".format(names[a][:21]) + " ".join("{:6.3f}".format(v) for v in matrix[a]))
        self.log.setPlainText("\n".join(lines))
