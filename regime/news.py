"""regime · 消息面强度打标（语义维度，框架骨架）。

eval-dataset 6.2：消息面强度 = 当日消息/公告，语义打标（EMBEDDING + LLM）→ ``无/弱/强``。
确定性侧只做「框架 + 聚合」：单条消息的语义分类由外部 LLM（可注入）完成，本模块把
「逐消息分类」聚合成「当日消息面强度」；低置信标「待考证」，不参与分层。

这是 15 项里唯一被 LLM 卡住的维度——本模块把框架立起来，外部接 embedding+LLM 分类器即可跑。
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict
from typing import Callable, Sequence

#: 消息面三态 + 待考证（按强度升序）。
NEWS_LEVELS = ("无", "弱", "强", "待考证")


@dataclasses.dataclass(frozen=True)
class NewsItem:
    """一条消息/公告。"""

    date: str
    source: str
    content: str


#: 单条消息分类器：content → '无'/'弱'/'强'/'待考证'（外部 LLM/embedding 实现）。
Classifier = Callable[[str], str]


def classify_news(items: Sequence[NewsItem], classifier: Classifier) -> dict[str, str]:
    """逐条分类 → 当日聚合（取当日最强级别；无有效分类则「待考证」）。

    聚合规则：``强 > 弱 > 无``；「待考证」不计入（低置信不参与分层）。
    """
    by_day: dict[str, list[NewsItem]] = defaultdict(list)
    for it in items:
        by_day[it.date].append(it)

    out: dict[str, str] = {}
    for d, its in by_day.items():
        levels = [classifier(it.content) for it in its]
        known = [l for l in levels if l in ("无", "弱", "强")]
        if not known:
            out[d] = "待考证"
        else:
            out[d] = max(known, key=lambda l: ("无", "弱", "强").index(l))
    return out
