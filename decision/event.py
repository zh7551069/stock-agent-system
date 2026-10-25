"""决策面 · 盘中哨兵（事件流，只发不落库）。agent-prompts #6。"""

from __future__ import annotations

import dataclasses
from typing import Optional

#: 事件类型（涨跌停 / 异动 / 信号触发 / 风控阈值）。
EVENT_TYPES = frozenset({"limit_up_down", "anomaly", "signal", "risk_threshold"})


@dataclasses.dataclass(frozen=True)
class Event:
    """盘中哨兵触发的一条事件（只发不落库，写域 event_stream）。"""

    event_id: str
    symbol: str                     # 标的
    etype: str                      # 事件类型
    threshold: str                  # 阈值描述
    ts: str                         # 时间戳
    value: Optional[float] = None   # 触发值


def validate_event(e: Event) -> list[str]:
    """返回违规列表；空 = 合法。"""
    v: list[str] = []
    if not e.event_id:
        v.append("event_id 缺失")
    if not e.symbol:
        v.append("symbol 缺失")
    if e.etype not in EVENT_TYPES:
        v.append(f"etype 非法: {e.etype!r}（应 ∈ {sorted(EVENT_TYPES)}）")
    if not e.ts:
        v.append("ts 缺失")
    return v
