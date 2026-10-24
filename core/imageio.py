"""
Чтение и запись изображений.

ВАЖНОЕ СОГЛАШЕНИЕ ПРОЕКТА
-------------------------
Внутри программы изображение — это массив NumPy формы (высота, ширина, 3) типа uint8
с каналами в порядке R, G, B. Серое изображение — массив (высота, ширина).

OpenCV по умолчанию хранит каналы в порядке B, G, R. Чтобы не путаться,
конвертация происходит ТОЛЬКО здесь, при чтении и записи файла.
"""
import cv2
import numpy as np


def load_image(path):
    """
    Прочитать картинку с диска -> массив RGB uint8 (H, W, 3).

    cv2.imread не умеет читать пути с русскими буквами на Windows, поэтому читаем
    файл как байты (np.fromfile) и отдаём OpenCV на раскодирование (imdecode).
    """
    data = np.fromfile(path, dtype=np.uint8)
    bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Не удалось прочитать изображение: " + str(path))
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def save_image(path, img):
    """Сохранить массив RGB (или серый) в файл; формат определяется по расширению."""
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    ext = "." + str(path).rsplit(".", 1)[-1]
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise ValueError("Не удалось сохранить изображение: " + str(path))
    buf.tofile(path)


def to_rgb(img):
    """Серое (H, W) -> RGB (H, W, 3) (три одинаковых канала). RGB возвращается как есть."""
    if img.ndim == 2:
        return np.stack([img, img, img], axis=2)
    return img
