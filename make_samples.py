"""
Создаёт тестовые данные в папке samples/ (чтобы было на чём проверять программу):
    scene.png           — «пейзаж» с домиком, солнцем и небом
    scene_rotated.png   — та же сцена, чуть повёрнутая и темнее (похожа на scene.png)
    pattern_a.png, pattern_b.png — две несвязанные картинки (для поиска похожих)
    noisy.png           — сцена с шумом «соль и перец» (для медианного фильтра)
    moving.avi          — видео: яркий шар катится по фону (для вычитания фона)

Запуск:  python make_samples.py
"""
import os

import cv2
import numpy as np

OUT = "samples"


def make_scene():
    h, w = 300, 480
    img = np.zeros((h, w, 3), np.uint8)
    # небо: вертикальный градиент от синего к светло-голубому
    for y in range(190):
        t = y / 189
        img[y, :] = (int(47 + 170 * t), int(111 + 125 * t), int(181 + 66 * t))
    # земля: градиент зелёного
    for y in range(190, h):
        t = (y - 190) / (h - 191)
        img[y, :] = (int(79 - 50 * t), int(138 - 80 * t), int(60 - 37 * t))
    cv2.circle(img, (400, 60), 34, (246, 209, 74), -1)                 # солнце
    cv2.rectangle(img, (60, 110), (190, 220), (150, 90, 60), -1)       # стены дома
    cv2.fillPoly(img, [np.array([(50, 110), (125, 55), (200, 110)])], (60, 60, 140))   # крыша
    for x in (80, 125, 160):
        cv2.rectangle(img, (x - 10, 135), (x + 10, 165), (240, 240, 240), -1)           # окна
    cv2.rectangle(img, (115, 180), (140, 220), (80, 50, 30), -1)                        # дверь
    cv2.rectangle(img, (260, 150), (330, 225), (200, 60, 60), -1)                       # красный сарай
    cv2.circle(img, (300, 205), 12, (30, 30, 30), -1)
    return img


def make_pattern(seed):
    rng = np.random.default_rng(seed)
    small = rng.integers(0, 256, (20, 30, 3), dtype=np.uint8)
    return cv2.resize(small, (480, 300), interpolation=cv2.INTER_CUBIC)


def save_rgb(name, img_rgb):
    cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))


def make_video(path, frames=90, w=320, h=200):
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 25, (w, h))
    bg = np.zeros((h, w, 3), np.uint8)
    for y in range(h):
        bg[y, :] = (60 + y // 4, 90 + y // 5, 120)
    cv2.rectangle(bg, (0, 150), (w, h), (50, 90, 50), -1)
    for t in range(frames):
        frame = bg.copy()
        x = 20 + int(t * (w - 60) / frames)
        y = 120 + int(15 * np.sin(t / 6))
        cv2.circle(frame, (x, y), 18, (250, 220, 60), -1)
        cv2.circle(frame, (x - 5, y - 5), 5, (255, 255, 255), -1)
        writer.write(frame)
    writer.release()


def main():
    os.makedirs(OUT, exist_ok=True)
    scene = make_scene()
    save_rgb("scene.png", scene)
    matrix = cv2.getRotationMatrix2D((240, 150), 6, 0.92)
    rotated = cv2.warpAffine(scene, matrix, (480, 300), borderMode=cv2.BORDER_REFLECT)
    save_rgb("scene_rotated.png", (rotated * 0.85).astype(np.uint8))
    save_rgb("pattern_a.png", make_pattern(1))
    save_rgb("pattern_b.png", make_pattern(2))
    noisy = scene.copy()
    rng = np.random.default_rng(0)
    mask = rng.random(scene.shape[:2])
    noisy[mask < 0.03] = 0
    noisy[mask > 0.97] = 255
    save_rgb("noisy.png", noisy)
    make_video(os.path.join(OUT, "moving.avi"))
    print("Готово: файлы в папке", OUT)


if __name__ == "__main__":
    main()
