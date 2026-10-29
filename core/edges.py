"""
Поиск границ: оператор Робертса и детектор Canny.

Граница — это место, где яркость резко меняется. Оценить «резкость изменения» можно
по разностям соседних пикселей (градиенту).
"""
import cv2
import numpy as np


def roberts(gray, normalize=False):
    """
    Оператор Робертса — разности по двум диагоналям окна 2x2:

        окно:  a b        Gx = a - d   (ядро [[ 1, 0], [ 0,-1]])
               c d        Gy = b - c   (ядро [[ 0, 1], [-1, 0]])

        G = sqrt(Gx^2 + Gy^2)  — сила границы в этой точке.

    Результат ограничиваем до 255. Размер картинки сохраняется: последняя строка и столбец
    (где окно 2x2 не помещается) остаются нулями.
    normalize=True растягивает результат так, чтобы самая сильная граница стала 255
    (для наглядности: слабые границы лучше видны на экране).
    """
    g = gray.astype(np.float64)
    a = g[:-1, :-1]
    b = g[:-1, 1:]
    c = g[1:, :-1]
    d = g[1:, 1:]
    gx = a - d
    gy = b - c
    strength = np.sqrt(gx ** 2 + gy ** 2)
    out = np.zeros_like(g)
    out[:-1, :-1] = strength
    if normalize and out.max() > 0:
        out = out / out.max() * 255
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def canny(gray, low=100, high=200, blur=True):
    """
    Детектор Canny: бинарная карта тонких границ (255 — граница). Считается своей реализацией
    canny_steps (см. ниже), где видны все пять шагов.
        градиент >= high  — «сильная» граница, сохраняется;
        low <= градиент < high — «слабая», сохраняется только если связана с сильной;
        градиент < low — отбрасывается.
    Обычно high : low = 2:1 … 3:1. blur=False отключает сглаживание.
    """
    return canny_steps(gray, low, high, sigma=1.4 if blur else 0)["edges"]


# ----------------------------------------------------------------------
# Canny по шагам (своя реализация на NumPy — чтобы видеть каждый этап)
# ----------------------------------------------------------------------

def sobel(gray):
    """
    Градиент по Собелю. Ядра 3x3:
        Kx = [[-1, 0, 1],        Ky = [[-1,-2,-1],
              [-2, 0, 2],               [ 0, 0, 0],
              [-1, 0, 1]]               [ 1, 2, 1]]
    Gx — перепад яркости слева направо, Gy — сверху вниз.
    Возвращает (величина G = sqrt(Gx^2 + Gy^2), направление theta = atan2(Gy, Gx) в градусах).
    """
    g = np.pad(gray.astype(np.float64), 1, mode="edge")           # рамка из копий краёв, чтобы окно помещалось
    h, w = gray.shape
    # g[y + dy, x + dx] для всех пикселей сразу: срезы массива вместо двух вложенных циклов
    def shifted(dy, dx):
        return g[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    gx = (shifted(-1, 1) + 2 * shifted(0, 1) + shifted(1, 1)) - (shifted(-1, -1) + 2 * shifted(0, -1) + shifted(1, -1))
    gy = (shifted(1, -1) + 2 * shifted(1, 0) + shifted(1, 1)) - (shifted(-1, -1) + 2 * shifted(-1, 0) + shifted(-1, 1))
    return np.hypot(gx, gy), np.degrees(np.arctan2(gy, gx))


def non_max_suppression(magnitude, angle):
    """
    Подавление немаксимумов: оставляем пиксель, только если он сильнее двух соседей ВДОЛЬ градиента
    (поперёк границы). Так толстая граница сжимается до линии в один пиксель.
    Направление градиента округляется до одного из четырёх: 0°, 45°, 90°, 135°.
    """
    h, w = magnitude.shape
    a = angle % 180                                    # направление «туда» и «обратно» — одна и та же ось
    m = np.pad(magnitude, 1, mode="constant")

    def neighbor(dy, dx):
        return m[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]

    out = np.zeros_like(magnitude)
    sectors = [
        ((a < 22.5) | (a >= 157.5), (0, 1), (0, -1)),       # градиент горизонтален: соседи слева и справа
        ((a >= 22.5) & (a < 67.5), (1, 1), (-1, -1)),       # диагональ «\»
        ((a >= 67.5) & (a < 112.5), (1, 0), (-1, 0)),       # градиент вертикален: соседи сверху и снизу
        ((a >= 112.5) & (a < 157.5), (1, -1), (-1, 1)),     # диагональ «/»
    ]
    for mask, (dy1, dx1), (dy2, dx2) in sectors:
        keep = mask & (magnitude > neighbor(dy1, dx1)) & (magnitude >= neighbor(dy2, dx2))   # > с одной стороны: при равенстве остаётся один пиксель
        out[keep] = magnitude[keep]
    return out


def double_threshold(thin, low, high):
    """Двойной порог: сильные (>= high), слабые (low <= G < high), остальное отбрасываем."""
    strong = thin >= high
    weak = (thin >= low) & ~strong
    return strong, weak


def hysteresis(strong, weak):
    """
    Гистерезис: слабая граница остаётся, только если она цепочкой соединена с сильной.
    Начинаем с сильных и по кругу добавляем слабых соседей (8 направлений), пока что-то добавляется.
    """
    result = strong.copy()
    while True:
        p = np.pad(result, 1, mode="constant")
        near_result = np.zeros_like(result)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near_result |= p[1 + dy:1 + dy + result.shape[0], 1 + dx:1 + dx + result.shape[1]]
        grown = result | (weak & near_result)
        if grown.sum() == result.sum():
            return grown
        result = grown


def canny_steps(gray, low=50, high=150, sigma=1.4):
    """
    Canny целиком, с промежуточными результатами (sigma = 0 — без сглаживания). Возвращает словарь:
        blurred   — после сглаживания Гауссом (sigma);
        magnitude — сила градиента G;
        thin      — после подавления немаксимумов;
        strong, weak — маски после двойного порога;
        edges     — итог после гистерезиса: массив uint8, 255 = граница.
    """
    blurred = cv2.GaussianBlur(gray, (0, 0), sigma) if sigma > 0 else gray   # ядро подбирается по sigma
    magnitude, angle = sobel(blurred)
    thin = non_max_suppression(magnitude, angle)
    strong, weak = double_threshold(thin, low, high)
    edge_mask = hysteresis(strong, weak)
    return {"blurred": blurred, "magnitude": magnitude, "thin": thin, "strong": strong, "weak": weak,
            "edges": edge_mask.astype(np.uint8) * 255}


def canny_stage_images(gray, steps):
    """
    Шесть картинок для показа по шагам (серые uint8): исходное, сглаженное, сила градиента,
    после подавления немаксимумов, двойной порог (белое — сильные, серое — слабые), итог.
    Силу градиента растягиваем на 0..255, иначе слабые границы не видны.
    """
    def stretch(a):
        top = a.max()
        return np.zeros(a.shape, np.uint8) if top == 0 else np.clip(np.rint(a / top * 255), 0, 255).astype(np.uint8)

    thresholds = np.zeros(gray.shape, np.uint8)
    thresholds[steps["weak"]] = 110
    thresholds[steps["strong"]] = 255
    return [("1. Исходное (серое)", gray),
            ("2. Сглаживание (Гаусс)", steps["blurred"]),
            ("3. Градиент: сила границы", stretch(steps["magnitude"])),
            ("4. Подавление немаксимумов", stretch(steps["thin"])),
            ("5. Двойной порог (белое — сильные, серое — слабые)", thresholds),
            ("6. Гистерезис: итог", steps["edges"])]
