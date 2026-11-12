"""Vertical (column) arithmetic view with one tappable cell per answer digit."""

from __future__ import annotations

from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from app.engine.vertical import VerticalProblem
from app.theme import INDIGO, INDIGO_SOFT, INK, LINE, WHITE
from app.ui.widgets.common import Lbl


class _DigitCell(Lbl, ButtonBehavior):
    """An answer cell: tap to select, type a digit to fill it."""

    selected = BooleanProperty(False)

    def __init__(self, index: int, on_select, **kwargs):
        kwargs.setdefault("font_size", 33)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("color", INK)
        super().__init__(text="", **kwargs)
        self.index = index
        self._on_select = on_select
        with self.canvas.before:
            self._fill_color = Color(*WHITE)
            self._fill = RoundedRectangle(radius=[dp(9)] * 4)
            self._border_color = Color(*LINE)
            self._border = Line(width=1)
        self.bind(pos=self._sync, size=self._sync, selected=self._sync_style)
        self._sync()
        self._sync_style()

    def _sync(self, *_):
        radius = [dp(9)] * 4
        self._fill.pos = self.pos
        self._fill.size = self.size
        self._fill.radius = radius
        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(9),
        )

    def _sync_style(self, *_):
        self._fill_color.rgba = INDIGO_SOFT if self.selected else WHITE
        self._border_color.rgba = INDIGO if self.selected else LINE

    def on_release(self):
        self._on_select(self.index)


class _RuleLine(Widget):
    """The horizontal line between the operands and the answer."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(*INK)
            self._line = Line(width=dp(2))
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_):
        y = self.center_y
        self._line.points = (self.x, y, self.right, y)


class VerticalProblemView(BoxLayout):
    """Display ``27 + 45`` with a two-cell answer row, right-aligned.

    The answer is typed digit by digit from the ones place (right) towards the
    left.  Tapping any cell selects it, so a child can also go back and fix a
    single digit without clearing the whole answer.
    """

    def __init__(self, problem: VerticalProblem, on_change=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", 0)
        super().__init__(**kwargs)
        self.problem = problem
        self.on_change = on_change
        self.places = problem.places
        self.cells = [""] * problem.answer_places
        self.selected = len(self.cells) - 1
        self.locked = False

        self._cell_width = dp(48)
        self._operator_width = dp(44)
        self._row_height = dp(54)
        self._gap = dp(2)

        self.add_widget(Widget())  # top spacer keeps the sum centred

        column_width = self._operator_width + self.places * (
            self._cell_width + self._gap
        )
        column_height = self._row_height * 3 + dp(10) + self._gap * 3
        center = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint_y=None,
            height=column_height,
        )
        column = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=column_width,
            spacing=self._gap,
        )
        column.add_widget(self._operand_row(problem.left, ""))
        column.add_widget(self._operand_row(problem.right, problem.operator))
        column.add_widget(self._rule_row())
        column.add_widget(self._answer_row())
        center.add_widget(column)
        self.add_widget(center)
        self.add_widget(Widget())  # bottom spacer
        self._refresh(callback=False)

    # -- layout ----------------------------------------------------------
    def _operand_row(self, digits: str, operator: str) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=self._row_height,
            spacing=self._gap,
        )
        row.add_widget(
            Lbl(
                operator,
                font_size=31,
                bold=True,
                halign="center",
                size_hint=(None, 1),
                width=self._operator_width,
            )
        )
        for char in digits.rjust(self.places):
            row.add_widget(
                Lbl(
                    char if char != " " else "",
                    font_size=34,
                    bold=True,
                    halign="center",
                    size_hint=(None, 1),
                    width=self._cell_width,
                )
            )
        return row

    def _rule_row(self) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(10),
            spacing=self._gap,
        )
        row.add_widget(Widget(size_hint=(None, 1), width=self._operator_width))
        row.add_widget(_RuleLine())
        return row

    def _answer_row(self) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=self._row_height,
            spacing=self._gap,
        )
        row.add_widget(Widget(size_hint=(None, 1), width=self._operator_width))
        for _ in range(self.places - len(self.cells)):
            row.add_widget(Widget(size_hint=(None, 1), width=self._cell_width))
        self._cell_widgets = []
        for index in range(len(self.cells)):
            cell = _DigitCell(
                index,
                self._select,
                size_hint=(None, 1),
                width=self._cell_width,
            )
            self._cell_widgets.append(cell)
            row.add_widget(cell)
        return row

    # -- interaction -----------------------------------------------------
    def _select(self, index: int):
        if self.locked:
            return
        self.selected = index
        self._refresh()

    def input_digit(self, digit: str):
        if self.locked or len(digit) != 1 or not digit.isdigit():
            return
        self.cells[self.selected] = digit
        target = self.selected - 1
        while target >= 0 and self.cells[target]:
            target -= 1
        if target >= 0:
            self.selected = target
        self._refresh()

    def backspace(self):
        if self.locked:
            return
        if self.cells[self.selected]:
            self.cells[self.selected] = ""
        else:
            target = self.selected + 1
            while target < len(self.cells) and not self.cells[target]:
                target += 1
            if target < len(self.cells):
                self.selected = target
                self.cells[target] = ""
        self._refresh()

    def clear(self):
        if self.locked:
            return
        self.cells = [""] * len(self.cells)
        self.selected = len(self.cells) - 1
        self._refresh()

    @property
    def filled(self) -> int:
        return sum(1 for cell in self.cells if cell)

    @property
    def is_complete(self) -> bool:
        return all(self.cells)

    @property
    def value(self) -> str:
        """The assembled answer, or ``""`` while any cell is still empty."""
        return "".join(self.cells) if self.is_complete else ""

    def _refresh(self, callback: bool = True):
        for cell in self._cell_widgets:
            cell.text = self.cells[cell.index]
            cell.selected = cell.index == self.selected
        if callback and self.on_change is not None:
            self.on_change()
