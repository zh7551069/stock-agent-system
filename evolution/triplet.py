"""自进化 · 意图-经验-效用三元组（self-evolution.md §1）。

资产登记官把每次决策蒸馏成结构化资产：意图 + 经验（决策包/抓手/依据/trace_id）+ 效用
（regime/超额/t值/胜率/判决，由**判决器回填**，非模型自评）+ 溯源边。
"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Sequence


@dataclasses.dataclass(frozen=True)
class Utility:
    """效用 = 判决器用真实结果算出的，不是模型自评。"""

    regime: tuple[str, ...]      # regime 标签（如「涨停家数<30」「大盘beta高」）
    excess: float                # 独立日超额（剔 beta）
    tstat: float                 # 配对 t
    win_rate: float              # 分层胜率
    verdict: str                 # 'rejected' / 'accepted' / 'unknown'


@dataclasses.dataclass(frozen=True)
class Experience:
    """经验 = 完整轨迹。"""

    decision_pack: Mapping        # 决策包（信号/进场/出场/仓位）
    grips: tuple[str, ...]        # 抓手（factor_id / caliber_id / knowledge_card_id）
    bases: tuple[str, ...]        # 依据
    trace_id: str                 # 四元 id 贯穿


@dataclasses.dataclass(frozen=True)
class Triplet:
    """意图-经验-效用三元组（记忆视图，供效用检索）。"""

    intent: str                   # strategy_gen / market_turn / risk_reduce …
    experience: Experience
    utility: Utility
    provenance: tuple[str, ...]   # 溯源边（factor:… / calib:… / skill:… / prompt:…）
