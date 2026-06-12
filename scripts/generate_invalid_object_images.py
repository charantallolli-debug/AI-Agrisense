#!/usr/bin/env python3
"""
Generate invalid (non-crop) training images for stage-1 rejection.

Categories: bottles, humans, phones, books, tables, laptops, random_room

These teach the crop classifier to reject deodorant bottles, people, devices, etc.
instead of predicting "Tomato Late Blight".

Usage:
  python scripts/generate_invalid_object_images.py
  python scripts/generate_invalid_object_images.py --per-category 120
"""
from __future__ import annotations

import argparse
import logging
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CATEGORIES = [
    "bottles",
    "humans",
    "phones",
    "books",
    "tables",
    "laptops",
    "random_room",
]

SIZE = (256, 256)


def _rand_color(rng: random.Random, lo=0, hi=255):
    return (rng.randint(lo, hi), rng.randint(lo, hi), rng.randint(lo, hi))


def _background(rng: random.Random) -> Image.Image:
    """Indoor / outdoor non-foliage backgrounds."""
    mode = rng.randint(0, 4)
    img = Image.new("RGB", SIZE)
    draw = ImageDraw.Draw(img)
    if mode == 0:
        top = _rand_color(rng, 180, 255)
        bottom = _rand_color(rng, 80, 160)
        for y in range(SIZE[1]):
            t = y / SIZE[1]
            c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            draw.line([(0, y), (SIZE[0], y)], fill=c)
    elif mode == 1:
        img.paste(_rand_color(rng, 40, 120), [0, 0, SIZE[0], SIZE[1]])
        for _ in range(rng.randint(5, 15)):
            x0, y0 = rng.randint(0, 180), rng.randint(0, 180)
            x1, y1 = x0 + rng.randint(30, 70), y0 + rng.randint(30, 70)
            draw.rectangle([x0, y0, min(x1, 255), min(y1, 255)], fill=_rand_color(rng))
    else:
        img.paste(_rand_color(rng), [0, 0, SIZE[0], SIZE[1]])
    if rng.random() > 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 1.2)))
    return img


def _draw_bottle(draw: ImageDraw.Draw, rng: random.Random, cx: int, cy: int, scale: float) -> None:
    """Spray deodorant, water bottle, medicine bottle shapes."""
    w = int(35 * scale)
    h = int(90 * scale)
    body = _rand_color(rng, 30, 220)
    cap_h = int(18 * scale)
    x1, y1 = cx - w, cy - h // 2
    x2, y2 = cx + w, cy + h // 2
    draw.rectangle([x1, y1, x2, y2], fill=body)
    cap_color = _rand_color(rng, 100, 255)
    draw.rectangle([cx - w // 2, y1 - cap_h, cx + w // 2, y1], fill=cap_color)
    if rng.random() > 0.4:
        nozzle = [cx - 8, y1 - cap_h - 12, cx + 8, y1 - cap_h]
        draw.ellipse(nozzle, fill=cap_color)
    if rng.random() > 0.3:
        draw.rectangle([x1 + 4, cy - 15, x2 - 4, cy + 25], fill=_rand_color(rng, 180, 255))


def generate_bottle(rng: random.Random) -> Image.Image:
    img = _background(rng)
    draw = ImageDraw.Draw(img)
    n = rng.randint(1, 2)
    for _ in range(n):
        _draw_bottle(draw, rng, rng.randint(60, 196), rng.randint(80, 200), rng.uniform(0.8, 1.4))
    if rng.random() > 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.5, 2.0)))
    return img


