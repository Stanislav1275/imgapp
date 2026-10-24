"""
Информация об изображении: размер на диске, разрешение, глубина цвета, формат и т. д.

Берём данные из файла через Pillow (он знает формат, режим и DPI) и дополняем
несколькими числами, посчитанными по самим пикселям.
"""
import os

import numpy as np
from PIL import Image

# Режим Pillow -> (число бит на пиксель, число каналов, человеческое описание).
# Глубина цвета = число бит, которое занимает ОДИН пиксель.
MODES = {
    "1":    (1,  1, "чёрно-белое, 1 бит"),
    "L":    (8,  1, "градации серого, 8 бит"),
    "LA":   (16, 2, "серое + прозрачность"),
    "P":    (8,  1, "палитра, до 256 цветов"),
    "RGB":  (24, 3, "True Color, по 8 бит на канал"),
    "RGBA": (32, 4, "RGB + прозрачность"),
    "CMYK": (32, 4, "CMYK, по 8 бит на канал"),
    "YCbCr": (24, 3, "YCbCr, по 8 бит на канал"),
    "I;16": (16, 1, "серое, 16 бит"),
    "I":    (32, 1, "серое, 32 бита"),
    "F":    (32, 1, "серое, дробное"),
}


def format_size(num_bytes):
    """12345 -> '12.1 КБ'. Удобный вывод размера файла."""
    size = float(num_bytes)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024 or unit == "ГБ":
            return "{:.0f} {}".format(size, unit) if unit == "Б" else "{:.1f} {}".format(size, unit)
        size /= 1024


def get_image_info(path):
    """
    Собрать сведения о файле картинки. Возвращает словарь
    {«название поля»: значение} — в таком виде его удобно выводить в окне.
    """
    file_size = os.path.getsize(path)
    with Image.open(path) as im:
        width, height = im.size
        mode = im.mode
        fmt = im.format or "неизвестно"
        dpi = im.info.get("dpi")
        rgb = np.asarray(im.convert("RGB"))

    bits, channels, description = MODES.get(mode, (0, 0, "нестандартный режим"))

    # Сколько разных цветов использовано: склеиваем R,G,B в одно число R*65536 + G*256 + B
    packed = (rgb[:, :, 0].astype(np.uint32) << 16) | (rgb[:, :, 1].astype(np.uint32) << 8) | rgb[:, :, 2]
    unique_colors = int(np.unique(packed).size)

    # Средняя яркость по формуле Y = 0.299 R + 0.587 G + 0.114 B
    gray = rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114

    raw_size = width * height * bits // 8     # столько занимала бы картинка без сжатия
    return {
        "Файл": os.path.basename(path),
        "Формат": fmt,
        "Размер на диске": format_size(file_size) + " ({} байт)".format(file_size),
        "Разрешение (пиксели)": "{} x {}".format(width, height),
        "Мегапиксели": "{:.2f}".format(width * height / 1e6),
        "Глубина цвета": "{} бит на пиксель".format(bits),
        "Режим": "{} ({})".format(mode, description),
        "Каналов": str(channels),
        "DPI": "{:.0f} x {:.0f}".format(*dpi) if dpi else "не указан",
        "Разных цветов": str(unique_colors),
        "Средняя яркость": "{:.1f} из 255".format(float(gray.mean())),
        "Размер без сжатия": format_size(raw_size),
        "Степень сжатия": "{:.1f} : 1".format(raw_size / file_size) if file_size else "-",
    }
