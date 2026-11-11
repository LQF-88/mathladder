"""Reusable Kivy widgets used by every screen."""

from __future__ import annotations

import datetime as _dt

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from app.theme import (
    CARD_RADIUS,
    CREAM,
    CREAM_DARK,
    FONT_NAME,
    INDIGO,
    INDIGO_SOFT,
    INK,
    LEVEL_TINTS,
    LINE,
    MUTED,
    MUTED_LIGHT,
    RED,
    TRACK,
    WHITE,
    YELLOW,
    readable_font_size,
)


def spacer(height: float = 8, width: float | None = None) -> Widget:
    if width is None:
        return Widget(size_hint_y=None, height=dp(height))
    return Widget(size_hint_x=None, width=dp(width))


class Lbl(Label):
    """Label with the CJK font, sensible wrapping and optional auto-height."""

    def __init__(
        self,
        text: str = "",
        font_size: float = 16,
        color=None,
        bold: bool = False,
        halign: str = "left",
        markup: bool = False,
        auto_height: bool = False,
        **kwargs,
    ):
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("valign", "middle")
        super().__init__(
            text=text,
            font_size=sp(readable_font_size(font_size)),
            color=color if color is not None else INK,
            bold=bold,
            halign=halign,
            markup=markup,
            **kwargs,
        )
        self._auto_height = auto_height
        if auto_height:
            self.size_hint_y = None
            self.bind(texture_size=self._fit_height)
        self.bind(size=self._fit_text_size, width=self._fit_text_size)
        self._fit_text_size()

    def _fit_text_size(self, *_):
        width = max(1, self.width)
        height = None if self._auto_height else max(1, self.height)
        self.text_size = (width, height)

    def _fit_height(self, *_):
        self.height = max(dp(16), self.texture_size[1])


def lbl(
    text: str,
    font_size: float = 16,
    color=None,
    bold: bool = False,
    halign: str = "left",
    markup: bool = False,
    auto_height: bool = False,
    **kwargs,
) -> Lbl:
    return Lbl(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        halign=halign,
        markup=markup,
        auto_height=auto_height,
        **kwargs,
    )


class Card(BoxLayout):
    bg_color = ListProperty(list(WHITE))
    radius = NumericProperty(CARD_RADIUS)
    border_color = ListProperty(list(LINE))

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(16))
        kwargs.setdefault("spacing", dp(8))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._shadow_color = Color(0.12, 0.1, 0.08, 0.045)
            self._shadow = RoundedRectangle(radius=[dp(self.radius)] * 4)
            self._fill_color = Color(*self.bg_color)
            self._fill = RoundedRectangle(radius=[dp(self.radius)] * 4)
            self._border = Line(width=1)
        self.bind(
            pos=self._sync,
            size=self._sync,
            bg_color=self._sync_fill,
            radius=self._sync,
            border_color=self._sync_border,
        )
        self._sync()

    def _sync(self, *_):
        radius = [dp(self.radius)] * 4
        self._shadow.pos = (self.x, self.y - dp(2))
        self._shadow.size = (self.width, self.height)
        self._shadow.radius = radius
        self._fill.pos = self.pos
        self._fill.size = self.size
        self._fill.radius = radius
        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(self.radius),
        )
        self._sync_fill()
        self._sync_border()

    def _sync_fill(self, *_):
        self._fill_color.rgba = self.bg_color

    def _sync_border(self, *_):
        self._border_color = None
        # Line instructions don't own a colour; set the instruction *before*
        # them via canvas.before ordering is awkward, so paint a very subtle
        # border by adjusting the fill alpha instead.
        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(self.radius),
        )


