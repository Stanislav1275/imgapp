"""
Проверки модуля core/colorspaces.py.

Запуск из папки imgapp:
    python -m unittest tests.test_colorspaces -v

Тесты служат ещё и примерами: смотрите, какие числа получаются для оранжевого (255, 128, 0).
"""
import colorsys
import itertools
import unittest

from core import colorspaces as cs


def close(a, b, eps=1e-6):
    """Два кортежа чисел равны с точностью eps."""
    return all(abs(x - y) <= eps for x, y in zip(a, b))


class ExampleOrange(unittest.TestCase):
    """Контрольный пример из курса: оранжевый (255, 128, 0)."""

    def test_hex(self):
        self.assertEqual(cs.rgb_to_hex(255, 128, 0), "#FF8000")
        self.assertEqual(cs.hex_to_rgb("#FF8000"), (255, 128, 0))
        self.assertEqual(cs.hex_to_rgb("f80"), (255, 136, 0))   # короткая запись

    def test_hsv_hsl(self):
        h, s, v = cs.rgb_to_hsv(255, 128, 0)
        self.assertAlmostEqual(h, 30.1176, places=3)            # 60 * (128/255) = 30.12°
        self.assertEqual((s, v), (1.0, 1.0))
        h, s, l = cs.rgb_to_hsl(255, 128, 0)
        self.assertAlmostEqual(l, 0.5)
        self.assertAlmostEqual(s, 1.0)

    def test_cmyk(self):
        c, m, y, k = cs.rgb_to_cmyk(255, 128, 0)
        self.assertAlmostEqual(c, 0.0)
        self.assertAlmostEqual(m, 1 - 128 / 255)
        self.assertAlmostEqual(y, 1.0)
        self.assertAlmostEqual(k, 0.0)

    def test_ycbcr(self):
        y, cb, cr = cs.rgb_to_ycbcr(255, 128, 0)
        self.assertEqual((round(y), round(cb), round(cr)), (151, 43, 202))

    def test_lab(self):
        L, a, b = cs.rgb_to_lab(255, 128, 0)
        self.assertEqual((round(L), round(a), round(b)), (67, 43, 74))


class SpecialCases(unittest.TestCase):
    def test_black_cmyk(self):
        self.assertEqual(cs.rgb_to_cmyk(0, 0, 0), (0.0, 0.0, 0.0, 1.0))

    def test_gray_has_no_hue_or_saturation(self):
        self.assertEqual(cs.rgb_to_hsv(100, 100, 100), (0.0, 0.0, 100 / 255))
        h, s, l = cs.rgb_to_hsl(100, 100, 100)
        self.assertEqual((h, s), (0.0, 0.0))

    def test_gray_ycbcr(self):
        y, cb, cr = cs.rgb_to_ycbcr(100, 100, 100)
        self.assertAlmostEqual(y, 100, places=6)
        self.assertAlmostEqual(cb, 128, places=3)
        self.assertAlmostEqual(cr, 128, places=3)

    def test_white_lab(self):
        L, a, b = cs.rgb_to_lab(255, 255, 255)
        self.assertAlmostEqual(L, 100, places=2)
        self.assertAlmostEqual(a, 0, places=1)
        self.assertAlmostEqual(b, 0, places=1)

    def test_unknown_model(self):
        with self.assertRaises(ValueError):
            cs.convert((1, 2, 3), "RGB", "XYZW")


class AgainstStandardLibrary(unittest.TestCase):
    """Сверяем HSV и HSL с colorsys из стандартной библиотеки Python."""

    SAMPLES = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 128, 0), (12, 200, 99),
               (255, 128, 128), (30, 30, 30), (250, 250, 5), (1, 2, 3), (200, 10, 180)]

    def test_hsv(self):
        for R, G, B in self.SAMPLES:
            h, s, v = colorsys.rgb_to_hsv(R / 255, G / 255, B / 255)
            mine = cs.rgb_to_hsv(R, G, B)
            self.assertTrue(close(mine, (h * 360, s, v)), (R, G, B, mine))

    def test_hsl(self):
        for R, G, B in self.SAMPLES:
            h, l, s = colorsys.rgb_to_hls(R / 255, G / 255, B / 255)   # colorsys: порядок H, L, S
            mine = cs.rgb_to_hsl(R, G, B)
            self.assertTrue(close(mine, (h * 360, s, l)), (R, G, B, mine))


class RoundTrip(unittest.TestCase):
    """RGB -> модель -> RGB должен вернуть исходный цвет (допуск 1 из-за округления)."""

    def test_all_models_on_grid(self):
        steps = (0, 1, 37, 128, 200, 254, 255)
        for model in cs.MODELS:
            for R, G, B in itertools.product(steps, repeat=3):
                there = cs.convert((R, G, B), "RGB", model)
                back = cs.convert(there, model, "RGB")
                self.assertTrue(close(back, (R, G, B), eps=1),
                                "{}: {} -> {} -> {}".format(model, (R, G, B), there, back))

    def test_any_to_any(self):
        """Цепочка из всех моделей по кругу возвращает исходный цвет."""
        color = (255, 128, 0)
        chain = cs.MODELS + ["RGB"]
        values, current = color, "RGB"
        for model in chain:
            values = cs.convert(values, current, model)
            current = model
        self.assertTrue(close(values, color, eps=1), values)


if __name__ == "__main__":
    unittest.main()
