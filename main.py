#!/usr/bin/env python3
"""LUMARIS — a travel poster for a place that does not exist.

A night poster for a stilt town on a glowing lagoon, drawn entirely
procedurally with PIL: no assets, no network, no fonts fetched from
anywhere. Deterministic: the same seed draws the same poster, so two
runs are byte-identical. Writes one image to /output/entry.png
(MAKEFUN_OUTPUT_DIR stands in for /output outside the grader).
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
OUT = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
SEED = 20261121

# Palette: one night, one warm light, one glow.
SKY_TOP = (13, 18, 46)
SKY_MID = (22, 44, 84)
SKY_HOR = (44, 92, 104)
LAGOON_TOP = (13, 92, 100)
LAGOON_BOT = (7, 46, 62)
CREAM = (245, 234, 208)
PALE = (214, 226, 232)
AMBER = (255, 196, 107)
GLOW = (127, 231, 212)
DARK = (18, 14, 38)
HOUSE = (24, 20, 48)
TERRA = (198, 110, 74)


def font(name, size):
    """DejaVu from the system (the grader sandbox has it, as the
    news-image entry proved); fall back to PIL's built-in font."""
    try:
        return ImageFont.truetype(
            f"/usr/share/fonts/truetype/dejavu/{name}", size
        )
    except OSError:
        return ImageFont.load_default()


def vgrad(w, h, stops):
    """Vertical gradient through (position, colour) stops."""
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[0, y] = tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
                break
        else:
            px[0, y] = stops[-1][1]
    return base.resize((w, h))


