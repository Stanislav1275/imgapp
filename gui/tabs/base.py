"""
Основа для всех вкладок: общий класс и мелкие помощники для построения интерфейса.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QSlider, QWidget


class BaseTab(QWidget):
    """
    Каждая вкладка — наследник этого класса.
    self.main — главное окно; из него берём текущее изображение: self.main.image (массив RGB или None).
    Когда пользователь открывает новое изображение, вызывается on_image_changed().
    """

    def __init__(self, main):
        super().__init__()
        self.main = main

    def on_image_changed(self):
        """Переопределяется во вкладках: обновить показ после загрузки нового изображения."""

    def has_image(self):
        """Проверка перед обработкой: если изображения нет, сообщаем об этом."""
        if self.main.image is None:
            QMessageBox.information(self, "Нет изображения", "Сначала откройте изображение (кнопка сверху).")
            return False
        return True


def make_slider(minimum, maximum, value, on_change):
    """Горизонтальный ползунок с готовым обработчиком on_change(значение)."""
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(value)
    slider.valueChanged.connect(on_change)
    return slider


def labeled(text, widget):
    """Строка «подпись + виджет»."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(QLabel(text))
    layout.addWidget(widget, 1)
    return row
