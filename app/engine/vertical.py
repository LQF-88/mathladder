"""Turn two-operand arithmetic prompts into a vertical (column) layout.

Only topics whose prompts are exactly ``a op b = ？`` with a non-negative
integer answer are eligible.  Everything else (fill-in-the-blank, mixed
operations, fractions, decimals, division, word problems) keeps the normal
horizontal answer pad.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import INPUT_NUMBER, Question

VERTICAL_TOPICS = frozenset(
    {
        "2A.add10",
        "A.add20",
        "A.sub20",
        "B.add2",
        "B.add3",
        "B.sub2",
        "B.sub3",
        "C.table",
        "C.x1",
        "C.x1_3",
        "C.x2",
    }
)

_PROMPT = re.compile(r"^(\d+)\s*([+\-×])\s*(\d+)\s*=\s*？$")


@dataclass(frozen=True)
class VerticalProblem:
    """The two operands and the answer, all as digit strings."""

    left: str
    operator: str
    right: str
    answer: str

    @property
    def places(self) -> int:
        """Number of digit columns needed for the widest row."""
        return max(len(self.left), len(self.right), len(self.answer))

    @property
    def answer_places(self) -> int:
        return len(self.answer)


def vertical_problem(question: Question) -> VerticalProblem | None:
    """Return the column layout for *question*, or ``None`` if unsupported."""
    if question.input_type != INPUT_NUMBER:
        return None
    if question.topic not in VERTICAL_TOPICS:
        return None
    match = _PROMPT.match(question.prompt.strip())
    if match is None:
        return None
    left, operator, right = match.groups()
    answer = question.answer.strip()
    if not answer.isdigit():
        return None
    if len(answer) > 1 and answer.startswith("0"):
        return None
    if operator == "-" and int(left) < int(right):
        return None
    return VerticalProblem(left=left, operator=operator, right=right, answer=answer)
