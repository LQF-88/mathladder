"""Desktop / Android entry point for MathLadder.

Desktop runs in a phone-shaped window so the layout matches the Android build.
On Android the window is provided by SDL2, so size settings are skipped.
"""

from __future__ import annotations

import os

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.config import Config

if not os.environ.get("ANDROID_ARGUMENT"):
    Config.set("graphics", "width", "430")
    Config.set("graphics", "height", "840")
    Config.set("graphics", "resizable", "1")
    Config.set(
        "kivy",
        "window_icon",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "assets", "icons", "icon-512.png"),
    )

from app.app import MathLadderApp

if __name__ == "__main__":
    MathLadderApp().run()
