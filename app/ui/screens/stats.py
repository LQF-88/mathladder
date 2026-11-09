"""Learning statistics, weekly chart, level progress and the mistake book."""

from __future__ import annotations

from datetime import datetime

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from app.engine.curriculum import LEVELS, TOPIC_BY_KEY
from app.engine.models import Question
from app.theme import (
    GREEN,
    INDIGO,
    INK,
    MUTED,
    ORANGE,
    ORANGE_SOFT,
    RED,
    WHITE,
    c,
)
from app.ui.widgets.common import (
    Badge,
    BaseScreen,
    Card,
    ConfirmDialog,
    Header,
    Lbl,
    PillButton,
    ProgressMeter,
    TappableCard,
    VScroll,
    WeekChart,
    star_markup,
    stat_tile,
)


class StatsScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="stats", **kwargs)
        self.header = Header(
            "学习统计",
            "MathLadder · 学习记录",
            back=app.open_home,
            actions=[("设置", app.open_settings)],
        )
        self.root.add_widget(self.header)
        self.scroll = VScroll(padding=16, spacing=12)
        self.root.add_widget(self.scroll)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        repo = self.app.repo
        box = self.scroll.box
        box.clear_widgets()

        overview = GridLayout(cols=2, spacing=dp(9), size_hint_y=None, height=dp(176))
        overview.add_widget(stat_tile(str(repo.total_answered()), "累计答题", INDIGO))
        overview.add_widget(
            stat_tile(f"{repo.overall_accuracy()}%", "总体正确率", GREEN)
        )
        overview.add_widget(stat_tile(str(repo.total_stars()), "收集星星", ORANGE))
        overview.add_widget(stat_tile(str(repo.mistake_count()), "错题本", RED))
        box.add_widget(overview)

        streak = repo.streak()
        streak_card = Card(
            bg_color=list(ORANGE_SOFT),
            padding=dp(14),
            spacing=dp(3),
            radius=16,
            size_hint_y=None,
            height=dp(70),
        )
        streak_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        streak_row.add_widget(
            Lbl(
                f"连续练习 {streak.get('current', 0)} 天",
                font_size=15,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(28),
            )
        )
        streak_row.add_widget(
            Lbl(
                f"最长纪录 {streak.get('best', 0)} 天",
                font_size=10.5,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(28),
            )
        )
        streak_card.add_widget(streak_row)
        streak_card.add_widget(
            Lbl(
                "每天 10 分钟，比偶尔练很久更有效。",
                font_size=10,
                color=MUTED,
                size_hint_y=None,
                height=dp(18),
            )
        )
        box.add_widget(streak_card)

        series = repo.daily_series(7)
        week_total = sum(value for _day, value in series)
        box.add_widget(self._section_title("最近 7 天", f"共 {week_total} 题"))
        chart_card = Card(
            padding=dp(14),
            spacing=dp(4),
            radius=18,
            size_hint_y=None,
            height=dp(182),
        )
        chart_card.add_widget(WeekChart(series))
        box.add_widget(chart_card)

        box.add_widget(self._section_title("各阶段进度", "点击进入"))
        for level in LEVELS:
            box.add_widget(self._level_row(level, repo))

        box.add_widget(self._section_title("错题本", f"{repo.mistake_count()} 道"))
        records = repo.mistakes()
        if not records:
            empty = Card(
                padding=dp(16),
                radius=16,
                size_hint_y=None,
                height=dp(66),
            )
            empty.add_widget(
                Lbl(
                    "还没有错题，继续保持！",
                    font_size=12,
                    color=MUTED,
                    halign="center",
                )
            )
            box.add_widget(empty)
        else:
            action_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
            redo = PillButton(
                text=f"重练全部错题 · {len(records)}",
                font_size=12,
                bold=True,
                bg_color=list(RED),
                text_color=list(WHITE),
                radius=12,
            )
            redo.bind(on_release=lambda *_: self.app.start_mistake_session(records))
            action_row.add_widget(redo)
            clear = PillButton(
                text="清空",
                font_size=12,
                bg_color=list(WHITE),
                text_color=list(RED),
                size_hint=(None, 1),
                width=dp(68),
                radius=12,
            )
            clear.bind(on_release=lambda *_: self._confirm_clear())
            action_row.add_widget(clear)
            box.add_widget(action_row)
            for record in records[:10]:
                box.add_widget(self._mistake_card(record))
            if len(records) > 10:
                box.add_widget(
                    Lbl(
                        f"仅显示最近 10 道，共 {len(records)} 道错题。",
                        font_size=10,
                        color=MUTED,
                        halign="center",
                        auto_height=True,
                    )
                )

        sessions = repo.recent_sessions(6)
        if sessions:
            box.add_widget(self._section_title("最近练习", ""))
            for session in sessions:
                box.add_widget(self._session_card(session))

    def _section_title(self, title: str, hint: str = "") -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        row.add_widget(
            Lbl(title, font_size=16, bold=True, color=INK, size_hint_y=None, height=dp(28))
        )
        row.add_widget(
            Lbl(
                hint,
                font_size=10.5,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(28),
            )
        )
        return row

    def _level_row(self, level, repo) -> TappableCard:
        progress = repo.level_progress(level.code)
        answered = int(progress.get("answered", 0))
        correct = int(progress.get("correct", 0))
        accuracy = round(correct * 100 / answered) if answered else 0
        card = TappableCard(
            orientation="horizontal",
            padding=dp(10),
            spacing=dp(10),
            radius=14,
            bg_color=list(WHITE),
            size_hint_y=None,
            height=dp(68),
        )
        card.add_widget(Badge(level.code, c(level.color), size=36, font_size=12))
        middle = BoxLayout(orientation="vertical", spacing=dp(4))
        name_row = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(6))
        name_row.add_widget(
            Lbl(
                level.name,
                font_size=12,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(18),
                shorten=True,
                shorten_from="right",
            )
        )
        name_row.add_widget(
            Lbl(
                f"{answered} 题 · {accuracy}%",
                font_size=9,
                color=MUTED,
                halign="right",
                size_hint=(None, None),
                size=(dp(82), dp(18)),
            )
        )
        middle.add_widget(name_row)
        middle.add_widget(ProgressMeter(repo.progress_percent(level.code), c(level.color)))
        card.add_widget(middle)
        card.add_widget(
            Lbl(
                star_markup(repo.stars(level.code)),
                font_size=9.5,
                markup=True,
                halign="right",
                size_hint=(None, 1),
                width=dp(36),
            )
        )
        card.bind(on_release=lambda *_: self.app.open_level(level.code))
        return card

    def _mistake_card(self, record) -> Card:
        question = Question.from_dict(record)
        card = Card(
            bg_color=list(WHITE),
            padding=dp(12),
            spacing=dp(4),
            radius=14,
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))
        topic = TOPIC_BY_KEY.get(question.topic)
        head = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(6))
        head.add_widget(
            Lbl(
                f"{question.level} · {topic.name if topic else '综合'}",
                font_size=9,
                bold=True,
                color=RED,
                size_hint_y=None,
                height=dp(18),
            )
        )
        head.add_widget(
            Lbl(
                "你的答案 " + str(record.get("user", "")),
                font_size=9,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(18),
            )
        )
        card.add_widget(head)
        card.add_widget(
            Lbl(
                question.prompt,
                font_size=11,
                color=INK,
                markup=True,
                auto_height=True,
            )
        )
        card.add_widget(
            Lbl(
                f"正确答案 {question.answer}",
                font_size=10,
                bold=True,
                color=GREEN,
                markup=True,
                auto_height=True,
            )
        )
        return card

    def _session_card(self, session: dict) -> Card:
        card = Card(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(8),
            radius=13,
            size_hint_y=None,
            height=dp(48),
        )
        try:
            date = datetime.fromisoformat(session.get("date", "")).strftime("%m-%d %H:%M")
        except ValueError:
            date = session.get("day", "")
        card.add_widget(
            Lbl(
                date,
                font_size=10,
                color=MUTED,
                size_hint=(None, 1),
                width=dp(78),
            )
        )
        card.add_widget(
            Lbl(
                f"{session.get('level', '')}",
                font_size=12,
                bold=True,
                color=INDIGO,
                size_hint=(None, 1),
                width=dp(30),
            )
        )
        card.add_widget(
            Lbl(
                f"{session.get('correct', 0)} / {session.get('total', 0)} 题",
                font_size=11,
                color=INK,
            )
        )
        card.add_widget(
            Lbl(
                f"{session.get('accuracy', 0)}%",
                font_size=11,
                bold=True,
                color=GREEN,
                halign="right",
                size_hint=(None, 1),
                width=dp(46),
            )
        )
        return card

    def _confirm_clear(self):
        dialog = ConfirmDialog(
            "清空错题本？",
            "所有错题记录会被删除，此操作无法撤销。",
            self._clear_mistakes,
            confirm_text="清空",
            danger=True,
        )
        dialog.open()

    def _clear_mistakes(self):
        self.app.repo.clear_mistakes()
        self.refresh()
