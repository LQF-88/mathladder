"""Every generator must produce well-formed, answerable questions."""

import random
import re

import pytest

from app.engine.checker import parse_value
from app.engine.curriculum import LEVELS, TOPIC_BY_KEY
from app.engine.generator import generate_question
from app.engine.models import INPUT_CHOICE

MARKUP = re.compile(r"\[/?sup\]|\[/?sub\]")


@pytest.mark.parametrize("topic", sorted(TOPIC_BY_KEY))
def test_topic_generates_consistent_questions(topic):
    key = TOPIC_BY_KEY[topic].key
    level_code = TOPIC_BY_KEY[topic].key.split(".")[0]
    rng = random.Random(f"test-{key}")
    qids = set()
    for _ in range(80):
        question = generate_question(key, rng)
        assert question.level == level_code
        assert question.topic == key
        assert question.prompt.strip()
        assert question.answer.strip()
        assert question.explanation.strip()
        assert question.qid and question.qid not in qids
        qids.add(question.qid)
        assert MARKUP.sub("", question.prompt) == question.prompt or (
            question.prompt.count("[sup]") == question.prompt.count("[/sup]")
            and question.prompt.count("[sub]") == question.prompt.count("[/sub]")
        )
        if question.input_type == INPUT_CHOICE:
            assert len(question.choices) == 4
            assert len(set(question.choices)) == 4
            assert question.answer in question.choices
        else:
            assert parse_value(question.answer) is not None, (
                f"{key} produced a non-numeric typed answer: {question.answer!r}"
            )
            assert not question.choices


def test_every_level_has_generators_for_all_topics():
    for level in LEVELS:
        for topic in level.topics:
            question = generate_question(topic.key, random.Random(7))
            assert question.topic == topic.key
