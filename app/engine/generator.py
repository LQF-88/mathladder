"""Question generators for every curriculum topic.

All content is produced algorithmically; the scanned reference pages are never
copied into the app.  Generators return :class:`Question` objects whose answers
are numbers, fractions, decimals or one of four choices.
"""

from __future__ import annotations

import math
import random
import uuid
from collections.abc import Callable
from decimal import Decimal
from fractions import Fraction

from .models import INPUT_CHOICE, INPUT_FRACTION, INPUT_NUMBER, Question

SHAPES = ["●", "○", "▲", "△", "■", "□", "★", "☆", "◆", "◇"]
CN_DIGITS = "零一二三四五六七八九"

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def sup(value: int | str) -> str:
    """Kivy markup superscript (the bundled CJK font lacks most superscripts)."""
    return f"[sup]{value}[/sup]"


def sub(value: int | str) -> str:
    """Kivy markup subscript."""
    return f"[sub]{value}[/sub]"


def fstr(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def cn_num(n: int) -> str:
    if n < 10:
        return CN_DIGITS[n]
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    if n < 100:
        tens, ones = divmod(n, 10)
        return CN_DIGITS[tens] + "十" + (CN_DIGITS[ones] if ones else "")
    return str(n)


def _q(
    level: str,
    topic: str,
    prompt: str,
    answer: str,
    *,
    input_type: str = INPUT_NUMBER,
    choices: list[str] | None = None,
    explanation: str = "",
    hint: str = "",
) -> Question:
    return Question(
        level=level,
        topic=topic,
        prompt=prompt,
        answer=str(answer),
        input_type=input_type,
        choices=list(choices or []),
        explanation=explanation,
        hint=hint,
        qid=uuid.uuid4().hex,
    )


def _choice(
    level: str,
    topic: str,
    prompt: str,
    correct: str,
    distractors: list[str],
    rng: random.Random,
    explanation: str = "",
) -> Question:
    options: list[str] = []
    for option in [correct, *distractors]:
        option = str(option)
        if option not in options:
            options.append(option)
    fallback = ["0", "1", "2", "3", "无法确定", "以上都不对"]
    for option in fallback:
        if len(options) >= 4:
            break
        if option not in options:
            options.append(option)
    options = options[:4]
    rng.shuffle(options)
    return _q(
        level,
        topic,
        prompt,
        correct,
        input_type=INPUT_CHOICE,
        choices=options,
        explanation=explanation,
    )


def _plus(a: int, b: int) -> str:
    return f"{a} + {b}" if b >= 0 else f"{a} - {abs(b)}"


def _paren(n: int) -> str:
    return f"({n})" if n < 0 else str(n)


def fmt_linear(a: int, b: int, var: str = "x") -> str:
    parts: list[str] = []
    if a:
        if a == 1:
            parts.append(var)
        elif a == -1:
            parts.append(f"-{var}")
        else:
            parts.append(f"{a}{var}")
    if b or not parts:
        if not parts:
            parts.append(str(b))
        elif b:
            parts.append(f"+ {b}" if b > 0 else f"- {abs(b)}")
    return " ".join(parts)


def fmt_quad(a: int, b: int, c: int, var: str = "x") -> str:
    parts: list[str] = []
    if a:
        if a == 1:
            parts.append(f"{var}²")
        elif a == -1:
            parts.append(f"-{var}²")
        else:
            parts.append(f"{a}{var}²")
    if b:
        body = var if abs(b) == 1 else f"{abs(b)}{var}"
        if not parts:
            parts.append(("-" if b < 0 else "") + body)
        else:
            parts.append(("+ " if b > 0 else "- ") + body)
    if c or not parts:
        if not parts:
            parts.append(str(c))
        else:
            parts.append(("+ " if c > 0 else "- ") + str(abs(c)))
    return " ".join(parts)


def fmt_factor(var: str, p: int) -> str:
    if p == 0:
        return f"({var})"
    return f"({var} + {p})" if p > 0 else f"({var} - {abs(p)})"


def dec_str(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text


def _sign_choice(n: int) -> str:
    return "正数" if n > 0 else "负数" if n < 0 else "零"


# ---------------------------------------------------------------------------
# 5A - lines, shapes and number awareness
# ---------------------------------------------------------------------------


def gen_5a_match(rng: random.Random) -> Question:
    target = rng.choice(SHAPES)
    others = rng.sample([s for s in SHAPES if s != target], 3)
    return _choice(
        "5A",
        "5A.match",
        f"找一找：哪一个和它一样？\n\n{target}",
        target,
        others,
        rng,
        explanation=f"它们都是同一个图形：{target}。",
    )


def gen_5a_pattern(rng: random.Random) -> Question:
    a, b = rng.sample(SHAPES, 2)
    pattern = [a, b]
    length = rng.choice([5, 6])
    shown = [pattern[i % 2] for i in range(length)]
    answer = pattern[length % 2]
    distractors = rng.sample([s for s in SHAPES if s != answer], 3)
    return _choice(
        "5A",
        "5A.pattern",
        "找规律，接下来应该是什么？\n\n" + " ".join(shown) + "  ？",
        answer,
        distractors,
        rng,
        explanation=f"图形按照 {a} {b} 的顺序重复出现。",
    )


def gen_5a_count(rng: random.Random) -> Question:
    n = rng.randint(1, 5)
    shape = rng.choice(SHAPES)
    return _q(
        "5A",
        "5A.count",
        f"数一数，一共有几个？\n\n{'  '.join([shape] * n)}",
        str(n),
        explanation=f"点着一个一个数，一共是 {n} 个。",
    )


def gen_5a_order(rng: random.Random) -> Question:
    start = rng.randint(1, 5)
    seq = list(range(start, start + 5))
    missing = rng.randint(1, 3)
    shown = ["＿" if i == missing else str(value) for i, value in enumerate(seq)]
    return _q(
        "5A",
        "5A.order",
        "按顺序填一填：\n\n" + "   ".join(shown),
        str(seq[missing]),
        explanation="每个数都比前一个大 1。",
    )


def gen_5a_compare(rng: random.Random) -> Question:
    a, b = rng.sample(range(1, 7), 2)
    shape = rng.choice(SHAPES)
    prompt = (
        "哪一组图形更多？\n\n"
        f"A 组：{' '.join([shape] * a)}\n\n"
        f"B 组：{' '.join([shape] * b)}"
    )
    answer = "A 组" if a > b else "B 组"
    return _q("5A", "5A.compare", prompt, answer, input_type=INPUT_CHOICE,
              choices=["A 组", "B 组", "一样多", "无法比较"],
              explanation=f"A 组 {a} 个，B 组 {b} 个。")

# ---------------------------------------------------------------------------
# 4A - numbers up to 50
# ---------------------------------------------------------------------------


def gen_4a_count(rng: random.Random) -> Question:
    n = rng.randint(1, 10)
    shape = rng.choice(SHAPES)
    return _q(
        "4A",
        "4A.count",
        f"数一数，一共有几个？\n\n{'  '.join([shape] * n)}",
        str(n),
        explanation=f"一个一个数，共 {n} 个。",
    )


def gen_4a_digit(rng: random.Random) -> Question:
    n = rng.randint(1, 50)
    others = rng.sample([x for x in range(1, 51) if x != n], 3)
    return _choice(
        "4A",
        "4A.digit",
        f"「{cn_num(n)}」是哪一个数字？",
        str(n),
        [str(x) for x in others],
        rng,
        explanation=f"{cn_num(n)} 写作 {n}。",
    )


def gen_4a_sequence(rng: random.Random) -> Question:
    n = rng.randint(1, 49)
    return _q(
        "4A",
        "4A.sequence",
        f"接着往下数：\n\n{n} → ？",
        str(n + 1),
        explanation=f"{n} 的后面一个数是 {n + 1}。",
    )


def gen_4a_compare(rng: random.Random) -> Question:
    a, b = rng.sample(range(1, 51), 2)
    answer = ">" if a > b else "<"
    return _choice(
        "4A",
        "4A.compare",
        f"比一比：{a} ○ {b}\n\n○ 里应该填什么？",
        answer,
        [">", "<", "="],
        rng,
        explanation=f"{a} {'大于' if a > b else '小于'} {b}。",
    )


def gen_4a_puzzle(rng: random.Random) -> Question:
    start = rng.randint(1, 44)
    seq = list(range(start, start + 5))
    missing = rng.randint(1, 3)
    shown = ["＿" if i == missing else str(value) for i, value in enumerate(seq)]
    return _q(
        "4A",
        "4A.puzzle",
        "数字拼图，填出缺少的数：\n\n" + "   ".join(shown),
        str(seq[missing]),
        explanation="数列每次增加 1。",
    )

# ---------------------------------------------------------------------------
# 3A - counting to 100, +1/+2/+3
# ---------------------------------------------------------------------------


def gen_3a_count100(rng: random.Random) -> Question:
    if rng.random() < 0.5:
        n = rng.randint(1, 98)
        return _q(
            "3A",
            "3A.count100",
            f"接着数：\n\n{n} → ？",
            str(n + 1),
            explanation=f"再数一个就是 {n + 1}。",
        )
    n = rng.choice(range(10, 91, 10))
    return _q(
        "3A",
        "3A.count100",
        "十个十个地数：\n\n" + "  ".join(str(x) for x in range(10, n + 1, 10)) + "  ？",
        str(n + 10),
        explanation="每次增加 10。",
    )


def gen_3a_plus1(rng: random.Random) -> Question:
    n = rng.randint(1, 98)
    return _q("3A", "3A.plus1", f"{n} + 1 = ？", str(n + 1),
              explanation=f"{n} 再添 1 就是 {n + 1}。")


def gen_3a_plus23(rng: random.Random) -> Question:
    n = rng.randint(1, 95)
    k = rng.choice([2, 3])
    return _q("3A", "3A.plus23", f"{n} + {k} = ？", str(n + k),
              explanation=f"从 {n} 往后数 {k} 步，得到 {n + k}。")


def gen_3a_sequence(rng: random.Random) -> Question:
    start = rng.randint(1, 80)
    step = rng.choice([1, 2, 3])
    seq = [start + i * step for i in range(5)]
    missing = rng.randint(1, 3)
    shown = ["＿" if i == missing else str(value) for i, value in enumerate(seq)]
    return _q(
        "3A",
        "3A.sequence",
        "找规律，填一填：\n\n" + "   ".join(shown),
        str(seq[missing]),
        explanation=f"数列每次都增加 {step}。",
    )


def gen_3a_tens(rng: random.Random) -> Question:
    n = rng.randint(11, 99)
    tens, ones = divmod(n, 10)
    if rng.random() < 0.5:
        return _q(
            "3A",
            "3A.tens",
            f"{n} 里面有几个十？",
            str(tens),
            explanation=f"{n} = {tens} 个十和 {ones} 个一。",
        )
    return _q(
        "3A",
        "3A.tens",
        f"{tens} 个十和 {ones} 个一合起来是多少？",
        str(n),
        explanation=f"{tens}0 + {ones} = {n}。",
    )

# ---------------------------------------------------------------------------
# 2A - addition within 10
# ---------------------------------------------------------------------------


def gen_2a_add10(rng: random.Random) -> Question:
    a = rng.randint(1, 9)
    b = rng.randint(1, 10 - a)
    return _q("2A", "2A.add10", f"{a} + {b} = ？", str(a + b),
              explanation=f"{a} 和 {b} 合起来是 {a + b}。")


def gen_2a_addfill(rng: random.Random) -> Question:
    a = rng.randint(1, 8)
    b = rng.randint(1, 9 - a)
    c = a + b
    if rng.random() < 0.5:
        return _q("2A", "2A.addfill", f"{a} + ？ = {c}", str(b),
                  explanation=f"{c} - {a} = {b}。")
    return _q("2A", "2A.addfill", f"？ + {b} = {c}", str(a),
              explanation=f"{c} - {b} = {a}。")


def gen_2a_decompose(rng: random.Random) -> Question:
    total = rng.randint(2, 10)
    part = rng.randint(1, total - 1)
    return _q(
        "2A",
        "2A.decompose",
        f"{total} 可以分成 {part} 和几？",
        str(total - part),
        explanation=f"{part} + {total - part} = {total}。",
    )


def gen_2a_add3(rng: random.Random) -> Question:
    a = rng.randint(1, 4)
    b = rng.randint(1, 4)
    c = rng.randint(1, max(1, 10 - a - b))
    return _q("2A", "2A.add3", f"{a} + {b} + {c} = ？", str(a + b + c),
              explanation=f"先算 {a} + {b} = {a + b}，再加 {c}，得到 {a + b + c}。")

# ---------------------------------------------------------------------------
# A - addition and subtraction within 20
# ---------------------------------------------------------------------------


def gen_a_add20(rng: random.Random) -> Question:
    total = rng.randint(11, 20)
    a = rng.randint(2, total - 2)
    b = total - a
    if rng.random() < 0.5:
        a, b = b, a
    return _q("A", "A.add20", f"{a} + {b} = ？", str(total),
              explanation=f"{a} + {b} = {total}。")


def gen_a_sub20(rng: random.Random) -> Question:
    a = rng.randint(11, 20)
    b = rng.randint(2, 9)
    return _q("A", "A.sub20", f"{a} - {b} = ？", str(a - b),
              explanation=f"从 {a} 里去掉 {b}，还剩 {a - b}。")


def gen_a_mixed(rng: random.Random) -> Question:
    total = rng.randint(11, 20)
    a = rng.randint(2, total - 2)
    b = total - a
    c = rng.randint(1, total - 1)
    return _q("A", "A.mixed", f"{a} + {b} - {c} = ？", str(total - c),
              explanation=f"先算 {a} + {b} = {total}，再减 {c}，得到 {total - c}。")


def gen_a_fill(rng: random.Random) -> Question:
    total = rng.randint(11, 20)
    a = rng.randint(2, total - 2)
    b = total - a
    if rng.random() < 0.5:
        return _q("A", "A.fill", f"{a} + ？ = {total}", str(b),
                  explanation=f"{total} - {a} = {b}。")
    return _q("A", "A.fill", f"？ - {b} = {a}", str(total),
              explanation=f"{a} + {b} = {total}。")


_A_WORDS = [
    ("树上有 {a} 只小鸟，又飞来 {b} 只，一共有多少只？", "add"),
    ("盘子里有 {a} 块饼干，吃掉 {b} 块，还剩多少块？", "sub"),
    ("书架上有 {a} 本书，又放上 {b} 本，现在一共有多少本？", "add"),
    ("小明有 {a} 张贴纸，送给同学 {b} 张，还剩多少张？", "sub"),
    ("停车场有 {a} 辆车，开走 {b} 辆，还剩多少辆？", "sub"),
    ("篮子里有 {a} 个苹果，又放进 {b} 个，一共有多少个？", "add"),
]


def gen_a_word(rng: random.Random) -> Question:
    template, kind = rng.choice(_A_WORDS)
    if kind == "add":
        a = rng.randint(5, 12)
        b = rng.randint(3, 8)
        prompt = template.format(a=a, b=b)
        answer = a + b
        explanation = f"{a} + {b} = {answer}。"
    else:
        a = rng.randint(10, 20)
        b = rng.randint(2, a - 1)
        prompt = template.format(a=a, b=b)
        answer = a - b
        explanation = f"{a} - {b} = {answer}。"
    return _q("A", "A.word", prompt, str(answer), explanation=explanation)

# ---------------------------------------------------------------------------
# B - two and three digit addition / subtraction
# ---------------------------------------------------------------------------


def gen_b_add2(rng: random.Random) -> Question:
    a = rng.randint(10, 89)
    b = rng.randint(2, 100 - a)
    return _q("B", "B.add2", f"{a} + {b} = ？", str(a + b),
              explanation=f"{a} + {b} = {a + b}。")


def gen_b_add3(rng: random.Random) -> Question:
    a = rng.randint(100, 899)
    b = rng.randint(10, min(99, 999 - a))
    return _q("B", "B.add3", f"{a} + {b} = ？", str(a + b),
              explanation=f"{a} + {b} = {a + b}。")


def gen_b_sub2(rng: random.Random) -> Question:
    a = rng.randint(21, 99)
    b = rng.randint(2, a - 1)
    return _q("B", "B.sub2", f"{a} - {b} = ？", str(a - b),
              explanation=f"{a} - {b} = {a - b}。")


def gen_b_sub3(rng: random.Random) -> Question:
    a = rng.randint(100, 999)
    b = rng.randint(10, min(99, a - 1))
    return _q("B", "B.sub3", f"{a} - {b} = ？", str(a - b),
              explanation=f"{a} - {b} = {a - b}。")


def gen_b_fill(rng: random.Random) -> Question:
    a = rng.randint(10, 80)
    b = rng.randint(2, 100 - a)
    total = a + b
    if rng.random() < 0.5:
        return _q("B", "B.fill", f"{a} + ？ = {total}", str(b),
                  explanation=f"{total} - {a} = {b}。")
    return _q("B", "B.fill", f"？ + {b} = {total}", str(a),
              explanation=f"{total} - {b} = {a}。")

# ---------------------------------------------------------------------------
# C - multiplication
# ---------------------------------------------------------------------------


def gen_c_table(rng: random.Random) -> Question:
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    return _q("C", "C.table", f"{a} × {b} = ？", str(a * b),
              explanation=f"口诀：{a} 乘 {b} 得 {a * b}。")


def gen_c_x1(rng: random.Random) -> Question:
    a = rng.randint(11, 99)
    b = rng.randint(2, 9)
    return _q("C", "C.x1", f"{a} × {b} = ？", str(a * b),
              explanation=f"{a} × {b} = {a * b}。")


def gen_c_x1_3(rng: random.Random) -> Question:
    a = rng.randint(101, 999)
    b = rng.randint(2, 9)
    return _q("C", "C.x1_3", f"{a} × {b} = ？", str(a * b),
              explanation=f"{a} × {b} = {a * b}。")


def gen_c_x2(rng: random.Random) -> Question:
    a = rng.randint(11, 49)
    b = rng.randint(11, 29)
    return _q("C", "C.x2", f"{a} × {b} = ？", str(a * b),
              explanation=f"{a} × {b} = {a * b}。")


def gen_c_fill(rng: random.Random) -> Question:
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    product = a * b
    if rng.random() < 0.5:
        return _q("C", "C.fill", f"{a} × ？ = {product}", str(b),
                  explanation=f"{product} ÷ {a} = {b}。")
    return _q("C", "C.fill", f"？ × {b} = {product}", str(a),
              explanation=f"{product} ÷ {b} = {a}。")

# ---------------------------------------------------------------------------
# D - division
# ---------------------------------------------------------------------------


def gen_d_basic(rng: random.Random) -> Question:
    b = rng.randint(2, 9)
    q = rng.randint(2, 9)
    return _q("D", "D.basic", f"{b * q} ÷ {b} = ？", str(q),
              explanation=f"{b} × {q} = {b * q}，所以商是 {q}。")


def gen_d_remainder(rng: random.Random) -> Question:
    b = rng.randint(2, 9)
    q = rng.randint(2, 9)
    r = rng.randint(1, b - 1)
    a = b * q + r
    if rng.random() < 0.5:
        return _q("D", "D.remainder", f"{a} ÷ {b} 的余数是多少？", str(r),
                  explanation=f"{a} ÷ {b} = {q} 余 {r}。")
    return _q("D", "D.remainder", f"{a} ÷ {b} 的商是多少？", str(q),
              explanation=f"{a} ÷ {b} = {q} 余 {r}。")


def gen_d_div2(rng: random.Random) -> Question:
    b = rng.randint(2, 9)
    q = rng.randint(3, 99 // b)
    return _q("D", "D.div2", f"{b * q} ÷ {b} = ？", str(q),
              explanation=f"{b} × {q} = {b * q}。")


def gen_d_div3(rng: random.Random) -> Question:
    b = rng.randint(2, 9)
    q = rng.randint(11, 999 // b)
    return _q("D", "D.div3", f"{b * q} ÷ {b} = ？", str(q),
              explanation=f"{b} × {q} = {b * q}。")


def gen_d_divisor2(rng: random.Random) -> Question:
    b = rng.randint(11, 19)
    q = rng.randint(2, 9)
    return _q("D", "D.divisor2", f"{b * q} ÷ {b} = ？", str(q),
              explanation=f"{b} × {q} = {b * q}。")


def gen_d_fill(rng: random.Random) -> Question:
    b = rng.randint(2, 9)
    q = rng.randint(2, 9)
    if rng.random() < 0.5:
        return _q("D", "D.fill", f"{b * q} ÷ ？ = {q}", str(b),
                  explanation=f"{b * q} ÷ {q} = {b}。")
    return _q("D", "D.fill", f"？ ÷ {b} = {q}", str(b * q),
              explanation=f"{b} × {q} = {b * q}。")

# ---------------------------------------------------------------------------
# E - fractions with the same denominator
# ---------------------------------------------------------------------------


def gen_e_add(rng: random.Random) -> Question:
    d = rng.randint(3, 12)
    a = rng.randint(1, d - 1)
    b = rng.randint(1, d - 1)
    total = Fraction(a + b, d)
    return _q("E", "E.add", f"{a}/{d} + {b}/{d} = ？", fstr(total),
              input_type=INPUT_FRACTION,
              explanation=f"分母不变，分子相加：({a} + {b})/{d} = {fstr(total)}。")


def gen_e_sub(rng: random.Random) -> Question:
    d = rng.randint(3, 12)
    a = rng.randint(2, d - 1)
    b = rng.randint(1, a - 1)
    result = Fraction(a - b, d)
    return _q("E", "E.sub", f"{a}/{d} - {b}/{d} = ？", fstr(result),
              input_type=INPUT_FRACTION,
              explanation=f"分母不变，分子相减：({a} - {b})/{d} = {fstr(result)}。")


def gen_e_mixed(rng: random.Random) -> Question:
    d = rng.randint(4, 12)
    a = rng.randint(1, d - 1)
    b = rng.randint(1, d - 1)
    c = rng.randint(1, max(1, a + b - 1))
    result = Fraction(a + b - c, d)
    return _q("E", "E.mixed", f"{a}/{d} + {b}/{d} - {c}/{d} = ？", fstr(result),
              input_type=INPUT_FRACTION,
              explanation=f"分子先加后减：({a} + {b} - {c})/{d} = {fstr(result)}。")


def gen_e_simplify(rng: random.Random) -> Question:
    d = rng.randint(4, 12)
    n = rng.randint(2, d - 1)
    g = math.gcd(n, d)
    while g == 1:
        d = rng.randint(4, 12)
        n = rng.randint(2, d - 1)
        g = math.gcd(n, d)
    result = Fraction(n, d)
    return _q("E", "E.simplify", f"把 {n}/{d} 化成最简分数。", fstr(result),
              input_type=INPUT_FRACTION,
              explanation=f"分子分母同时除以 {g}，得到 {fstr(result)}。")


def gen_e_fill(rng: random.Random) -> Question:
    d = rng.randint(4, 12)
    a = rng.randint(1, d - 2)
    b = rng.randint(a + 1, d - 1)
    missing = Fraction(b - a, d)
    return _q("E", "E.fill", f"{a}/{d} + ？ = {b}/{d}", fstr(missing),
              input_type=INPUT_FRACTION,
              explanation=f"？ = {b}/{d} - {a}/{d} = {fstr(missing)}。")

# ---------------------------------------------------------------------------
# F - four operations, fractions, decimals, x
# ---------------------------------------------------------------------------


def gen_f_order(rng: random.Random) -> Question:
    kind = rng.randint(0, 5)
    if kind == 0:
        a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 6)
        return _q("F", "F.order", f"({a} + {b}) × {c} = ？", str((a + b) * c),
                  explanation=f"先算括号：{a} + {b} = {a + b}，再乘 {c}。")
    if kind == 1:
        a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
        return _q("F", "F.order", f"{a} + {b} × {c} = ？", str(a + b * c),
                  explanation=f"先乘后加：{b} × {c} = {b * c}，再加 {a}。")
    if kind == 2:
        a, b, c = rng.randint(11, 40), rng.randint(2, 9), rng.randint(2, 9)
        return _q("F", "F.order", f"{a} × {b} - {c} = ？", str(a * b - c),
                  explanation=f"先算 {a} × {b} = {a * b}，再减 {c}。")
    if kind == 3:
        a = rng.randint(5, 9)
        b = rng.randint(2, a - 1)
        c = rng.randint(2, 9)
        return _q("F", "F.order", f"({a} - {b}) × {c} = ？", str((a - b) * c),
                  explanation=f"先算括号：{a} - {b} = {a - b}，再乘 {c}。")
    if kind == 4:
        b = rng.randint(2, 9)
        q = rng.randint(2, 9)
        c = rng.randint(1, 20)
        return _q("F", "F.order", f"{b * q} ÷ {b} + {c} = ？", str(q + c),
                  explanation=f"先算除法：{b * q} ÷ {b} = {q}，再加 {c}。")
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    q = rng.randint(2, 5)
    return _q("F", "F.order", f"{a} + {b * q} ÷ {b} = ？", str(a + q),
              explanation=f"先算除法：{b * q} ÷ {b} = {q}，再加 {a}。")


def gen_f_frac(rng: random.Random) -> Question:
    kind = rng.choice(["mul", "div", "add", "sub"])
    b = rng.randint(2, 9)
    d = rng.randint(2, 9)
    a = rng.randint(1, b - 1) if b > 1 else 1
    c = rng.randint(1, d - 1) if d > 1 else 1
    f1, f2 = Fraction(a, b), Fraction(c, d)
    if kind == "mul":
        result = f1 * f2
        prompt = f"{a}/{b} × {c}/{d} = ？"
    elif kind == "div":
        result = f1 / f2
        prompt = f"{a}/{b} ÷ {c}/{d} = ？"
    elif kind == "add":
        result = f1 + f2
        prompt = f"{a}/{b} + {c}/{d} = ？"
    else:
        result = f1 - f2
        prompt = f"{a}/{b} - {c}/{d} = ？"
    return _q("F", "F.frac", prompt, fstr(result), input_type=INPUT_FRACTION,
              explanation=f"结果是 {fstr(result)}。")


def gen_f_decimal(rng: random.Random) -> Question:
    a = Decimal(rng.randint(10, 200)) / 100
    b = Decimal(rng.randint(10, 200)) / 100
    if rng.random() < 0.5:
        result = a + b
        prompt = f"{dec_str(a)} + {dec_str(b)} = ？"
    else:
        if a < b:
            a, b = b, a
        result = a - b
        prompt = f"{dec_str(a)} - {dec_str(b)} = ？"
    return _q("F", "F.decimal", prompt, dec_str(result),
              explanation="小数点对齐后计算。")


def gen_f_solve_x(rng: random.Random) -> Question:
    x = rng.randint(1, 12)
    a = rng.randint(2, 9)
    b = rng.randint(1, 20)
    if rng.random() < 0.5:
        c = a * x + b
        return _q("F", "F.solve_x", f"{a}x + {b} = {c}，x = ？", str(x),
                  explanation=f"{a}x = {c - b}，x = {x}。")
    c = a * x - b
    return _q("F", "F.solve_x", f"{a}x - {b} = {c}，x = ？", str(x),
              explanation=f"{a}x = {c + b}，x = {x}。")


_F_WORDS = [
    "一支笔 {a} 元，一本本子 {b} 元，买 2 支笔和 3 本本子一共要多少元？",
    "一辆汽车每小时行 {a} 千米，{b} 小时行多少千米？",
    "一箱牛奶有 {a} 盒，平均分给 {b} 个小组，每个小组分到多少盒？",
    "一根绳子长 {a} 米，用去 {b} 米，还剩多少米？",
]


def gen_f_word(rng: random.Random) -> Question:
    template = rng.choice(_F_WORDS)
    if template.startswith("一支笔"):
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        answer = 2 * a + 3 * b
        explanation = f"2 × {a} + 3 × {b} = {answer}（元）。"
    elif template.startswith("一辆汽车"):
        a = rng.randint(30, 90)
        b = rng.randint(2, 6)
        answer = a * b
        explanation = f"{a} × {b} = {answer}（千米）。"
    elif template.startswith("一箱牛奶"):
        b = rng.randint(2, 9)
        a = b * rng.randint(2, 9)
        answer = a // b
        explanation = f"{a} ÷ {b} = {answer}（盒）。"
    else:
        a = rng.randint(10, 50)
        b = rng.randint(2, a - 1)
        answer = a - b
        explanation = f"{a} - {b} = {answer}（米）。"
    return _q("F", "F.word", template.format(a=a, b=b), str(answer),
              explanation=explanation)


def gen_f_convert(rng: random.Random) -> Question:
    if rng.random() < 0.5:
        d = rng.choice([4, 5, 8, 10, 20])
        n = rng.randint(1, d - 1)
        value = Fraction(n, d)
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        correct = dec_str(decimal)
        distractors = [
            dec_str(decimal + Decimal("0.1")),
            dec_str(decimal - Decimal("0.1")),
            f"{d}.{n}",
        ]
        prompt = f"{n}/{d} 写成小数是多少？"
        explanation = f"{n}/{d} = {correct}。"
    else:
        d = rng.choice([4, 5, 8, 10, 20])
        n = rng.randint(1, d - 1)
        while math.gcd(n, d) != 1:
            n = rng.randint(1, d - 1)
        value = Fraction(n, d)
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        text = dec_str(decimal)
        correct = f"{n}/{d}"
        distractors = [f"{d}/{n}", f"{n}/{d + 1}", f"{n + 1}/{d}"]
        prompt = f"小数 {text} 写成分数是多少？"
        explanation = f"{text} = {correct}。"
    return _choice("F", "F.convert", prompt, correct, distractors, rng,
                   explanation=explanation)

# ---------------------------------------------------------------------------
# G - integers, expressions, linear equations
# ---------------------------------------------------------------------------


def gen_g_int_add(rng: random.Random) -> Question:
    a = rng.randint(-20, 20)
    b = rng.randint(-20, 20)
    if a == 0 and b == 0:
        a = 5
    if rng.random() < 0.5:
        prompt = f"{a} + {_paren(b)}" if b < 0 else f"{a} + {b}"
        answer = a + b
        explanation = f"{a} + {b} = {answer}。"
    else:
        prompt = f"{a} - {_paren(b)}" if b < 0 else f"{a} - {b}"
        answer = a - b
        explanation = f"{a} - {b} = {answer}。"
    return _q("G", "G.int_add", prompt + " = ？", str(answer), explanation=explanation)


def gen_g_int_muldiv(rng: random.Random) -> Question:
    a = rng.randint(-12, 12)
    b = rng.randint(-12, 12)
    if a == 0 or b == 0:
        a = 4
        b = -3
    if rng.random() < 0.5:
        return _q("G", "G.int_muldiv", f"{_paren(a)} × {_paren(b)} = ？", str(a * b),
                  explanation="同号得正，异号得负。")
    b = abs(b)
    return _q("G", "G.int_muldiv", f"{_paren(a * b)} ÷ {b} = ？", str(a),
              explanation=f"商是 {a}，注意符号。")


def gen_g_int_mixed(rng: random.Random) -> Question:
    a = rng.randint(-9, 9)
    b = rng.randint(2, 8)
    c = rng.randint(2, 6)
    d = rng.randint(-9, 9)
    if rng.random() < 0.5:
        result = a + b * c
        prompt = f"{a} + {b} × {c}"
        explanation = f"先算 {b} × {c} = {b * c}，再加 {a}，得到 {result}。"
    else:
        result = (a + d) * c
        prompt = f"({a} + {d}) × {c}"
        explanation = f"先算括号：{a} + {d} = {a + d}，再乘 {c}。"
    return _q("G", "G.int_mixed", prompt + " = ？", str(result), explanation=explanation)


def gen_g_eval(rng: random.Random) -> Question:
    a = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = rng.randint(-9, 9)
    x = rng.randint(-5, 5)
    answer = a * x + b
    text = fmt_linear(a, b)
    return _q("G", "G.eval", f"当 x = {x} 时，{text} 的值是多少？", str(answer),
              explanation=f"把 x = {x} 代入：{a} × {x} + {b} = {answer}。")


def gen_g_simplify(rng: random.Random) -> Question:
    a = rng.randint(1, 6)
    b = rng.randint(-6, 6)
    c = rng.randint(1, 6)
    d = rng.randint(-6, 6)
    if a == c and b == d:
        c += 2
    correct = fmt_linear(a + c, b + d)
    distractors = [
        fmt_linear(a + c, -(b + d)),
        fmt_linear(a + c + 1, b + d),
        fmt_linear(abs(a - c) or 1, b + d),
    ]
    return _choice(
        "G",
        "G.simplify",
        f"化简：({fmt_linear(a, b)}) + ({fmt_linear(c, d)})",
        correct,
        distractors,
        rng,
        explanation=f"合并同类项，得到 {correct}。",
    )


def gen_g_equation(rng: random.Random) -> Question:
    x = rng.randint(-9, 9)
    a = rng.randint(2, 9)
    b = rng.randint(-12, 12)
    c = a * x + b
    return _q("G", "G.equation", f"{fmt_linear(a, b)} = {c}，x = ？", str(x),
              explanation=f"移项得 {a}x = {c - b}，所以 x = {x}。")

# ---------------------------------------------------------------------------
# H - equations, systems, inequalities, Pythagoras
# ---------------------------------------------------------------------------


def gen_h_equation(rng: random.Random) -> Question:
    if rng.random() < 0.5:
        a = rng.randint(2, 9)
        b = rng.randint(1, 9)
        x = rng.randint(-5, 10)
        c = a * (x + b)
        return _q("H", "H.equation", f"{a}(x + {b}) = {c}，x = ？", str(x),
                  explanation=f"两边除以 {a}：x + {b} = {x + b}，所以 x = {x}。")
    a = rng.randint(2, 9)
    x = a * rng.randint(1, 9)
    b = rng.randint(-10, 10)
    c = x // a + b
    return _q("H", "H.equation", f"x/{a} + {b} = {c}，x = ？", str(x),
              explanation=f"x/{a} = {x // a}，所以 x = {x}。")


def gen_h_system(rng: random.Random) -> Question:
    x = rng.randint(1, 10)
    y = rng.randint(1, 10)
    s = x + y
    d = x - y
    ask_x = rng.random() < 0.5
    prompt = f"x + y = {s}\nx - y = {d}\n\n求 {'x' if ask_x else 'y'} 的值。"
    return _q("H", "H.system", prompt, str(x if ask_x else y),
              explanation=f"两式相加得 2x = {s + d}，所以 x = {x}，y = {y}。")


def gen_h_inequality(rng: random.Random) -> Question:
    a = rng.randint(2, 5)
    b = rng.randint(-5, 8)
    m = rng.randint(0, 8)
    c = a * (m + 1) + b
    prompt = f"{a}x + {b} < {c}，x 的最大整数值是多少？"
    return _q("H", "H.inequality", prompt, str(m),
              explanation=f"解得 x < {m + 1}，所以最大整数是 {m}。")


def gen_h_polynomial(rng: random.Random) -> Question:
    if rng.random() < 0.5:
        a = rng.randint(2, 5)
        m = rng.randint(1, 3)
        b = rng.randint(2, 5)
        n = rng.randint(1, 2)
        correct = f"{a * b}x{sup(m + n)}"
        prompt = f"{a}x{sup(m)} · {b}x{sup(n)} = ？"
        distractors = [f"{a * b}x{sup(m * n)}", f"{a + b}x{sup(m + n)}", f"{a * b}x{sup(m + n + 1)}"]
        return _choice("H", "H.polynomial", prompt, correct, distractors, rng,
                       explanation=f"系数相乘，指数相加，得到 {correct}。")
    b = rng.randint(2, 5)
    q = rng.randint(2, 4)
    a = b * q
    n = rng.randint(2, 4)
    m = rng.randint(1, n - 1)
    correct = f"{q}x{sup(n - m)}"
    prompt = f"{a}x{sup(n)} ÷ {b}x{sup(m)} = ？"
    distractors = [f"{q}x{sup(n + m)}", f"{a - b}x{sup(n - m)}", f"{q + 1}x{sup(n - m)}"]
    return _choice("H", "H.polynomial", prompt, correct, distractors, rng,
                   explanation=f"系数相除，指数相减，得到 {correct}。")


def gen_h_pythagoras(rng: random.Random) -> Question:
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25), (9, 12, 15)]
    a, b, c = rng.choice(triples)
    scale = rng.choice([1, 1, 2])
    a, b, c = a * scale, b * scale, c * scale
    if rng.random() < 0.5:
        return _q("H", "H.pythagoras",
                  f"直角三角形的两条直角边分别是 {a} 和 {b}，斜边是多少？", str(c),
                  explanation=f"斜边 = √({a}² + {b}²) = {c}。")
    return _q("H", "H.pythagoras",
              f"直角三角形的斜边是 {c}，一条直角边是 {a}，另一条直角边是多少？", str(b),
              explanation=f"另一条直角边 = √({c}² - {a}²) = {b}。")


def gen_h_function(rng: random.Random) -> Question:
    k = rng.choice([-4, -3, -2, 2, 3, 4])
    b = rng.randint(-6, 6)
    x = rng.randint(-5, 5)
    y = k * x + b
    text = fmt_linear(k, b)
    if rng.random() < 0.6:
        return _q("H", "H.function", f"已知 y = {text}，当 x = {x} 时，y = ？", str(y),
                  explanation=f"y = {k} × {x} + {b} = {y}。")
    return _q("H", "H.function", f"已知 y = {text}，当 y = {y} 时，x = ？", str(x),
              explanation=f"{k}x + {b} = {y}，解得 x = {x}。")

# ---------------------------------------------------------------------------
# I - factoring, radicals, quadratics
# ---------------------------------------------------------------------------


def gen_i_factor(rng: random.Random) -> Question:
    while True:
        p = rng.randint(-6, 6)
        q = rng.randint(-6, 6)
        if p and q and p != q and p + q != 0:
            break
    correct = fmt_factor("x", p) + fmt_factor("x", q)
    distractors = [
        fmt_factor("x", -p) + fmt_factor("x", -q),
        fmt_factor("x", p) + fmt_factor("x", -q),
        fmt_factor("x", -p) + fmt_factor("x", q),
    ]
    prompt = f"分解因式：{fmt_quad(1, p + q, p * q)} = ？"
    return _choice("I", "I.factor", prompt, correct, distractors, rng,
                   explanation=f"常数项分解成 {p} × {q}，且 {p} + {q} = {p + q}。")


def gen_i_radical(rng: random.Random) -> Question:
    m = rng.choice([2, 3, 5, 6, 7])
    k = rng.randint(2, 6)
    n = k * k * m
    return _q("I", "I.radical",
              f"把 √{n} 化成 k√{m} 的形式，k = ？", str(k),
              explanation=f"√{n} = √({k}² × {m}) = {k}√{m}。")


def gen_i_quadratic(rng: random.Random) -> Question:
    p = rng.randint(-6, 8)
    q = rng.randint(-6, 8)
    while q == p:
        q = rng.randint(-6, 8)
    kind = rng.choice(["larger", "smaller", "sum", "product"])
    if kind == "larger":
        answer = max(p, q)
        ask = "较大的根"
    elif kind == "smaller":
        answer = min(p, q)
        ask = "较小的根"
    elif kind == "sum":
        answer = p + q
        ask = "两根之和"
    else:
        answer = p * q
        ask = "两根之积"
    prompt = f"方程 {fmt_quad(1, -(p + q), p * q)} = 0 的{ask}是多少？"
    return _q("I", "I.quadratic", prompt, str(answer),
              explanation=f"方程可分解为 {fmt_factor('x', -p)}{fmt_factor('x', -q)} = 0，两根是 {p} 和 {q}。")


def gen_i_parabola(rng: random.Random) -> Question:
    h = rng.randint(-5, 5)
    k = rng.randint(-9, 9)
    if h == 0:
        square = "x²"
    elif h > 0:
        square = f"(x - {h})²"
    else:
        square = f"(x + {abs(h)})²"
    if k > 0:
        text = f"{square} + {k}"
    elif k < 0:
        text = f"{square} - {abs(k)}"
    else:
        text = square
    if rng.random() < 0.5:
        return _q("I", "I.parabola", f"二次函数 y = {text} 的顶点横坐标是多少？", str(h),
                  explanation=f"顶点式 y = (x - h)² + k 的顶点是 ({h}, {k})。")
    return _q("I", "I.parabola", f"二次函数 y = {text} 的最小值是多少？", str(k),
              explanation=f"顶点纵坐标就是最小值 {k}。")


def gen_i_pythagoras(rng: random.Random) -> Question:
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25)]
    a, b, c = rng.choice(triples)
    scale = rng.choice([1, 1, 2])
    a, b, c = a * scale, b * scale, c * scale
    if rng.random() < 0.5:
        prompt = f"一把梯子长 {c} 米，底端离墙 {a} 米，梯子顶端离地面多少米？"
        return _q("I", "I.pythagoras", prompt, str(b),
                  explanation=f"顶端高度 = √({c}² - {a}²) = {b}（米）。")
    prompt = f"一个长方形的长是 {a} 米，宽是 {b} 米，对角线长多少米？"
    return _q("I", "I.pythagoras", prompt, str(c),
              explanation=f"对角线 = √({a}² + {b}²) = {c}（米）。")


