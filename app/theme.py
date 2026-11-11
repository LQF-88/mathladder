"""App-wide colours, fonts and small drawing helpers."""

from __future__ import annotations

import os

from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, "assets")
FONT_REGULAR = os.path.join(ASSETS_DIR, "fonts", "NotoSansSC-Regular.otf")
FONT_BOLD = os.path.join(ASSETS_DIR, "fonts", "NotoSansSC-Bold.otf")
FONT_NAME = "NotoSC"

# Override Kivy's default font as well, so every stock widget gets CJK glyphs.
LabelBase.register(name="Roboto", fn_regular=FONT_REGULAR, fn_bold=FONT_BOLD)
LabelBase.register(name=FONT_NAME, fn_regular=FONT_REGULAR, fn_bold=FONT_BOLD)


def c(hex_color: str, alpha: float = 1.0) -> list[float]:
    rgba = get_color_from_hex(hex_color)
    rgba[3] = alpha
    return rgba


CREAM = c("#FFF8F0")
CREAM_DARK = c("#F7ECDF")
WHITE = c("#FFFFFF")
INK = c("#2B2D42")
MUTED = c("#7A7F9A")
MUTED_LIGHT = c("#A8ACC0")
LINE = c("#ECE6DE")
INDIGO = c("#5B6CFF")
INDIGO_DARK = c("#4250D8")
INDIGO_SOFT = c("#EEF0FF")
ORANGE = c("#FF8A5B")
ORANGE_SOFT = c("#FFF0E8")
GREEN = c("#35C28A")
GREEN_SOFT = c("#E7F8F1")
RED = c("#FF5C6C")
RED_SOFT = c("#FFECEF")
YELLOW = c("#FFB020")
YELLOW_SOFT = c("#FFF6DF")
TRACK = c("#EFEDE8")

LEVEL_TINTS = {
    "5A": c("#FFF0E8"),
    "4A": c("#FFF4E4"),
    "3A": c("#FFF9DE"),
    "2A": c("#F3FBDD"),
    "A": c("#E7F8F1"),
    "B": c("#E3F8F5"),
    "C": c("#E5F7FA"),
    "D": c("#E8F3FD"),
    "E": c("#EEF0FF"),
    "F": c("#F1EEFF"),
    "G": c("#F4EDFF"),
    "H": c("#FAECFF"),
    "I": c("#FDECFF"),
    "J": c("#FFEBF4"),
    "K": c("#FFEDF1"),
    "L": c("#FFEEE9"),
}

FONT_SIZE_TITLE = 22
SCREEN_PAD = 16
CARD_RADIUS = 18

# The UI was originally designed with desktop-sized type, which is hard to read
# on phones where Kivy's density is close to 1. Scale every designed font size
# up a little, giving the smallest labels the biggest relative boost. This is
# applied on top of Kivy's own system font-scale, not instead of it.
FONT_SCALE = 1.15
FONT_BOOST = 1.0


def readable_font_size(size: float) -> float:
    """Return a phone-friendly size for a designed font size."""
    return size * FONT_SCALE + FONT_BOOST
