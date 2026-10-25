"""决策面 · 决策包契约（protocol.md「决策包契约」+ agent-prompts #2/#3）。

策略师产出 machine-readable proposal，调度器组装成决策包，回测判决官**直接消费**（影子回放 +
配对检验）。字段：信号 / 进场 / 出场 / 仓位 / 风控门 / 抓手引用 / 依据。

铁律：每个抓手必须引用来源（factor_id / caliber_id / knowledge_card_id / skill_id），
禁止无抓手凭空决策（对应「未经严谨考证的数据不用于决策」）。
"""

from __future__ import annotations

import dataclasses
from typing import Sequence


@dataclasses.dataclass(frozen=True)
class DecisionPack:
    """一个机器可读的决策包（proposal 的最终态）。"""

    decision_id: str
    strategy_id: str
    signal: str                    # 触发信号
    entry: str                     # 进场规则
    exit: str                      # 出场规则（stop / TP）
    position: float                # 仓位，∈ [0, 1]
    risk: str                      # 风控门（回撤约束等）
    grips: tuple[str, ...]         # 抓手引用（factor_id / caliber_id / knowledge_card_id / skill_id）
    bases: tuple[str, ...]         # 依据（为什么这样决策）


def validate_pack(p: DecisionPack) -> list[str]:
    """返回违规列表；空 = 合法。"""
    v: list[str] = []
    if not p.decision_id:
        v.append("decision_id 缺失")
    if not p.strategy_id:
        v.append("strategy_id 缺失")
    if not p.signal:
        v.append("signal 缺失")
    if not p.entry:
        v.append("entry 缺失")
    if not p.exit:
        v.append("exit 缺失")
    if not (0.0 <= p.position <= 1.0):
        v.append(f"position 越界: {p.position}（应 ∈ [0,1]）")
    if not p.grips:
        v.append("grips 空（禁止无抓手凭空决策）")
    return v
