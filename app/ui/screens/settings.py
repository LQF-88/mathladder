"""Settings: session size, feedback options, local data controls and about."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout

from app.theme import (
    INDIGO,
    INK,
    LINE,
    MUTED,
    RED,
    WHITE,
)
from app.ui.widgets.common import (
    BaseScreen,
    Card,
    ConfirmDialog,
    Header,
    Lbl,
    PillButton,
    Segmented,
    TappableCard,
    Toggle,
    VScroll,
)


class SettingsScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="settings", **kwargs)
        self.header = Header(
            "设置",
            "MathLadder · 偏好与数据",
            back=app.close_settings,
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

        box.add_widget(self._section_title("练习"))
        count_card = Card(
            padding=dp(16),
            spacing=dp(8),
            radius=18,
            size_hint_y=None,
            height=dp(128),
        )
        count_card.add_widget(
            Lbl(
                "每组题目数量",
                font_size=13.5,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(22),
            )
        )
        count = int(repo.get_setting("questions_per_session", 20))
        count_card.add_widget(
            Segmented(
                options=[(10, "10 题"), (20, "20 题"), (30, "30 题")],
                value=count,
                callback=lambda value: repo.set_setting(
                    "questions_per_session", int(value)
                ),
            )
        )
        count_card.add_widget(
            Lbl(
                "进入等级页时仍可临时调整。",
                font_size=9.5,
                color=MUTED,
                size_hint_y=None,
                height=dp(16),
            )
        )
        box.add_widget(count_card)

        vertical_card = Card(
            padding=dp(16),
            spacing=dp(2),
            radius=18,
            size_hint_y=None,
            height=dp(80),
        )
        vertical_card.add_widget(
            self._row(
                "竖式输入",
                "加减法和乘法题用竖式，逐位填写答案",
                Toggle(
                    active=bool(repo.get_setting("vertical_input", True)),
                    callback=lambda value: repo.set_setting(
                        "vertical_input", bool(value)
                    ),
                ),
            )
        )
        box.add_widget(vertical_card)

        box.add_widget(self._section_title("答题反馈"))
        feedback_card = Card(
            padding=dp(16),
            spacing=dp(2),
            radius=18,
            size_hint_y=None,
            height=dp(136),
        )
        feedback_card.add_widget(
            self._row(
                "答题音效",
                "答对和答错时播放提示音",
                Toggle(
                    active=bool(repo.get_setting("sound", True)),
                    callback=lambda value: repo.set_setting("sound", bool(value)),
                ),
            )
        )
        feedback_card.add_widget(self._divider())
        feedback_card.add_widget(
            self._row(
                "答对后自动下一题",
                "答错时停留在讲解页，方便订正",
                Toggle(
                    active=bool(repo.get_setting("auto_next", False)),
                    callback=lambda value: repo.set_setting("auto_next", bool(value)),
                ),
            )
        )
        box.add_widget(feedback_card)

        box.add_widget(self._section_title("本机数据"))
        data_card = Card(
            padding=dp(16),
            spacing=dp(2),
            radius=18,
            size_hint_y=None,
            height=dp(136),
        )
        mistake_count = repo.mistake_count()
        data_card.add_widget(
            self._row(
                "清空错题本",
                f"当前记录 {mistake_count} 道错题",
                self._small_button("清空", self._confirm_clear_mistakes),
                width=dp(72),
            )
        )
        data_card.add_widget(self._divider())
        data_card.add_widget(
            self._row(
                "重置学习数据",
                "等级进度、星星、错题和历史记录都会清除",
                self._small_button("重置", self._confirm_reset, danger=True),
                width=dp(72),
            )
        )
        box.add_widget(data_card)

        box.add_widget(self._section_title("关于"))
        about = TappableCard(
            orientation="horizontal",
            padding=dp(14),
            spacing=dp(8),
            radius=16,
            bg_color=list(WHITE),
            size_hint_y=None,
            height=dp(58),
        )
        about_text = BoxLayout(orientation="vertical", spacing=dp(1))
        about_text.add_widget(
            Lbl("关于数学阶梯", font_size=12.5, bold=True, color=INK,
                size_hint_y=None, height=dp(22))
        )
        about_text.add_widget(
            Lbl("课程说明、字体许可与免责声明", font_size=9.5, color=MUTED,
                size_hint_y=None, height=dp(16))
        )
        about.add_widget(about_text)
        about.add_widget(
            Lbl("→", font_size=16, color=INDIGO, halign="right",
                size_hint=(None, 1), width=dp(20))
        )
        about.bind(on_release=lambda *_: self.app.open_about())
        box.add_widget(about)

        box.add_widget(
            Lbl(
                "所有学习数据只保存在本机，不会上传。",
                font_size=10,
                color=MUTED,
                halign="center",
                auto_height=True,
            )
        )

    def _section_title(self, title: str) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(28))
        row.add_widget(
            Lbl(title, font_size=15, bold=True, color=INK, size_hint_y=None, height=dp(26))
        )
        return row

    def _divider(self):
        divider = Card(
            bg_color=list(LINE),
            padding=0,
            radius=1,
            size_hint_y=None,
            height=dp(1),
        )
        return divider

    def _row(self, title: str, description: str, control, width: float = dp(88)) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        text = BoxLayout(orientation="vertical", spacing=dp(1))
        text.add_widget(
            Lbl(
                title,
                font_size=12.5,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(22),
            )
        )
        text.add_widget(
            Lbl(
                description,
                font_size=9.5,
                color=MUTED,
                size_hint_y=None,
                height=dp(16),
                shorten=True,
                shorten_from="right",
            )
        )
        row.add_widget(text)
        anchor = AnchorLayout(
            anchor_x="right",
            anchor_y="center",
            size_hint=(None, 1),
            width=width,
        )
        anchor.add_widget(control)
        row.add_widget(anchor)
        return row

    def _small_button(self, text: str, callback, danger: bool = False) -> PillButton:
        button = PillButton(
            text=text,
            font_size=11.5,
            bold=True,
            bg_color=list(RED if danger else INDIGO),
            text_color=list(WHITE),
            size_hint=(None, None),
            size=(dp(60), dp(32)),
            radius=10,
        )
        button.bind(on_release=lambda *_: callback())
        return button

    def _confirm_clear_mistakes(self):
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

    def _confirm_reset(self):
        dialog = ConfirmDialog(
            "重置全部学习数据？",
            "等级进度、星星、错题本和练习历史都会清除，且无法恢复。",
            self._reset,
            confirm_text="重置",
            danger=True,
        )
        dialog.open()

    def _reset(self):
        self.app.repo.reset()
        self.refresh()
