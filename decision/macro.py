"""决策面 · 大盘分析师（大势研判 + regime 标签）。agent-prompts #5。"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Sequence


@dataclasses.dataclass(frozen=True)
class MacroView:
    """大盘分析师的一次日频研判。"""

    date: str                        # 研判日
    trend: str                       # 大势研判（趋势/区间/风险）
    rotation: tuple[str, ...]        # 板块/题材轮动（启动/退潮）
    regime: Mapping[str, str]        # regime 标签（涨停家数/beta/拥挤度/换手率）
    confidence: float                # 置信度 ∈ [0, 1]
    bases: tuple[str, ...]           # 依据引用


def validate_macro(m: MacroView) -> list[str]:
    """返回违规列表；空 = 合法。"""
    v: list[str] = []
    if not m.date:
        v.append("date 缺失")
    if not m.trend:
        v.append("trend 缺失")
    if not m.regime:
        v.append("regime 缺失（每条判断需带 regime 标签，供定向观测）")
    if not (0.0 <= m.confidence <= 1.0):
        v.append(f"confidence 越界: {m.confidence}（应 ∈ [0,1]）")
    if not m.bases:
        v.append("bases 空（结论需有依据引用）")
    return v
