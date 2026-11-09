"""Session building and mistake replay."""

from app.engine.curriculum import LEVEL_BY_CODE
from app.engine.models import Question
from app.engine.session import build_session, questions_from_mistakes


def test_session_has_requested_size_and_level_topics():
    for code in ("5A", "2A", "D", "H", "L"):
        questions = build_session(code, count=20, seed=11)
        assert len(questions) == 20
        allowed = {topic.key for topic in LEVEL_BY_CODE[code].topics}
        assert {question.topic for question in questions} <= allowed


def test_topic_filter_limits_questions():
    questions = build_session("C", count=12, topic_key="C.x1", seed=5)
    assert len(questions) == 12
    assert all(question.topic == "C.x1" for question in questions)


def test_same_seed_repeats_prompts():
    first = build_session("G", count=10, seed=123)
    second = build_session("G", count=10, seed=123)
    assert [question.prompt for question in first] == [
        question.prompt for question in second
    ]
    assert [question.answer for question in first] == [
        question.answer for question in second
    ]


def test_questions_from_mistakes_round_trip():
    question = Question(
        level="A",
        topic="A.add20",
        prompt="8 + 9 = ?",
        answer="17",
        choices=[],
        explanation="8 + 9 = 17",
        qid="abc123",
    )
    record = question.to_dict()
    record["user"] = "16"
    rebuilt = questions_from_mistakes([record])
    assert len(rebuilt) == 1
    copy = rebuilt[0]
    assert copy.qid == question.qid
    assert copy.prompt == question.prompt
    assert copy.answer == question.answer
    assert copy.explanation == question.explanation
    assert copy.level == question.level
    assert copy.topic == question.topic
