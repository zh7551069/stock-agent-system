"""评测集设计 · 覆盖率 + 优先级（eval-dataset 6.2 的元规则，确定性实现）。

- 覆盖率 4 维度：能力（策略/因子/大盘/盘中）× 场景（涨停/暴跌/横盘/轮动）× 难度
  （简单/复杂/边界）× 目标（效果/安全/成本/稳定性）——评测集要贴合线上分布。
- 优先级 = 业务频率 × 失败损失：P0 核心高风险 → P1 高频 → P2 长尾 → P3 探索。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

#: 覆盖率四维度取值（eval-dataset 6.2）。
CAPABILITIES = ("策略", "因子", "大盘", "盘中")
SCENARIOS = ("涨停", "暴跌", "横盘", "轮动")
DIFFICULTIES = ("简单", "复杂", "边界")
GOALS = ("效果", "安全", "成本", "稳定性")

DIMENSIONS = {
    "能力": CAPABILITIES,
    "场景": SCENARIOS,
    "难度": DIFFICULTIES,
    "目标": GOALS,
}

#: 优先级分桶阈值（业务频率 × 失败损失；占位，待业务数据标定）。
PRIORITY_THRESHOLDS = (10.0, 1.0, 0.1)  # >=10→P0, >=1→P1, >=0.1→P2, else P3


def priority_score(freq: float, loss: float) -> float:
    """优先级 = 业务频率 × 失败损失（eval-dataset 6.2）。"""
    return freq * loss


def priority_bucket(score: float, thresholds: Sequence[float] = PRIORITY_THRESHOLDS) -> str:
    """分数 → P0/P1/P2/P3（按阈值降序匹配）。"""
    for i, t in enumerate(thresholds):
        if score >= t:
            return f"P{i}"
    return f"P{len(thresholds)}"


def coverage(cases: Sequence[Mapping]) -> dict[str, dict[str, int]]:
    """四维覆盖计数：``{维度: {取值: 计数}}``。"""
    out: dict[str, dict[str, int]] = {dim: defaultdict(int) for dim in DIMENSIONS}
    for c in cases:
        for dim in DIMENSIONS:
            v = c.get(dim)
            if v:
                out[dim][v] += 1
    return {dim: dict(cnt) for dim, cnt in out.items()}


def coverage_gaps(cases: Sequence[Mapping]) -> dict[str, list[str]]:
    """找出四维中未被任何 case 覆盖的取值（供补齐合成样本）。"""
    cov = coverage(cases)
    return {
        dim: [v for v in DIMENSIONS[dim] if cov[dim].get(v, 0) == 0]
        for dim in DIMENSIONS
    }
