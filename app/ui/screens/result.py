"""Session summary with stars, stats and a wrong-answer review."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from app.engine.curriculum import TOPIC_BY_KEY
from app.theme import (
    GREEN,
    INDIGO,
    INK,
    MUTED,
    ORANGE,
    RED,
    WHITE,
)
from app.ui.widgets.common import (
    BaseScreen,
    Card,
    Header,
    Lbl,
    PillButton,
    VScroll,
    format_seconds,
    star_markup,
)


class ResultScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="result", **kwargs)
        self.header = Header("练习结果", back=app.open_home)
        self.root.add_widget(self.header)
        self.scroll = VScroll(padding=16, spacing=12)
        self.root.add_widget(self.scroll)
        self.result = None

    def show_result(self, result):
        self.result = result
        self.refresh()

    def refresh(self):
        if self.result is None:
            return
        result = self.result
        level = self.app.level_of(result.level)
        topic_name = (
            "错题重练"
            if result.from_mistakes
            else (TOPIC_BY_KEY[result.topic].name if result.topic in TOPIC_BY_KEY else "混合练习")
        )
        self.header.title_label.text = f"{level.code} · 练习结果"
        if self.header.subtitle_label is not None:
            self.header.subtitle_label.text = topic_name

        box = self.scroll.box
        box.clear_widgets()

        good = result.accuracy >= 80
        hero = Card(
            padding=dp(20),
            spacing=dp(10),
            radius=22,
            size_hint_y=None,
            height=dp(286),
        )
        hero.add_widget(
            Lbl(
                star_markup(result.stars, size=3),
                font_size=30,
                halign="center",
                markup=True,
                size_hint_y=None,
                height=dp(36),
            )
        )
        hero.add_widget(
            Lbl(
                "这一组完成啦！" if good else "慢一点也没关系",
                font_size=18,
                bold=True,
                color=INK,
                halign="center",
                size_hint_y=None,
                height=dp(26),
            )
        )
        hero.add_widget(
            Lbl(
                f"{result.correct} / {result.total}",
                font_size=44,
                bold=True,
                color=GREEN if good else ORANGE,
                halign="center",
                size_hint_y=None,
                height=dp(58),
            )
        )
        hero.add_widget(
            Lbl(
                f"正确率 {result.accuracy}%",
                font_size=12,
                color=MUTED,
                halign="center",
                size_hint_y=None,
                height=dp(20),
            )
        )
        stats = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8))
        stats.add_widget(self._stat(str(result.total), "本组题数", INDIGO))
        stats.add_widget(self._stat(str(result.correct), "答对", GREEN))
        stats.add_widget(self._stat(format_seconds(result.seconds), "用时", ORANGE))
        hero.add_widget(stats)
        box.add_widget(hero)

        again = PillButton(
            text=f"再来一组 · {level.code}",
            font_size=15,
            bold=True,
            bg_color=list(INDIGO),
            text_color=list(WHITE),
            radius=14,
            size_hint_y=None,
            height=dp(48),
        )
        again.bind(on_release=lambda *_: self._again())
        box.add_widget(again)

        bottom_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        if result.wrong:
            redo = PillButton(
                text=f"重做错题 · {len(result.wrong)}",
                font_size=13,
                bold=True,
                bg_color=list(RED),
                text_color=list(WHITE),
                radius=13,
            )
            redo.bind(on_release=lambda *_: self._retry_wrong())
            bottom_row.add_widget(redo)
        home = PillButton(
            text="返回首页",
            font_size=13,
            bg_color=list(WHITE),
            text_color=list(INK),
            radius=13,
        )
        home.bind(on_release=lambda *_: self.app.open_home())
        bottom_row.add_widget(home)
        box.add_widget(bottom_row)

        if result.wrong:
            box.add_widget(self._section(f"错题回顾 · {len(result.wrong)} 道"))
            for question, user_answer in result.wrong:
                box.add_widget(self._wrong_card(question, user_answer))
            tip = (
                "错题已加入错题本，之后可以在统计页或对应等级页重练。"
                if not result.from_mistakes
                else "本次答对的错题已从错题本移除。"
            )
            box.add_widget(
                Lbl(
                    tip,
                    font_size=10,
                    color=MUTED,
                    halign="center",
                    auto_height=True,
                )
            )
        else:
            box.add_widget(
                Lbl(
                    "全部答对，太棒了！下一组继续保持。",
                    font_size=12,
                    color=MUTED,
                    halign="center",
                    auto_height=True,
                )
            )

    def _stat(self, value: str, label: str, color) -> BoxLayout:
        cell = BoxLayout(orientation="vertical", spacing=dp(1))
        cell.add_widget(
            Lbl(
                value,
                font_size=17,
                bold=True,
                color=color,
                halign="center",
                size_hint_y=None,
                height=dp(23),
            )
        )
        cell.add_widget(
            Lbl(
                label,
                font_size=9.5,
                color=MUTED,
                halign="center",
                size_hint_y=None,
                height=dp(15),
            )
        )
        return cell

    def _section(self, title: str) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(30))
        row.add_widget(
            Lbl(title, font_size=15, bold=True, color=INK, size_hint_y=None, height=dp(28))
        )
        return row

    def _wrong_card(self, question, user_answer: str) -> Card:
        card = Card(
            bg_color=list(WHITE),
            padding=dp(14),
            spacing=dp(6),
            radius=16,
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))
        head = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
        head.add_widget(
            Lbl(
                "错题",
                font_size=9.5,
                bold=True,
                color=RED,
                size_hint_y=None,
                height=dp(20),
            )
        )
        head.add_widget(
            Lbl(
                f"你的答案 {user_answer or '未作答'}",
                font_size=9.5,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(20),
            )
        )
        card.add_widget(head)
        card.add_widget(
            Lbl(
                question.prompt,
                font_size=11.5,
                color=INK,
                markup=True,
                auto_height=True,
            )
        )
        card.add_widget(
            Lbl(
                f"[color={self._hex(RED)}]正确答案[/color] {question.answer}",
                font_size=11.5,
                bold=True,
                color=INK,
                markup=True,
                auto_height=True,
            )
        )
        if question.explanation:
            card.add_widget(
                Lbl(
                    question.explanation,
                    font_size=10.5,
                    color=MUTED,
                    markup=True,
                    auto_height=True,
                )
            )
        return card

    @staticmethod
    def _hex(rgba) -> str:
        return f"#{int(rgba[0] * 255):02X}{int(rgba[1] * 255):02X}{int(rgba[2] * 255):02X}"

    def _again(self):
        result = self.result
        if result is None:
            self.app.open_home()
            return
        topic = result.topic if result.topic in TOPIC_BY_KEY else None
        self.app.start_practice(result.level, topic_key=topic, count=result.total)

    def _retry_wrong(self):
        if self.result is not None:
            self.app.retry_wrong(self.result)
