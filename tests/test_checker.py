"""Answer checking normalises fractions, decimals, percentages and choices."""

from fractions import Fraction

import pytest

from app.engine.checker import is_correct, normalize, parse_value, pretty_answer
from app.engine.models import INPUT_CHOICE, Question


def _question(answer: str, input_type: str = "number") -> Question:
    return Question(
        level="2A",
        topic="2A.add10",
        prompt="1 + 1 = ?",
        answer=answer,
        input_type=input_type,
    )


def test_normalize_handles_fullwidth_and_spaces():
    assert normalize(" １２．５ ") == "12.5"
    assert normalize("1 / 2") == "1/2"
    assert normalize("−3") == "-3"


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("1/2", Fraction(1, 2)),
        ("2/4", Fraction(1, 2)),
        ("0.5", Fraction(1, 2)),
        ("1 1/2", Fraction(3, 2)),
        ("50%", Fraction(1, 2)),
        ("-3/4", Fraction(-3, 4)),
        ("１２", Fraction(12)),
    ],
)
def test_parse_value(text, value):
    assert parse_value(text) == value


@pytest.mark.parametrize("text", ["", "abc", "1/0", "--2", "x + 1"])
def test_parse_value_rejects_non_numbers(text):
    assert parse_value(text) is None


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ("1/2", "2/4"),
        ("0.5", "1/2"),
        ("1 1/2", "3/2"),
        ("50%", "0.5"),
        ("-3", "－３"),
        ("12", "１２"),
    ],
)
def test_numeric_equivalence(expected, actual):
    assert is_correct(_question(expected), actual)


@pytest.mark.parametrize(
    ("expected", "actual"),
    [("1/2", "1/3"), ("0.5", "0.6"), ("-3", "3"), ("12", ""), ("12", "abc")],
)
def test_wrong_or_unparseable_answers(expected, actual):
    assert not is_correct(_question(expected), actual)


def test_choice_requires_exact_option_text():
    question = _question("4x[sup]3[/sup] + C", INPUT_CHOICE)
    assert is_correct(question, "4x[sup]3[/sup] + C")
    assert is_correct(question, " 4X[sup]3[/sup]+C ")
    assert not is_correct(question, "4x[sup]3[/sup]")


def test_pretty_answer_keeps_generated_text():
    question = _question("3/4")
    assert pretty_answer(question) == "3/4"
