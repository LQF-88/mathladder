"""Tests for the vertical (column) answer layout selection."""

from __future__ import annotations

import random

from app.engine.generator import GENERATORS
from app.engine.models import INPUT_CHOICE, INPUT_FRACTION, INPUT_NUMBER, Question
from app.engine.vertical import VERTICAL_TOPICS, VerticalProblem, vertical_problem


def make_question(
    prompt: str,
    answer: str,
    topic: str = "B.add2",
    input_type: str = INPUT_NUMBER,
    choices: list[str] | None = None,
) -> Question:
    return Question(
        level="B",
        topic=topic,
        prompt=prompt,
        answer=answer,
        input_type=input_type,
        choices=choices or [],
        explanation="",
        hint="",
        qid="test",
    )


def test_two_digit_addition_builds_two_columns() -> None:
    problem = vertical_problem(make_question("27 + 45 = ？", "72"))
    assert problem == VerticalProblem(
        left="27", operator="+", right="45", answer="72"
    )
    assert problem.places == 2
    assert problem.answer_places == 2


def test_three_digit_operand_aligns_to_widest_row() -> None:
    problem = vertical_problem(
        make_question("456 + 78 = ？", "534", topic="B.add3")
    )
    assert problem is not None
    assert problem.places == 3
    assert problem.answer_places == 3


def test_multiplication_can_have_more_answer_digits() -> None:
    problem = vertical_problem(
        make_question("49 × 29 = ？", "1421", topic="C.x2")
    )
    assert problem is not None
    assert problem.places == 4
    assert problem.answer_places == 4


def test_leading_zero_answer_is_rejected() -> None:
    assert vertical_problem(make_question("5 + 1 = ？", "06")) is None


def test_fill_in_the_blank_is_not_vertical() -> None:
    assert vertical_problem(make_question("27 + ？ = 72", "45")) is None


def test_mixed_operations_are_not_vertical() -> None:
    assert (
        vertical_problem(
            make_question("5 + 7 - 3 = ？", "9", topic="A.mixed")
        )
        is None
    )


def test_choice_and_fraction_questions_are_not_vertical() -> None:
    assert (
        vertical_problem(
            make_question(
                "27 + 45 = ？",
                "72",
                input_type=INPUT_CHOICE,
                choices=["72", "73"],
            )
        )
        is None
    )
    assert (
        vertical_problem(
            make_question("1/2 + 1/2 = ？", "1", input_type=INPUT_FRACTION)
        )
        is None
    )


def test_subtraction_with_negative_result_is_rejected() -> None:
    assert (
        vertical_problem(make_question("3 - 8 = ？", "-5", topic="B.sub2"))
        is None
    )


def test_every_supported_generator_parses_and_matches_arithmetic() -> None:
    rng = random.Random(20261112)
    for topic in sorted(VERTICAL_TOPICS):
        generator = GENERATORS[topic]
        for _ in range(25):
            question = generator(rng)
            problem = vertical_problem(question)
            assert problem is not None, question.prompt
            left, right = int(problem.left), int(problem.right)
            if problem.operator == "+":
                expected = left + right
            elif problem.operator == "-":
                expected = left - right
            else:
                expected = left * right
            assert problem.answer == str(expected)
            assert problem.places >= problem.answer_places
