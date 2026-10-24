"""
Проверки features, similarity, video на синтетических данных.

Запуск из папки imgapp:  python -m unittest tests.test_vision -v
"""
import os
import tempfile
import unittest

import cv2
import numpy as np

from core import features, similarity, video


def checkerboard(size=64, cell=16):
    """Шахматная доска: углы клеток — идеальные ключевые точки."""
    ys, xs = np.mgrid[0:size, 0:size]
    board = (((xs // cell) + (ys // cell)) % 2 * 255).astype(np.uint8)
    return np.stack([board] * 3, axis=2)


def textured(seed, size=256):
    """Картинка со случайной «пятнистой» текстурой — на ней SIFT находит много точек."""
    rng = np.random.default_rng(seed)
    small = rng.integers(0, 256, (24, 24, 3), dtype=np.uint8)
    return cv2.resize(small, (size, size), interpolation=cv2.INTER_CUBIC)


class Detectors(unittest.TestCase):
    def test_harris_finds_corners_of_checkerboard(self):
        points = features.harris(checkerboard())
        self.assertGreaterEqual(len(points), 9)              # внутренних углов 3 x 3
        # каждая найденная точка — рядом с линией сетки (координата, кратная 16, плюс-минус 2)
        for x, y in points:
            self.assertLessEqual(min(x % 16, 16 - x % 16), 2)
            self.assertLessEqual(min(y % 16, 16 - y % 16), 2)

    def test_harris_flat_image_has_no_points(self):
        self.assertEqual(features.harris(np.full((40, 40, 3), 100, np.uint8)), [])

    def test_fast_finds_corners_of_square(self):
        # Белый квадрат на чёрном: у его угла кольцо из 16 точек содержит 12 подряд тёмных -> угол.
        # (На шахматной доске FAST ничего не найдёт: в центре «крестика» тёмные и светлые дуги чередуются
        # по 8 точек, а нужно не менее 9 подряд.)
        # Квадрат слегка размываем: на идеально резком квадрате у соседних пикселей оценки угла
        # одинаковы, и подавление немаксимумов (nonmax) убирает все точки сразу.
        img = np.zeros((64, 64, 3), np.uint8)
        img[20:44, 20:44] = 255
        img = cv2.GaussianBlur(img, (3, 3), 0)
        points = features.fast(img)
        self.assertEqual(len(points), 4)
        for x, y in points:                                   # все точки — рядом с одним из 4 углов квадрата
            self.assertLessEqual(min(abs(x - 20), abs(x - 43)), 3)
            self.assertLessEqual(min(abs(y - 20), abs(y - 43)), 3)

    def test_fast_flat_image_has_no_points(self):
        self.assertEqual(features.fast(np.full((40, 40, 3), 100, np.uint8)), [])

    def test_sift_finds_points_on_texture(self):
        self.assertGreater(len(features.sift(textured(0))), 10)

    def test_detect_by_name_and_draw(self):
        img = textured(1)
        for name in features.DETECTORS:
            points = features.detect(name, img)
            drawn = features.draw_points(img, points)
            self.assertEqual(drawn.shape, img.shape)
        with self.assertRaises(ValueError):
            features.detect("SURF", img)


class Similarity(unittest.TestCase):
    def test_finds_the_pair_with_same_content(self):
        a = textured(10)
        # b — та же картинка, слегка повёрнутая, уменьшенная и чуть темнее
        matrix = cv2.getRotationMatrix2D((128, 128), 5, 0.9)
        b = cv2.warpAffine(a, matrix, (256, 256), borderMode=cv2.BORDER_REFLECT)
        b = (b * 0.9).astype(np.uint8)
        images = [textured(11), a, textured(12), b]          # похожие — индексы 1 и 3
        i, j, score, mat = similarity.most_similar_pair(images)
        self.assertEqual((i, j), (1, 3))
        self.assertGreater(score, 0.1)
        self.assertEqual(mat.shape, (4, 4))
        self.assertTrue(np.allclose(mat, mat.T))

    def test_histogram_method_runs(self):
        a = textured(20)
        self.assertAlmostEqual(similarity.histogram_score(a, a), 1.0, places=5)
        i, j, score, _ = similarity.most_similar_pair([a, textured(21), a.copy()], method="hist")
        self.assertEqual((i, j), (0, 2))

    def test_needs_two_images(self):
        with self.assertRaises(ValueError):
            similarity.most_similar_pair([textured(1)])


def make_test_video(path, frames=40, w=160, h=120, size=24, speed=3):
    """Серый фон и белый квадрат, который едет слева направо."""
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 20, (w, h))
    for t in range(frames):
        frame = np.full((h, w, 3), 90, np.uint8)
        x = 5 + t * speed
        frame[48:48 + size, x:x + size] = 255
        writer.write(frame)
    writer.release()


class Video(unittest.TestCase):
    def test_background_subtraction_finds_moving_square(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.avi")
            make_test_video(path)
            detector = video.MotionDetector()
            last_mask, last_frame = None, None
            count = 0
            for frame in video.read_frames(path):
                last_mask, last_frame = detector.mask(frame), frame
                count += 1
            self.assertEqual(count, 40)
            # в последнем кадре квадрат стоит в x = 5 + 39*3 = 122..146
            inside = last_mask[48:72, 122:146]
            self.assertGreater(float((inside > 0).mean()), 0.5)       # квадрат найден
            self.assertEqual(int((last_mask[:, :60] > 0).sum()), 0)   # слева фон — движения нет

    def test_blur_changes_only_moving_area(self):
        frame = np.zeros((60, 60, 3), np.uint8)
        frame[::2] = 255                                              # полосатый кадр
        mask = np.zeros((60, 60), np.uint8)
        mask[20:40, 20:40] = 255
        out = video.blur_moving(frame, mask, ksize=9, grow=1)
        self.assertTrue(np.array_equal(out[:10], frame[:10]))         # далеко от маски без изменений
        self.assertFalse(np.array_equal(out[25:35, 25:35], frame[25:35, 25:35]))  # внутри размыто

    def test_foreground_keeps_only_masked(self):
        frame = np.full((10, 10, 3), 200, np.uint8)
        mask = np.zeros((10, 10), np.uint8)
        mask[:5] = 255
        out = video.foreground(frame, mask)
        self.assertTrue(np.all(out[:5] == 200))
        self.assertTrue(np.all(out[5:] == 0))

    def test_process_video_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = os.path.join(tmp, "in.avi"), os.path.join(tmp, "out.avi")
            make_test_video(src, frames=10)
            video.process_video(src, "blur", out_path=dst)
            self.assertEqual(len(list(video.read_frames(dst))), 10)
            frames = video.process_video(src, "mask", max_frames=5)
            self.assertEqual(len(frames), 5)

    def test_bad_path(self):
        with self.assertRaises(ValueError):
            list(video.read_frames("no_such_file.avi"))


if __name__ == "__main__":
    unittest.main()
