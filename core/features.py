"""
Ключевые точки (особые точки): места, которые легко найти снова на другом снимке
(углы, пятна, резкие перепады яркости).

Реализованы три детектора из четырёх по заданию (SURF пропущен: он запатентован
и недоступен в обычной сборке OpenCV):
    Харрис — ищет углы по матрице производных;
    SIFT   — ищет устойчивые к масштабу и повороту пятна (+ умеет описывать их дескриптором);
    FAST   — очень быстрая проверка: «яркость пикселя заметно отличается от кольца вокруг».

Все детекторы здесь возвращают одно и то же: список точек [(x, y), ...].
"""
import cv2
import numpy as np

DETECTORS = ["Харрис", "SIFT", "FAST"]


def _to_gray(img):
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def harris(img, block_size=2, ksize=3, k=0.04, ratio=0.01):
    """
    Детектор Харриса. Для каждого пикселя по окну block_size x block_size считается матрица

        M = [ сумма Ix^2   сумма Ix*Iy ]       Ix, Iy — производные яркости по x и y
            [ сумма Ix*Iy  сумма Iy^2  ]

    и оценка угла  R = det(M) - k * (trace(M))^2.
        R большое положительное — угол (яркость меняется в обоих направлениях);
        R отрицательное — край (меняется в одном направлении);
        R около нуля — ровное место.
    Оставляем точки, где R > ratio * R_max и которые являются локальным максимумом (чтобы вокруг
    одного угла не было облака точек).
    """
    gray = np.float32(_to_gray(img))
    response = cv2.cornerHarris(gray, block_size, ksize, k)
    local_max = response == cv2.dilate(response, np.ones((5, 5), np.uint8))
    mask = (response > ratio * response.max()) & local_max
    ys, xs = np.nonzero(mask)
    return list(zip(xs.tolist(), ys.tolist()))


def sift_keypoints(img, max_points=0):
    """SIFT: список объектов cv2.KeyPoint (у каждого есть .pt = (x, y) и .size — масштаб)."""
    sift = cv2.SIFT_create(nfeatures=max_points)
    return sift.detect(_to_gray(img), None)


def sift(img, max_points=0):
    return [kp.pt for kp in sift_keypoints(img, max_points)]


def fast(img, threshold=20, nonmax=True):
    """
    FAST: вокруг пикселя берётся кольцо из 16 точек радиуса 3. Если подряд идут не менее
    9 точек кольца, которые все ярче центра на threshold или все темнее на threshold,
    пиксель считается углом. Метод очень быстрый, но не даёт дескриптора.
    """
    detector = cv2.FastFeatureDetector_create(threshold=int(threshold), nonmaxSuppression=nonmax)
    return [kp.pt for kp in detector.detect(_to_gray(img), None)]


def detect(name, img, **params):
    """Найти точки детектором по имени из DETECTORS. Возвращает список (x, y)."""
    if name == "Харрис":
        return harris(img, **params)
    if name == "SIFT":
        return sift(img, **params)
    if name == "FAST":
        return fast(img, **params)
    raise ValueError("Неизвестный детектор: " + name)


def draw_points(img, points, color=(255, 0, 0), radius=4):
    """Нарисовать кружки на копии картинки. Возвращает RGB-изображение."""
    out = np.ascontiguousarray(img if img.ndim == 3 else np.stack([img] * 3, axis=2)).copy()
    for x, y in points:
        cv2.circle(out, (int(round(x)), int(round(y))), radius, color, 1, cv2.LINE_AA)
    return out