def gen_i_fraction(rng: random.Random) -> Question:
    a = rng.randint(2, 9)
    correct = f"x + {a}"
    distractors = [f"x - {a}", f"x² + {a}", f"{a}x + 1"]
    return _choice(
        "I",
        "I.fraction",
        f"化简分式：(x² - {a * a})/(x - {a})  （x ≠ {a}）",
        correct,
        distractors,
        rng,
        explanation=f"分子用平方差公式：x² - {a * a} = (x + {a})(x - {a})，约分后得 x + {a}。",
    )

# ---------------------------------------------------------------------------
# J - polynomials, discriminant, Vieta, remainder
# ---------------------------------------------------------------------------


def gen_j_expand(rng: random.Random) -> Question:
    a = rng.randint(-6, 6)
    b = rng.randint(-6, 6)
    if a == 0:
        a = 2
    if b == 0:
        b = -3
    correct = fmt_quad(1, a + b, a * b)
    distractors = [
        fmt_quad(1, a + b, a * b + 1),
        fmt_quad(1, a - b, a * b),
        fmt_quad(1, a + b, -(a * b)),
    ]
    return _choice(
        "J",
        "J.expand",
        f"展开：{fmt_factor('x', a)}{fmt_factor('x', b)} = ？",
        correct,
        distractors,
        rng,
        explanation=f"一次项系数是 {a} + {b} = {a + b}，常数项是 {a} × {b} = {a * b}。",
    )


