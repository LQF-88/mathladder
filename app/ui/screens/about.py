"""About screen: curriculum notes, privacy, licences and disclaimers."""

from __future__ import annotations

import os

from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from app.engine.curriculum import LEVELS, TOPIC_BY_KEY
from app.theme import ASSETS_DIR, INDIGO, INK, MUTED, WHITE
from app.ui.widgets.common import (
    BaseScreen,
    Card,
    Header,
    Lbl,
    VScroll,
)


class AboutScreen(BaseScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, name="about", **kwargs)
        self.header = Header(
            "关于",
            "MathLadder · 数学阶梯",
            back=app.close_about,
        )
        self.root.add_widget(self.header)
        self.scroll = VScroll(padding=16, spacing=12)
        self.root.add_widget(self.scroll)
        self._built = False

    def on_pre_enter(self, *args):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        box = self.scroll.box

        brand = Card(
            padding=dp(18),
            spacing=dp(5),
            radius=22,
            size_hint_y=None,
            height=dp(214),
        )
        logo_anchor = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint_y=None,
            height=dp(92),
        )
        logo_anchor.add_widget(
            Image(
                source=os.path.join(ASSETS_DIR, "icons", "icon-192.png"),
                size_hint=(None, None),
                size=(dp(84), dp(84)),
            )
        )
        brand.add_widget(logo_anchor)
        brand.add_widget(
            Lbl(
                "数学阶梯",
                font_size=22,
                bold=True,
                color=INK,
                halign="center",
                size_hint_y=None,
                height=dp(30),
            )
        )
        brand.add_widget(
            Lbl(
                f"MathLadder  ·  v{self.app.VERSION}",
                font_size=10.5,
                color=MUTED,
                halign="center",
                size_hint_y=None,
                height=dp(17),
            )
        )
        brand.add_widget(
            Lbl(
                "从数数到微积分，每天一小步。",
                font_size=12,
                color=INDIGO,
                halign="center",
                size_hint_y=None,
                height=dp(20),
            )
        )
        brand.add_widget(
            Lbl(
                f"{len(LEVELS)} 个阶段 · {len(TOPIC_BY_KEY)} 个题型 · 无限自动出题",
                font_size=9.5,
                color=MUTED,
                halign="center",
                size_hint_y=None,
                height=dp(16),
            )
        )
        box.add_widget(brand)

        box.add_widget(
            self._text_card(
                "这是什么？",
                "数学阶梯是一款完全离线的数学练习应用。它参考公文式数学 "
                "5A–L 的学习顺序安排内容：从数数、比较大小、加减乘除，到分数、"
                f"小数、代数式、方程、函数与微积分，共 {len(LEVELS)} 个阶段、"
                f"{len(TOPIC_BY_KEY)} 个题型。\n\n"
                "所有题目由程序即时生成，因此可以无限练习；答案支持整数、"
                "分数、小数和选择题。",
            )
        )
        box.add_widget(
            self._text_card(
                "怎么使用？",
                "1. 在首页选择当前阶段，也可以直接点“每日一练”。\n"
                "2. 每组可选 10、20 或 30 题，进入后专注作答。\n"
                "3. 每题提交后立刻看到正确答案与讲解。\n"
                "4. 答错的题会自动进入错题本，答对一次后移出。\n\n"
                "建议每天练习 10–20 分钟，短而稳定比一次做很多更有效。",
            )
        )
        box.add_widget(
            self._text_card(
                "数据与隐私",
                "学习进度、星级、练习记录和错题本只保存在这台设备的应用私有目录中，"
                "不会上传到任何服务器，也不需要账号。\n\n"
                "卸载应用或在设置中重置数据会永久删除这些记录。",
            )
        )
        box.add_widget(
            self._text_card(
                "版权与免责声明",
                "本应用是独立开发的学习工具，与公文式教育（KUMON）及其关联公司"
                "没有任何隶属、授权或合作关系。“KUMON”“公文式”等名称与商标归其"
                "权利人所有。\n\n"
                "应用中的题目全部由算法生成，不包含任何教材扫描页或原题复制。"
                "本应用仅用于个人学习辅助，不对学习成绩作任何保证。",
            )
        )
        box.add_widget(
            self._text_card(
                "开放源代码与字体许可",
                "应用源代码以 MIT License 发布，欢迎学习、修改和自用；"
                "发布衍生版本时请保留许可声明。\n\n"
                "界面字体为 Noto Sans SC，采用 SIL Open Font License 1.1 授权，"
                "许可原文随应用资源一并分发（assets/fonts/OFL.txt）。",
            )
        )
        box.add_widget(
            Lbl(
                "感谢使用数学阶梯，祝你每天都有新进步。",
                font_size=10.5,
                color=MUTED,
                halign="center",
                auto_height=True,
            )
        )

    def _text_card(self, title: str, body: str) -> Card:
        card = Card(
            bg_color=list(WHITE),
            padding=dp(16),
            spacing=dp(6),
            radius=18,
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(
            Lbl(
                title,
                font_size=14,
                bold=True,
                color=INK,
                size_hint_y=None,
                height=dp(24),
            )
        )
        body_box = BoxLayout(size_hint_y=None)
        body_label = Lbl(body, font_size=11.5, color=MUTED, auto_height=True)
        body_box.bind(minimum_height=body_box.setter("height"))
        body_box.add_widget(body_label)
        card.add_widget(body_box)
        return card
