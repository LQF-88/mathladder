"""Tiny JSON repository for progress, settings, sessions and mistakes.

The app is fully offline; a single JSON document is stored in Kivy's
``user_data_dir`` (private app storage on Android).  Writes are atomic so a
crash cannot leave a half-written progress file.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Any

from app.engine.curriculum import LEVEL_BY_CODE, LEVELS
from app.engine.models import Question, SessionResult


def _today() -> str:
    return date.today().isoformat()


def _yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def _default_data() -> dict[str, Any]:
    return {
        "version": 1,
        "settings": {
            "questions_per_session": 20,
            "sound": True,
            "auto_next": False,
            "vertical_input": True,
        },
        "progress": {},
        "sessions": [],
        "mistakes": [],
        "streak": {"current": 0, "best": 0, "last_day": None},
        "daily": {},
    }


def _default_level() -> dict[str, Any]:
    return {
        "answered": 0,
        "correct": 0,
        "sessions": 0,
        "stars": 0,
        "last_day": None,
        "topics": {},
    }


class Repository:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load()

    # -- persistence -----------------------------------------------------
    def _load(self) -> dict[str, Any]:
        if not os.path.exists(self.path):
            return _default_data()
        try:
            with open(self.path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, ValueError):
            return _default_data()
        data = _default_data()
        if isinstance(raw, dict):
            data.update(raw)
        data["settings"] = {**_default_data()["settings"], **(data.get("settings") or {})}
        if not isinstance(data.get("progress"), dict):
            data["progress"] = {}
        if not isinstance(data.get("sessions"), list):
            data["sessions"] = []
        if not isinstance(data.get("mistakes"), list):
            data["mistakes"] = []
        if not isinstance(data.get("daily"), dict):
            data["daily"] = {}
        streak = data.get("streak")
        if not isinstance(streak, dict):
            data["streak"] = {"current": 0, "best": 0, "last_day": None}
        return data

    def save(self) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix="mathladder-", suffix=".json", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # -- settings --------------------------------------------------------
    @property
    def settings(self) -> dict[str, Any]:
        return self.data["settings"]

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save()

    # -- progress --------------------------------------------------------
    def level_progress(self, code: str) -> dict[str, Any]:
        current = self.data["progress"].get(code)
        if not isinstance(current, dict):
            current = _default_level()
            self.data["progress"][code] = current
        for key, value in _default_level().items():
            current.setdefault(key, value)
        if not isinstance(current.get("topics"), dict):
            current["topics"] = {}
        return current

    def progress_percent(self, code: str) -> float:
        level = LEVEL_BY_CODE.get(code)
        target = level.target if level else 200
        answered = self.level_progress(code).get("answered", 0)
        return min(1.0, answered / target) if target else 0.0

    def stars(self, code: str) -> int:
        return int(self.level_progress(code).get("stars", 0))

    def total_stars(self) -> int:
        return sum(self.stars(level.code) for level in LEVELS)

    def total_answered(self) -> int:
        return sum(int(self.level_progress(level.code).get("answered", 0)) for level in LEVELS)

    def total_correct(self) -> int:
        return sum(int(self.level_progress(level.code).get("correct", 0)) for level in LEVELS)

    def overall_accuracy(self) -> int:
        answered = self.total_answered()
        return round(self.total_correct() * 100 / answered) if answered else 0

    def streak(self) -> dict[str, Any]:
        streak = self.data["streak"]
        if streak.get("last_day") and streak.get("last_day") not in (_today(), _yesterday()):
            # The stored streak is stale, but keep it as "best" for display.
            streak["current"] = 0
        return streak

    def recommended_level(self) -> str:
        sessions = self.data.get("sessions") or []
        if sessions:
            last_level = sessions[-1].get("level")
            if last_level in LEVEL_BY_CODE:
                return last_level
        for level in LEVELS:
            if self.level_progress(level.code)["answered"] < 40:
                return level.code
        return LEVELS[0].code

    def last_practiced_topic(self, code: str) -> str | None:
        for session in reversed(self.data.get("sessions") or []):
            if session.get("level") == code and session.get("topic"):
                return session["topic"]
        return None

    # -- sessions --------------------------------------------------------
    def record_session(self, result: SessionResult) -> None:
        today = _today()
        progress = self.level_progress(result.level)
        progress["answered"] += result.total
        progress["correct"] += result.correct
        progress["sessions"] += 1
        progress["stars"] = max(int(progress.get("stars", 0)), result.stars)
        progress["last_day"] = today
        topic = progress["topics"].get(result.topic)
        if not isinstance(topic, dict):
            topic = {"answered": 0, "correct": 0}
            progress["topics"][result.topic] = topic
        topic["answered"] += result.total
        topic["correct"] += result.correct

        self.data["sessions"].append(
            {
                "date": datetime.now().isoformat(timespec="seconds"),
                "day": today,
                "level": result.level,
                "topic": result.topic,
                "total": result.total,
                "correct": result.correct,
                "seconds": result.seconds,
                "accuracy": result.accuracy,
            }
        )
        self.data["sessions"] = self.data["sessions"][-200:]

        daily = self.data["daily"].setdefault(today, {"answered": 0, "correct": 0})
        daily["answered"] += result.total
        daily["correct"] += result.correct
        self._prune_daily()

        streak = self.data["streak"]
        last_day = streak.get("last_day")
        if last_day != today:
            if last_day == _yesterday():
                streak["current"] = int(streak.get("current", 0)) + 1
            else:
                streak["current"] = 1
            streak["last_day"] = today
        streak["best"] = max(int(streak.get("best", 0)), int(streak.get("current", 0)))

        for question, user_answer in result.wrong:
            self.add_mistake(question, user_answer)
        if result.from_mistakes and result.correct_ids:
            corrected = set(result.correct_ids)
            self.data["mistakes"] = [
                item for item in self.data["mistakes"] if item.get("qid") not in corrected
            ]
        self.save()

    def _prune_daily(self) -> None:
        cutoff = (date.today() - timedelta(days=89)).isoformat()
        daily = {key: value for key, value in self.data["daily"].items() if key >= cutoff}
        self.data["daily"] = daily

    # -- mistakes --------------------------------------------------------
    def add_mistake(self, question: Question, user_answer: str) -> None:
        record = question.to_dict()
        record["user"] = user_answer
        record["date"] = datetime.now().isoformat(timespec="seconds")
        mistakes = [
            item for item in self.data["mistakes"] if item.get("qid") != question.qid
        ]
        mistakes.append(record)
        self.data["mistakes"] = mistakes[-100:]

    def mistakes(self, level: str | None = None) -> list[dict[str, Any]]:
        records = list(self.data.get("mistakes") or [])
        if level:
            records = [item for item in records if item.get("level") == level]
        return list(reversed(records))

    def mistake_count(self, level: str | None = None) -> int:
        return len(self.mistakes(level))

    def clear_mistakes(self) -> None:
        self.data["mistakes"] = []
        self.save()

    # -- statistics ------------------------------------------------------
    def daily_series(self, days: int = 7) -> list[tuple[str, int]]:
        series: list[tuple[str, int]] = []
        for offset in range(days - 1, -1, -1):
            day = (date.today() - timedelta(days=offset)).isoformat()
            bucket = self.data["daily"].get(day) or {}
            series.append((day, int(bucket.get("answered", 0))))
        return series

    def recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        return list(reversed(self.data.get("sessions") or []))[:limit]

    def reset(self) -> None:
        self.data = _default_data()
        self.save()
