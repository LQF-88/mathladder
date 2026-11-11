"""Home screen: brand, streak and the 16-level ladder."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from app.engine.curriculum import LEVELS
from app.theme import (
    INDIGO,
    INK,
    MUTED,
    ORANGE,
    WHITE,
    YELLOW,
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
    TappableCard,
    VScroll,
    star_markup,
)


class HomeScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="home", **kwargs)
        self.root.add_widget(
            Header(
                "数学阶梯",
                "MathLadder · 每天一小步",
                actions=[("统计", app.open_stats), ("设置", app.open_settings)],
            )
        )
        self.scroll = VScroll(padding=16, spacing=12)
        self.root.add_widget(self.scroll)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        repo = self.app.repo
        box = self.scroll.box
        box.clear_widgets()

        recommended = repo.recommended_level()
        streak = repo.streak().get("current", 0)
        hero = Card(
            bg_color=list(INDIGO),
            padding=dp(18),
            spacing=dp(9),
            radius=22,
            size_hint_y=None,
            height=dp(196),
        )
        top = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        mark = Card(
            bg_color=[1, 1, 1, 0.14],
            padding=0,
            radius=16,
            size_hint=(None, None),
            size=(dp(50), dp(50)),
        )
        mark.add_widget(Lbl("★", font_size=26, color=YELLOW, halign="center"))
        top.add_widget(mark)
        greeting = BoxLayout(orientation="vertical", spacing=dp(1))
        greeting.add_widget(
            Lbl("今天也来闯一关吧", font_size=17, bold=True, color=WHITE,
                size_hint_y=None, height=dp(25))
        )
        greeting.add_widget(
            Lbl(
                f"连续练习 {streak} 天" if streak else "从第一关开始，慢慢变强",
                font_size=11.5,
                color=[1, 1, 1, 0.78],
                size_hint_y=None,
                height=dp(18),
            )
        )
        top.add_widget(greeting)
        hero.add_widget(top)

        stats = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        stats.add_widget(self._hero_stat(str(repo.total_answered()), "累计答题"))
        stats.add_widget(self._hero_stat(f"{repo.overall_accuracy()}%", "正确率"))
        stats.add_widget(self._hero_stat(str(repo.total_stars()), "收集星星"))
        hero.add_widget(stats)

        level = self.app.level_of(recommended)
        daily = PillButton(
            text=f"每日一练 · {level.code} {level.name}",
            font_size=14,
            bold=True,
            bg_color=list(ORANGE),
            text_color=list(WHITE),
            radius=14,
            size_hint_y=None,
            height=dp(44),
        )
        daily.bind(
            on_release=lambda *_: self.app.start_practice(recommended, count=10)
        )
        hero.add_widget(daily)
        box.add_widget(hero)

        section = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        section.add_widget(
            Lbl("选择阶梯", font_size=16, bold=True, color=INK, size_hint_y=None, height=dp(26))
        )
        section.add_widget(
            Lbl(
                f"{repo.total_answered()} 题 · {len(LEVELS)} 个阶段",
                font_size=10.5,
                color=MUTED,
                halign="right",
                size_hint_y=None,
                height=dp(26),
            )
        )
        box.add_widget(section)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for level in LEVELS:
            grid.add_widget(self._level_card(level))
        box.add_widget(grid)

        box.add_widget(
            Lbl(
                "题目由本应用自动生成，参考公文数学 5A-L 的学习顺序。\n"
                "本应用与公文式教育（KUMON）无隶属关系。",
                font_size=9.5,
                color=MUTED,
                halign="center",
                auto_height=True,
            )
        )

    def _hero_stat(self, value: str, label: str) -> BoxLayout:
        cell = BoxLayout(orientation="vertical", spacing=dp(0))
        cell.add_widget(
            Lbl(value, font_size=18, bold=True, color=WHITE, halign="center",
                size_hint_y=None, height=dp(24))
        )
        cell.add_widget(
            Lbl(label, font_size=9.5, color=[1, 1, 1, 0.68], halign="center",
                size_hint_y=None, height=dp(15))
        )
        return cell

    def _level_card(self, level):
        repo = self.app.repo
        progress = repo.level_progress(level.code)
        percent = repo.progress_percent(level.code)
        card = TappableCard(
            padding=dp(11),
            spacing=dp(5),
            radius=16,
            bg_color=list(WHITE),
            size_hint_y=None,
            height=dp(118),
        )
        top = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        top.add_widget(Badge(level.code, c(level.color), size=34, font_size=11.5))
        top.add_widget(BoxLayout())
        top.add_widget(
            Lbl(
                star_markup(repo.stars(level.code)),
                font_size=10,
                halign="right",
                markup=True,
                size_hint_y=None,
                height=dp(30),
            )
        )
        card.add_widget(top)
        card.add_widget(
            Lbl(
                f"{level.code} · {level.name}",
                font_size=13.5,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(21),
                shorten=True,
                shorten_from="right",
            )
        )
        card.add_widget(ProgressMeter(percent, c(level.color)))
        bottom = BoxLayout(size_hint_y=None, height=dp(15), spacing=dp(4))
        bottom.add_widget(
            Lbl(
                level.subtitle,
                font_size=9,
                color=MUTED,
                size_hint_y=None,
                height=dp(15),
                shorten=True,
                shorten_from="right",
            )
        )
        bottom.add_widget(
            Lbl(
                f"{progress['answered']} 题",
                font_size=9,
                color=MUTED,
                halign="right",
                size_hint=(None, None),
                size=(dp(48), dp(15)),
            )
        )
        card.add_widget(bottom)
        card.bind(on_release=lambda *_: self.app.open_level(level.code))
        return card
