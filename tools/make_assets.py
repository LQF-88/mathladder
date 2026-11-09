"""Generate app icon, splash screen and feedback sounds.

Run from the repository root:
    python tools/make_assets.py

The generated files are committed so a normal app build does not need Pillow.
"""

from __future__ import annotations

import math
import os
import struct
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = os.path.join(ROOT, "app", "assets", "fonts", "NotoSansSC-Bold.otf")
FONT_REGULAR = os.path.join(ROOT, "app", "assets", "fonts", "NotoSansSC-Regular.otf")
ICON_DIR = os.path.join(ROOT, "app", "assets", "icons")
SOUND_DIR = os.path.join(ROOT, "app", "assets", "sounds")

INDIGO = (91, 108, 255)
INDIGO_DARK = (63, 76, 204)
ORANGE = (255, 138, 91)
GREEN = (53, 194, 138)
CREAM = (255, 248, 240)
INK = (43, 45, 66)
MUTED = (122, 127, 154)


def draw_logo(size: int = 1024, rounded: bool = True, plate: bool = True) -> Image.Image:
    radius = int(size * 0.22) if rounded else 0

    # Background + decorations are clipped to the rounded square.
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(base)
    bd.rounded_rectangle((0, 0, size, size), radius=radius, fill=INDIGO)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    base.putalpha(mask)

    img = base
    d = ImageDraw.Draw(img)

    if plate:
        # Cream plate keeps the mark readable on every launcher background.
        plate_box = (
            int(size * 0.145),
            int(size * 0.145),
            int(size * 0.855),
            int(size * 0.855),
        )
        d.rounded_rectangle(plate_box, radius=int(size * 0.20), fill=CREAM)

    # Three ascending steps: 1, 2, 3.
    bar_w = int(size * 0.135)
    gap = int(size * 0.045)
    base_y = int(size * 0.715)
    start_x = int(size * 0.285)
    heights = [int(size * 0.16), int(size * 0.25), int(size * 0.34)]
    colors = [GREEN, ORANGE, INDIGO]
    font = ImageFont.truetype(FONT_BOLD, int(size * 0.105))
    for i, (h, color) in enumerate(zip(heights, colors, strict=False)):
        x0 = start_x + i * (bar_w + gap)
        x1 = x0 + bar_w
        y0 = base_y - h
        d.rounded_rectangle((x0, y0, x1, base_y), radius=int(bar_w * 0.22), fill=color)
        label = str(i + 1)
        bbox = d.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(
            (x0 + (bar_w - tw) / 2 - bbox[0], base_y - th - int(size * 0.025) - bbox[1]),
            label,
            font=font,
            fill=CREAM,
        )

    # Star above the tallest step.
    cx, cy, r = int(size * 0.745), int(size * 0.245), int(size * 0.070)
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.44
        points.append((cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
    d.polygon(points, fill=ORANGE)
    return img


def make_icons() -> None:
    os.makedirs(ICON_DIR, exist_ok=True)
    logo = draw_logo(1024)
    for size in (1024, 512, 192):
        logo.resize((size, size), Image.LANCZOS).save(
            os.path.join(ICON_DIR, f"icon-{size}.png")
        )
    # Android adaptive-friendly full-bleed version without rounded corners.
    draw_logo(1024, rounded=False).save(os.path.join(ICON_DIR, "icon-foreground.png"))


def make_splash() -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), CREAM)
    d = ImageDraw.Draw(img)
    d.ellipse((-260, 1230, 420, 1910), fill=(255, 238, 224))
    d.ellipse((730, -170, 1330, 430), fill=(226, 230, 255))

    logo = draw_logo(680, plate=False)
    img.paste(logo, ((w - 680) // 2, 430), logo)

    title_font = ImageFont.truetype(FONT_BOLD, 118)
    sub_font = ImageFont.truetype(FONT_REGULAR, 52)
    tag_font = ImageFont.truetype(FONT_REGULAR, 38)

    def center_text(text, font, y, fill):
        bbox = d.textbbox((0, 0), text, font=font)
        d.text(((w - (bbox[2] - bbox[0])) / 2 - bbox[0], y), text, font=font, fill=fill)

    center_text("数学阶梯", title_font, 1180, INK)
    center_text("MathLadder", sub_font, 1330, INDIGO)
    center_text("每天一小步 · 数学一大步", tag_font, 1460, MUTED)
    img.save(os.path.join(ICON_DIR, "splash.png"))


def _tone(freq: float, dur: float, volume: float = 0.32) -> list[int]:
    rate = 44100
    n = int(rate * dur)
    out = []
    for i in range(n):
        env = min(1.0, i / 400) * min(1.0, (n - i) / 900)
        out.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / rate)))
    return out


def write_wav(path: str, samples: list[int], rate: int = 44100) -> None:
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", s) for s in samples))


def make_sounds() -> None:
    os.makedirs(SOUND_DIR, exist_ok=True)
    correct = _tone(880, 0.09) + _tone(1174.66, 0.14)
    wrong = _tone(220, 0.11, 0.28) + _tone(164.81, 0.18, 0.26)
    write_wav(os.path.join(SOUND_DIR, "correct.wav"), correct)
    write_wav(os.path.join(SOUND_DIR, "wrong.wav"), wrong)


if __name__ == "__main__":
    make_icons()
    make_splash()
    make_sounds()
    print("assets written to", ICON_DIR, SOUND_DIR)