class TappableCard(ButtonBehavior, Card):
    """Card that responds to taps."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rest_bg = list(self.bg_color)
        self.bind(state=self._on_state)

    def _on_state(self, *_):
        if self.state == "down":
            self.bg_color = [
                max(0, self._rest_bg[0] * 0.94),
                max(0, self._rest_bg[1] * 0.94),
                max(0, self._rest_bg[2] * 0.94),
                self._rest_bg[3],
            ]
        else:
            self.bg_color = self._rest_bg


class PillButton(Button):
    bg_color = ListProperty(list(WHITE))
    pressed_color = ListProperty([0, 0, 0, 0])
    text_color = ListProperty(list(INK))
    radius = NumericProperty(14)

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("font_name", FONT_NAME)
        font_size = kwargs.get("font_size", 15)
        if isinstance(font_size, (int, float)):
            font_size = sp(readable_font_size(font_size))
        kwargs["font_size"] = font_size
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("disabled_color", [*MUTED_LIGHT[:3], 0.7])
        super().__init__(**kwargs)
        self.color = self.text_color
        with self.canvas.before:
            self._bg_color = Color(*self.bg_color)
            self._bg = RoundedRectangle(radius=[dp(self.radius)] * 4)
        self.bind(
            pos=self._sync,
            size=self._sync,
            radius=self._sync,
            bg_color=self._sync_color,
            state=self._sync_color,
            disabled=self._sync_color,
            text_color=self._sync_text,
            width=self._sync_text_size,
            height=self._sync_text_size,
        )
        self._sync()
        self._sync_text()

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bg.radius = [dp(self.radius)] * 4

    def _sync_color(self, *_):
        base = list(self.bg_color)
        if self.pressed_color[3] and self.state == "down":
            base = list(self.pressed_color)
        elif self.state == "down":
            base = [base[0] * 0.9, base[1] * 0.9, base[2] * 0.9, base[3]]
        if self.disabled and base[3] > 0:
            base[3] = base[3] * 0.45
        self._bg_color.rgba = base

    def _sync_text(self, *_):
        self.color = self.text_color

    def _sync_text_size(self, *_):
        self.text_size = (max(1, self.width - dp(14)), max(1, self.height))


class Toggle(ButtonBehavior, Widget):
    """Small iOS-style switch drawn on canvas."""

    active = BooleanProperty(False)

    def __init__(self, active: bool = False, callback=None, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(48), dp(28)))
        super().__init__(**kwargs)
        self.callback = callback
        self.active = bool(active)
        with self.canvas:
            self._track_color = Color(*TRACK)
            self._track = RoundedRectangle()
            self._knob_color = Color(*WHITE)
            self._knob = Ellipse()
        self.bind(pos=self._sync, size=self._sync, active=self._sync)
        self._sync()

    def on_release(self):
        self.active = not self.active
        if self.callback:
            self.callback(self.active)

    def _sync(self, *_):
        self._track_color.rgba = INDIGO if self.active else TRACK
        self._track.pos = self.pos
        self._track.size = self.size
        self._track.radius = [self.height / 2] * 4
        diameter = max(1, self.height - dp(6))
        knob_y = self.y + (self.height - diameter) / 2
        knob_x = self.right - diameter - dp(3) if self.active else self.x + dp(3)
        self._knob.pos = (knob_x, knob_y)
        self._knob.size = (diameter, diameter)


class Header(BoxLayout):
    def __init__(self, title: str, subtitle: str | None = None, back=None, actions=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=(dp(12), dp(6), dp(12), dp(4)),
            spacing=dp(6),
            **kwargs,
        )
        self.app = None
        if back:
            back_button = PillButton(
                text="←",
                font_size=22,
                bold=True,
                size_hint=(None, 1),
                width=dp(40),
                bg_color=[0, 0, 0, 0],
                text_color=INK,
                radius=12,
            )
            back_button.bind(on_release=lambda *_: back())
            self.add_widget(back_button)
        title_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(1))
        self.title_label = Lbl(
            title,
            font_size=20,
            bold=True,
            color=INK,
            size_hint_y=None,
            height=dp(29),
            shorten=True,
            shorten_from="right",
        )
        self.subtitle_label = None
        title_box.add_widget(self.title_label)
        if subtitle:
            self.subtitle_label = Lbl(
                subtitle,
                font_size=10.5,
                color=MUTED,
                size_hint_y=None,
                height=dp(15),
                shorten=True,
                shorten_from="right",
            )
            title_box.add_widget(self.subtitle_label)
        self.add_widget(title_box)
        for label, callback in actions or []:
            button = PillButton(
                text=label,
                font_size=12,
                size_hint=(None, None),
                size=(dp(52), dp(34)),
                bg_color=WHITE,
                text_color=INK,
                radius=12,
            )
            button.bind(on_release=lambda _btn, cb=callback: cb())
            self.add_widget(button)


class ProgressMeter(Widget):
    value = NumericProperty(0.0)
    color = ListProperty(list(INDIGO))
    track_color = ListProperty(list(TRACK))

    def __init__(self, value: float = 0.0, color=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(8))
        super().__init__(**kwargs)
        self.value = value
        if color is not None:
            self.color = list(color)
        with self.canvas:
            self._track_color = Color(*self.track_color)
            self._track = RoundedRectangle()
            self._fill_color = Color(*self.color)
            self._fill = RoundedRectangle()
        self.bind(
            pos=self._sync,
            size=self._sync,
            value=self._sync,
            color=self._sync_colors,
            track_color=self._sync_colors,
        )
        self._sync()

    def _sync(self, *_):
        radius = [max(2, self.height / 2)] * 4
        self._track.pos = self.pos
        self._track.size = self.size
        self._track.radius = radius
        width = max(0, self.width * max(0.0, min(1.0, self.value)))
        self._fill.pos = self.pos
        self._fill.size = (width, self.height)
        self._fill.radius = radius
        # A zero-width rounded rectangle can leave stale geometry in Kivy's
        # vertex buffer; hide it explicitly at 0%.
        self._fill_color.a = 1.0 if width > 0.5 else 0.0

    def _sync_colors(self, *_):
        self._track_color.rgba = self.track_color
        self._fill_color.rgba = self.color
        self._sync()


class Segmented(BoxLayout):
    def __init__(self, options, value, callback=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
            **kwargs,
        )
        self.options = options
        self.value = value
        self.callback = callback
        self.buttons: dict = {}
        for option, label in options:
            button = PillButton(
                text=label,
                font_size=13,
                radius=12,
                bg_color=CREAM_DARK,
                text_color=MUTED,
            )
            button.bind(on_release=lambda _b, opt=option: self.select(opt, notify=True))
            self.buttons[option] = button
            self.add_widget(button)
        self._style()

    def select(self, value, notify: bool = True):
        self.value = value
        self._style()
        if notify and self.callback:
            self.callback(value)

    def _style(self):
        for option, button in self.buttons.items():
            if option == self.value:
                button.bg_color = list(INDIGO)
                button.text_color = list(WHITE)
                button.bold = True
            else:
                button.bg_color = list(CREAM_DARK)
                button.text_color = list(MUTED)
                button.bold = False


class VScroll(ScrollView):
    def __init__(self, padding: float = 16, spacing: float = 12, **kwargs):
        super().__init__(
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=[*MUTED_LIGHT[:3], 0.35],
            bar_inactive_color=[*MUTED_LIGHT[:3], 0.12],
            scroll_type=["bars", "content"],
            **kwargs,
        )
        self.box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(spacing),
            padding=(dp(padding), dp(8), dp(padding), dp(padding)),
        )
        self.box.bind(minimum_height=self.box.setter("height"))
        self.add_widget(self.box)


class Badge(BoxLayout):
    """Coloured rounded square with a short label."""

    def __init__(self, text: str, color, size: float = 52, font_size: float = 16, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(size), dp(size))
        self.padding = 0
        self.bg = Card(
            bg_color=list(color),
            radius=14,
            padding=0,
            size_hint=(1, 1),
        )
        self.bg.add_widget(
            Lbl(text, font_size=font_size, bold=True, color=WHITE, halign="center")
        )
        self.add_widget(self.bg)


class WeekChart(Widget):
    """Seven bars drawn on canvas with day labels underneath."""

    def __init__(self, data: list[tuple[str, int]], **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(142))
        super().__init__(**kwargs)
        self.data = list(data)
        self._bars = []
        with self.canvas:
            self._baseline_color = Color(*LINE)
            self._baseline = Line(width=1)
            for _ in range(7):
                bar_color = Color(*INDIGO)
                bar = RoundedRectangle()
                self._bars.append((bar_color, bar))
        self._labels = []
        for _ in range(7):
            label = Lbl("", font_size=10, color=MUTED, halign="center")
            self.add_widget(label)
            self._labels.append(label)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        if not self.data or not self.width:
            return
        width = self.width
        height = self.height
        baseline_y = dp(38)
        chart_height = max(dp(20), height - baseline_y - dp(6))
        max_value = max(1, max(value for _day, value in self.data))
        slot = width / 7
        bar_width = min(dp(22), slot * 0.44)
        self._baseline_color.rgba = LINE
        self._baseline.points = (
            self.x,
            self.y + baseline_y,
            self.x + width,
            self.y + baseline_y,
        )
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        for index, (day, value) in enumerate(self.data):
            centre = slot * index + slot / 2
            bar_height = 0 if value <= 0 else max(dp(6), chart_height * value / max_value)
            bar_color, bar = self._bars[index]
            if value <= 0:
                bar_color.rgba = [0, 0, 0, 0]
            elif index == 6:
                bar_color.rgba = INDIGO
            else:
                bar_color.rgba = [0.66, 0.7, 1.0, 1.0]
            bar.pos = (self.x + centre - bar_width / 2, self.y + baseline_y)
            bar.size = (bar_width, max(dp(3), bar_height))
            bar.radius = [dp(6)] * 4
            try:
                weekday = _dt.date.fromisoformat(day).weekday()
                day_name = "日" if weekday == 6 else weekday_names[weekday]
            except ValueError:
                day_name = ""
            label = self._labels[index]
            label.text = f"{day_name}\n{value}" if value else day_name
            label.size_hint = (None, None)
            label.size = (slot, dp(40))
            label.pos = (self.x + centre - slot / 2, self.y)
            label.text_size = (slot, dp(40))


class ConfirmDialog(ModalView):
    def __init__(self, title: str, body: str, on_confirm, confirm_text: str = "确定", danger: bool = False, **kwargs):
        super().__init__(
            size_hint=(0.88, None),
            height=dp(222),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0.42),
            **kwargs,
        )
        card = Card(
            padding=dp(20),
            spacing=dp(10),
            radius=20,
            size_hint=(1, 1),
        )
        card.add_widget(
            Lbl(title, font_size=18, bold=True, color=INK, size_hint_y=None, height=dp(28))
        )
        card.add_widget(
            Lbl(
                body,
                font_size=13,
                color=MUTED,
                auto_height=True,
            )
        )
        card.add_widget(spacer(2))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel = PillButton(
            text="取消",
            bg_color=CREAM_DARK,
            text_color=INK,
            radius=12,
        )
        cancel.bind(on_release=lambda *_: self.dismiss())
        confirm = PillButton(
            text=confirm_text,
            bg_color=RED if danger else INDIGO,
            text_color=WHITE,
            bold=True,
            radius=12,
        )

        def _confirm(*_):
            self.dismiss()
            Clock.schedule_once(lambda *_: on_confirm(), 0.05)

        confirm.bind(on_release=_confirm)
        row.add_widget(cancel)
        row.add_widget(confirm)
        card.add_widget(row)
        self.add_widget(card)


class BaseScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        with self.canvas.before:
            self._bg_color = Color(*CREAM)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self.root = BoxLayout(orientation="vertical")
        self.add_widget(self.root)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


def tint_for(code: str):
    return LEVEL_TINTS.get(code, INDIGO_SOFT)


def star_markup(stars: int, size: int = 3) -> str:
    filled = "★" * max(0, min(size, stars))
    empty = "☆" * (size - max(0, min(size, stars)))
    if not filled:
        return f"[color=#D9DCE8]{empty}[/color]"
    return f"[color={_hex(YELLOW)}]{filled}[/color][color=#D9DCE8]{empty}[/color]"


def _hex(rgba) -> str:
    return f"#{int(rgba[0] * 255):02X}{int(rgba[1] * 255):02X}{int(rgba[2] * 255):02X}"


def stat_tile(value: str, label: str, color=INDIGO) -> Card:
    card = Card(padding=dp(13), spacing=dp(2), radius=16)
    card.add_widget(
        Lbl(value, font_size=23, bold=True, color=color, halign="center", size_hint_y=None, height=dp(34))
    )
    card.add_widget(
        Lbl(label, font_size=11, color=MUTED, halign="center", size_hint_y=None, height=dp(18))
    )
    return card


def format_seconds(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
