"""Answer normalisation and checking.

Answers in the generator are deliberately restricted to numbers, fractions,
decimals or one of the presented choices.  That keeps checking exact and avoids
shipping a computer-algebra system in the Android APK.
"""

from __future__ import annotations

import re
from fractions import Fraction

from .models import INPUT_CHOICE, Question

_FULLWIDTH = str.maketrans(
    {
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
        "．": ".",
        "／": "/",
        "－": "-",
        "＋": "+",
        "＝": "=",
        "，": ",",
        "；": ";",
        "：": ":",
        "（": "(",
        "）": ")",
        "　": " ",
    }
)

_PUNCT = str.maketrans(
    {
        "×": "*",
        "÷": "/",
        "−": "-",
        "–": "-",
        "—": "-",
        "√": "√",
    }
)

_MIXED = re.compile(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$")


def normalize(text: str) -> str:
    text = (text or "").strip().translate(_FULLWIDTH).translate(_PUNCT)
    text = text.replace(" ", "").replace(",", "").lower()
    return text


def parse_value(text: str) -> Fraction | None:
    """Parse a number, fraction, mixed number or percentage into a Fraction."""
    cleaned = (text or "").strip().translate(_FULLWIDTH).translate(_PUNCT)
    if not cleaned:
        return None
    # Mixed numbers need their separating space, so check before stripping it.
    mixed = _MIXED.match(cleaned)
    if mixed:
        whole = int(mixed.group(1))
        num = int(mixed.group(2))
        den = int(mixed.group(3))
        if den == 0:
            return None
        value = Fraction(num, den)
        return whole - value if whole < 0 else whole + value
    text = cleaned.replace(" ", "").replace(",", "").lower()
    if not text:
        return None
    if text.endswith("%"):
        base = parse_value(text[:-1])
        return base / 100 if base is not None else None
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def is_correct(question: Question, user_answer: str) -> bool:
    if not (user_answer or "").strip():
        return False
    if question.input_type == INPUT_CHOICE:
        return normalize(user_answer) == normalize(question.answer)
    expected = parse_value(question.answer)
    actual = parse_value(user_answer)
    if expected is None or actual is None:
        return normalize(user_answer) == normalize(question.answer)
    return expected == actual


def pretty_answer(question: Question) -> str:
    """Answer string shown to the learner after checking."""
    if question.input_type == INPUT_CHOICE:
        return question.answer
    return question.answer
