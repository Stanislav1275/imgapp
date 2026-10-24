"""Проверка темы оформления (без Qt): стиль собирается для обеих тем, и все цвета заданы."""
import unittest

from gui import theme


class Theme(unittest.TestCase):
    def test_both_themes_have_same_keys(self):
        self.assertEqual(set(theme.LIGHT), set(theme.DARK))

    def test_stylesheet_has_no_unfilled_placeholders(self):
        for colors in (theme.LIGHT, theme.DARK):
            qss = theme.stylesheet(colors)
            self.assertNotIn("$", qss)
            self.assertIn(colors["accent"], qss)

    def test_braces_are_balanced(self):
        qss = theme.stylesheet(theme.LIGHT)
        self.assertEqual(qss.count("{"), qss.count("}"))


if __name__ == "__main__":
    unittest.main()
