"""Level detail: overview, start controls, topics and level mistakes."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from app.theme import (
    INDIGO,
    INK,
    LEVEL_TINTS,
    MUTED,
    RED,
    RED_SOFT,
    WHITE,
    c,
)
from app.ui.widgets.common import (
    Badge,
    BaseScreen,
    Card,
    Header,
    Lbl,
    PillButton,
    ProgressMeter,
    Segmented,
    TappableCard,
    VScroll,
    star_markup,
)


class LevelScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="level", **kwargs)
        self.code = "5A"
        self.header = Header("阶梯", back=app.open_home)
        self.root.add_widget(self.header)
        self.scroll = VScroll(padding=16, spacing=12)
        self.root.add_widget(self.scroll)
        self.selected_count = int(app.repo.get_setting("questions_per_session", 20))

    def show_level(self, code: str):
        self.code = code
        self.selected_count = int(self.app.repo.get_setting("questions_per_session", 20))

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        level = self.app.level_of(self.code)
        repo = self.app.repo
        progress = repo.level_progress(level.code)
        accuracy = (
            round(progress["correct"] * 100 / progress["answered"])
            if progress["answered"]
            else 0
        )
        self._set_header(level)

        box = self.scroll.box
        box.clear_widgets()

        hero = Card(
            bg_color=list(LEVEL_TINTS.get(level.code, WHITE)),
            padding=dp(18),
            spacing=dp(8),
            radius=22,
            size_hint_y=None,
        )
        hero.bind(minimum_height=hero.setter("height"))
        title_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12))
        title_row.add_widget(Badge(level.code, c(level.color), size=56, font_size=17))
        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_box.add_widget(
            Lbl(level.name, font_size=19, bold=True, color=INK, size_hint_y=None, height=dp(27))
        )
        title_box.add_widget(
            Lbl(level.subtitle, font_size=10.5, color=MUTED, size_hint_y=None, height=dp(17))
        )
        title_box.add_widget(
            Lbl(star_markup(repo.stars(level.code)), font_size=11, markup=True,
                size_hint_y=None, height=dp(18))
        )
        title_row.add_widget(title_box)
        hero.add_widget(title_row)
        hero.add_widget(
            Lbl(level.description, font_size=12, color=INK, auto_height=True)
        )
        stats = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        stats.add_widget(self._mini_stat(str(progress["answered"]), "已练题数"))
        stats.add_widget(self._mini_stat(f"{accuracy}%", "正确率"))
        stats.add_widget(self._mini_stat(f"{repo.stars(level.code)}/3", "星级"))
        hero.add_widget(stats)
        bar_row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(6))
        bar_row.add_widget(ProgressMeter(repo.progress_percent(level.code), c(level.color)))
        bar_row.add_widget(
            Lbl(
                f"{int(repo.progress_percent(level.code) * 100)}%",
                font_size=10.5,
                color=MUTED,
                halign="right",
                size_hint=(None, None),
                size=(dp(38), dp(18)),
            )
        )
        hero.add_widget(bar_row)
        box.add_widget(hero)

        start_card = Card(padding=dp(16), spacing=dp(10), radius=20, size_hint_y=None, height=dp(166))
        start_head = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        start_head.add_widget(
            Lbl("开始练习", font_size=15, bold=True, color=INK, size_hint_y=None, height=dp(24))
        )
        start_head.add_widget(
            Lbl("混合本阶段全部题型", font_size=9.5, color=MUTED, halign="right",
                size_hint_y=None, height=dp(24))
        )
        start_card.add_widget(start_head)
        self.count_segment = Segmented(
            options=[(10, "10 题"), (20, "20 题"), (30, "30 题")],
            value=self.selected_count,
            callback=self._set_count,
        )
        start_card.add_widget(self.count_segment)
        start_button = PillButton(
            text=f"开始练习 · {level.code}",
            font_size=15,
            bold=True,
            bg_color=list(INDIGO),
            text_color=list(WHITE),
            size_hint_y=None,
            height=dp(46),
            radius=14,
        )
        start_button.bind(on_release=lambda *_: self._start(None))
        start_card.add_widget(start_button)
        box.add_widget(start_card)

        mistake_records = repo.mistakes(level.code)
        if mistake_records:
            mistake_card = Card(
                bg_color=list(RED_SOFT),
                padding=dp(14),
                spacing=dp(6),
                radius=18,
                size_hint_y=None,
                height=dp(96),
            )
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
            row.add_widget(
                Lbl(f"本阶段错题本 · {len(mistake_records)} 道", font_size=13.5, bold=True,
                    color=RED, size_hint_y=None, height=dp(34),
                    shorten=True, shorten_from="right")
            )
            redo = PillButton(
                text="重练错题",
                font_size=12,
                bold=True,
                bg_color=list(RED),
                text_color=list(WHITE),
                size_hint=(None, None),
                size=(dp(90), dp(36)),
                radius=11,
            )
            redo.bind(on_release=lambda *_: self._start_mistakes(mistake_records))
            row.add_widget(redo)
            mistake_card.add_widget(row)
            mistake_card.add_widget(
                Lbl("答对后会从错题本中移除。", font_size=10, color=MUTED,
                    size_hint_y=None, height=dp(19))
            )
            box.add_widget(mistake_card)

        box.add_widget(self._section_title("专项练习", f"{len(level.topics)} 个题型"))
        topics_progress = progress.get("topics") or {}
        for topic in level.topics:
            box.add_widget(self._topic_card(topic, topics_progress.get(topic.key) or {}))

        box.add_widget(
            Lbl(
                "建议每天 10-20 分钟，保持短而稳定的练习节奏。",
                font_size=10,
                color=MUTED,
                halign="center",
                auto_height=True,
            )
        )

    def _set_header(self, level):
        self.header.title_label.text = f"{level.code} · {level.name}"
        if self.header.subtitle_label is not None:
            self.header.subtitle_label.text = level.subtitle

    def _mini_stat(self, value: str, label: str) -> BoxLayout:
        cell = BoxLayout(orientation="vertical")
        cell.add_widget(
            Lbl(value, font_size=17, bold=True, color=INK, halign="center",
                size_hint_y=None, height=dp(23))
        )
        cell.add_widget(
            Lbl(label, font_size=9, color=MUTED, halign="center",
                size_hint_y=None, height=dp(14))
        )
        return cell

    def _section_title(self, title: str, hint: str = "") -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        row.add_widget(
            Lbl(title, font_size=16, bold=True, color=INK, size_hint_y=None, height=dp(28))
        )
        row.add_widget(
            Lbl(hint, font_size=10.5, color=MUTED, halign="right",
                size_hint_y=None, height=dp(28))
        )
        return row

    def _set_count(self, value):
        self.selected_count = int(value)
        self.app.repo.set_setting("questions_per_session", int(value))

    def _start(self, topic_key):
        self.app.start_practice(
            self.code, topic_key=topic_key, count=self.selected_count
        )

    def _start_mistakes(self, records):
        self.app.start_mistake_session(records, level=self.code)

    def _topic_card(self, topic, stats) -> TappableCard:
        answered = int(stats.get("answered", 0))
        correct = int(stats.get("correct", 0))
        accuracy = round(correct * 100 / answered) if answered else 0
        card = TappableCard(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(10),
            radius=15,
            bg_color=list(WHITE),
            size_hint_y=None,
            height=dp(68),
        )
        middle = BoxLayout(orientation="vertical", spacing=dp(2))
        middle.add_widget(
            Lbl(topic.name, font_size=13.5, bold=True, color=INK,
                size_hint_y=None, height=dp(21))
        )
        middle.add_widget(
            Lbl(topic.description, font_size=9.5, color=MUTED,
                size_hint_y=None, height=dp(16), shorten=True, shorten_from="right")
        )
        middle.add_widget(
            Lbl(
                f"已练 {answered} 题 · 正确率 {accuracy}%" if answered else "还没有练习",
                font_size=9,
                color=MUTED,
                size_hint_y=None,
                height=dp(14),
            )
        )
        card.add_widget(middle)
        arrow = Lbl("→", font_size=17, color=INDIGO, halign="right",
                    size_hint=(None, 1), width=dp(20))
        card.add_widget(arrow)
        card.bind(on_release=lambda *_: self._start(topic.key))
        return card
