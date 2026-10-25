"""对账官 · 对账结论 + 归因结论 + 回滚信号（确定性核心）。

输入用**已算好的数值**注入（excess_net / tstat 来自判决器），本模块只做：
判定（rejected/accepted/unknown）→ 信用传播归因 → 回滚信号。
"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Optional, Sequence

from reconcile.graph import ProvenanceGraph


@dataclasses.dataclass(frozen=True)
class Reconciliation:
    """一次对账的可追溯结论。"""

    decision_id: str
    verdict: str                    # 'rejected' | 'accepted' | 'unknown'
    excess_net: Optional[float]     # 剔 beta 净超额（判决器回填）
    tstat: Optional[float]          # 配对 t（判决器回填）
    blame: Mapping[str, float]      # 节点 → 信用（rejected 时才非空，已降序）
    rollback: Sequence[str]         # 信用超阈值的节点 = 回滚信号（降序）


def reconcile(
    decision_id: str,
    excess_net: Optional[float],
    tstat: Optional[float],
    graph: ProvenanceGraph,
    *,
    sig_t: float = 2.0,             # |t| 显著阈值
    blame: float = 1.0,
    decay: float = 0.5,
    rollback_threshold: float = 0.25,
) -> Reconciliation:
    """对账 + 归因。

    - ``tstat <= -sig_t`` → rejected（显著坏）→ 沿溯源图传播 blame，产出回滚信号。
    - ``tstat >= +sig_t`` → accepted（显著好）。
    - 其余（含 None）→ unknown（证据不足，不下结论）。
    """
    verdict = "unknown"
    if excess_net is not None and tstat is not None:
        if tstat <= -sig_t:
            verdict = "rejected"
        elif tstat >= sig_t:
            verdict = "accepted"

    blame_map: dict[str, float] = {}
    if verdict == "rejected":
        blame_map = graph.credit_propagate(decision_id, blame=blame, decay=decay)

    # 降序排列（信用高 = 最该背锅）
    sorted_blame = dict(sorted(blame_map.items(), key=lambda kv: kv[1], reverse=True))
    rollback = [n for n, c in sorted_blame.items() if c >= rollback_threshold]

    return Reconciliation(
        decision_id=decision_id,
        verdict=verdict,
        excess_net=excess_net,
        tstat=tstat,
        blame=sorted_blame,
        rollback=tuple(rollback),
    )
