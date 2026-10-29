#!/usr/bin/env bash
# Сборка программы в запускаемый файл (macOS / Linux). Запускать из папки проекта с активным .venv:
#     source .venv/bin/activate
#     bash build_app.sh
# Готовая программа появится в папке dist/ (на macOS это ImageApp.app).
set -e
pip install pyinstaller
pyinstaller --noconfirm --windowed --name ImageApp \
    --add-data "samples:samples" \
    --collect-all cv2 \
    main.py
echo "Готово: папка dist/"
