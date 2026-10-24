"""
Гистограммы изображения.

Гистограмма — это список из 256 чисел: hist[v] = сколько пикселей имеют яркость v.
Мы как бы заводим 256 корзин и бросаем в корзину v по одному шарику за каждый пиксель яркости v.
"""
import numpy as np

CHANNELS = {"Яркость": "y", "R": "r", "G": "g", "B": "b"}


def channel_values(img, channel):
    """
    Выбрать плоский массив значений 0..255 для гистограммы.
    channel: "y" — яркость, "r", "g", "b" — отдельные каналы.
    Серое изображение подходит для любого канала (у него один канал).
    """
    if img.ndim == 2:
        return img.ravel()
    if channel == "r":
        return img[:, :, 0].ravel()
    if channel == "g":
        return img[:, :, 1].ravel()
    if channel == "b":
        return img[:, :, 2].ravel()
    gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
    return np.clip(np.round(gray), 0, 255).astype(np.uint8).ravel()


def compute_histogram(img, channel="y"):
    """256 чисел: сколько пикселей имеет яркость 0, 1, ... 255."""
    return np.bincount(channel_values(img, channel), minlength=256)


def normalized(hist):
    """Нормированная гистограмма: доли вместо количеств (сумма равна 1)."""
    return hist / hist.sum()


def cumulative(hist):
    """Накопленная гистограмма: сколько пикселей имеют яркость не больше v."""
    return np.cumsum(hist)


def stats(img, channel="y"):
    """Краткие числа по гистограмме: минимум, максимум, среднее, медиана."""
    v = channel_values(img, channel)
    return {"min": int(v.min()), "max": int(v.max()),
            "mean": float(v.mean()), "median": float(np.median(v))}
