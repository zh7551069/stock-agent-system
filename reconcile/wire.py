"""对账官 · 接线层：判决器输出 → 评测库 verdict 行 + 对账结论。

把 judge/ 的判决汇总（剔 beta 超额 / 单样本 t / 配对 t / 分层胜率）接成评测库
``verdict`` 表的一行，并复用 :func:`reconcile.reconcile` 产出归因结论与回滚信号。
这是「判决器 → 评测库 → 对账官」闭环的临门一脚。

judge/ 侧的真实汇总来自 ``judge.baseline`` / ``judge.probe`` 的 by_horizon 结构；
本模块只定义**中间表示**（:class:`JudgedSignal`）与转换，不 import judge（保持物理隔离），
上游把 JSON 汇总转成 JudgedSignal 即可。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Optional

from reconcile.graph import ProvenanceGraph
from reconcile.reconcile import Reconciliation, reconcile


@dataclasses.dataclass(frozen=True)
class JudgedSignal:
    """一个信号/决策的判决汇总（来自 judge 的 by_horizon）。

    - ``excess``      剔 beta 超额（主观察窗，如 T+20）
    - ``t_stat``      单样本 t（超额序列对 0 的 t）
    - ``paired_t``    配对 t（vs 同日随机对照）——reconcile 用它做显著性判定
    - 三者是**不同统计量**，缺一不可混用；「涨停 vs 对照」主显著性看 paired_t。
    """

    decision_id: str
    signal: str
    regime_slice: str
    excess: Optional[float] = None
    t_stat: Optional[float] = None
    paired_t: Optional[float] = None
    layered_win_rate: Optional[float] = None


@dataclasses.dataclass(frozen=True)
class VerdictRow:
    """评测库 ``verdict`` 表的一行（对齐 scripts/eval_dataset_v1.sql）。"""

    decision_id: str
    excess: Optional[float]
    t_stat: Optional[float]
    paired_t: Optional[float]
    layered_win_rate: Optional[float]
    verdict: str                      # 'rejected' / 'accepted' / 'unknown'
    regime_slice: str
    judged_at: str

    def to_dict(self) -> dict:
        """规范序列化（列名 == verdict 表列名）。"""
        return {
            "decision_id": self.decision_id,
            "excess": self.excess,
            "t_stat": self.t_stat,
            "paired_t": self.paired_t,
            "layered_win_rate": self.layered_win_rate,
            "verdict": self.verdict,
            "regime_slice": self.regime_slice,
            "judged_at": self.judged_at,
        }


@dataclasses.dataclass(frozen=True)
class WireResult:
    """接线结果：verdict 行 + 对账结论（两者 verdict 必一致）。"""

    verdict: VerdictRow
    reconciliation: Reconciliation


def wire(
    js: JudgedSignal,
    graph: ProvenanceGraph,
    *,
    sig_t: float = 2.0,
    decay: float = 0.5,
    rollback_threshold: float = 0.25,
    judged_at: Optional[str] = None,
) -> WireResult:
    """判决汇总 → verdict 行 + 对账结论。

    verdict 由 :func:`reconcile` 的阈值判定得出（保证 verdict 行与归因结论一致）；
    ``judged_at`` 是落库时间戳（生产走墙钟，测试注入固定值）。
    """
    rec = reconcile(
        js.decision_id, js.excess, js.paired_t, graph,
        sig_t=sig_t, decay=decay, rollback_threshold=rollback_threshold,
    )
    row = VerdictRow(
        decision_id=js.decision_id,
        excess=js.excess,
        t_stat=js.t_stat,
        paired_t=js.paired_t,
        layered_win_rate=js.layered_win_rate,
        verdict=rec.verdict,
        regime_slice=js.regime_slice,
        judged_at=judged_at or dt.datetime.now().isoformat(timespec="seconds"),
    )
    return WireResult(verdict=row, reconciliation=rec)
