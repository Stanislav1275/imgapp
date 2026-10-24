"""
Демонстрация без окна: прогоняет ВСЕ функции программы на примерах из samples/
и сохраняет результаты в папку demo_output/ (удобно для скриншотов в отчёт и для проверки).

Запуск:
    python make_samples.py     # один раз, создаст samples/
    python run_demo.py
"""
import os

import numpy as np

from core import (binarize, colorspaces, edges, features, filters, histogram, imageio,
                  info, morphology, similarity, tone, video)

OUT = "demo_output"


def save(name, img):
    imageio.save_image(os.path.join(OUT, name), img)


def hist_picture(hists, colors, width=512, height=200):
    """Простая картинка-гистограмма (столбики) для отчёта; hists — список гистограмм, colors — цвета RGB."""
    canvas = np.full((height, width, 3), 255, np.uint8)
    top = max(1, max(int(h.max()) for h in hists))
    for h, color in zip(hists, colors):
        for v in range(256):
            bar = int(h[v] / top * (height - 10))
            x0, x1 = v * width // 256, (v + 1) * width // 256
            region = canvas[height - bar:, x0:x1]
            canvas[height - bar:, x0:x1] = (0.5 * region + 0.5 * np.array(color)).astype(np.uint8)
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    path = "samples/scene.png"
    img = imageio.load_image(path)

    print("== Информация о файле ==")
    for key, value in info.get_image_info(path).items():
        print("  {:<24} {}".format(key, value))

    print("== Перевод цвета (255, 128, 0) ==")
    for model in colorspaces.MODELS:
        print("  RGB -> {:<6} {}".format(model, np.round(colorspaces.convert((255, 128, 0), "RGB", model), 3)))

    gray = tone.to_gray(img)
    save("01_gray.png", gray)

    save("02_bright_plus.png", tone.adjust_brightness(img, 60))
    save("03_contrast_1.5.png", tone.adjust_contrast(img, 1.5))
    save("04_gamma_0.5.png", tone.adjust_gamma(img, 0.5))
    save("05_saturation_2.png", tone.adjust_saturation(img, 2.0))

    h_before = histogram.compute_histogram(img, "y")
    h_after = histogram.compute_histogram(tone.adjust_brightness(img, -60), "y")
    save("06_hist_before_after.png", hist_picture([h_before, h_after], [(120, 120, 120), (220, 60, 60)]))
    save("07_hist_rgb.png", hist_picture([histogram.compute_histogram(img, c) for c in "rgb"],
                                         [(220, 40, 40), (40, 170, 70), (50, 90, 230)]))

    save("08_gray_stretch.png", tone.linear_stretch(gray))
    save("09_gray_negative.png", tone.negative(gray))
    save("10_gray_log.png", tone.log_transform(gray))
    save("11_gray_equalize.png", tone.equalize(gray))

    bw, T = binarize.otsu(gray)
    print("== Порог Оцу ==", T)
    save("12_binary_otsu.png", bw)
    kernel = morphology.make_kernel(size=5)
    for code in morphology.OPERATIONS.values():
        save("13_morph_{}.png".format(code), morphology.apply(code, bw, kernel))

    save("14_sharpen.png", filters.sharpen(img, 1.0))
    save("15_motion_blur.png", filters.motion_blur(img, 21, 20))
    save("16_emboss.png", filters.emboss(img))
    noisy = imageio.load_image("samples/noisy.png")
    save("17_noisy.png", noisy)
    save("18_median.png", filters.median(noisy, 3))

    save("19_canny.png", edges.canny(gray, 80, 160))
    save("20_roberts.png", edges.roberts(gray, normalize=True))

    for name in features.DETECTORS:
        points = features.detect(name, img)
        print("== Ключевые точки: {} -> {} шт.".format(name, len(points)))
        save("21_points_{}.png".format(name), features.draw_points(img, points))

    names = ["scene.png", "scene_rotated.png", "pattern_a.png", "pattern_b.png"]
    images = [imageio.load_image("samples/" + n) for n in names]
    i, j, score, matrix = similarity.most_similar_pair(images)
    print("== Самые похожие: {} и {} (оценка {:.3f})".format(names[i], names[j], score))
    print(np.round(matrix, 3))

    frames = video.process_video("samples/moving.avi", "mask", max_frames=60)
    save("22_video_mask.png", frames[-1])
    frames = video.process_video("samples/moving.avi", "blur", max_frames=60)
    save("23_video_blur.png", frames[-1])
    print("Готово: результаты в папке", OUT)


if __name__ == "__main__":
    main()
