"""
Вкладка «Видео»: вычитание фона и размытие движущихся объектов.
Кадры читаются по одному по таймеру (QTimer), поэтому окно не «зависает».
"""
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QVBoxLayout)

from core import video
from gui.tabs.base import BaseTab
from gui.widgets import ImageView

MODES = [("Маска движения (вычитание фона)", "mask"),
         ("Только движущиеся объекты", "foreground"),
         ("Размытие движущихся объектов", "blur")]


class VideoTab(BaseTab):
    TITLE = "Видео"

    def __init__(self, main):
        super().__init__(main)
        self.path = None
        self.frames = None            # генератор кадров
        self.detector = None
        self.interval = 40            # мс между кадрами (уточняется по fps видео)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

        self.original_view = ImageView("исходное видео")
        self.result_view = ImageView("результат")
        self.mode = QComboBox()
        for title, code in MODES:
            self.mode.addItem(title, code)
        self.mode.currentIndexChanged.connect(self.restart)
        open_button = QPushButton("Открыть видео…")
        open_button.clicked.connect(self.open_video)
        self.play_button = QPushButton("Пуск")
        self.play_button.clicked.connect(self.toggle)
        save_button = QPushButton("Сохранить результат…")
        save_button.clicked.connect(self.save_result)
        self.status = QLabel("Откройте видеофайл (avi, mp4, mov).")

        row = QHBoxLayout()
        row.addWidget(open_button)
        row.addWidget(QLabel("Режим:"))
        row.addWidget(self.mode)
        row.addWidget(self.play_button)
        row.addWidget(save_button)
        row.addStretch(1)
        views = QHBoxLayout()
        views.addWidget(self.original_view)
        views.addWidget(self.result_view)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(views, 1)
        layout.addWidget(self.status)

    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть видео", "", "Видео (*.avi *.mp4 *.mov *.mkv);;Все файлы (*)")
        if not path:
            return
        self.path = path
        self.restart()

    def restart(self, *_):
        """Начать видео сначала (при открытии файла или смене режима). Алгоритму фона нужно «перезапомнить» сцену."""
        self.timer.stop()
        self.play_button.setText("Пуск")
        if not self.path:
            return
        try:
            self.frames = video.read_frames(self.path)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.detector = video.MotionDetector()
        self.interval = int(1000 / video.video_fps(self.path))
        self.status.setText("Файл: {}".format(self.path))
        self.next_frame()                                  # сразу показать первый кадр

    def toggle(self):
        if self.frames is None:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText("Пуск")
        else:
            self.timer.start(self.interval)
            self.play_button.setText("Пауза")

    def render(self, frame, mask):
        code = self.mode.currentData()
        if code == "mask":
            return np.stack([mask] * 3, axis=2)
        if code == "foreground":
            return video.foreground(frame, mask)
        return video.blur_moving(frame, mask)

    def next_frame(self):
        try:
            frame = next(self.frames)
        except StopIteration:
            self.timer.stop()
            self.play_button.setText("Пуск")
            self.status.setText("Видео закончилось. Нажмите «Пуск», чтобы воспроизвести снова.")
            self.frames = video.read_frames(self.path)       # подготовить повторный просмотр
            self.detector = video.MotionDetector()
            return
        mask = self.detector.mask(frame)
        self.original_view.set_image(frame)
        self.result_view.set_image(self.render(frame, mask))

    def save_result(self):
        if not self.path:
            QMessageBox.information(self, "Нет видео", "Сначала откройте видео.")
            return
        out, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "result.avi", "AVI (*.avi)")
        if not out:
            return
        self.timer.stop()
        self.play_button.setText("Пуск")
        video.process_video(self.path, self.mode.currentData(), out_path=out)
        self.status.setText("Сохранено: {}".format(out))
        self.restart()
