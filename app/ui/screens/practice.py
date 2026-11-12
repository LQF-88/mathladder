"""The practice screen: question card, answer pad and immediate feedback."""

from __future__ import annotations

import time

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from app.engine.checker import is_correct
from app.engine.curriculum import TOPIC_BY_KEY
from app.engine.models import INPUT_CHOICE, SessionResult
from app.engine.vertical import vertical_problem
from app.theme import (
    CREAM_DARK,
    GREEN,
    GREEN_SOFT,
    INDIGO,
    INDIGO_SOFT,
    INK,
    MUTED,
    RED,
    RED_SOFT,
    WHITE,
)
from app.ui.widgets.common import (
    BaseScreen,
    Card,
    ConfirmDialog,
    Header,
    Lbl,
    PillButton,
    ProgressMeter,
    VScroll,
    format_seconds,
    spacer,
)
from app.ui.widgets.vertical import VerticalProblemView


class PracticeScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="practice", **kwargs)
        self.header = Header("练习", back=self.request_back)
        self.timer_label = Lbl(
            "00:00",
            font_size=12,
            bold=True,
            color=MUTED,
            halign="right",
            size_hint=(None, 1),
            width=dp(58),
        )
        self.header.add_widget(self.timer_label)
        self.root.add_widget(self.header)

        progress_wrap = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(50),
            padding=(dp(16), dp(2), dp(16), dp(4)),
            spacing=dp(4),
        )
        row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(8))
        self.counter_label = Lbl(
            "第 1 / 20 题",
            font_size=11.5,
            bold=True,
            color=INK,
            size_hint_y=None,
            height=dp(22),
        )
        self.score_label = Lbl(
            "答对 0 题",
            font_size=10.5,
            color=MUTED,
            halign="right",
            size_hint_y=None,
            height=dp(22),
        )
        row.add_widget(self.counter_label)
        row.add_widget(self.score_label)
        progress_wrap.add_widget(row)
        self.progress = ProgressMeter(0, INDIGO)
        progress_wrap.add_widget(self.progress)
        self.root.add_widget(progress_wrap)

        self.question_wrap = BoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(2), dp(16), dp(6)),
        )
        self.question_card = Card(padding=dp(16), spacing=dp(8), radius=20)
        topic_row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(8))
        self.topic_label = Lbl(
            "", font_size=10, color=MUTED, size_hint_y=None, height=dp(22)
        )
        self.level_label = Lbl(
            "",
            font_size=10,
            color=MUTED,
            halign="right",
            size_hint_y=None,
            height=dp(22),
        )
        topic_row.add_widget(self.topic_label)
        topic_row.add_widget(self.level_label)
        self.question_card.add_widget(topic_row)
        self.prompt_label = Lbl(
            "",
            font_size=30,
            color=INK,
            halign="center",
            valign="middle",
            markup=True,
            size_hint_y=1,
        )
        self.question_card.add_widget(self.prompt_label)
        self.question_wrap.add_widget(self.question_card)
        self.root.add_widget(self.question_wrap)

        self.answer_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(304),
            padding=(dp(16), 0, dp(16), dp(12)),
            spacing=dp(6),
        )
        self.root.add_widget(self.answer_box)

        self.questions = []
        self.index = 0
        self.level = "5A"
        self.topic_key: str | None = None
        self.from_mistakes = False
        self.typed = ""
        self.answered = False
        self.correct_count = 0
        self.wrong: list[tuple] = []
        self.correct_ids: list[str] = []
        self.start_time = 0.0
        self.elapsed = 0
        self._timer_event = None
        self._auto_event = None
        self._ok_button = None
        self._rendered_choices: list[PillButton] = []
        self.vertical_view: VerticalProblemView | None = None

    # -- session lifecycle ------------------------------------------------
    def start(self, level_code, topic_key, questions, from_mistakes=False):
        self.level = level_code
        self.topic_key = topic_key
        self.questions = list(questions)
        self.from_mistakes = from_mistakes
        self.index = 0
        self.correct_count = 0
        self.wrong = []
        self.correct_ids = []
        self.answered = False
        self.typed = ""
        self.elapsed = 0
        self.start_time = time.monotonic()
        level = self.app.level_of(level_code)
        topic_name = TOPIC_BY_KEY[topic_key].name if topic_key else "混合练习"
        if from_mistakes:
            topic_name = "错题重练"
        self.header.title_label.text = f"{level.code} · {level.name}"
        if self.header.subtitle_label is not None:
            self.header.subtitle_label.text = topic_name
        self.timer_label.text = "00:00"
        if self._timer_event is not None:
            self._timer_event.cancel()
        self._timer_event = Clock.schedule_interval(self._tick, 1.0)
        self._render_question()

    def _tick(self, *_):
        self.elapsed = int(time.monotonic() - self.start_time)
        self.timer_label.text = format_seconds(self.elapsed)

    def _stop_timer(self):
        if self._timer_event is not None:
            self._timer_event.cancel()
            self._timer_event = None
        self._cancel_auto()

    def _cancel_auto(self):
        if self._auto_event is not None:
            self._auto_event.cancel()
            self._auto_event = None

    # -- rendering -------------------------------------------------------
    def _render_question(self):
        if not self.questions:
            self.app.open_home()
            return
        self._cancel_auto()
        self._clear_vertical()
        question = self.questions[self.index]
        topic = TOPIC_BY_KEY.get(question.topic)
        self.topic_label.text = topic.name if topic else ""
        self.level_label.text = f"{self.index + 1} / {len(self.questions)}"
        self.counter_label.text = f"第 {self.index + 1} / {len(self.questions)} 题"
        self.score_label.text = f"答对 {self.correct_count} 题"
        self.progress.value = self.index / max(1, len(self.questions))
        self.answered = False
        self.typed = ""
        self._ok_button = None
        self._rendered_choices = []

        problem = None
        if self.app.repo.get_setting("vertical_input", True):
            problem = vertical_problem(question)
        if problem is not None:
            self.prompt_label.text = ""
            self.prompt_label.size_hint_y = None
            self.prompt_label.height = 0
            self.vertical_view = VerticalProblemView(
                problem, on_change=self._update_input
            )
            self.question_card.add_widget(self.vertical_view)
        else:
            self.prompt_label.text = question.prompt
            self.prompt_label.size_hint_y = 1
            self._fit_prompt(question.prompt)

        if question.input_type == INPUT_CHOICE:
            self._build_choices(question)
        else:
            self._build_keypad()

    def _clear_vertical(self):
        if self.vertical_view is not None:
            self.question_card.remove_widget(self.vertical_view)
            self.vertical_view = None

    def _fit_prompt(self, prompt: str):
        plain_len = len(prompt)
        if self.level in ("5A", "4A", "3A", "2A"):
            size = 32 if plain_len < 70 else 27
        elif self.level in ("A", "B", "C", "D"):
            size = 29 if plain_len < 60 else 24
        elif self.level in ("E", "F"):
            size = 27 if plain_len < 55 else 22
        else:
            size = 24 if plain_len < 55 else 19
        if plain_len > 110:
            size = min(size, 18)
        self.prompt_label.font_size = dp(size)

    def _build_choices(self, question):
        self.answer_box.clear_widgets()
        self.answer_box.height = dp(156)
        grid = GridLayout(cols=2, spacing=dp(9), size_hint_y=None, height=dp(140))
        self._rendered_choices = []
        for option in question.choices:
            button = PillButton(
                text=option,
                font_size=15,
                bold=False,
                markup=True,
                bg_color=list(INDIGO_SOFT),
                text_color=list(INK),
                radius=14,
            )
            button.bind(on_release=lambda btn, value=option: self._submit(value))
            grid.add_widget(button)
            self._rendered_choices.append(button)
        self.answer_box.add_widget(grid)

    def _build_keypad(self):
        self.answer_box.clear_widgets()
        self.answer_box.height = dp(304)
        vertical = self.vertical_view is not None
        input_card = Card(
            bg_color=list(INDIGO_SOFT),
            padding=dp(8),
            radius=13,
            size_hint_y=None,
            height=dp(52),
        )
        self.input_label = Lbl(
            "从个位开始，一位一位填写" if vertical else "点下面数字键输入答案",
            font_size=17,
            bold=True,
            color=MUTED,
            halign="center",
            size_hint_y=None,
            height=dp(34),
        )
        input_card.add_widget(self.input_label)
        self.answer_box.add_widget(input_card)
        self.answer_box.add_widget(spacer(1))

        grid = GridLayout(
            cols=3 if vertical else 4,
            spacing=dp(7),
            size_hint_y=None,
            height=dp(224),
        )
        if vertical:
            keys = [
                ("1", "1"),
                ("2", "2"),
                ("3", "3"),
                ("4", "4"),
                ("5", "5"),
                ("6", "6"),
                ("7", "7"),
                ("8", "8"),
                ("9", "9"),
                ("退格", "back"),
                ("0", "0"),
                ("确定", "ok"),
            ]
        else:
            keys = [
                ("1", "1"),
                ("2", "2"),
                ("3", "3"),
                ("退格", "back"),
                ("4", "4"),
                ("5", "5"),
                ("6", "6"),
                ("/", "/"),
                ("7", "7"),
                ("8", "8"),
                ("9", "9"),
                ("-", "-"),
                (".", "."),
                ("0", "0"),
                ("清空", "clear"),
                ("确定", "ok"),
            ]
        for label, action in keys:
            if action == "ok":
                button = PillButton(
                    text=label,
                    font_size=15,
                    bold=True,
                    bg_color=list(INDIGO),
                    text_color=list(WHITE),
                    radius=12,
                )
                button.disabled = True
                self._ok_button = button
                button.bind(on_release=lambda *_: self._confirm_typed())
            elif action in ("back", "clear"):
                button = PillButton(
                    text=label,
                    font_size=12,
                    bg_color=list(CREAM_DARK),
                    text_color=list(INK),
                    radius=12,
                )
                button.bind(on_release=lambda _b, act=action: self._edit(act))
            elif action in ("/", "-", "."):
                button = PillButton(
                    text=label,
                    font_size=18,
                    bold=True,
                    bg_color=list(WHITE),
                    text_color=list(INDIGO),
                    radius=12,
                )
                button.bind(on_release=lambda _b, val=action: self._append(val))
            else:
                button = PillButton(
                    text=label,
                    font_size=20,
                    bold=True,
                    bg_color=list(WHITE),
                    text_color=list(INK),
                    radius=12,
                )
                button.bind(on_release=lambda _b, val=action: self._append(val))
            grid.add_widget(button)
        self.answer_box.add_widget(grid)
        self._update_input()

    def _update_input(self):
        if not hasattr(self, "input_label"):
            return
        if self.vertical_view is not None:
            filled = self.vertical_view.filled
            total = len(self.vertical_view.cells)
            if self.vertical_view.is_complete:
                self.input_label.text = "已填满 · 点“确定”检查"
            else:
                self.input_label.text = f"从个位开始 · 已填 {filled}/{total} 位"
            self.input_label.color = INK if filled else MUTED
            if self._ok_button is not None:
                self._ok_button.disabled = not self.vertical_view.is_complete
            return
        if self.typed:
            self.input_label.text = self.typed
            self.input_label.color = INK
        else:
            self.input_label.text = "点下面数字键输入答案"
            self.input_label.color = MUTED
        if self._ok_button is not None:
            self._ok_button.disabled = not bool(self.typed)

    def _append(self, char: str):
        if self.answered:
            return
        if self.vertical_view is not None:
            if char.isdigit():
                self.vertical_view.input_digit(char)
            return
        if char == "-":
            if self.typed:
                return
        elif char == ".":
            if "." in self.typed or "/" in self.typed:
                return
        elif char == "/" and ("/" in self.typed or not self.typed):
            return
        if len(self.typed) >= 10:
            return
        self.typed += char
        self._update_input()

    def _edit(self, action: str):
        if self.answered:
            return
        if self.vertical_view is not None:
            if action == "back":
                self.vertical_view.backspace()
            else:
                self.vertical_view.clear()
            return
        if action == "back":
            self.typed = self.typed[:-1]
        else:
            self.typed = ""
        self._update_input()

    def _confirm_typed(self):
        if self.vertical_view is not None:
            value = self.vertical_view.value
            if value:
                self._submit(value)
            return
        if self.typed:
            self._submit(self.typed)

    # -- answering -------------------------------------------------------
    def _submit(self, user_answer: str):
        if self.answered or not self.questions:
            return
        self.answered = True
        if self.vertical_view is not None:
            self.vertical_view.locked = True
        question = self.questions[self.index]
        correct = is_correct(question, user_answer)
        if correct:
            self.correct_count += 1
            self.correct_ids.append(question.qid)
        else:
            self.wrong.append((question, user_answer))
        self.score_label.text = f"答对 {self.correct_count} 题"
        self.app.play_feedback(correct)
        self._render_feedback(question, user_answer, correct)

    def _render_feedback(self, question, user_answer: str, correct: bool):
        self.answer_box.clear_widgets()
        self.answer_box.height = dp(252)
        card = Card(
            bg_color=list(GREEN_SOFT if correct else RED_SOFT),
            padding=dp(14),
            spacing=dp(5),
            radius=18,
        )
        head = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        head.add_widget(
            Lbl(
                "回答正确！" if correct else "答案不对，再看一看",
                font_size=15,
                bold=True,
                color=GREEN if correct else RED,
                size_hint_y=None,
                height=dp(26),
            )
        )
        head.add_widget(
            Lbl(
                "继续保持" if correct else "看看讲解",
                font_size=9.5,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(26),
            )
        )
        card.add_widget(head)
        if not correct:
            card.add_widget(
                Lbl(
                    f"正确答案：{question.answer}",
                    font_size=13,
                    bold=True,
                    color=INK,
                    markup=True,
                    size_hint_y=None,
                    height=dp(22),
                )
            )
        explanation = question.explanation or ""
        body = VScroll(padding=0, spacing=0)
        body.size_hint_y = 1
        body.box.add_widget(
            Lbl(
                explanation,
                font_size=11.5,
                color=INK,
                auto_height=True,
                markup=True,
            )
        )
        card.add_widget(body)
        next_text = "查看结果" if self.index + 1 >= len(self.questions) else "下一题"
        next_button = PillButton(
            text=next_text + "  →",
            font_size=14,
            bold=True,
            bg_color=list(INDIGO),
            text_color=list(WHITE),
            size_hint_y=None,
            height=dp(44),
            radius=13,
        )
        next_button.bind(on_release=lambda *_: self._advance())
        card.add_widget(next_button)
        self.answer_box.add_widget(card)
        auto_next = self.app.repo.get_setting("auto_next", False)
        if correct and auto_next:
            self._auto_event = Clock.schedule_once(lambda *_: self._advance(), 1.15)

    def _advance(self):
        self._cancel_auto()
        if self.index + 1 >= len(self.questions):
            self._finish()
            return
        self.index += 1
        self._render_question()

    def _finish(self):
        self._stop_timer()
        seconds = max(1, int(time.monotonic() - self.start_time))
        self.progress.value = 1.0
        result = SessionResult(
            level=self.level,
            topic=self.topic_key or "mixed",
            total=len(self.questions),
            correct=self.correct_count,
            seconds=seconds,
            wrong=self.wrong,
            correct_ids=self.correct_ids,
            from_mistakes=self.from_mistakes,
        )
        self.app.finish_session(result)

    # -- navigation ------------------------------------------------------
    def request_back(self):
        if self.answered or self.correct_count or self.index > 0:
            dialog = ConfirmDialog(
                "退出本次练习？",
                "未完成的题目不会计入学习记录，本次成绩也不会保存。",
                self._exit,
                confirm_text="退出",
                danger=True,
            )
            dialog.open()
        else:
            self._exit()

    def _exit(self):
        self._stop_timer()
        self.app.open_home()