def generate_human(rng: random.Random) -> Image.Image:
    """Abstract person silhouettes (not photorealistic faces)."""
    img = _background(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = rng.randint(100, 156), rng.randint(120, 200)
    skin = (rng.randint(140, 220), rng.randint(100, 180), rng.randint(80, 150))
    clothes = _rand_color(rng, 20, 180)
    # Head
    r = rng.randint(22, 32)
    draw.ellipse([cx - r, cy - 80 - r, cx + r, cy - 80 + r], fill=skin)
    # Torso
    draw.rectangle([cx - 40, cy - 75, cx + 40, cy + 10], fill=clothes)
    # Arms
    draw.line([cx - 40, cy - 50, cx - 75, cy + 5], fill=skin, width=rng.randint(8, 14))
    draw.line([cx + 40, cy - 50, cx + 75, cy + 5], fill=skin, width=rng.randint(8, 14))
    # Legs
    draw.rectangle([cx - 35, cy + 10, cx - 5, cy + 90], fill=_rand_color(rng, 20, 100))
    draw.rectangle([cx + 5, cy + 10, cx + 35, cy + 90], fill=_rand_color(rng, 20, 100))
    return img


def generate_phone(rng: random.Random) -> Image.Image:
    img = _background(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = rng.randint(70, 186), rng.randint(50, 180)
    w, h = rng.randint(50, 70), rng.randint(100, 140)
    frame = (rng.randint(10, 50), rng.randint(10, 50), rng.randint(10, 50))
    screen = (rng.randint(0, 30), rng.randint(0, 30), rng.randint(40, 80))
    draw.rectangle([cx - w, cy - h, cx + w, cy + h], fill=frame, outline=(0, 0, 0))
    draw.rectangle([cx - w + 8, cy - h + 12, cx + w - 8, cy + h - 20], fill=screen)
    for _ in range(rng.randint(2, 6)):
        bx0 = cx - w + 12 + rng.randint(0, 15)
        by0 = cy - h + 20 + rng.randint(0, 60)
        bx1 = bx0 + rng.randint(20, 50)
        by1 = by0 + rng.randint(10, 35)
        draw.rectangle([bx0, by0, min(bx1, cx + w - 5), min(by1, cy + h - 25)], fill=_rand_color(rng, 60, 200))
    return img


def generate_book(rng: random.Random) -> Image.Image:
    img = _background(rng)
    draw = ImageDraw.Draw(img)
    for i in range(rng.randint(1, 3)):
        cx = rng.randint(60, 180)
        cy = rng.randint(100, 200)
        w, h = rng.randint(70, 100), rng.randint(90, 120)
        color = _rand_color(rng, 80, 220)
        draw.rectangle([cx - w // 2, cy - h, cx + w // 2, cy], fill=color, outline=(0, 0, 0))
        # Pages lines
        for line_y in range(cy - h + 10, cy - 10, 8):
            draw.line([cx - w // 2 + 8, line_y, cx + w // 2 - 8, line_y], fill=(240, 235, 220), width=1)
    return img


def generate_table(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", SIZE, _rand_color(rng, 100, 200))
    draw = ImageDraw.Draw(img)
    # Wall
    draw.rectangle([0, 0, SIZE[0], SIZE[1] // 2], fill=_rand_color(rng, 150, 240))
    # Table surface (dominant)
    wood = (rng.randint(80, 160), rng.randint(50, 120), rng.randint(30, 80))
    draw.polygon([(0, 140), (256, 120), (256, 256), (0, 256)], fill=wood)
    # Objects on table (mug, paper — not crops)
    if rng.random() > 0.4:
        draw.ellipse([80, 150, 130, 200], fill=_rand_color(rng))
    if rng.random() > 0.4:
        draw.rectangle([150, 160, 220, 190], fill=(250, 250, 240))
    return img


def generate_laptop(rng: random.Random) -> Image.Image:
    img = _background(rng)
    draw = ImageDraw.Draw(img)
    cx, cy = 128, 150
    # Base
    draw.polygon([(40, cy + 40), (216, cy + 40), (200, cy + 70), (56, cy + 70)], fill=(80, 80, 85))
    # Screen
    draw.polygon([(50, cy - 60), (206, cy - 60), (216, cy + 35), (40, cy + 35)], fill=(30, 30, 35))
    screen_gray = rng.randint(40, 100)
    draw.polygon([(58, cy - 52), (198, cy - 52), (206, cy + 28), (50, cy + 28)], fill=(screen_gray,) * 3)
    # Keyboard hint
    for row in range(4):
        for col in range(8):
            draw.rectangle(
                [60 + col * 18, cy + 45 + row * 5, 72 + col * 18, cy + 48 + row * 5],
                fill=(120, 120, 125),
            )
    return img


def generate_random_room(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", SIZE, _rand_color(rng, 90, 180))
    draw = ImageDraw.Draw(img)
    # Floor
    floor_c = _rand_color(rng, 60, 140)
    draw.rectangle([0, SIZE[1] // 2, SIZE[0], SIZE[1]], fill=floor_c)
    # Wall with window / furniture blocks
    draw.rectangle([0, 0, SIZE[0], SIZE[1] // 2], fill=_rand_color(rng, 120, 230))
    if rng.random() > 0.5:
        draw.rectangle([60, 40, 180, 120], fill=(180, 210, 240))  # window
    # Couch / shelf blocks
    draw.rectangle([20, 130, 100, 200], fill=_rand_color(rng, 40, 150))
    draw.rectangle([160, 100, 240, 180], fill=_rand_color(rng, 40, 150))
    # Clutter
    for _ in range(rng.randint(3, 8)):
        x0, y0 = rng.randint(0, 200), rng.randint(0, 200)
        x1, y1 = x0 + rng.randint(15, 55), y0 + rng.randint(15, 55)
        draw.ellipse([x0, y0, min(x1, 255), min(y1, 255)], fill=_rand_color(rng))
    if rng.random() > 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.8, 2.5)))
    return img


GENERATORS = {
    "bottles": generate_bottle,
    "humans": generate_human,
    "phones": generate_phone,
    "books": generate_book,
    "tables": generate_table,
    "laptops": generate_laptop,
    "random_room": generate_random_room,
}


def generate_category(out_dir: Path, category: str, count: int, seed: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed + hash(category) % 10000)
    gen = GENERATORS[category]
    written = 0
    for i in range(count):
        path = out_dir / f"{category}_{i:04d}.jpg"
        if path.exists():
            written += 1
            continue
        img = gen(rng)
        # Simulate mobile JPEG compression
        img.save(path, "JPEG", quality=rng.randint(72, 92))
        written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate invalid object training images")
    parser.add_argument("--per-category", type=int, default=100, help="Images per folder")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base = DATA_PATHS["dataset_sources"] / "invalid_objects"
    base.mkdir(parents=True, exist_ok=True)

    logger.info("Generating invalid object images in %s", base)
    total = 0
    for cat in CATEGORIES:
        n = generate_category(base / cat, cat, args.per_category, args.seed)
        total += n
        logger.info("  %s: %d images", cat, n)

    logger.info("Done — %d total images across %d categories", total, len(CATEGORIES))
    logger.info("Next: python scripts/prepare_indian_agriculture_dataset.py")


if __name__ == "__main__":
    main()
