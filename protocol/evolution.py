"""协议注册表 · 进化动作契约（因子工坊 4 类动作 + 禁止裸动作）。

protocol.md + self-evolution.md §1：4 类动作（add/remove_factor、edit_factor_definition、
tune_factor_params、reweight_factors），且**每个动作必须附归因证据 id**（禁止笼统「改因子」）。

注：tune_factor_params 的「前视防护」靠合法搜索区间校验，而搜索区间是**因子定义**的属性
（agent-prompts #4「公式 + 参数 + 合法搜索区间」），故由因子层（decision.factor.FactorDict.apply）
用因子声明的区间校验，不在本协议层重复要求动作携带区间。
"""

from __future__ import annotations

from typing import Any, Mapping

#: 4 类合法动作。
VALID_ACTIONS = frozenset({
    "add_factor",
    "remove_factor",
    "edit_factor_definition",
    "tune_factor_params",
    "reweight_factors",
})


def validate_evolution_action(action: Mapping[str, Any]) -> list[str]:
    """返回违规列表；空 = 合法。"""
    violations: list[str] = []
    t = action.get("type")
    if t not in VALID_ACTIONS:
        violations.append(f"type 非法: {t!r}（应 ∈ {sorted(VALID_ACTIONS)}）")
    if not action.get("evidence_id"):
        violations.append("缺 evidence_id（禁止裸动作：每个动作必须附归因证据 id）")
    return violations
