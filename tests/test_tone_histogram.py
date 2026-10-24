"""
Проверки core/tone.py, core/histogram.py, core/info.py.
Числа взяты из примеров курса (строка пикселей 40, 80, 120, 160, 200).

Запуск из папки imgapp:  python -m unittest tests.test_tone_histogram -v
"""
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from core import histogram, imageio, info, tone

ROW = np.array([[40, 80, 120, 160, 200]], dtype=np.uint8)   # серая строка из 5 пикселей


def as_list(a):
    return a.ravel().tolist()


class Adjustments(unittest.TestCase):
    def test_neutral_values_do_not_change_image(self):
        img = np.random.default_rng(0).integers(0, 256, (8, 8, 3), dtype=np.uint8)
        self.assertTrue(np.array_equal(tone.adjust_all(img), img))
        self.assertTrue(np.array_equal(tone.adjust_brightness(img, 0), img))
        self.assertTrue(np.array_equal(tone.adjust_contrast(img, 1), img))
        self.assertTrue(np.array_equal(tone.adjust_gamma(img, 1), img))
        self.assertTrue(np.array_equal(tone.adjust_saturation(img, 1), img))

    def test_brightness_example(self):
        self.assertEqual(as_list(tone.adjust_brightness(ROW, 50)), [90, 130, 170, 210, 250])

    def test_brightness_clips(self):
        self.assertEqual(as_list(tone.adjust_brightness(ROW, 100)), [140, 180, 220, 255, 255])

    def test_contrast_example(self):
        # 40 -> 1.5*(40-128)+128 = -4 -> обрезано до 0
        self.assertEqual(as_list(tone.adjust_contrast(ROW, 1.5)), [0, 56, 116, 176, 236])

    def test_contrast_keeps_128(self):
        self.assertEqual(int(tone.adjust_contrast(np.array([[128]], np.uint8), 2.0)[0, 0]), 128)

    def test_gamma_examples(self):
        self.assertEqual(as_list(tone.adjust_gamma(ROW, 0.5)), [101, 143, 175, 202, 226])
        self.assertEqual(as_list(tone.adjust_gamma(ROW, 2.0)), [6, 25, 56, 100, 157])

    def test_gamma_keeps_ends(self):
        ends = np.array([[0, 255]], np.uint8)
        for g in (0.3, 0.5, 2.0, 3.0):
            self.assertEqual(as_list(tone.adjust_gamma(ends, g)), [0, 255])

    def test_saturation_zero_gives_gray(self):
        img = np.array([[[255, 128, 0]]], np.uint8)
        out = tone.adjust_saturation(img, 0)[0, 0]
        self.assertTrue(out[0] == out[1] == out[2])
        self.assertEqual(int(out[0]), int(round(0.299 * 255 + 0.587 * 128)))   # серый = Y = 151

    def test_slider_conversion(self):
        beta, alpha, gamma, k = tone.slider_to_params(20, 50, 50, 100)
        self.assertAlmostEqual(beta, 51.0)
        self.assertAlmostEqual(alpha, 1.5)
        self.assertAlmostEqual(gamma, 0.5)
        self.assertAlmostEqual(k, 1.0)

    def test_gray_conversion(self):
        img = np.array([[[255, 128, 0], [255, 255, 255], [0, 0, 0]]], np.uint8)
        self.assertEqual(as_list(tone.to_gray(img)), [151, 255, 0])


class GrayCorrections(unittest.TestCase):
    def test_linear_stretch(self):
        out = tone.linear_stretch(np.array([[100, 150, 200]], np.uint8))
        self.assertEqual(as_list(out), [0, 128, 255])

    def test_negative(self):
        self.assertEqual(as_list(tone.negative(ROW)), [215, 175, 135, 95, 55])

    def test_log_keeps_ends(self):
        out = tone.log_transform(np.array([[0, 255]], np.uint8))
        self.assertEqual(as_list(out), [0, 255])

    def test_equalize_spreads_values(self):
        gray = np.array([[100, 100, 101, 101, 102, 102]], np.uint8)
        out = tone.equalize(gray)
        self.assertEqual(int(out.min()), 0)
        self.assertEqual(int(out.max()), 255)

    def test_equalize_flat_image(self):
        flat = np.full((3, 3), 77, np.uint8)
        self.assertTrue(np.array_equal(tone.equalize(flat), flat))


class Histograms(unittest.TestCase):
    def setUp(self):
        # пример из курса: 16 пикселей, яркость 10 у 7, 128 у 2, 200 у 4, 255 у 3
        values = [10] * 7 + [128] * 2 + [200] * 4 + [255] * 3
        self.gray = np.array(values, np.uint8).reshape(4, 4)

    def test_counts(self):
        h = histogram.compute_histogram(self.gray)
        self.assertEqual((h[10], h[128], h[200], h[255]), (7, 2, 4, 3))
        self.assertEqual(int(h.sum()), 16)
        self.assertEqual(len(h), 256)

    def test_normalized_and_cumulative(self):
        h = histogram.compute_histogram(self.gray)
        self.assertAlmostEqual(float(histogram.normalized(h).sum()), 1.0)
        c = histogram.cumulative(h)
        self.assertEqual((int(c[9]), int(c[10]), int(c[199]), int(c[255])), (0, 7, 9, 16))

    def test_channels(self):
        img = np.zeros((2, 2, 3), np.uint8)
        img[:, :, 0] = 255                                  # чисто красная картинка
        self.assertEqual(int(histogram.compute_histogram(img, "r")[255]), 4)
        self.assertEqual(int(histogram.compute_histogram(img, "g")[0]), 4)
        self.assertEqual(int(histogram.compute_histogram(img, "y")[76]), 4)   # 0.299*255 = 76.2

    def test_histogram_before_is_not_changed_by_operation(self):
        """Гистограмма «до» считается по исходнику: операция не должна менять исходный массив."""
        before = histogram.compute_histogram(self.gray).copy()
        tone.adjust_brightness(self.gray, -100)
        self.assertTrue(np.array_equal(before, histogram.compute_histogram(self.gray)))

    def test_stats(self):
        s = histogram.stats(self.gray)
        self.assertEqual((s["min"], s["max"]), (10, 255))


class FileInfo(unittest.TestCase):
    def test_png_info_and_roundtrip(self):
        img = np.zeros((20, 30, 3), np.uint8)
        img[:, :15] = (255, 128, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "тест.png")             # русское имя файла
            Image.fromarray(img).save(path, dpi=(96, 96))
            data = info.get_image_info(path)
            self.assertEqual(data["Формат"], "PNG")
            self.assertEqual(data["Разрешение (пиксели)"], "30 x 20")
            self.assertIn("24 бит", data["Глубина цвета"])
            self.assertEqual(data["Разных цветов"], "2")
            self.assertEqual(data["DPI"], "96 x 96")
            loaded = imageio.load_image(path)
            self.assertTrue(np.array_equal(loaded, img))      # RGB остаётся RGB
            out = os.path.join(tmp, "out.png")
            imageio.save_image(out, loaded)
            self.assertTrue(np.array_equal(imageio.load_image(out), img))

    def test_format_size(self):
        self.assertEqual(info.format_size(500), "500 Б")
        self.assertEqual(info.format_size(2048), "2.0 КБ")


if __name__ == "__main__":
    unittest.main()