def gen_j_factor(rng: random.Random) -> Question:
    a = rng.randint(2, 9)
    if rng.random() < 0.5:
        correct = fmt_factor("x", a) + fmt_factor("x", -a)
        prompt = f"分解因式：x² - {a * a} = ？"
        distractors = [
            f"(x + {a})²",
            f"(x - {a})²",
            f"(x + {a})(x + {a})",
        ]
        explanation = f"平方差公式：x² - {a * a} = (x + {a})(x - {a})。"
    else:
        correct = f"(x + {a})²"
        prompt = f"分解因式：x² + {2 * a}x + {a * a} = ？"
        distractors = [f"(x - {a})²", f"(x + {a})(x - {a})", f"(x + {2 * a})²"]
        explanation = f"完全平方公式：x² + {2 * a}x + {a * a} = (x + {a})²。"
    return _choice("J", "J.factor", prompt, correct, distractors, rng,
                   explanation=explanation)


def gen_j_discriminant(rng: random.Random) -> Question:
    a = rng.randint(1, 5)
    b = rng.randint(-8, 8)
    c = rng.randint(-5, 5)
    d = b * b - 4 * a * c
    return _q("J", "J.discriminant",
              f"方程 {fmt_quad(a, b, c)} = 0 的判别式 Δ = ？", str(d),
              explanation=f"Δ = b² - 4ac = {b}² - 4 × {a} × {_paren(c)} = {d}。")


