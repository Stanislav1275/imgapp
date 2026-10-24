"""
Проверки binarize, morphology, filters, edges на маленьких массивах, где ответ можно посчитать вручную.

Запуск из папки imgapp:  python -m unittest tests.test_processing -v
"""
import unittest

import numpy as np

from core import binarize, edges, filters, morphology


def square(size=9, lo=2, hi=7):
    """Чёрная картинка size x size с белым квадратом [lo, hi)."""
    img = np.zeros((size, size), np.uint8)
    img[lo:hi, lo:hi] = 255
    return img


class Binarization(unittest.TestCase):
    def test_global_threshold_example(self):
        row = np.array([[40, 80, 120, 160, 200]], np.uint8)
        self.assertEqual(binarize.threshold(row, 128).ravel().tolist(), [0, 0, 0, 255, 255])
        self.assertEqual(binarize.threshold(row, 100).ravel().tolist(), [0, 0, 255, 255, 255])

    def test_threshold_is_strict(self):
        """Условие r > T строгое: пиксель, равный порогу, остаётся чёрным."""
        self.assertEqual(int(binarize.threshold(np.array([[128]], np.uint8), 128)[0, 0]), 0)

    def test_otsu_course_example(self):
        # гистограмма 10:7, 128:2, 200:4, 255:3 — из курса; первый максимум у T = 10
        gray = np.array([10] * 7 + [128] * 2 + [200] * 4 + [255] * 3, np.uint8).reshape(4, 4)
        self.assertEqual(binarize.otsu_threshold(gray), 10)

    def test_otsu_two_levels(self):
        gray = np.array([[50] * 8 + [200] * 8], np.uint8)
        out, T = binarize.otsu(gray)
        self.assertTrue(50 <= T < 200)
        self.assertEqual(out.ravel().tolist(), [0] * 8 + [255] * 8)


class Morphology(unittest.TestCase):
    def setUp(self):
        self.k = morphology.make_kernel(size=3)

    def test_erode_shrinks_square(self):
        out = morphology.erode(square(), self.k)
        self.assertEqual(int((out == 255).sum()), 3 * 3)       # квадрат 5x5 стал 3x3

    def test_dilate_grows_square(self):
        out = morphology.dilate(square(), self.k)
        self.assertEqual(int((out == 255).sum()), 7 * 7)       # квадрат 5x5 стал 7x7

    def test_opening_removes_noise_point(self):
        img = square()
        img[0, 8] = 255                                        # одиночная белая точка-шум
        out = morphology.opening(img, self.k)
        self.assertEqual(int(out[0, 8]), 0)
        self.assertTrue(np.array_equal(out, square()))         # квадрат восстановлен

    def test_closing_fills_hole(self):
        img = square()
        img[4, 4] = 0                                          # чёрная дырка внутри квадрата
        out = morphology.closing(img, self.k)
        self.assertEqual(int(out[4, 4]), 255)

    def test_gradient_is_outline(self):
        out = morphology.gradient(square(), self.k)
        self.assertEqual(int(out[4, 4]), 0)                    # внутри квадрата пусто
        self.assertEqual(int(out[2, 4]), 255)                  # на краю — контур

    def test_apply_by_name(self):
        for name in morphology.OPERATIONS.values():
            self.assertEqual(morphology.apply(name, square(), self.k).shape, (9, 9))


class Filters(unittest.TestCase):
    def test_flat_image_unchanged_by_sharpen_and_blur(self):
        flat = np.full((10, 10, 3), 90, np.uint8)
        self.assertTrue(np.array_equal(filters.sharpen(flat), flat))
        self.assertTrue(np.array_equal(filters.motion_blur(flat, 9, 30), flat))

    def test_sharpen_kernel_sum_is_one(self):
        for s in (0.5, 1.0, 2.0):
            self.assertAlmostEqual(float(np.sum(filters.sharpen_kernel(s))), 1.0)
        self.assertEqual(filters.sharpen_kernel(1.0), [[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

    def test_sharpen_increases_edge_contrast(self):
        step = np.zeros((5, 8), np.uint8)
        step[:, 4:] = 100
        out = filters.sharpen(step)
        self.assertEqual(int(out[2, 3]), 0)                    # перед краем темнее (обрезано до 0)
        self.assertGreater(int(out[2, 4]), 100)                # после края светлее

    def test_motion_kernel(self):
        k = filters.motion_blur_kernel(5, 0)
        self.assertAlmostEqual(float(k.sum()), 1.0, places=5)
        self.assertEqual(int((k > 0).sum()), 5)                # 5 одинаковых ненулевых элементов
        self.assertTrue(np.all(k[2, :] > 0))                   # они лежат в средней строке (угол 0)

    def test_motion_blur_smears_point(self):
        img = np.zeros((9, 9), np.uint8)
        img[4, 4] = 255
        out = filters.motion_blur(img, 5, 0)
        self.assertEqual(out[4, 2:7].tolist(), [51] * 5)       # 255 / 5 = 51 вдоль строки
        self.assertEqual(int(out[3].sum()), 0)

    def test_emboss_flat_is_gray(self):
        flat = np.full((6, 6), 200, np.uint8)
        self.assertTrue(np.all(filters.emboss(flat) == 128))

    def test_median_removes_salt(self):
        img = np.full((7, 7), 100, np.uint8)
        img[3, 3] = 255                                        # одиночная «соль»
        self.assertTrue(np.all(filters.median(img, 3) == 100))


class Edges(unittest.TestCase):
    def test_roberts_manual(self):
        # окно 2x2: a=10 b=20 / c=30 d=60 -> Gx = a-d = -50, Gy = b-c = -10, G = sqrt(2600) = 51
        g = np.array([[10, 20], [30, 60]], np.uint8)
        out = edges.roberts(g)
        self.assertEqual(int(out[0, 0]), 51)
        self.assertEqual(out.shape, g.shape)
        self.assertEqual((int(out[1, 0]), int(out[0, 1]), int(out[1, 1])), (0, 0, 0))

    def test_roberts_flat_has_no_edges(self):
        self.assertTrue(np.all(edges.roberts(np.full((6, 6), 77, np.uint8)) == 0))

    def test_roberts_finds_vertical_edge(self):
        img = np.zeros((6, 6), np.uint8)
        img[:, 3:] = 200
        out = edges.roberts(img)
        self.assertTrue(np.all(out[:5, 2] > 100))              # граница между столбцами 2 и 3
        self.assertTrue(np.all(out[:5, 0] == 0))

    def test_canny_binary_output(self):
        out = edges.canny(square(32, 8, 24), 50, 150)
        self.assertTrue(set(np.unique(out).tolist()) <= {0, 255})
        self.assertGreater(int((out == 255).sum()), 0)
        self.assertEqual(int(out[16, 16]), 0)                  # внутри квадрата границ нет


if __name__ == "__main__":
    unittest.main()
