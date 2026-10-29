"""Проверка Canny по шагам: каждый шаг на маленьком примере, где ответ понятен, и сверка с OpenCV."""
import unittest

import cv2
import numpy as np

from core import edges


def vertical_step(size=12):
    """Левая половина тёмная (50), правая светлая (200): одна вертикальная граница."""
    img = np.full((size, size), 50, np.uint8)
    img[:, size // 2:] = 200
    return img


def test_scene():
    """Искусственная картинка из кругов, прямоугольников и слабого шума: не зависит от папки samples."""
    rng = np.random.default_rng(1)
    img = np.full((240, 320), 90, np.uint8)
    cv2.circle(img, (100, 110), 60, 200, -1)
    cv2.rectangle(img, (180, 40), (290, 150), 30, -1)
    cv2.circle(img, (230, 190), 35, 160, -1)
    img = cv2.GaussianBlur(img, (0, 0), 1.0).astype(np.int16) + rng.integers(-6, 7, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


class CannySteps(unittest.TestCase):
    def test_sobel_on_vertical_step(self):
        magnitude, angle = edges.sobel(vertical_step())
        # на границе (между столбцами 5 и 6): Gx = (1 + 2 + 1) * 150 = 600, Gy = 0
        self.assertAlmostEqual(float(magnitude[5, 5]), 600.0)
        self.assertAlmostEqual(float(magnitude[5, 6]), 600.0)
        self.assertAlmostEqual(float(angle[5, 5]), 0.0)          # градиент направлен вправо
        self.assertAlmostEqual(float(magnitude[5, 2]), 0.0)      # в ровном месте градиента нет

    def test_sobel_direction_of_horizontal_edge(self):
        img = vertical_step().T.copy()                           # теперь граница горизонтальная
        magnitude, angle = edges.sobel(img)
        self.assertAlmostEqual(float(angle[5, 5]), 90.0)         # градиент направлен вниз

    def test_non_max_suppression_thins_the_edge(self):
        magnitude, angle = edges.sobel(vertical_step())
        thin = edges.non_max_suppression(magnitude, angle)
        # вдоль строки граница шириной 2 пикселя (столбцы 5 и 6); остаётся один из них
        self.assertEqual(int((thin[5] > 0).sum()), 1)

    def test_double_threshold_split(self):
        thin = np.array([[10, 60, 120, 200]], dtype=np.float64)
        strong, weak = edges.double_threshold(thin, 50, 150)
        self.assertEqual(strong.tolist(), [[False, False, False, True]])
        self.assertEqual(weak.tolist(), [[False, True, True, False]])

    def test_hysteresis_keeps_connected_weak_only(self):
        strong = np.zeros((1, 8), bool)
        weak = np.zeros((1, 8), bool)
        strong[0, 0] = True
        weak[0, 1:4] = True            # цепочка слабых, связана с сильным
        weak[0, 6] = True              # одинокий слабый
        result = edges.hysteresis(strong, weak)
        self.assertEqual(result[0].tolist(), [True, True, True, True, False, False, False, False])

    def test_steps_dictionary(self):
        steps = edges.canny_steps(vertical_step(32), 50, 150)
        for key in ("blurred", "magnitude", "thin", "strong", "weak", "edges"):
            self.assertIn(key, steps)
        self.assertTrue(set(np.unique(steps["edges"]).tolist()) <= {0, 255})

    def test_low_threshold_adds_edges(self):
        gray = test_scene()
        many = int((edges.canny(gray, 20, 60) > 0).sum())
        few = int((edges.canny(gray, 80, 160) > 0).sum())
        self.assertGreater(many, few)

    def test_agrees_with_opencv(self):
        """Наша версия и cv2.Canny (с честным L2-градиентом и тем же сглаживанием) почти не расходятся."""
        gray = test_scene()
        own = edges.canny(gray, 50, 150) > 0
        reference = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 1.4), 50, 150, L2gradient=True) > 0
        overlap = (own & reference).sum() / max(own.sum(), reference.sum())
        self.assertGreater(overlap, 0.95)

    def test_stage_images(self):
        gray = vertical_step(32)
        pictures = edges.canny_stage_images(gray, edges.canny_steps(gray, 50, 150))
        self.assertEqual(len(pictures), 6)
        for _title, picture in pictures:
            self.assertEqual(picture.shape, gray.shape)
            self.assertEqual(picture.dtype, np.uint8)
        self.assertEqual(int(pictures[4][1].max()), 255)         # на двойном пороге есть сильные точки


if __name__ == "__main__":
    unittest.main()
