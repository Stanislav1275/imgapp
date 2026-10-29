"""
Создаёт рисунки для отчёта в папке report/figures/ и файл data.json с числами для текста отчёта.
Все картинки получены кодом проекта (папка core), ничего не нарисовано вручную.

Запуск из корня проекта:
    python make_samples.py                 # один раз
    python report/make_figures.py          # рисунки на тестовых данных
    python report/make_figures.py my.jpg   # анализ глубины цвета на ВАШЕЙ фотографии (рис. 1)
"""
import io
import json
import os
import sys

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core import (binarize, edges, features, filters, histogram, imageio, morphology,  # noqa: E402
                  similarity, tone, video)

OUT = os.path.join("report", "figures")
os.makedirs(OUT, exist_ok=True)
DATA = {}
plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "figure.dpi": 130})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def grid(images, titles, cols, name, figsize_per=(3.4, 2.4), cmap=None):
    rows = (len(images) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(figsize_per[0] * cols, figsize_per[1] * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax in axes:
        ax.axis("off")
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img, cmap="gray" if img.ndim == 2 else cmap, vmin=0, vmax=255)
        ax.set_title(title)
    fig.tight_layout()
    save(fig, name)


# ----------------------------------------------------------------------
# Рисунок 1: глубина цвета
# ----------------------------------------------------------------------
def gradient_test_image(w=480, h=300):
    """Плавный цветовой градиент: оттенок по горизонтали, яркость по вертикали, внизу серая шкала."""
    hue = np.tile(np.linspace(0, 179, w, dtype=np.float32), (h, 1))
    val = np.tile(np.linspace(255, 70, h, dtype=np.float32)[:, None], (1, w))
    sat = np.full((h, w), 230, np.float32)
    hsv = np.stack([hue, sat, val], axis=2).astype(np.uint8)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    ramp = np.tile(np.linspace(0, 255, w).astype(np.uint8), (40, 1))
    img[-40:] = np.stack([ramp] * 3, axis=2)
    return img


def png_size(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, "PNG", optimize=True)
    return buf.tell()


def depth_figure(src):
    pil = Image.fromarray(src)
    rows, shown, titles = [], [], []
    h, w = src.shape[:2]

    def add(label, bits, pil_out, shown_rgb):
        arr = np.asarray(shown_rgb.convert("RGB"))
        packed = (arr[:, :, 0].astype(np.uint32) << 16) | (arr[:, :, 1].astype(np.uint32) << 8) | arr[:, :, 2]
        rows.append({"label": label, "bits": bits, "colors_max": 2 ** bits, "colors_used": int(np.unique(packed).size),
                     "png_bytes": png_size(pil_out), "raw_bytes": w * h * bits // 8})
        shown.append(arr)
        titles.append("{} ({} бит)".format(label, bits))

    add("True Color", 24, pil, pil)
    r = [(src[:, :, 0] >> 3).astype(np.float64), (src[:, :, 1] >> 2).astype(np.float64),
         (src[:, :, 2] >> 3).astype(np.float64)]                              # 5-6-5, в дробных числах (без переполнения uint8)
    hi = np.stack([np.round(r[0] * 255 / 31), np.round(r[1] * 255 / 63), np.round(r[2] * 255 / 31)], axis=2)
    hi = Image.fromarray(hi.astype(np.uint8))
    add("High Color 5-6-5", 16, hi, hi)
    for bits, label in ((8, "256 цветов"), (4, "16 цветов"), (2, "4 цвета")):
        p = pil.quantize(colors=2 ** bits, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        add(label, bits, p, p)
    one = pil.convert("L").convert("1")                                       # дизеринг Флойда-Стейнберга
    add("2 цвета, дизеринг", 1, one, one)
    grid(shown, titles, 3, "fig01_depth.png", (3.5, 2.5))
    return rows


# ----------------------------------------------------------------------
# Рисунок 2 и 3: пояснения к формулам
# ----------------------------------------------------------------------
def hue_figure():
    H = np.linspace(0, 360, 721)
    rgb = []
    for h in H:
        R, G, B = [v / 255 for v in __import__("core.colorspaces", fromlist=["x"]).hsv_to_rgb(h % 360, 1, 1)]
        rgb.append((R, G, B))
    rgb = np.array(rgb)
    fig, (ax, strip) = plt.subplots(2, 1, figsize=(8, 3.6), gridspec_kw={"height_ratios": [4, 0.7]}, sharex=True)
    for k, (c, name) in enumerate(zip(("#d62728", "#2ca02c", "#1f77b4"), ("r", "g", "b"))):
        ax.plot(H, rgb[:, k], color=c, lw=2.2, label=name)
    for x in range(0, 361, 60):
        ax.axvline(x, color="#bbb", lw=0.8, ls=":")
    ax.set_ylabel("значение канала")
    ax.set_title("Каналы r, g, b при S = V = 1 как функции оттенка H (шесть секторов по 60°)")
    ax.legend(loc="center right")
    strip.imshow(rgb[None, :, :], aspect="auto", extent=[0, 360, 0, 1])
    strip.set_yticks([])
    strip.set_xticks(range(0, 361, 60))
    strip.set_xlabel("H, градусы")
    fig.tight_layout()
    save(fig, "fig02_hue.png")


def srgb_figure():
    from core import colorspaces as cs
    L = np.linspace(0, 1, 1001)
    c = np.array([cs.linear_to_srgb(v) for v in L])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    a1.plot(L, c, lw=2.2, label="sRGB (две ветки)")
    a1.plot(L, L ** (1 / 2.2), "--", color="#d62728", label="L^(1/2.2)")
    a1.plot(L, L, ":", color="#777", label="без кодирования")
    a1.set_xlabel("линейная яркость L")
    a1.set_ylabel("закодированное значение c")
    a1.legend()
    a1.set_title("Кодирование sRGB")
    z = np.linspace(0, 0.02, 400)
    a2.plot(z, [cs.linear_to_srgb(v) for v in z], lw=2.2, label="sRGB")
    a2.plot(z, 12.92 * z, "--", color="#2ca02c", label="прямая 12.92·L")
    a2.plot(z, 1.055 * z ** (1 / 2.4) - 0.055, ":", color="#d62728", label="1.055·L^(1/2.4) − 0.055")
    a2.axvline(0.0031308, color="#777", lw=0.8)
    a2.set_ylim(0, 0.2)
    a2.set_xlabel("L (увеличено около нуля)")
    a2.legend(loc="lower right")
    a2.set_title("Стык двух веток при L = 0.0031308")
    fig.tight_layout()
    save(fig, "fig03_srgb.png")


# ----------------------------------------------------------------------
# Яркостные преобразования
# ----------------------------------------------------------------------
def tone_curves():
    r = np.arange(256, dtype=np.float64)
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
    for beta in (-50, 0, 50):
        axes[0].plot(r, np.clip(r + beta, 0, 255), label="β = {}".format(beta))
    axes[0].set_title("Яркость: s = r + β")
    for alpha in (0.5, 1, 1.5, 2):
        axes[1].plot(r, np.clip(alpha * (r - 128) + 128, 0, 255), label="α = {}".format(alpha))
    axes[1].set_title("Контраст: s = α(r − 128) + 128")
    for g in (0.5, 1, 2):
        axes[2].plot(r, 255 * (r / 255) ** g, label="γ = {}".format(g))
    axes[2].set_title("Гамма: s = 255(r/255)^γ")
    for ax in axes:
        ax.set_xlabel("r (до)")
        ax.set_xlim(0, 255)
        ax.set_ylim(0, 255)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("s (после)")
    fig.tight_layout()
    save(fig, "fig04_tone_curves.png")


def tone_results(scene):
    items = [scene, tone.adjust_brightness(scene, 60), tone.adjust_contrast(scene, 1.5),
             tone.adjust_gamma(scene, 0.5), tone.adjust_saturation(scene, 2.0), tone.to_gray(scene)]
    titles = ["Исходное", "Яркость β = +60", "Контраст α = 1.5", "Гамма γ = 0.5", "Насыщенность k = 2", "Серое (Y)"]
    grid(items, titles, 3, "fig05_tone.png")


def hist_figures(scene):
    fig, axes = plt.subplots(1, 4, figsize=(12, 2.6), sharey=False)
    for ax, (code, title, color) in zip(axes, (("y", "Яркость Y", "#555"), ("r", "Канал R", "#d62728"),
                                               ("g", "Канал G", "#2ca02c"), ("b", "Канал B", "#1f77b4"))):
        ax.bar(range(256), histogram.compute_histogram(scene, code), width=1.0, color=color)
        ax.set_title(title)
        ax.set_xlim(0, 255)
    fig.tight_layout()
    save(fig, "fig06a_hist_channels.png")

    before = histogram.compute_histogram(scene, "y")
    fig, axes = plt.subplots(1, 3, figsize=(11, 2.9), sharey=True)
    for ax, (title, out) in zip(axes, (("Яркость β = −60", tone.adjust_brightness(scene, -60)),
                                       ("Контраст α = 1.5", tone.adjust_contrast(scene, 1.5)),
                                       ("Гамма γ = 0.5", tone.adjust_gamma(scene, 0.5)))):
        after = histogram.compute_histogram(out, "y")
        ax.bar(range(256), after, width=1.0, color="#d9822b", alpha=0.75, label="после")
        ax.plot(range(256), before, color="#333", lw=1.2, label="до")
        ax.set_ylim(0, before.max())                          # шкала по «до», как в программе
        ax.set_xlim(0, 255)
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "fig06b_hist_before_after.png")


# ----------------------------------------------------------------------
# Морфология, бинаризация
# ----------------------------------------------------------------------
def binary_with_noise():
    img = np.zeros((220, 320), np.uint8)
    cv2.rectangle(img, (30, 40), (130, 170), 255, -1)
    cv2.circle(img, (220, 105), 55, 255, -1)
    cv2.line(img, (30, 195), (300, 195), 255, 3)
    rng = np.random.default_rng(3)
    chance = rng.random(img.shape)
    out = img.copy()
    out[(img == 0) & (chance < 0.012)] = 255            # белый шум на фоне (соль)
    out[(img == 255) & (chance < 0.03)] = 0             # чёрные дырки в объектах (перец)
    return out


def morph_figure(coins_gray):
    k = morphology.make_kernel(size=3)
    noisy = binary_with_noise()
    items = [noisy] + [morphology.apply(c, noisy, k) for c in ("erode", "dilate", "open", "close", "gradient")]
    titles = ["Исходное (шум и дырки)", "Эрозия", "Дилатация", "Открытие", "Закрытие", "Градиент"]
    grid(items, titles, 3, "fig07_morph.png", (3.3, 2.5))
    binary, T = binarize.otsu(coins_gray)
    k5 = morphology.make_kernel(size=5)
    items = [binary] + [morphology.apply(c, binary, k5) for c in ("erode", "dilate", "open", "close", "gradient")]
    grid(items, titles[:1] and ["Монеты, бинаризация Оцу (T = {})".format(T), "Эрозия 5×5", "Дилатация 5×5",
                                "Открытие 5×5", "Закрытие 5×5", "Градиент 5×5"], 3, "fig07b_morph_coins.png", (3.3, 2.5))


def binarization_figure(photo):
    gray = photo if photo.ndim == 2 else tone.to_gray(photo)
    h, w = gray.shape
    light = np.tile(np.linspace(0.35, 1.0, w), (h, 1))               # неравномерное освещение слева направо
    uneven = np.clip(gray * light, 0, 255).astype(np.uint8)
    otsu_img, T = binarize.otsu(uneven)
    items = [uneven, binarize.threshold(uneven, 128), otsu_img, binarize.adaptive(uneven, 31, 6)]
    titles = ["Серое, неравномерный свет", "Глобальный порог T = 128",
              "Оцу (T = {})".format(T), "Адаптивный (окно 31, C = 6)"]
    grid(items, titles, 2, "fig08_binarization.png", (4.2, 2.8))
    fig, ax = plt.subplots(figsize=(6, 2.6))
    ax.bar(range(256), histogram.compute_histogram(uneven), width=1.0, color="#777")
    ax.axvline(T, color="#d62728", lw=2, label="порог Оцу T = {}".format(T))
    ax.set_xlim(0, 255)
    ax.legend()
    ax.set_title("Гистограмма и порог, найденный методом Оцу")
    fig.tight_layout()
    save(fig, "fig08b_otsu_hist.png")
    return T


def contours_figure():
    img = np.zeros((260, 360), np.uint8)
    cv2.rectangle(img, (20, 20), (240, 240), 255, -1)       # 0: большой квадрат
    cv2.circle(img, (130, 130), 80, 0, -1)                  # его «дыра»: чёрный круг
    cv2.rectangle(img, (90, 90), (170, 170), 255, -1)       # белый квадрат внутри дыры
    cv2.circle(img, (130, 130), 20, 0, -1)                  # чёрная дырка внутри маленького квадрата
    cv2.circle(img, (305, 70), 36, 255, -1)                 # отдельный круг справа
    cv2.rectangle(img, (270, 170), (340, 235), 255, -1)     # отдельный прямоугольник
    contours, hier = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    canvas = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    palette = [(220, 40, 40), (40, 160, 70), (40, 90, 230), (230, 140, 20), (150, 40, 200), (0, 160, 170)]
    rows = []
    for i, c in enumerate(contours):
        cv2.drawContours(canvas, contours, i, palette[i % len(palette)], 2)
        m = cv2.moments(c)
        x, y = c[0][0]
        cv2.putText(canvas, str(i), (int(x) + 4, int(y) + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    palette[i % len(palette)], 2)
        rows.append([i] + [int(v) for v in hier[0][i]])
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    ax.imshow(canvas)
    ax.axis("off")
    ax.set_title("Контуры RETR_TREE и их номера")
    save(fig, "fig09_hierarchy.png")
    _, hier_ext = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return rows, len(contours), len(cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0])


# ----------------------------------------------------------------------
# Фильтры, ключевые точки, сходство, видео
# ----------------------------------------------------------------------
def filters_figure(scene):
    gray = tone.to_gray(scene)
    noisy = filters.add_salt_pepper(scene, 0.06, seed=0)
    items = [scene, filters.sharpen(scene), filters.motion_blur(scene, 21, 20), filters.emboss(scene),
             noisy, filters.median(noisy, 3), edges.canny(gray, 80, 160), edges.roberts(gray, normalize=True)]
    titles = ["Исходное", "Резкость", "Размытие в движении (L = 21, 20°)", "Тиснение",
              "Шум «соль и перец»", "Медиана 3×3", "Canny (80; 160)", "Робертс (нормировано)"]
    grid(items, titles, 4, "fig10_filters.png", (3.1, 2.2))


def keypoints_figure(scene):
    items, titles, counts = [], [], {}
    for name in features.DETECTORS:
        pts = features.detect(name, scene)
        counts[name] = len(pts)
        items.append(features.draw_points(scene, pts, (255, 0, 0), 3))
        titles.append("{}: {} точек".format(name, len(pts)))
    grid(items, titles, 3, "fig11_keypoints.png", (3.7, 2.5))
    return counts


def similarity_figure():
    names = ["photo_chelsea.png", "photo_chelsea_edit.png", "photo_astronaut.png", "photo_rocket.png",
             "photo_coffee.jpg"]
    images = [imageio.load_image("samples/" + n) for n in names]
    i, j, score, matrix = similarity.most_similar_pair(images)
    n = len(names)
    fig = plt.figure(figsize=(13, 3.2))
    for k, (img, name) in enumerate(zip(images, names)):
        ax = fig.add_subplot(1, n + 2, k + 1)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title("{}: {}".format(k, name.replace("photo_", "")), fontsize=8, color="#d62728" if k in (i, j) else "black")
    ax = fig.add_subplot(1, n + 2, (n + 1, n + 2))
    im = ax.imshow(matrix, cmap="viridis", vmin=0, vmax=1)
    for a in range(n):
        for b in range(n):
            ax.text(b, a, "{:.2f}".format(matrix[a, b]), ha="center", va="center",
                    color="white" if matrix[a, b] < 0.6 else "black")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_title("Матрица оценок")
    fig.tight_layout()
    save(fig, "fig12_similarity.png")
    return names[i], names[j], score, matrix.round(3).tolist()


def video_figure():
    frames = list(video.read_frames("samples/moving.avi", 60))
    detector = video.MotionDetector()
    last_mask = None
    for f in frames:
        last_mask = detector.mask(f)
    f = frames[-1]
    items = [f, np.stack([last_mask] * 3, axis=2), video.foreground(f, last_mask), video.blur_moving(f, last_mask)]
    titles = ["Кадр 60", "Маска движения (MOG2)", "Только движущееся", "Размытие движущегося"]
    grid(items, titles, 4, "fig13_video.png", (3.0, 2.0))


def canny_figure(scene):
    """Шесть шагов Canny на одном снимке и влияние порогов; числа для текста отчёта."""
    gray = tone.to_gray(scene)
    steps = edges.canny_steps(gray, 50, 150, 1.4)
    pictures = edges.canny_stage_images(gray, steps)
    grid([p for _t, p in pictures], [t for t, _p in pictures], 3, "fig14_canny_steps.png", (3.6, 2.5), cmap="gray")
    pairs = [(20, 60), (50, 150), (100, 200)]
    results = [edges.canny(gray, lo, hi) for lo, hi in pairs]
    grid(results, ["пороги {} / {}: {} точек".format(lo, hi, int((r > 0).sum())) for (lo, hi), r in zip(pairs, results)],
         3, "fig15_canny_thresholds.png", (3.6, 2.5), cmap="gray")
    reference = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 1.4), 50, 150, L2gradient=True) > 0
    own = steps["edges"] > 0
    return {"pixels": int(gray.size), "magnitude_over_low": int((steps["magnitude"] >= 50).sum()),
            "after_nms": int((steps["thin"] >= 50).sum()), "strong": int(steps["strong"].sum()),
            "weak": int(steps["weak"].sum()), "final": int(own.sum()),
            "weak_kept": int(own.sum() - steps["strong"].sum()),
            "opencv_final": int(reference.sum()), "overlap": round(float((own & reference).sum() / max(own.sum(), reference.sum())), 4),
            "counts_by_thresholds": {"{}/{}".format(lo, hi): int((r > 0).sum()) for (lo, hi), r in zip(pairs, results)}}


def main():
    scene = imageio.load_image("samples/photo_coffee.jpg")
    coins = tone.to_gray(imageio.load_image("samples/photo_coins.png"))
    astronaut = imageio.load_image("samples/photo_astronaut.png")
    src = imageio.load_image(sys.argv[1]) if len(sys.argv) > 1 else imageio.load_image("samples/photo_chelsea.png")
    if src.shape[1] > 900:
        scale = 900 / src.shape[1]
        src = cv2.resize(src, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    DATA["depth"] = depth_figure(src)
    hue_figure()
    srgb_figure()
    tone_curves()
    tone_results(scene)
    hist_figures(scene)
    morph_figure(coins)
    DATA["otsu_T_uneven"] = binarization_figure(coins)
    rows, n_tree, n_ext = contours_figure()
    DATA["hierarchy"] = {"rows": rows, "n_tree": n_tree, "n_external": n_ext}
    filters_figure(scene)
    DATA["keypoints"] = keypoints_figure(astronaut)
    a, b, score, matrix = similarity_figure()
    DATA["similarity"] = {"a": a, "b": b, "score": score, "matrix": matrix}
    video_figure()
    DATA["canny"] = canny_figure(scene)
    with open(os.path.join(OUT, "data.json"), "w", encoding="utf8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=1)
    print(json.dumps(DATA, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