def gen_j_vieta(rng: random.Random) -> Question:
    p = rng.randint(-6, 8)
    q = rng.randint(-6, 8)
    while q == p:
        q = rng.randint(-6, 8)
    if rng.random() < 0.5:
        answer = p + q
        ask = "两根之和"
    else:
        answer = p * q
        ask = "两根之积"
    prompt = f"方程 {fmt_quad(1, -(p + q), p * q)} = 0 的{ask}是多少？"
    return _q("J", "J.vieta", prompt, str(answer),
              explanation=f"由韦达定理，两根之和为 {p + q}，两根之积为 {p * q}。")


def fmt_cubic(a: int, b: int, c: int) -> str:
    text = "x³"
    if a:
        body = "x²" if abs(a) == 1 else f"{abs(a)}x²"
        text += (" + " if a > 0 else " - ") + body
    if b:
        body = "x" if abs(b) == 1 else f"{abs(b)}x"
        text += (" + " if b > 0 else " - ") + body
    if c:
        text += (" + " if c > 0 else " - ") + str(abs(c))
    return text


def gen_j_remainder(rng: random.Random) -> Question:
    a = rng.randint(-5, 5)
    b = rng.randint(-5, 5)
    c = rng.randint(-5, 5)
    r = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    value = r ** 3 + a * r * r + b * r + c
    divisor = f"(x + {abs(r)})" if r < 0 else f"(x - {r})"
    prompt = f"多项式 P(x) = {fmt_cubic(a, b, c)}，P(x) 除以 {divisor} 的余数是？"
    return _q("J", "J.remainder", prompt, str(value),
              explanation=f"由余式定理，余数 = P({r}) = {value}。")


