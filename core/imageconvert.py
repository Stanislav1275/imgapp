"""
Перевод ВСЕГО изображения в другую цветовую модель и определение текущей модели файла.

Формулы берём из colorspaces.py (те же, что для одного пикселя на вкладке «Цвет»), здесь только
обёртка: пройти по пикселям, разложить результат на каналы и привести каналы к виду, который
можно показать (серые картинки 0..255).

Важно: внутри программы изображение всегда хранится как RGB. «Преобразовать» значит: посчитать
значения новой модели (например, H, S, V) и показать каждый её канал отдельной картинкой.
"""
import numpy as np
from PIL import Image

from core import colorspaces, imageio

# Каналы каждой модели: (имя, минимум, максимум). Нужны, чтобы растянуть значение на шкалу 0..255.
CHANNELS = {
    "RGB":   [("R", 0, 255), ("G", 0, 255), ("B", 0, 255)],
    "CMYK":  [("C", 0, 1), ("M", 0, 1), ("Y", 0, 1), ("K", 0, 1)],
    "HSV":   [("H", 0, 360), ("S", 0, 1), ("V", 0, 1)],
    "HSL":   [("H", 0, 360), ("S", 0, 1), ("L", 0, 1)],
    "YCbCr": [("Y", 0, 255), ("Cb", 0, 255), ("Cr", 0, 255)],
    "LAB":   [("L", 0, 100), ("a", -128, 127), ("b", -128, 127)],
}

# Режим Pillow (так файл хранит цвет) -> (модель, пояснение)
FILE_MODES = {
    "RGB": ("RGB", "RGB, 3 канала по 8 бит"),
    "RGBA": ("RGB", "RGB + прозрачность (прозрачность отбрасывается)"),
    "P": ("RGB", "палитра (при чтении превращается в RGB)"),
    "L": ("Градации серого", "один канал яркости, 8 бит"),
    "LA": ("Градации серого", "серое + прозрачность"),
    "1": ("Градации серого", "чёрно-белое, 1 бит"),
    "I;16": ("Градации серого", "серое, 16 бит"),
    "I": ("Градации серого", "серое, 32 бита"),
    "F": ("Градации серого", "серое, дробное"),
    "CMYK": ("CMYK", "4 канала C, M, Y, K"),
    "YCbCr": ("YCbCr", "яркость Y и две цветоразности Cb, Cr"),
    "LAB": ("LAB", "светлота L и две цветовые оси a, b"),
    "HSV": ("HSV", "тон H, насыщенность S, яркость V"),
}


def file_color_model(path):
    """
    Определить, в какой цветовой модели файл хранит изображение (по режиму Pillow).
    Возвращает (название модели, пояснение). Для неизвестного режима — ("неизвестно", сам режим).
    """
    with Image.open(path) as im:
        mode = im.mode
        is_jpeg = im.format == "JPEG"
    model, text = FILE_MODES.get(mode, ("неизвестно", "режим " + mode))
    if is_jpeg and mode == "RGB":
        text += "; JPEG хранит YCbCr, но при чтении отдаёт RGB"
    return model, text


def image_to_model(img, target):
    """
    Пересчитать изображение (RGB или серое) в модель target.
    Возвращает массив float (H, W, n) — по одному слою на канал модели, в «естественных» единицах
    (H в градусах, S и V в долях 0..1 и т. д.).
    """
    if target not in colorspaces.MODELS:
        raise ValueError("Неизвестная модель: " + str(target))
    rgb = imageio.to_rgb(img)
    height, width = rgb.shape[:2]
    flat = rgb.reshape(-1, 3)
    # Одинаковые цвета считаем один раз: так заметно быстрее, особенно для картинок с малым числом цветов.
    colors, inverse = np.unique(flat, axis=0, return_inverse=True)
    values = np.array([colorspaces.convert(tuple(int(v) for v in color), "RGB", target) for color in colors],
                      dtype=np.float64)
    return values[inverse.reshape(-1)].reshape(height, width, -1)


def planes_for_view(planes, target):
    """
    Растянуть каждый канал на 0..255, чтобы показать его серой картинкой.
    Возвращает список (имя канала, массив uint8 (H, W)).
    """
    result = []
    for k, (name, low, high) in enumerate(CHANNELS[target]):
        scaled = (planes[:, :, k] - low) / (high - low) * 255
        result.append((name, np.clip(np.rint(scaled), 0, 255).astype(np.uint8)))
    return result


def as_three_channel_picture(views):
    """
    Три канала модели, положенные в R, G, B одной картинки (так выглядит, например, «HSV как RGB»).
    Для моделей с четырьмя каналами (CMYK) возвращает None.
    """
    if len(views) != 3:
        return None
    return np.stack([plane for _name, plane in views], axis=2)
