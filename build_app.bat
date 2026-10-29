@echo off
rem Сборка в .exe для Windows. Запускать из папки проекта с активным .venv.
pip install pyinstaller
pyinstaller --noconfirm --windowed --name ImageApp --add-data "samples;samples" --collect-all cv2 main.py
echo Готово: папка dist
