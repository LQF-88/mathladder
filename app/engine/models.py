"""Data models shared by the question engine, storage and UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

INPUT_NUMBER = "number"
INPUT_FRACTION = "fraction"
INPUT_CHOICE = "choice"


@dataclass
class Question:
    level: str
    topic: str
    prompt: str
    answer: str
    input_type: str = INPUT_NUMBER
    choices: list[str] = field(default_factory=list)
    explanation: str = ""
    hint: str = ""
    qid: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "topic": self.topic,
            "prompt": self.prompt,
            "answer": self.answer,
            "input_type": self.input_type,
            "choices": list(self.choices),
            "explanation": self.explanation,
            "hint": self.hint,
            "qid": self.qid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        return cls(
            level=data.get("level", ""),
            topic=data.get("topic", ""),
            prompt=data.get("prompt", ""),
            answer=str(data.get("answer", "")),
            input_type=data.get("input_type", INPUT_NUMBER),
            choices=list(data.get("choices") or []),
            explanation=data.get("explanation", ""),
            hint=data.get("hint", ""),
            qid=data.get("qid", ""),
        )


@dataclass
class SessionResult:
    level: str
    topic: str
    total: int
    correct: int
    seconds: int
    wrong: list[tuple[Question, str]] = field(default_factory=list)
    correct_ids: list[str] = field(default_factory=list)
    from_mistakes: bool = False

    @property
    def accuracy(self) -> int:
        if not self.total:
            return 0
        return round(self.correct * 100 / self.total)

    @property
    def stars(self) -> int:
        if self.accuracy >= 95:
            return 3
        if self.accuracy >= 80:
            return 2
        if self.accuracy >= 60:
            return 1
        return 0