def gen_j_irrational(rng: random.Random) -> Question:
    n = rng.randint(10, 90)
    root = math.isqrt(n)
    while root * root == n:
        n = rng.randint(10, 90)
        root = math.isqrt(n)
    return _q("J", "J.irrational", f"√{n} 的整数部分是多少？", str(root),
              explanation=f"{root}² = {root * root} < {n} < {root + 1}² = {(root + 1) ** 2}，所以整数部分是 {root}。")

# ---------------------------------------------------------------------------
# K - linear/quadratic functions and exponents
# ---------------------------------------------------------------------------


def gen_k_linear(rng: random.Random) -> Question:
    k = rng.choice([-4, -3, -2, 2, 3, 4])
    b = rng.randint(-6, 6)
    x = rng.randint(-5, 5)
    y = k * x + b
    if rng.random() < 0.5:
        return _q("K", "K.linear", f"一次函数 y = {fmt_linear(k, b)}，当 x = {x} 时，y = ？", str(y),
                  explanation=f"y = {k} × {x} + {b} = {y}。")
    return _q("K", "K.linear", f"一次函数 y = {fmt_linear(k, b)} 的斜率是多少？", str(k),
              explanation=f"y = kx + b 中，k = {k} 就是斜率。")


def gen_k_vertex(rng: random.Random) -> Question:
    a = rng.choice([1, 2, -1, -2])
    h = rng.randint(-4, 4)
    k = rng.randint(-8, 8)
    b = -2 * a * h
    c = a * h * h + k
    if rng.random() < 0.5:
        return _q("K", "K.vertex",
                  f"二次函数 y = {fmt_quad(a, b, c)} 的顶点横坐标是多少？", str(h),
                  explanation=f"顶点横坐标 x = -b/(2a) = {h}。")
    return _q("K", "K.vertex",
              f"二次函数 y = {fmt_quad(a, b, c)} 的顶点纵坐标是多少？", str(k),
              explanation=f"代入 x = {h}，得到顶点纵坐标 {k}。")


