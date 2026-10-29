"""
Окно с результатом перевода всего изображения в другую цветовую модель:
каждый канал новой модели показан отдельной серой картинкой, плюс (для трёх каналов) картинка,
в которой каналы положены в R, G, B. Кнопка «Сохранить каналы…» записывает каждый канал в файл.
"""
import os

from PySide6.QtWidgets import (QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout)

from core import imageconvert, imageio
from gui.widgets import ImageView


class ChannelsDialog(QDialog):
    def __init__(self, parent, source_model, target, views, base_name):
        super().__init__(parent)
        self.setWindowTitle("{} → {}".format(source_model, target))
        self.resize(1000, 700)
        self.views = views
        self.base_name = base_name

        pictures = list(views)
        combined = imageconvert.as_three_channel_picture(views)
        if combined is not None:
            pictures.append(("{} как RGB".format(target), combined))

        title = QLabel("Изображение в модели {}: каждый канал — серая картинка (светлее = больше значение)".format(target))
        grid = QGridLayout()
        for k, (name, picture) in enumerate(pictures):
            view = ImageView(name)
            view.set_image(picture)
            caption = QLabel(name)
            grid.addWidget(view, 0 if k < 2 else 2, (k % 2) * 1)
            grid.addWidget(caption, 1 if k < 2 else 3, k % 2)

        save_button = QPushButton("Сохранить каналы…")
        save_button.clicked.connect(self.save_channels)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(save_button)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(grid, 1)
        layout.addLayout(buttons)

    def save_channels(self):
        """Каждый канал — отдельный PNG: <имя>_H.png, <имя>_S.png и т. д."""
        folder = QFileDialog.getExistingDirectory(self, "Куда сохранить каналы")
        if not folder:
            return
        for name, plane in self.views:
            imageio.save_image(os.path.join(folder, "{}_{}.png".format(self.base_name, name)), plane)
        QMessageBox.information(self, "Готово", "Сохранено файлов: {}".format(len(self.views)))
