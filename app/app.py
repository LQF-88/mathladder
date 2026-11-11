"""Application object: screen wiring, navigation, sound and session lifecycle."""

from __future__ import annotations

import os
from collections import Counter

from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from app.engine.curriculum import LEVEL_BY_CODE, TOPIC_BY_KEY, level_of
from app.engine.session import build_session, questions_from_mistakes
from app.storage.repository import Repository
from app.theme import ASSETS_DIR, CREAM
from app.ui.screens.about import AboutScreen
from app.ui.screens.home import HomeScreen
from app.ui.screens.level import LevelScreen
from app.ui.screens.practice import PracticeScreen
from app.ui.screens.result import ResultScreen
from app.ui.screens.settings import SettingsScreen
from app.ui.screens.stats import StatsScreen


class MathLadderApp(App):
    name = "MathLadder"
    VERSION = "1.0.2"

    def build(self):
        self.title = "数学阶梯 · MathLadder"
        Window.clearcolor = CREAM
        data_dir = self.user_data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.repo = Repository(os.path.join(data_dir, "progress.json"))
        self.sounds = self._load_sounds()
        self._settings_return = "home"
        self._about_return = "settings"

        self.sm = ScreenManager(transition=SlideTransition(duration=0.18))
        self.home_screen = HomeScreen(self)
        self.level_screen = LevelScreen(self)
        self.practice_screen = PracticeScreen(self)
        self.result_screen = ResultScreen(self)
        self.stats_screen = StatsScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.about_screen = AboutScreen(self)
        for screen in (
            self.home_screen,
            self.level_screen,
            self.practice_screen,
            self.result_screen,
            self.stats_screen,
            self.settings_screen,
            self.about_screen,
        ):
            self.sm.add_widget(screen)
        self.sm.current = "home"
        Window.bind(on_keyboard=self._on_keyboard)
        return self.sm

    def _load_sounds(self) -> dict:
        sounds = {}
        for key, filename in (("correct", "correct.wav"), ("wrong", "wrong.wav")):
            path = os.path.join(ASSETS_DIR, "sounds", filename)
            try:
                sound = SoundLoader.load(path)
            except Exception as exc:  # audio backends vary by platform
                Logger.warning("MathLadder: could not load %s (%s)", path, exc)
                sound = None
            if sound is not None:
                sound.volume = 0.45
            sounds[key] = sound
        return sounds

    # -- navigation ------------------------------------------------------
    def level_of(self, code: str):
        return level_of(code)

    def open_home(self):
        if self.sm.current != "home":
            self.sm.current = "home"

    def open_level(self, code: str):
        self.level_screen.show_level(code)
        self.sm.current = "level"

    def open_stats(self):
        self.sm.current = "stats"

    def open_settings(self):
        current = self.sm.current
        if current not in ("settings", "about", "practice"):
            self._settings_return = current
        self.sm.current = "settings"

    def close_settings(self):
        target = self._settings_return
        if target not in self.sm.screen_names:
            target = "home"
        self.sm.current = target

    def open_about(self):
        current = self.sm.current
        self._about_return = current if current in self.sm.screen_names else "settings"
        self.sm.current = "about"

    def close_about(self):
        target = self._about_return
        if target not in self.sm.screen_names:
            target = "settings"
        self.sm.current = target

    # -- sessions --------------------------------------------------------
    def start_practice(self, level_code: str, topic_key=None, count=None):
        if level_code not in LEVEL_BY_CODE:
            level_code = "5A"
        count = int(count or self.repo.get_setting("questions_per_session", 20))
        count = max(1, min(50, count))
        questions = build_session(level_code, count=count, topic_key=topic_key)
        if not questions:
            Logger.warning("MathLadder: no questions generated for %s", level_code)
            return
        self.practice_screen.start(level_code, topic_key, questions)
        self.sm.current = "practice"

    def start_mistake_session(self, records, level: str | None = None):
        records = list(records or [])[:30]
        questions = questions_from_mistakes(records)
        if not questions:
            return
        if level not in LEVEL_BY_CODE:
            counts = Counter(question.level for question in questions)
            level = counts.most_common(1)[0][0]
        self.practice_screen.start(level, None, questions, from_mistakes=True)
        self.sm.current = "practice"

    def retry_wrong(self, result):
        questions = [question for question, _answer in result.wrong]
        if not questions:
            self.open_home()
            return
        topic = result.topic if result.topic in TOPIC_BY_KEY else None
        self.practice_screen.start(
            result.level, topic, questions, from_mistakes=True
        )
        self.sm.current = "practice"

    def finish_session(self, result):
        try:
            self.repo.record_session(result)
        except Exception as exc:  # never lose the result screen to a save error
            Logger.exception("MathLadder: failed to save session (%s)", exc)
        self.result_screen.show_result(result)
        self.sm.current = "result"

    # -- feedback --------------------------------------------------------
    def play_feedback(self, correct: bool):
        if not self.repo.get_setting("sound", True):
            return
        sound = self.sounds.get("correct" if correct else "wrong")
        if sound is None:
            return
        try:
            sound.stop()
            sound.play()
        except Exception as exc:
            Logger.warning("MathLadder: sound playback failed (%s)", exc)

    # -- Android / desktop back -----------------------------------------
    def _on_keyboard(self, _window, key, *_args):
        if key not in (27, 1001):  # Escape or Android back
            return False
        current = self.sm.current
        if current == "practice":
            self.practice_screen.request_back()
            return True
        if current in ("level", "stats", "result"):
            self.open_home()
            return True
        if current == "settings":
            self.close_settings()
            return True
        if current == "about":
            self.close_about()
            return True
        return False

    def on_pause(self):
        return True

    def on_resume(self):
        return True