def gen_k_extremum(rng: random.Random) -> Question:
    a = rng.randint(1, 3)
    h = rng.randint(-4, 4)
    k = rng.randint(-8, 8)
    sign = "最小值" if a > 0 else "最大值"
    coef = abs(a)
    square = "x²" if h == 0 else (f"(x - {h})²" if h > 0 else f"(x + {abs(h)})²")
    body = square if coef == 1 else f"{coef}{square}"
    if a < 0:
        body = "-" + body
    if k > 0:
        text = f"{body} + {k}"
    elif k < 0:
        text = f"{body} - {abs(k)}"
    else:
        text = body
    return _q("K", "K.extremum", f"二次函数 y = {text} 的{sign}是多少？", str(k),
              explanation=f"顶点纵坐标是 {k}，开口{'向上' if a > 0 else '向下'}，所以{sign}是 {k}。")


def gen_k_exponent(rng: random.Random) -> Question:
    base = rng.choice([2, 3, 5])
    m = rng.randint(2, 4)
    n = rng.randint(2, 4)
    if rng.random() < 0.5:
        return _q("K", "K.exponent", f"{base}{sup(m)} × {base}{sup(n)} = {base}{sup('x')}，x = ？", str(m + n),
                  explanation=f"同底数幂相乘，指数相加：{m} + {n} = {m + n}。")
    return _q("K", "K.exponent", f"{base}{sup(m)} × {base}{sup(n)} = ？", str(base ** (m + n)),
              explanation=f"{base}{sup(m)} × {base}{sup(n)} = {base}{sup(m + n)} = {base ** (m + n)}。")


