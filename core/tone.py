"""
Яркостные преобразования: серое, яркость, контраст, гамма, насыщенность,
линейная и нелинейная коррекция чёрно-белого.

Идея всех преобразований одна: для каждого пикселя считаем новое значение s по старому r.
  r — яркость до (0..255),  s — яркость после (0..255).
Значения за пределами 0..255 обрезаются (clip).

Нейтральные значения (при них картинка не меняется):
    яркость  beta  = 0      контраст  alpha = 1
    гамма    gamma = 1      насыщенность k  = 1
"""
import numpy as np


def _clip_to_uint8(x):
    """Обрезать массив чисел до 0..255 и сделать из него изображение uint8."""
    return np.clip(np.round(x), 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------
# Серое
# ----------------------------------------------------------------------

def to_gray(img):
    """Цветное -> серое: Y = 0.299 R + 0.587 G + 0.114 B. Результат (H, W)."""
    r = img[:, :, 0].astype(np.float64)
    g = img[:, :, 1].astype(np.float64)
    b = img[:, :, 2].astype(np.float64)
    return _clip_to_uint8(0.299 * r + 0.587 * g + 0.114 * b)


# ----------------------------------------------------------------------
# Четыре основных параметра
# ----------------------------------------------------------------------

def adjust_brightness(img, beta):
    """Яркость: прибавить число к каждому пикселю. s = r + beta."""
    return _clip_to_uint8(img.astype(np.float64) + beta)


def adjust_contrast(img, alpha):
    """Контраст: растянуть разницу от середины 128 в alpha раз. s = alpha * (r - 128) + 128."""
    return _clip_to_uint8(alpha * (img.astype(np.float64) - 128) + 128)


def adjust_gamma(img, gamma):
    """
    Гамма: s = 255 * (r / 255) ^ gamma.
    gamma < 1 — светлее (тени поднимаются), gamma > 1 — темнее. 0 и 255 остаются на месте.
    """
    return _clip_to_uint8(255 * (img.astype(np.float64) / 255) ** gamma)


def adjust_saturation(img, k):
    """
    Насыщенность: отодвинуть каждый канал от серого цвета пикселя в k раз.
        gray = 0.299 R + 0.587 G + 0.114 B
        c' = gray + k * (c - gray)
    k = 0 даёт серое изображение, k = 1 — без изменений, k > 1 — ярче цвета.
    """
    x = img.astype(np.float64)
    gray = (0.299 * x[:, :, 0] + 0.587 * x[:, :, 1] + 0.114 * x[:, :, 2])[:, :, None]
    return _clip_to_uint8(gray + k * (x - gray))


def adjust_all(img, beta=0.0, alpha=1.0, gamma=1.0, k=1.0):
    """
    Все четыре сразу в фиксированном порядке: насыщенность -> гамма -> контраст -> яркость.
    Именно в таком порядке считает и демонстрационный стенд в курсе.
    Для серого изображения насыщенность пропускается.
    """
    out = img
    if out.ndim == 3 and k != 1.0:
        out = adjust_saturation(out, k)
    if gamma != 1.0:
        out = adjust_gamma(out, gamma)
    if alpha != 1.0:
        out = adjust_contrast(out, alpha)
    if beta != 0.0:
        out = adjust_brightness(out, beta)
    return out


def slider_to_params(brightness_slider, contrast_slider, gamma_slider, saturation_slider=100):
    """
    Перевод положений ползунков в числа формул (так договорились в курсе):
        яркость  −100..100  ->  beta  = 2.55 * значение   (−255..255)
        контраст −100..100  ->  alpha = 1 + значение / 100 (0..2)
        гамма    20..300    ->  gamma = значение / 100     (0.2..3)
        насыщенность 0..200 ->  k     = значение / 100     (0..2)
    """
    return (2.55 * brightness_slider,
            1 + contrast_slider / 100,
            gamma_slider / 100,
            saturation_slider / 100)


# ----------------------------------------------------------------------
# Коррекция чёрно-белого изображения
# ----------------------------------------------------------------------

def linear_stretch(gray):
    """
    ЛИНЕЙНАЯ коррекция: растянуть фактический диапазон [min, max] на весь [0, 255].
        s = (r - min) / (max - min) * 255
    """
    lo, hi = int(gray.min()), int(gray.max())
    if hi == lo:
        return gray.copy()
    return _clip_to_uint8((gray.astype(np.float64) - lo) / (hi - lo) * 255)


def negative(gray):
    """ЛИНЕЙНАЯ коррекция (инверсия): s = 255 - r."""
    return 255 - gray


def log_transform(gray):
    """
    НЕЛИНЕЙНАЯ коррекция: логарифм. s = c * ln(1 + r), c = 255 / ln(256).
    Сильно поднимает тёмные участки, светлые почти не трогает.
    """
    c = 255 / np.log(256)
    return _clip_to_uint8(c * np.log1p(gray.astype(np.float64)))


def gamma_gray(gray, gamma):
    """НЕЛИНЕЙНАЯ коррекция: степенная (гамма), та же формула, что для цветного."""
    return adjust_gamma(gray, gamma)


def equalize(gray):
    """
    НЕЛИНЕЙНАЯ коррекция: выравнивание гистограммы.
    Идея: новое значение = доля пикселей не ярче данного, умноженная на 255.
        cdf(v) = число пикселей с яркостью <= v   (накопленная гистограмма)
        s = (cdf(r) - cdf_min) / (N - cdf_min) * 255
    """
    hist = np.bincount(gray.ravel(), minlength=256)
    cdf = np.cumsum(hist)
    cdf_min = cdf[np.nonzero(hist)[0][0]]          # первая ненулевая точка
    total = gray.size
    if total == cdf_min:                           # одноцветное изображение
        return gray.copy()
    lut = np.round((cdf - cdf_min) / (total - cdf_min) * 255)
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return lut[gray]
