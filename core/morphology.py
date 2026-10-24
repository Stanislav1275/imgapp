"""
Морфологические операции над (обычно бинарным) изображением.

Структурный элемент (ядро) — маленькая фигура из единиц, которую «прикладываем» к каждому пикселю.
    Эрозия (сужение):   пиксель остаётся белым, только если ядро целиком помещается в белое.
                        Белые объекты уменьшаются, мелкие белые точки исчезают.
    Дилатация (расширение): пиксель становится белым, если ядро хоть частью касается белого.
                        Белые объекты растут, маленькие чёрные дырки зарастают.
    Открытие = эрозия, потом дилатация: убирает мелкий белый шум, форма крупных объектов сохраняется.
    Закрытие = дилатация, потом эрозия: закрывает мелкие чёрные дыры внутри объектов.
    Градиент = дилатация - эрозия: остаётся только контур объектов.
"""
import cv2
import numpy as np

KERNEL_SHAPES = {"Прямоугольник": cv2.MORPH_RECT, "Эллипс": cv2.MORPH_ELLIPSE, "Крест": cv2.MORPH_CROSS}

OPERATIONS = {
    "Эрозия": "erode",
    "Дилатация": "dilate",
    "Открытие": "open",
    "Закрытие": "close",
    "Градиент": "gradient",
}


def make_kernel(shape=cv2.MORPH_RECT, size=3):
    """Ядро size x size заданной формы (size делаем нечётным, чтобы был центр)."""
    if size % 2 == 0:
        size += 1
    return cv2.getStructuringElement(shape, (size, size))


def erode(img, kernel, iterations=1):
    return cv2.erode(img, kernel, iterations=iterations)


def dilate(img, kernel, iterations=1):
    return cv2.dilate(img, kernel, iterations=iterations)


def opening(img, kernel, iterations=1):
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=iterations)


def closing(img, kernel, iterations=1):
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iterations)


def gradient(img, kernel, iterations=1):
    return cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel, iterations=iterations)


def apply(name, img, kernel, iterations=1):
    """Применить операцию по её коду из OPERATIONS ('erode', 'dilate', 'open', 'close', 'gradient')."""
    functions = {"erode": erode, "dilate": dilate, "open": opening, "close": closing, "gradient": gradient}
    return functions[name](img, kernel, iterations)
