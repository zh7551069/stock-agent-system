"""评测平台 · 三重门控（增益 / 遗忘 / 安全）——过程进化的发布门禁。

self-evolution.md §5：只发布「被验证」的能力；未通过则回滚到上一版。

| 门控 | 判据 |
| --- | --- |
| 增益 | 过程 badcase 率下降，且达到最小效应量 |
| 遗忘 | 问题回归集全过；已修复问题不复发；其他评估器不退化 |
| 安全 | A 股规则合规：无越权；无口径违规 |
"""

from __future__ import annotations

import dataclasses
from typing import Sequence


@dataclasses.dataclass(frozen=True)
class GateResult:
    """三重门控结果。"""

    gain_ok: bool
    forget_ok: bool
    safety_ok: bool
    reasons: tuple[str, ...] = ()       # 未通过的理由

    @property
    def passed(self) -> bool:
        return self.gain_ok and self.forget_ok and self.safety_ok

    @property
    def decision(self) -> str:
        return "promote" if self.passed else "rollback"


def triple_gate(
    *,
    old_badcase_rate: float,
    new_badcase_rate: float,
    min_effect: float = 0.0,
    regression_pass: bool = True,
    recurrence: bool = False,           # 已修复问题是否复发
    degradation: bool = False,          # 其他评估器是否退化
    violations: Sequence[str] = (),     # 安全违规（越权/口径）
) -> GateResult:
    """三重门控 → 发布/回滚。"""
    reasons: list[str] = []

    gain_ok = new_badcase_rate < old_badcase_rate - min_effect
    if not gain_ok:
        reasons.append(f"增益不足：新 badcase 率 {new_badcase_rate} 未低于 {old_badcase_rate - min_effect}")

    forget_ok = regression_pass and (not recurrence) and (not degradation)
    if not forget_ok:
        reasons.append("遗忘门控未过：回归集未全过 / 已修复问题复发 / 其他评估器退化")

    safety_ok = len(violations) == 0
    if not safety_ok:
        reasons.append(f"安全门控未过：{len(violations)} 条违规（越权/口径）")

    return GateResult(gain_ok=gain_ok, forget_ok=forget_ok, safety_ok=safety_ok, reasons=tuple(reasons))
