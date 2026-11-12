"""Generate the documentation screenshots on a desktop.

The script boots the real app in a phone-shaped window, fills a throw-away
profile with a little progress, walks through the main screens and writes PNGs
to docs/screenshots/.  It is a development tool and is excluded from the APK.

Usage: python tools/make_screenshots.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.config import Config  # noqa: E402

Config.set("graphics", "width", "430")
Config.set("graphics", "height", "840")
Config.set("graphics", "resizable", "0")

from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402

from app.app import MathLadderApp  # noqa: E402
from app.engine.models import SessionResult  # noqa: E402
from app.engine.session import build_session  # noqa: E402

OUT_DIR = ROOT / "docs" / "screenshots"
SHOTS = [
    "01-home",
    "02-level",
    "03-practice",
    "04-feedback",
    "05-result",
    "06-stats",
    "07-settings",
    "08-about",
]


class ScreenshotApp(MathLadderApp):
    name = "MathLadderScreenshots"
    _data_dir = tempfile.mkdtemp(prefix="mathladder-shots-")

    @property
    def user_data_dir(self):
        return self._data_dir

    def on_start(self):
        self._seed_progress()
        self._pending = iter(self._steps())
        Clock.schedule_once(self._next_step, 0.8)

    # -- demo data -------------------------------------------------------
    def _seed_progress(self):
        seed_rows = [
            ("5A", "5A.count", 20, 18, 310),
            ("4A", "4A.sequence", 20, 16, 280),
            ("3A", "3A.plus1", 12, 11, 190),
            ("C", "C.table", 12, 10, 240),
            ("E", "E.same", 8, 6, 210),
            ("G", "G.linear", 10, 7, 330),
        ]
        for level, topic, total, correct, seconds in seed_rows:
            questions = build_session(level, count=total, seed=7)
            wrong = [(q, "0") for q in questions[correct:]]
            result = SessionResult(
                level=level,
                topic=topic,
                total=total,
                correct=correct,
                seconds=seconds,
                wrong=wrong,
                correct_ids=[q.qid for q in questions[:correct]],
            )
            self.repo.record_session(result)
        self.home_screen.refresh()

    # -- tour ------------------------------------------------------------
    def _steps(self):
        yield self._shot_home, "01-home"

        def level():
            self.open_level("C")

        yield level, "02-level"
        yield self._start_demo_practice, "03-practice"
        yield self._answer_demo_question, "04-feedback"
        yield self._show_demo_result, "05-result"

        def stats():
            self.open_stats()

        yield stats, "06-stats"

        def settings():
            self.open_settings()

        yield settings, "07-settings"

        def about():
            self.open_about()

        yield about, "08-about"

    @staticmethod
    def _shot_home():
        pass

    def _start_demo_practice(self):
        self.start_practice("C", topic_key="C.x1", count=10)

    def _answer_demo_question(self):
        screen = self.practice_screen
        if not screen.questions:
            return
        question = screen.questions[screen.index]
        if screen.vertical_view is not None:
            for digit in reversed(question.answer):
                screen.vertical_view.input_digit(digit)
            screen._confirm_typed()
            return
        screen._submit(question.answer)

    def _show_demo_result(self):
        questions = build_session("C", count=10, seed=21)
        wrong_questions = questions[8:]
        result = SessionResult(
            level="C",
            topic="C.x1",
            total=10,
            correct=8,
            seconds=168,
            wrong=[(wrong_questions[0], "24"), (wrong_questions[1], "36")],
            correct_ids=[q.qid for q in questions[:8]],
        )
        self.finish_session(result)

    def _next_step(self, _dt):
        try:
            action, label = next(self._pending)
        except StopIteration:
            Clock.schedule_once(self._finish, 0.8)
            return
        action()
        Clock.schedule_once(lambda dt: self._capture(label), 1.25)
        Clock.schedule_once(self._next_step, 1.65)

    def _capture(self, label):
        target = OUT_DIR / f"{label}.png"
        if target.exists():
            target.unlink()
        Window.screenshot(name=str(target))

    def _finish(self, _dt):
        # Window.screenshot() chooses "<name>0001.png"; normalise the names.
        for label in SHOTS:
            final = OUT_DIR / f"{label}.png"
            candidates = sorted(OUT_DIR.glob(f"{label}*.png"))
            for candidate in candidates:
                if candidate != final:
                    candidate.replace(final)
                    break
        print(f"saved {len(SHOTS)} screenshots to {OUT_DIR}")
        self.stop()


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("*.png"):
        stale.unlink()
    app = ScreenshotApp()
    app.run()
    shutil.rmtree(app.user_data_dir, ignore_errors=True)