def gen_k_exp_eq(rng: random.Random) -> Question:
    base = rng.choice([2, 3, 5])
    n = rng.randint(2, 4)
    return _q("K", "K.exp_eq", f"{base}{sup('x')} = {base ** n}，x = ？", str(n),
              explanation=f"{base ** n} = {base}{sup(n)}，所以 x = {n}。")


def gen_k_inequality(rng: random.Random) -> Question:
    p = rng.randint(-5, 3)
    q = rng.randint(p + 1, 6)
    less = rng.random() < 0.5
    prompt = f"不等式 (x - {p})(x - {q}) {'<' if less else '>'} 0 的解集是？"
    if less:
        correct = f"{p} < x < {q}"
        distractors = [f"x < {p} 或 x > {q}", f"x ≤ {p} 或 x ≥ {q}", f"{p} < x ≤ {q}"]
        explanation = "两根之间小于零。"
    else:
        correct = f"x < {p} 或 x > {q}"
        distractors = [f"{p} < x < {q}", f"x ≤ {p} 或 x ≥ {q}", f"x > {p} 或 x < {q}"]
        explanation = "两根之外大于零。"
    return _choice("K", "K.inequality", prompt, correct, distractors, rng,
                   explanation=explanation)

# ---------------------------------------------------------------------------
# L - logarithms and calculus
# ---------------------------------------------------------------------------


def gen_l_log(rng: random.Random) -> Question:
    base = rng.choice([2, 3, 5, 10])
    n = rng.randint(2, 4)
    return _q("L", "L.log", f"log{sub(base)} {base ** n} = ？", str(n),
              explanation=f"{base}{sup(n)} = {base ** n}，所以 log{sub(base)} {base ** n} = {n}。")


def gen_l_log_eq(rng: random.Random) -> Question:
    base = rng.choice([2, 3, 5])
    n = rng.randint(2, 4)
    return _q("L", "L.log_eq", f"log{sub(base)} x = {n}，x = ？", str(base ** n),
              explanation=f"x = {base}{sup(n)} = {base ** n}。")


def gen_l_log_prop(rng: random.Random) -> Question:
    base = rng.choice([2, 3, 5])
    p = rng.randint(1, 3)
    q = rng.randint(1, 3)
    if rng.random() < 0.5:
        prompt = f"log{sub(base)} {base ** p} + log{sub(base)} {base ** q} = ？"
        answer = p + q
        explanation = f"同底对数相加，真数相乘：log{sub(base)} {base ** (p + q)} = {p + q}。"
    else:
        if p == q:
            p += 1
        high, low = max(p, q), min(p, q)
        prompt = f"log{sub(base)} {base ** high} - log{sub(base)} {base ** low} = ？"
        answer = high - low
        explanation = f"同底对数相减，真数相除：log{sub(base)} {base ** (high - low)} = {high - low}。"
    return _q("L", "L.log_prop", prompt, str(answer), explanation=explanation)


