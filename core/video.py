"""
Работа с видео: вычитание фона и размытие движущихся объектов.

Вычитание фона (MOG2): алгоритм по кадрам запоминает, как обычно выглядит каждый пиксель
(как смесь нескольких гауссовых распределений). Если пиксель резко отличается от запомненного
— он «переднего плана» (движется). Результат — маска: белое = движущееся, чёрное = фон.
"""
import cv2
import numpy as np


class MotionDetector:
    """Обёртка над MOG2: подаёте кадры по очереди, получаете маску движения."""

    def __init__(self, history=200, var_threshold=25, clean_size=3):
        self.subtractor = cv2.createBackgroundSubtractorMOG2(history=history,
                                                             varThreshold=var_threshold,
                                                             detectShadows=True)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (clean_size, clean_size))

    def mask(self, frame_rgb):
        """
        Маска движения для кадра (0 или 255).
        MOG2 помечает тени серым (127); оставляем только уверенно белое (> 200).
        Потом открытие убирает мелкие точки шума.
        """
        raw = self.subtractor.apply(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
        binary = np.where(raw > 200, 255, 0).astype(np.uint8)
        return cv2.morphologyEx(binary, cv2.MORPH_OPEN, self.kernel)


def foreground(frame_rgb, mask):
    """Показать только движущиеся объекты (остальное чёрное)."""
    return cv2.bitwise_and(frame_rgb, frame_rgb, mask=mask)


def blur_moving(frame_rgb, mask, ksize=31, grow=7):
    """
    Размыть только движущиеся объекты. Сначала расширяем маску (grow), чтобы захватить края объекта,
    потом берём размытую версию кадра там, где маска белая, и исходный кадр — остальное.
    """
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    wide = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    blurred = cv2.GaussianBlur(frame_rgb, (ksize, ksize), 0)
    return np.where(wide[:, :, None] > 0, blurred, frame_rgb)


def read_frames(path, max_frames=None):
    """Генератор кадров видео в RGB. Читает по одному, чтобы не держать всё видео в памяти."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Не удалось открыть видео: " + str(path))
    count = 0
    try:
        while max_frames is None or count < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            count += 1
    finally:
        cap.release()


def video_fps(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()
    return fps


def process_video(path, mode, out_path=None, max_frames=None):
    """
    Обработать видео целиком. mode: "mask" (маска движения), "foreground" (только движущееся),
    "blur" (размыть движущееся). Если указан out_path — результат записывается в файл (.avi).
    Возвращает список обработанных кадров только если out_path не задан (для коротких роликов).
    """
    detector = MotionDetector()
    writer, frames = None, []
    for frame in read_frames(path, max_frames):
        mask = detector.mask(frame)
        if mode == "mask":
            result = np.stack([mask] * 3, axis=2)
        elif mode == "foreground":
            result = foreground(frame, mask)
        else:
            result = blur_moving(frame, mask)
        if out_path:
            if writer is None:
                h, w = result.shape[:2]
                writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"MJPG"),
                                         video_fps(path), (w, h))
            writer.write(cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        else:
            frames.append(result)
    if writer is not None:
        writer.release()
    return frames
