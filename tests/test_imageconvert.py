"""Проверка перевода всего изображения между моделями и определения модели файла."""
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from core import colorspaces, imageconvert


def small_image():
    return np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                     [[255, 255, 255], [0, 0, 0], [255, 128, 0]]], dtype=np.uint8)


class ImageConvert(unittest.TestCase):
    def test_matches_single_pixel_conversion(self):
        img = small_image()
        for model in colorspaces.MODELS:
            planes = imageconvert.image_to_model(img, model)
            for y in range(2):
                for x in range(3):
                    expected = colorspaces.convert(tuple(int(v) for v in img[y, x]), "RGB", model)
                    np.testing.assert_allclose(planes[y, x], expected)

    def test_shape_has_one_layer_per_channel(self):
        img = small_image()
        self.assertEqual(imageconvert.image_to_model(img, "CMYK").shape, (2, 3, 4))
        self.assertEqual(imageconvert.image_to_model(img, "HSV").shape, (2, 3, 3))

    def test_gray_image_is_accepted(self):
        gray = np.full((4, 5), 100, dtype=np.uint8)
        planes = imageconvert.image_to_model(gray, "HSV")
        self.assertEqual(planes.shape, (4, 5, 3))
        np.testing.assert_allclose(planes[:, :, 1], 0)          # у серого насыщенность 0

    def test_unknown_model(self):
        with self.assertRaises(ValueError):
            imageconvert.image_to_model(small_image(), "XYZ")

    def test_views_are_scaled_to_byte_range(self):
        views = imageconvert.planes_for_view(imageconvert.image_to_model(small_image(), "HSV"), "HSV")
        self.assertEqual([name for name, _ in views], ["H", "S", "V"])
        for _name, plane in views:
            self.assertEqual(plane.dtype, np.uint8)
        v_plane = dict(views)["V"]
        self.assertEqual(int(v_plane[1, 1]), 0)                  # чёрный: V = 0
        self.assertEqual(int(v_plane[1, 0]), 255)                # белый: V = 1

    def test_lab_negative_axes_are_shifted(self):
        views = dict(imageconvert.planes_for_view(imageconvert.image_to_model(small_image(), "LAB"), "LAB"))
        self.assertEqual(int(views["L"][1, 1]), 0)               # чёрный: L = 0
        self.assertTrue(120 <= int(views["a"][1, 0]) <= 135)     # белый: a около 0 -> середина шкалы

    def test_three_channel_picture(self):
        views = imageconvert.planes_for_view(imageconvert.image_to_model(small_image(), "YCbCr"), "YCbCr")
        self.assertEqual(imageconvert.as_three_channel_picture(views).shape, (2, 3, 3))
        cmyk = imageconvert.planes_for_view(imageconvert.image_to_model(small_image(), "CMYK"), "CMYK")
        self.assertIsNone(imageconvert.as_three_channel_picture(cmyk))


class FileModel(unittest.TestCase):
    def detect(self, mode, name):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, name)
            Image.new(mode, (8, 8)).save(path)
            return imageconvert.file_color_model(path)[0]

    def test_detects_models(self):
        self.assertEqual(self.detect("RGB", "a.png"), "RGB")
        self.assertEqual(self.detect("L", "a.png"), "Градации серого")
        self.assertEqual(self.detect("CMYK", "a.tif"), "CMYK")
        self.assertEqual(self.detect("RGBA", "a.png"), "RGB")


if __name__ == "__main__":
    unittest.main()
