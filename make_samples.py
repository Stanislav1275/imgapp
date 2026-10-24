"""
Создаёт примеры в папке samples/ из СВОБОДНЫХ фотографий, которые входят в пакет scikit-image
(в готовом архиве проекта папка samples/ уже заполнена, запускать этот файл не обязательно).

Что получится:
    photo_coffee.jpg        чашка кофе — цвета, яркость, фильтры (формат JPEG)
    photo_chelsea.png       кот — ключевые точки, поиск похожих
    photo_chelsea_edit.png  тот же кот: повёрнут, уменьшен, темнее (для поиска похожих)
    photo_astronaut.png     портрет астронавта — ключевые точки, поиск похожих
    photo_rocket.png        запуск ракеты — поиск похожих
    photo_coins.png         монеты (серое 8 бит) — бинаризация, морфология, контуры
    photo_noisy.png         кот с шумом «соль и перец» — медианный фильтр
    moving.avi              видео: по фону-фотографии летят мяч и коробка — вычитание фона

Источники (по документации scikit-image, раздел skimage.data): astronaut — NASA, общественное достояние;
coffee и chelsea (кот) — лицензия CC0; coins, rocket — свободные изображения из набора данных scikit-image.
Проверьте условия использования, если планируете публиковать картинки отдельно от проекта.

Запуск:  pip install scikit-image   (нужен только для этого файла)
         python make_samples.py
"""
import os

import cv2
import numpy as np
from skimage import data

from core import filters, imageio

OUT = "samples"


def path(name):
    return os.path.join(OUT, name)


def make_video(file, background, frames=100):
    h, w = background.shape[:2]
    writer = cv2.VideoWriter(file, cv2.VideoWriter_fourcc(*"MJPG"), 25, (w, h))
    for t in range(frames):
        frame = background.copy()
        # жёлтый мяч летит слева направо по волне
        x = int(30 + t * (w - 60) / frames)
        y = int(h * 0.45 + 40 * np.sin(t / 7))
        cv2.circle(frame, (x + 6, y + 8), 22, (40, 40, 40), -1)            # тень
        cv2.circle(frame, (x, y), 22, (250, 210, 40), -1)
        cv2.circle(frame, (x - 7, y - 7), 6, (255, 255, 255), -1)
        # красная коробка едет справа налево внизу
        bx = int(w - 40 - t * (w - 110) / frames)
        cv2.rectangle(frame, (bx, int(h * 0.78)), (bx + 46, int(h * 0.78) + 34), (200, 50, 50), -1)
        cv2.rectangle(frame, (bx, int(h * 0.78)), (bx + 46, int(h * 0.78) + 34), (255, 255, 255), 2)
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    writer.release()


def main():
    os.makedirs(OUT, exist_ok=True)
    chelsea = data.chelsea()
    imageio.save_image(path("photo_coffee.jpg"), data.coffee())
    imageio.save_image(path("photo_chelsea.png"), chelsea)
    h, w = chelsea.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), 7, 0.9)
    edited = cv2.warpAffine(chelsea, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)
    imageio.save_image(path("photo_chelsea_edit.png"), (edited * 0.8).astype(np.uint8))
    imageio.save_image(path("photo_astronaut.png"), data.astronaut())
    imageio.save_image(path("photo_rocket.png"), data.rocket())
    imageio.save_image(path("photo_coins.png"), data.coins())
    imageio.save_image(path("photo_noisy.png"), filters.add_salt_pepper(chelsea, 0.06, seed=0))
    make_video(path("moving.avi"), chelsea)
    print("Готово: файлы в папке", OUT)


if __name__ == "__main__":
    main()
