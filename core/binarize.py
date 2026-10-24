"""
Бинаризация: превращаем серое изображение в чёрно-белое (только 0 и 255).

Правило одно для всех способов:
    s = 255, если r > T, иначе 0
    r — яркость пикселя до, s — после, T — порог.
Способы отличаются только тем, откуда берётся T.
"""
import cv2
import numpy as np


def threshold(gray, T):
    """Глобальный порог: T задан вручную."""
    return np.where(gray > T, 255, 0).astype(np.uint8)


def otsu_threshold(gray):
    """
    Метод Оцу: перебираем все T от 0 до 254 и выбираем то, при котором
    межклассовая дисперсия максимальна:
        sigma_b^2(T) = w0 * w1 * (mu0 - mu1)^2
    w0, w1 — доли тёмных (r <= T) и светлых (r > T) пикселей, mu0, mu1 — их средние яркости.
    Возвращает найденный порог T (при равных значениях — наименьший).
    """
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    levels = np.arange(256)
    best_T, best_sigma = 0, -1.0
    for T in range(255):
        n0 = hist[:T + 1].sum()
        n1 = total - n0
        if n0 == 0 or n1 == 0:
            continue
        mu0 = (hist[:T + 1] * levels[:T + 1]).sum() / n0
        mu1 = (hist[T + 1:] * levels[T + 1:]).sum() / n1
        sigma = (n0 / total) * (n1 / total) * (mu0 - mu1) ** 2
        if sigma > best_sigma:
            best_sigma, best_T = sigma, T
    return best_T


def otsu(gray):
    """Бинаризация с автоподбором порога по Оцу. Возвращает (картинка, найденный T)."""
    T = otsu_threshold(gray)
    return threshold(gray, T), T


def adaptive(gray, block_size=11, C=2):
    """
    Адаптивный порог: T свой для каждого пикселя = среднее по окну block_size x block_size минус C.
    Помогает, когда освещение неравномерное.
    """
    if block_size % 2 == 0:
        block_size += 1                    # окно должно быть нечётным
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                 cv2.THRESH_BINARY, block_size, C)
