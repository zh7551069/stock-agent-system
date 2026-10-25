"""对账官（reconcile）——结果归因 · 信用传播（确定性核心）。

职责：T+N 收盘后，对「决策 vs 实际结果」对账，并沿**溯源图**做多步结构归因。
这是自进化链路的枢纽（任务 7 的「结果归因」侧）——把「这条决策为什么差」定位到
「因子失效 / 口径错 / skill 过时」这些**可追溯节点**上，输出回滚信号。

设计原则：

1. **只做可验证归因**：信用传播只用于因子/策略/决策资产（可验证算子，有闭式奖励）；
   过程质量（推理/工具）交给会话评估官的评估器，本包不越界。
2. **沿依赖边，不按时间**：归因按溯源图的图距离传播（时间相邻 ≠ 因果来源）。
3. **确定性**：纯图算法，不读墙钟、不用随机；同一输入必得同一输出。
4. **物理隔离**：不 import 任何决策层模块；输入用已算好的数值（excess/tstat）注入。

模块：

- ``graph``      : 溯源图 + 信用传播（BFS 按图距离衰减）
- ``reconcile``  : 对账结论 + 归因结论 + 回滚信号
- ``wire``       : 判决器输出 → 评测库 verdict 行 + 对账结论（接线层）
- ``from_judge`` : judge 报告 JSON → JudgedSignal（上游转换）
"""

from reconcile.from_judge import DEFAULT_HORIZON, from_baseline, from_probe
from reconcile.graph import ProvenanceEdge, ProvenanceGraph
from reconcile.reconcile import Reconciliation, reconcile
from reconcile.wire import JudgedSignal, VerdictRow, WireResult, wire

__all__ = [
    "DEFAULT_HORIZON",
    "JudgedSignal",
    "ProvenanceEdge",
    "ProvenanceGraph",
    "Reconciliation",
    "VerdictRow",
    "WireResult",
    "from_baseline",
    "from_probe",
    "reconcile",
    "wire",
]
