"""Build a balanced practice session from the generator registry."""

from __future__ import annotations

import random

from .curriculum import level_of
from .generator import generate_question
from .models import Question


def build_session(
    level_code: str,
    count: int = 20,
    topic_key: str | None = None,
    seed: int | None = None,
) -> list[Question]:
    """Return ``count`` questions for a level, avoiding duplicate prompts.

    If ``topic_key`` is given only that topic is used; otherwise topics rotate
    so a mixed session samples the whole level.
    """
    level = level_of(level_code)
    rng = random.Random(seed)
    keys = [topic_key] if topic_key else [topic.key for topic in level.topics]

    questions: list[Question] = []
    seen: set[str] = set()
    cycle: list[str] = []
    attempts = 0
    max_attempts = max(200, count * 60)

    while len(questions) < count and attempts < max_attempts:
        attempts += 1
        if not cycle:
            cycle = keys[:]
            rng.shuffle(cycle)
        key = cycle.pop()
        question = generate_question(key, rng)
        if question.prompt in seen:
            continue
        seen.add(question.prompt)
        questions.append(question)

    # Very narrow topics can run out of unique prompts.  Fill the remainder
    # with repeats rather than returning a short worksheet.
    while len(questions) < count:
        key = rng.choice(keys)
        questions.append(generate_question(key, rng))

    rng.shuffle(questions)
    return questions


def questions_from_mistakes(records: list[dict]) -> list[Question]:
    questions: list[Question] = []
    for record in records:
        data = {
            key: record.get(key)
            for key in (
                "level",
                "topic",
                "prompt",
                "answer",
                "input_type",
                "choices",
                "explanation",
                "hint",
                "qid",
            )
        }
        questions.append(Question.from_dict(data))
    return questions
