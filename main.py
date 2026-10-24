"""
Запуск приложения:   python main.py
Нужны пакеты из requirements.txt:   pip install -r requirements.txt
"""
import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
