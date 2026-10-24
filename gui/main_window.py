"""
Главное окно: кнопка «Открыть…», строка состояния и вкладки.
Текущее изображение хранится здесь (self.image) и доступно всем вкладкам как self.main.image.
"""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTabWidget

from core import imageio
from gui.tabs.color_tab import ColorTab
from gui.tabs.features_tab import FeaturesTab
from gui.tabs.filters_tab import FiltersTab
from gui.tabs.gray_tab import GrayTab
from gui.tabs.info_tab import InfoTab
from gui.tabs.morph_tab import MorphTab
from gui.tabs.similarity_tab import SimilarityTab
from gui.tabs.tone_tab import ToneTab
from gui.tabs.video_tab import VideoTab

IMAGE_FILTER = "Изображения (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;Все файлы (*)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработка изображений")
        self.resize(1280, 820)
        self.image = None          # массив RGB (H, W, 3) или None
        self.path = None           # путь к файлу

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tab_list = [InfoTab(self), ColorTab(self), ToneTab(self), GrayTab(self), MorphTab(self),
                         FiltersTab(self), FeaturesTab(self), SimilarityTab(self), VideoTab(self)]
        for tab in self.tab_list:
            self.tabs.addTab(tab, tab.TITLE)

        open_action = QAction("Открыть изображение…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        toolbar = self.addToolBar("Файл")
        toolbar.addAction(open_action)
        self.statusBar().showMessage("Откройте изображение (Ctrl+O)")

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", IMAGE_FILTER)
        if not path:
            return
        try:
            image = imageio.load_image(path)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.image, self.path = image, path
        self.statusBar().showMessage("{}  ({} x {})".format(path, image.shape[1], image.shape[0]))
        for tab in self.tab_list:
            tab.on_image_changed()
