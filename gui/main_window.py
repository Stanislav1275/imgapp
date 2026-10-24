"""
Главное окно: панель сверху («Открыть», «Примеры», «Тема»), вкладки и строка состояния.
Текущее изображение хранится здесь (self.image) и доступно всем вкладкам как self.main.image.

Удобства:
    * файл можно перетащить мышью в окно;
    * меню «Примеры» открывает готовые фотографии из папки samples;
    * внизу показывается цвет пикселя под курсором;
    * последняя папка и выбранная тема запоминаются.
"""
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow, QMenu, QMessageBox,
                               QSizePolicy, QTabWidget, QToolButton, QWidget)

from core import colorspaces, imageio
from gui import theme
from gui.tabs.color_tab import ColorTab
from gui.tabs.features_tab import FeaturesTab
from gui.tabs.filters_tab import FiltersTab
from gui.tabs.gray_tab import GrayTab
from gui.tabs.info_tab import InfoTab
from gui.tabs.morph_tab import MorphTab
from gui.tabs.similarity_tab import SimilarityTab
from gui.tabs.tone_tab import ToneTab
from gui.tabs.video_tab import VideoTab
from gui.widgets import HistogramView, ImageView

IMAGE_FILTER = "Изображения (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;Все файлы (*)"
SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"

# Подписи к готовым примерам (если файла нет в списке, показывается его имя)
SAMPLE_TITLES = {
    "photo_coffee.jpg": "Кофе: цвет, яркость, фильтры (JPEG)",
    "photo_chelsea.png": "Кот: ключевые точки",
    "photo_chelsea_edit.png": "Кот, повёрнутый и тёмный: поиск похожих",
    "photo_astronaut.png": "Астронавт: ключевые точки",
    "photo_rocket.png": "Ракета",
    "photo_coins.png": "Монеты (серое): бинаризация, морфология",
    "photo_noisy.png": "Кот с шумом: медианный фильтр",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработка изображений")
        self.resize(1320, 840)
        self.setAcceptDrops(True)                  # разрешаем перетаскивать файлы в окно
        self.image = None                          # массив RGB (H, W, 3) или None
        self.path = None                           # путь к файлу

        self.settings = QSettings("imgapp", "imgapp")
        self.dark = str(self.settings.value("dark", "false")) == "true"
        theme.apply(QApplication.instance(), self.dark)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)            # плоские вкладки без рамки
        self.setCentralWidget(self.tabs)
        self.tab_list = [InfoTab(self), ColorTab(self), ToneTab(self), GrayTab(self), MorphTab(self),
                         FiltersTab(self), FeaturesTab(self), SimilarityTab(self), VideoTab(self)]
        for tab in self.tab_list:
            self.tabs.addTab(tab, tab.TITLE)
            layout = tab.layout()
            if layout is not None:                 # больше воздуха вокруг содержимого вкладок
                layout.setContentsMargins(24, 20, 24, 20)
                layout.setSpacing(16)

        self.build_toolbar()
        self.pixel_label = QLabel("")
        self.pixel_label.setObjectName("pixelInfo")
        self.statusBar().addPermanentWidget(self.pixel_label)
        self.statusBar().showMessage("Откройте изображение (Ctrl+O), выберите пример или перетащите файл в окно")
        for view in self.findChildren(ImageView):  # у каждой картинки показываем цвет пикселя под курсором
            view.hovered.connect(lambda x, y, v=view: self.show_pixel(v, x, y))

        first_sample = SAMPLES_DIR / "photo_coffee.jpg"
        if first_sample.exists():
            self.load_path(str(first_sample))      # чтобы окно сразу не было пустым

    # ---- панель сверху ----
    def build_toolbar(self):
        toolbar = self.addToolBar("Файл")
        toolbar.setMovable(False)
        title = QLabel("Обработка изображений")
        title.setObjectName("appTitle")
        toolbar.addWidget(title)
        toolbar.addSeparator()
        open_action = QAction("Открыть…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setToolTip("Открыть изображение (Ctrl+O)")
        open_action.triggered.connect(self.open_image)
        toolbar.addAction(open_action)
        toolbar.widgetForAction(open_action).setObjectName("primary")      # главная кнопка — цветная

        menu = QMenu(self)
        files = sorted(p for p in SAMPLES_DIR.glob("photo_*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        for path in files:
            action = menu.addAction(SAMPLE_TITLES.get(path.name, path.name))
            action.triggered.connect(lambda checked=False, p=str(path): self.load_path(p))
        examples = QToolButton()
        examples.setText("Примеры  ▾")      # стрелку рисуем текстом: родная стрелка Qt в QSS выходит огромной
        examples.setToolTip("Готовые фотографии из папки samples")
        examples.setMenu(menu)
        examples.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        examples.setEnabled(bool(files))
        toolbar.addWidget(examples)

        spacer = QWidget()                         # растяжка: кнопка темы уезжает вправо
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        theme_action = QAction("◐  Тема", self)
        theme_action.setToolTip("Светлая / тёмная тема")
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

    def toggle_theme(self):
        self.dark = not self.dark
        theme.apply(QApplication.instance(), self.dark)
        self.settings.setValue("dark", "true" if self.dark else "false")
        for hist in self.findChildren(HistogramView):
            hist.update()                          # гистограммы рисуют себя сами и берут цвета из темы

    # ---- загрузка изображения ----
    def open_image(self):
        start = str(self.settings.value("last_dir", str(SAMPLES_DIR)))
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", start, IMAGE_FILTER)
        if path:
            self.load_path(path)

    def load_path(self, path):
        """Прочитать файл и показать во всех вкладках."""
        try:
            image = imageio.load_image(path)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.image, self.path = image, path
        self.settings.setValue("last_dir", str(Path(path).parent))
        self.statusBar().showMessage("{}  ({} x {})".format(path, image.shape[1], image.shape[0]))
        for tab in self.tab_list:
            tab.on_image_changed()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.load_path(urls[0].toLocalFile())

    # ---- цвет пикселя под курсором ----
    def show_pixel(self, view, x, y):
        img = view.image()
        if img is None or y >= img.shape[0] or x >= img.shape[1]:
            return
        if img.ndim == 2:
            self.pixel_label.setText("({}, {})   яркость {}".format(x, y, int(img[y, x])))
        else:
            R, G, B = (int(v) for v in img[y, x][:3])
            self.pixel_label.setText("({}, {})   R {}  G {}  B {}   {}".format(
                x, y, R, G, B, colorspaces.rgb_to_hex(R, G, B)))
