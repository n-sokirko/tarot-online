"""
Process zodiac card images:
  1. Crop out the ornate frame + number (top) + text labels (bottom)
  2. Make dark background pixels transparent (alpha channel)
  3. Save back as PNG with transparency
"""
from PIL import Image
import numpy as np
import os

SLUGS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

SRC_DIR = r"E:\taro_cards\frontend\public\zodiac"
DST_DIR = r"E:\taro_cards\frontend\public\zodiac"

# Crop fractions: (left, top, right, bottom) — how much to cut from each side
CROP = (0.13, 0.08, 0.13, 0.20)

# Pixels with V < BG_THRESHOLD and not golden become transparent
BG_THRESHOLD = 0.30
# Feather zone: pixels with BG_THRESHOLD <= V < FEATHER_MAX get partial alpha
FEATHER_MAX  = 0.45


def remove_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    data = np.array(rgba, dtype=np.float32)

    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]

    # Brightness (Value in HSV)
    v = np.maximum(np.maximum(r, g), b) / 255.0

    # "Golden" detector: warm hue with reasonable brightness
    # Golden/amber pixels have high R, decent G, low B
    is_golden = (r > 140) & (g > 80) & (b < 120) & ((r - b) > 60)

    # Build alpha
    alpha = np.ones(v.shape, dtype=np.float32) * 255.0
    # Hard background
    mask_bg = (v < BG_THRESHOLD) & ~is_golden
    alpha[mask_bg] = 0.0
    # Feather zone
    mask_feather = (v >= BG_THRESHOLD) & (v < FEATHER_MAX) & ~is_golden
    t = (v[mask_feather] - BG_THRESHOLD) / (FEATHER_MAX - BG_THRESHOLD)
    alpha[mask_feather] = (t * 255.0)

    data[:, :, 3] = np.clip(alpha, 0, 255)
    return Image.fromarray(data.astype(np.uint8), "RGBA")


def crop_card(img: Image.Image) -> Image.Image:
    w, h = img.size
    l = int(w * CROP[0])
    t = int(h * CROP[1])
    r = int(w * (1 - CROP[2]))
    b = int(h * (1 - CROP[3]))
    return img.crop((l, t, r, b))


def process(slug: str):
    path = os.path.join(SRC_DIR, f"{slug}.png")
    if not os.path.exists(path):
        print(f"  SKIP {slug} (not found)")
        return
    img = Image.open(path)
    img = crop_card(img)
    img = remove_background(img)
    out = os.path.join(DST_DIR, f"{slug}.png")
    img.save(out, "PNG")
    print(f"  OK   {slug}.png  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    print("Processing zodiac images...")
    for slug in SLUGS:
        process(slug)
    print("Done.")
