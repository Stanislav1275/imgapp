"""Вкладка «Изображение»: просмотр и сведения о файле."""
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QTableWidget,
                               QTableWidgetItem)

from core import info
from gui.tabs.base import BaseTab
from gui.widgets import ImageView


class InfoTab(BaseTab):
    TITLE = "Изображение"

    def __init__(self, main):
        super().__init__(main)
        self.view = ImageView("Откройте изображение: кнопка «Открыть…» сверху")
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        layout = QHBoxLayout(self)
        layout.addWidget(self.view, 3)
        layout.addWidget(self.table, 2)

    def on_image_changed(self):
        self.view.set_image(self.main.image)
        rows = list(info.get_image_info(self.main.path).items()) if self.main.path else []
        self.table.setRowCount(len(rows))
        for r, (name, value) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(str(value)))
