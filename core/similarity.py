"""
Поиск двух самых похожих изображений среди 3..10 загруженных.

Основной метод — по ключевым точкам SIFT:
  1. У каждого изображения находим точки SIFT и их дескрипторы (вектор из 128 чисел, «отпечаток» окрестности).
  2. Для пары изображений ищем для каждого дескриптора первого его двух ближайших соседей во втором.
  3. Тест Лоу: совпадение считается хорошим, если ближайший сосед заметно ближе второго
     (расстояние1 < 0.75 * расстояние2). Это отсеивает случайные совпадения.
  4. Оценка похожести пары = (число хороших совпадений) / (меньшее из чисел точек двух изображений).
Пара с наибольшей оценкой — самые похожие изображения.

Дополнительный метод — сравнение цветовых гистограмм (быстрее, но не видит содержание).
"""
import itertools

import cv2
import numpy as np

MAX_SIDE = 512          # перед поиском точек уменьшаем большую картинку, чтобы считалось быстро
RATIO = 0.75            # порог теста Лоу


def _resize(img):
    h, w = img.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def sift_descriptors(img):
    """Возвращает (число точек, массив дескрипторов или None)."""
    gray = cv2.cvtColor(_resize(img), cv2.COLOR_RGB2GRAY) if img.ndim == 3 else _resize(img)
    keypoints, desc = cv2.SIFT_create().detectAndCompute(gray, None)
    return len(keypoints), desc


def sift_score(info_a, info_b):
    """Оценка похожести двух изображений по их (число точек, дескрипторы). Число от 0 до 1."""
    n_a, desc_a = info_a
    n_b, desc_b = info_b
    if desc_a is None or desc_b is None or min(n_a, n_b) < 2:
        return 0.0
    pairs = cv2.BFMatcher(cv2.NORM_L2).knnMatch(desc_a, desc_b, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < RATIO * p[1].distance]
    return len(good) / min(n_a, n_b)


def histogram_score(img_a, img_b):
    """Корреляция цветовых гистограмм HSV (от -1 до 1; чем больше, тем больше похожи по цветам)."""
    def hist(img):
        hsv = cv2.cvtColor(_resize(img), cv2.COLOR_RGB2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        return cv2.normalize(h, h).flatten()
    return float(cv2.compareHist(hist(img_a), hist(img_b), cv2.HISTCMP_CORREL))


def similarity_matrix(images, method="sift"):
    """Матрица N x N оценок похожести (на диагонали 1)."""
    n = len(images)
    matrix = np.eye(n)
    if method == "sift":
        infos = [sift_descriptors(img) for img in images]
        score = lambda i, j: sift_score(infos[i], infos[j])
    else:
        score = lambda i, j: histogram_score(images[i], images[j])
    for i, j in itertools.combinations(range(n), 2):
        matrix[i, j] = matrix[j, i] = score(i, j)
    return matrix


def most_similar_pair(images, method="sift"):
    """
    Найти два самых похожих изображения.
    Возвращает (i, j, оценка, матрица). Нужно от 2 изображений; по заданию от 3 до 10.
    """
    if len(images) < 2:
        raise ValueError("Нужно минимум два изображения")
    matrix = similarity_matrix(images, method)
    best = max(itertools.combinations(range(len(images)), 2), key=lambda p: matrix[p[0], p[1]])
    return best[0], best[1], float(matrix[best[0], best[1]]), matrix
