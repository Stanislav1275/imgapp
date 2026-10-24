"""
Общие виджеты окна: показ картинки, показ гистограммы, перевод массива NumPy в картинку Qt.

В этом файле — только отрисовка. Никаких вычислений над изображениями здесь нет (они в папке core).
"""
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


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


class ImageView(QLabel):
    """
    Область, в которой показывается изображение с сохранением пропорций.
    Если по ней щёлкнуть мышью, подаётся сигнал clicked(x, y) с координатами ПИКСЕЛЯ ИЗОБРАЖЕНИЯ.
    """
    clicked = Signal(int, int)

    def __init__(self, placeholder="Нет изображения"):
        super().__init__(placeholder)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(160, 120)
        # Ignored: размер области не зависит от размера картинки внутри (иначе окно будет «расти»)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setStyleSheet("background: #2b2b2b; color: #999; border: 1px solid #555;")
        self._image = None

    def set_image(self, img):
        """Показать массив NumPy. None — очистить."""
        self._image = img
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

    def mousePressEvent(self, event):
        """Перевод координат щелчка из координат окна в координаты пикселя изображения."""
        pixmap = self.pixmap()
        if self._image is None or pixmap is None or pixmap.isNull():
            return
        pos = event.position()
        left = (self.width() - pixmap.width()) / 2          # картинка по центру: считаем отступ
        top = (self.height() - pixmap.height()) / 2
        fx = (pos.x() - left) / pixmap.width()
        fy = (pos.y() - top) / pixmap.height()
        if 0 <= fx < 1 and 0 <= fy < 1:
            height, width = self._image.shape[:2]
            self.clicked.emit(int(fx * width), int(fy * height))


class HistogramView(QWidget):
    """
    Рисует гистограмму «до» (серая линия) и «после» (цветные столбики).
    Шкала по вертикали определяется ТОЛЬКО гистограммой «до», поэтому серая линия не меняется
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
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        if self.before is None:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return
        width, height = self.width(), self.height()
        pad = 16
        plot_h = height - pad - 4
        top = max(1, int(np.max(self.before)))                # шкала по «до»
        bar_w = width / 256

        if self.after is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.color)
            for v in range(256):
                h = min(plot_h, self.after[v] / top * plot_h)
                painter.drawRect(int(v * bar_w), int(height - pad - h), int(bar_w) + 1, int(h))

        painter.setPen(QPen(QColor(90, 90, 90), 1.5))
        points = [(v * bar_w + bar_w / 2, height - pad - min(plot_h, self.before[v] / top * plot_h))
                  for v in range(256)]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setPen(QColor(120, 120, 120))
        painter.drawLine(0, height - pad, width, height - pad)
        painter.drawText(2, height - 2, "0")
        painter.drawText(width // 2 - 8, height - 2, "128")
        painter.drawText(width - 26, height - 2, "255")