def _power_term(coef: int, n: int) -> str:
    if n == 0:
        return str(coef)
    body = "x" if n == 1 else f"x{sup(n)}"
    if coef == 1:
        return body
    if coef == -1:
        return f"-{body}"
    return f"{coef}{body}"


def gen_l_derivative(rng: random.Random) -> Question:
    a = rng.randint(1, 4)
    n = rng.randint(2, 3)
    b = rng.randint(-5, 5)
    c = rng.randint(-5, 5)
    x0 = rng.randint(-3, 3)
    answer = a * n * (x0 ** (n - 1)) + b
    f = _power_term(a, n)
    if b:
        f += f" + {b}x" if b > 0 else f" - {abs(b)}x"
    if c:
        f += f" + {c}" if c > 0 else f" - {abs(c)}"
    return _q("L", "L.derivative", f"f(x) = {f}，求 f'({x0})。", str(answer),
              explanation=f"f'(x) = {_power_term(a * n, n - 1)} + {b}，代入 x = {x0} 得 {answer}。")


def gen_l_tangent(rng: random.Random) -> Question:
    b = rng.randint(-5, 5)
    c = rng.randint(-5, 5)
    x0 = rng.randint(-3, 3)
    slope = 2 * x0 + b
    text = fmt_quad(1, b, c)
    return _q("L", "L.tangent", f"曲线 y = {text} 在 x = {x0} 处的切线斜率是多少？", str(slope),
              explanation=f"y' = 2x + {b}，代入 x = {x0}，斜率 = {slope}。")


def gen_l_integral(rng: random.Random) -> Question:
    n = rng.randint(1, 3)
    a = rng.randint(1, 5)
    value = Fraction(a ** (n + 1), n + 1)
    power = "x" if n == 1 else f"x{sup(n)}"
    prompt = f"定积分 ∫{sub(0)}{sup(a)} {power} dx = ？"
    antideriv = f"x{sup(n + 1)}/{n + 1}"
    return _q("L", "L.integral", prompt, fstr(value), input_type=INPUT_FRACTION,
              explanation=f"∫ {power} dx = {antideriv}，代入 0 到 {a} 得 {fstr(value)}。")


def gen_l_indefinite(rng: random.Random) -> Question:
    n = rng.randint(1, 3)
    q = rng.randint(1, 4)
    a = q * (n + 1)
    correct = ("" if q == 1 else str(q)) + f"x{sup(n + 1)} + C"
    prompt = f"∫ {a}x{sup(n)} dx = ？"
    distractors = [
        f"{a}x{sup(n + 1)} + C",
        f"{q}x{sup(n)} + C",
        f"{a}x{sup(n)} + C",
    ]
    return _choice("L", "L.indefinite", prompt, correct, distractors, rng,
                   explanation=f"原函数是 {correct}（C 为常数）。")


def gen_l_extremum(rng: random.Random) -> Question:
    h = rng.randint(-5, 5)
    c = rng.randint(-9, 9)
    minimum = c - h * h
    text = fmt_quad(1, -2 * h, c)
    derivative = fmt_linear(2, -2 * h)
    return _q("L", "L.extremum", f"函数 f(x) = {text} 的极小值是多少？", str(minimum),
              explanation=f"f'(x) = {derivative}，令 f'(x) = 0 得 x = {h}，极小值为 {minimum}。")


GENERATORS: dict[str, Callable[[random.Random], Question]] = {
    # 5A
    "5A.match": gen_5a_match,
    "5A.pattern": gen_5a_pattern,
    "5A.count": gen_5a_count,
    "5A.order": gen_5a_order,
    "5A.compare": gen_5a_compare,
    # 4A
    "4A.count": gen_4a_count,
    "4A.digit": gen_4a_digit,
    "4A.sequence": gen_4a_sequence,
    "4A.compare": gen_4a_compare,
    "4A.puzzle": gen_4a_puzzle,
    # 3A
    "3A.count100": gen_3a_count100,
    "3A.plus1": gen_3a_plus1,
    "3A.plus23": gen_3a_plus23,
    "3A.sequence": gen_3a_sequence,
    "3A.tens": gen_3a_tens,
    # 2A
    "2A.add10": gen_2a_add10,
    "2A.addfill": gen_2a_addfill,
    "2A.decompose": gen_2a_decompose,
    "2A.add3": gen_2a_add3,
    # A
    "A.add20": gen_a_add20,
    "A.sub20": gen_a_sub20,
    "A.mixed": gen_a_mixed,
    "A.fill": gen_a_fill,
    "A.word": gen_a_word,
    # B
    "B.add2": gen_b_add2,
    "B.add3": gen_b_add3,
    "B.sub2": gen_b_sub2,
    "B.sub3": gen_b_sub3,
    "B.fill": gen_b_fill,
    # C
    "C.table": gen_c_table,
    "C.x1": gen_c_x1,
    "C.x1_3": gen_c_x1_3,
    "C.x2": gen_c_x2,
    "C.fill": gen_c_fill,
    # D
    "D.basic": gen_d_basic,
    "D.remainder": gen_d_remainder,
    "D.div2": gen_d_div2,
    "D.div3": gen_d_div3,
    "D.divisor2": gen_d_divisor2,
    "D.fill": gen_d_fill,
    # E
    "E.add": gen_e_add,
    "E.sub": gen_e_sub,
    "E.mixed": gen_e_mixed,
    "E.simplify": gen_e_simplify,
    "E.fill": gen_e_fill,
    # F
    "F.order": gen_f_order,
    "F.frac": gen_f_frac,
    "F.decimal": gen_f_decimal,
    "F.solve_x": gen_f_solve_x,
    "F.word": gen_f_word,
    "F.convert": gen_f_convert,
    # G
    "G.int_add": gen_g_int_add,
    "G.int_muldiv": gen_g_int_muldiv,
    "G.int_mixed": gen_g_int_mixed,
    "G.eval": gen_g_eval,
    "G.simplify": gen_g_simplify,
    "G.equation": gen_g_equation,
    # H
    "H.equation": gen_h_equation,
    "H.system": gen_h_system,
    "H.inequality": gen_h_inequality,
    "H.polynomial": gen_h_polynomial,
    "H.pythagoras": gen_h_pythagoras,
    "H.function": gen_h_function,
    # I
    "I.factor": gen_i_factor,
    "I.radical": gen_i_radical,
    "I.quadratic": gen_i_quadratic,
    "I.parabola": gen_i_parabola,
    "I.pythagoras": gen_i_pythagoras,
    "I.fraction": gen_i_fraction,
    # J
    "J.expand": gen_j_expand,
    "J.factor": gen_j_factor,
    "J.discriminant": gen_j_discriminant,
    "J.vieta": gen_j_vieta,
    "J.remainder": gen_j_remainder,
    "J.irrational": gen_j_irrational,
    # K
    "K.linear": gen_k_linear,
    "K.vertex": gen_k_vertex,
    "K.extremum": gen_k_extremum,
    "K.exponent": gen_k_exponent,
    "K.exp_eq": gen_k_exp_eq,
    "K.inequality": gen_k_inequality,
    # L
    "L.log": gen_l_log,
    "L.log_eq": gen_l_log_eq,
    "L.log_prop": gen_l_log_prop,
    "L.derivative": gen_l_derivative,
    "L.tangent": gen_l_tangent,
    "L.integral": gen_l_integral,
    "L.indefinite": gen_l_indefinite,
    "L.extremum": gen_l_extremum,
}


def generate_question(topic_key: str, rng: random.Random) -> Question:
    return GENERATORS[topic_key](rng)


__all__ = ["GENERATORS", "fstr", "generate_question", "sub", "sup"]
