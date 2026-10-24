"""
Общие виджеты окна: показ картинки, показ гистограммы, перевод массива NumPy в картинку Qt,
курсор ожидания.

В этом файле — только отрисовка. Никаких вычислений над изображениями здесь нет (они в папке core).
"""
from contextlib import contextmanager

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QMenu, QSizePolicy, QWidget

from core import imageio
from gui import theme


def numpy_to_pixmap(img):
    """Массив (H, W, 3) RGB или (H, W) серый -> QPixmap, который умеет показывать Qt."""
    img = np.ascontiguousarray(img)
    if img.ndim == 2:
        height, width = img.shape
        fmt, bytes_per_line = QImage.Format.Format_Grayscale8, width
    else:
        height, width, _ = img.shape
        fmt, bytes_per_line = QImage.Format.Format_RGB888, 3 * width
    qimage = QImage(img.data, width, height, bytes_per_line, fmt)
    return QPixmap.fromImage(qimage.copy())      # copy(): картинка не должна зависеть от памяти массива


@contextmanager
def busy():
    """
    Курсор «ожидание» на время долгой операции:
        with busy():
            долгая_работа()
    """
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    QApplication.processEvents()                  # дать окну перерисовать курсор до начала работы
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


class ImageView(QLabel):
    """
    Область, в которой показывается изображение с сохранением пропорций.
    Сигналы (координаты — это ПИКСЕЛЬ ИЗОБРАЖЕНИЯ, а не окна):
        clicked(x, y) — щелчок мышью по картинке;
        hovered(x, y) — мышь движется над картинкой.
    Правая кнопка мыши: «Сохранить изображение…».
    """
    clicked = Signal(int, int)
    hovered = Signal(int, int)

    def __init__(self, placeholder="Нет изображения"):
        super().__init__(placeholder)
        self.setObjectName("imageView")               # по этому имени стиль из theme.py находит виджет
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(160, 120)
        self.setMouseTracking(True)
        # Ignored: размер области не зависит от размера картинки внутри (иначе окно будет «расти»)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self._image = None
        self.setProperty("empty", True)

    def image(self):
        """Что сейчас показано (массив NumPy или None)."""
        return self._image

    def set_image(self, img):
        """Показать массив NumPy. None — очистить."""
        self._image = img
        self.setProperty("empty", img is None)        # пустая область рисуется пунктиром (см. theme.py)
        self.style().unpolish(self)
        self.style().polish(self)
        if img is None:
            self.clear()
            return
        self._redraw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._redraw()

    def _redraw(self):
        if self._image is None:
            return
        pixmap = numpy_to_pixmap(self._image)
        self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))

    def _image_coords(self, pos):
        """Координаты щелчка в окне -> координаты пикселя изображения (или None, если мимо картинки)."""
        pixmap = self.pixmap()
        if self._image is None or pixmap is None or pixmap.isNull():
            return None
        left = (self.width() - pixmap.width()) / 2          # картинка по центру: считаем отступ
        top = (self.height() - pixmap.height()) / 2
        fx = (pos.x() - left) / pixmap.width()
        fy = (pos.y() - top) / pixmap.height()
        if 0 <= fx < 1 and 0 <= fy < 1:
            height, width = self._image.shape[:2]
            return int(fx * width), int(fy * height)
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._image_coords(event.position())
            if point:
                self.clicked.emit(*point)

    def mouseMoveEvent(self, event):
        point = self._image_coords(event.position())
        if point:
            self.hovered.emit(*point)

    def contextMenuEvent(self, event):
        """Правая кнопка: сохранить то, что сейчас показано."""
        if self._image is None:
            return
        menu = QMenu(self)
        save_action = menu.addAction("Сохранить изображение…")
        if menu.exec(event.globalPos()) == save_action:
            path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "result.png",
                                                  "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)")
            if path:
                imageio.save_image(path, self._image)


class HistogramView(QWidget):
    """
    Рисует гистограмму «до» (линия) и «после» (цветные столбики).
    Шкала по вертикали определяется ТОЛЬКО гистограммой «до», поэтому линия не меняется
    при движении ползунков. Столбик «после», вышедший за шкалу, обрезается.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(140)
        self.before = None
        self.after = None
        self.color = QColor(220, 70, 70)

    def set_data(self, before, after=None, color=(220, 70, 70)):
        self.before, self.after = before, after
        self.color = QColor(*color)
        self.update()

    def paintEvent(self, event):
        c = theme.COLORS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(c["border"]), 1))
        painter.setBrush(QColor(c["hist_bg"]))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)       # карточка со скруглением
        if self.before is None:
            painter.setPen(QColor(c["hist_axis"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return
        left, right, bottom, top_pad = 14, 14, 22, 12
        plot_w = self.width() - left - right
        plot_h = self.height() - bottom - top_pad
        base = self.height() - bottom                          # y нулевой линии
        top = max(1, int(np.max(self.before)))                # шкала по «до»
        bar_w = plot_w / 256

        painter.setPen(QPen(QColor(c["border"]), 1))           # тонкие линии сетки на 25 / 50 / 75 %
        for k in (1, 2, 3):
            y = int(base - plot_h * k / 4)
            painter.drawLine(left, y, left + plot_w, y)

        if self.after is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            fill = QColor(self.color)
            fill.setAlpha(170)
            painter.setBrush(fill)
            for v in range(256):
                h = min(plot_h, self.after[v] / top * plot_h)
                painter.drawRect(int(left + v * bar_w), int(base - h), int(bar_w) + 1, int(h))

        painter.setPen(QPen(QColor(c["hist_line"]), 1.6))
        points = [(left + v * bar_w + bar_w / 2, base - min(plot_h, self.before[v] / top * plot_h))
                  for v in range(256)]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setPen(QColor(c["hist_axis"]))
        painter.drawLine(left, base, left + plot_w, base)
        painter.drawText(left, self.height() - 6, "0")
        painter.drawText(left + plot_w // 2 - 8, self.height() - 6, "128")
        painter.drawText(left + plot_w - 20, self.height() - 6, "255")