def tracked_text(draw, cx, y, text, fnt, fill, tracking=0):
    """Draw centred text with letter tracking; returns its width."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wd in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += wd + tracking
    return total


def main():
    rng = random.Random(SEED)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)

    # --- Sky and lagoon -------------------------------------------------
    sky = vgrad(W, 660, [(0.0, SKY_TOP), (0.55, SKY_MID), (1.0, SKY_HOR)])
    img.paste(sky, (0, 0))
    lagoon = vgrad(W, H - 640, [(0.0, LAGOON_TOP), (1.0, LAGOON_BOT)])
    img.paste(lagoon, (0, 640))
    d = ImageDraw.Draw(img)

    # --- Stars ----------------------------------------------------------
    for _ in range(190):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 560)
        r = rng.choice([1, 1, 1, 2, 2, 3])
        a = rng.randint(120, 235)
        col = (a, a, min(255, a + 20))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    # A few bright four-point stars.
    for _ in range(7):
        x = rng.uniform(60, W - 60)
        y = rng.uniform(40, 420)
        s = rng.uniform(5, 9)
        d.line([x - s, y, x + s, y], fill=(235, 240, 245), width=1)
        d.line([x, y - s, x, y + s], fill=(235, 240, 245), width=1)

    # --- Moon with halo ---------------------------------------------------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    mx, my, mr = 168, 330, 74
    gd.ellipse([mx - mr - 46, my - mr - 46, mx + mr + 46, my + mr + 46],
               fill=(245, 234, 208, 46))
    gd.ellipse([mx - mr - 18, my - mr - 18, mx + mr + 18, my + mr + 18],
               fill=(245, 234, 208, 70))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow.filter(
        ImageFilter.GaussianBlur(18))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=CREAM)
    for cx, cy, cr, shade in [(140, 306, 13, (228, 214, 184)),
                              (188, 352, 9, (228, 214, 184)),
                              (196, 308, 6, (232, 220, 192))]:
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=shade)

    # --- Lighthouse (right) ---------------------------------------------
    lx = 848
    base_y, top_y = 648, 372
    # Tower: tapered, cream with terracotta bands.
    d.polygon([(lx - 34, base_y), (lx - 20, top_y),
               (lx + 20, top_y), (lx + 34, base_y)], fill=CREAM)
    for by in (452, 522, 592):
        w0 = 34 - (by - base_y) * (14 / (base_y - top_y))
        d.polygon([(lx - w0, by - 14), (lx - w0 + 4, by - 26),
                   (lx + w0 - 4, by - 26), (lx + w0, by - 14)],
                  fill=TERRA)
    # Gallery + lamp room.
    d.rectangle([lx - 26, top_y - 14, lx + 26, top_y], fill=DARK)
    d.rectangle([lx - 18, top_y - 44, lx + 18, top_y - 14], fill=AMBER)
    d.polygon([(lx - 24, top_y - 44), (lx + 24, top_y - 44),
               (lx + 14, top_y - 58), (lx - 14, top_y - 58)], fill=DARK)
    # Beam: a soft cone of light sweeping left over the town.
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(lx, top_y - 28), (120, 420), (120, 560)], fill=(255, 236, 180, 52))
    bd.polygon([(lx, top_y - 28), (1000, 330), (1000, 430)], fill=(255, 236, 180, 40))
    img.paste(Image.alpha_composite(img.convert("RGBA"), beam.filter(
        ImageFilter.GaussianBlur(6))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    # Lamp glow: a tight halo, not a ball — the lamp room stays rectangular.
    d.ellipse([lx - 21, top_y - 50, lx + 21, top_y - 8], fill=(255, 220, 130))
    d.ellipse([lx - 14, top_y - 44, lx + 14, top_y - 14], fill=(255, 244, 200))

    # --- Stilt town on the horizon --------------------------------------
    horizon = 640
    houses = [
        # x, width, height, roof peak
        (70, 92, 74, 34), (168, 76, 96, 40), (252, 104, 66, 30),
        (364, 84, 88, 36), (456, 96, 70, 32), (560, 78, 98, 42),
        (646, 92, 72, 30), (726, 70, 60, 26),
    ]
    for hx, hw, hh, peak in houses:
        # Stilts down into the lagoon.
        for sx in (hx + 8, hx + hw // 2, hx + hw - 8):
            d.line([sx, horizon + 6, sx, horizon + 44], fill=DARK, width=4)
        # Body and gable roof.
        d.rectangle([hx, horizon - hh, hx + hw, horizon + 6], fill=HOUSE)
        d.polygon([(hx - 6, horizon - hh), (hx + hw // 2, horizon - hh - peak),
                   (hx + hw + 6, horizon - hh)], fill=(30, 26, 56))
        # Warm windows.
        for wx in range(hx + 12, hx + hw - 10, 26):
            wy = horizon - hh + 18 + (rng.choice([0, 22]))
            d.rectangle([wx, wy, wx + 12, wy + 16], fill=AMBER)
    # A pier reaching out into the glow.
    d.rectangle([300, horizon + 8, 560, horizon + 18], fill=DARK)
    for px in range(310, 560, 36):
        d.line([px, horizon + 18, px, horizon + 52], fill=DARK, width=5)
    d.ellipse([548, horizon - 6, 572, horizon + 18], fill=AMBER)  # pier lamp

    # --- Lagoon glow, sparkles, reflections -----------------------------
    glow2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g2 = ImageDraw.Draw(glow2)
    for cx, cy, rx, ry in [(300, 800, 260, 60), (700, 880, 300, 70),
                           (512, 960, 340, 60), (150, 920, 160, 46)]:
        g2.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(*GLOW, 44))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow2.filter(
        ImageFilter.GaussianBlur(30))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(260):
        x = rng.uniform(0, W)
        y = rng.uniform(660, 1000)
        r = rng.choice([1, 1, 2, 2, 3])
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(150, 235, 215) if rng.random() < 0.75 else (255, 220, 140))
    # Reflections: lighthouse beam and window light shimmering down.
    for i in range(26):
        x = lx + rng.uniform(-26, 26)
        y0 = 700 + i * 11
        ln = rng.uniform(14, 42)
        d.line([x, y0, x, y0 + ln], fill=(255, 210, 130), width=3)
    for i in range(18):
        x = rng.uniform(120, 700)
        y0 = rng.uniform(690, 900)
        d.line([x, y0, x, y0 + rng.uniform(10, 26)], fill=AMBER, width=2)
    # Two small boats, one with a lantern.
    for bx, by, s in [(620, 780, 1.0), (230, 850, 0.8)]:
        bw, bh = int(86 * s), int(20 * s)
        d.polygon([(bx - bw // 2, by), (bx + bw // 2, by),
                   (bx + bw // 2 - 10, by + bh), (bx - bw // 2 + 10, by + bh)],
                  fill=DARK)
        d.line([bx, by - int(34 * s), bx, by], fill=DARK, width=3)
        d.polygon([(bx, by - int(34 * s)), (bx + int(26 * s), by - 2),
                   (bx, by - 2)], fill=CREAM)
        d.ellipse([bx - 5, by - 12, bx + 5, by - 2], fill=AMBER)

    # --- Type: the place's name, then its promise ------------------------
    name_font = font("DejaVuSans-Bold.ttf", 148)
    tag_font = font("DejaVuSans.ttf", 33)
    # Soft shadow so the name holds against the sky.
    tracked_text(d, W // 2 + 4, 66, "LUMARIS", name_font, (8, 10, 28), tracking=14)
    tracked_text(d, W // 2, 62, "LUMARIS", name_font, CREAM, tracking=14)
    tracked_text(d, W // 2, 226, "WHERE THE SEA LIGHTS THE WAY HOME",
                 tag_font, PALE, tracking=6)
    # A small rule with a diamond, under the tagline.
    d.line([W // 2 - 150, 288, W // 2 - 14, 288], fill=AMBER, width=2)
    d.line([W // 2 + 14, 288, W // 2 + 150, 288], fill=AMBER, width=2)
    d.polygon([(W // 2, 280), (W // 2 + 8, 288), (W // 2, 296), (W // 2 - 8, 288)],
              fill=AMBER)

    # --- Thin frame -------------------------------------------------------
    d.rectangle([26, 26, W - 26, H - 26], outline=(245, 234, 208), width=3)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "entry.png"
    img.save(path)

    # The gate refuses anything over 1 MiB or 1024 px a side, so fail
    # loudly here instead of handing in an image the judge never sees.
    size = path.stat().st_size
    if img.size != (1024, 1024) or size > 1_048_576:
        raise SystemExit(
            f"entry.png failed the gate: {img.size} px, {size} bytes"
        )
    print("wrote", path, img.size, f"{size} bytes")


if __name__ == "__main__":
    main()
