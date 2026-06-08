"""
Process planet card images:
  1. Crop the ornate frame from edges
  2. Make dark background transparent
  3. Save to frontend/public/planets/
"""
from PIL import Image
import numpy as np
import os

MAPPING = {
    "1.png":  "sun.png",
    "2.png":  "moon.png",
    "3.png":  "mercury.png",
    "4.png":  "venus.png",
    "5.png":  "mars.png",
    "6.png":  "jupiter.png",
    "7.png":  "saturn.png",
    "8.png":  "uranus.png",
    "9.png":  "neptune.png",
    "10.png": "ascendant.png",
}

SRC_DIR = r"E:\taro_cards"
DST_DIR = r"E:\taro_cards\frontend\public\planets"

# Crop fractions: left, top, right, bottom
CROP = (0.11, 0.07, 0.11, 0.10)

BG_THRESHOLD = 0.28
FEATHER_MAX  = 0.42

os.makedirs(DST_DIR, exist_ok=True)


def remove_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    data = np.array(rgba, dtype=np.float32)
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    v = np.maximum(np.maximum(r, g), b) / 255.0
    is_golden = (r > 140) & (g > 80) & (b < 130) & ((r - b) > 50)
    alpha = np.ones(v.shape, dtype=np.float32) * 255.0
    mask_bg = (v < BG_THRESHOLD) & ~is_golden
    alpha[mask_bg] = 0.0
    mask_feather = (v >= BG_THRESHOLD) & (v < FEATHER_MAX) & ~is_golden
    t = (v[mask_feather] - BG_THRESHOLD) / (FEATHER_MAX - BG_THRESHOLD)
    alpha[mask_feather] = t * 255.0
    data[:, :, 3] = np.clip(alpha, 0, 255)
    return Image.fromarray(data.astype(np.uint8), "RGBA")


def crop_card(img: Image.Image) -> Image.Image:
    w, h = img.size
    l = int(w * CROP[0])
    t = int(h * CROP[1])
    r = int(w * (1 - CROP[2]))
    b = int(h * (1 - CROP[3]))
    return img.crop((l, t, r, b))


def process(src_name: str, dst_name: str):
    src = os.path.join(SRC_DIR, src_name)
    dst = os.path.join(DST_DIR, dst_name)
    if not os.path.exists(src):
        print(f"  SKIP {src_name}")
        return
    img = Image.open(src)
    img = crop_card(img)
    img = remove_background(img)
    img.save(dst, "PNG")
    print(f"  OK   {src_name} -> {dst_name}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    print("Processing planet images...")
    for src, dst in MAPPING.items():
        process(src, dst)
    print("Done.")
