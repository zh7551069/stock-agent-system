"""决策面 · 因子工坊（因子字典 + 4 类动作落库）。

agent-prompts #4 + self-evolution.md §1：因子字典条目 = factor_id/定义/参数/口径/来源/版本；
4 类动作 = add/remove_factor、edit_factor_definition、tune_factor_params、reweight_factors，
每个动作必须带归因证据 id（protocol.validate_evolution_action 校验）。
硬约束：tune 必须给合法搜索区间（前视防护），reweight 权重必须归一化。
"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Optional


@dataclasses.dataclass(frozen=True)
class Factor:
    """因子字典条目（最小可验证单元）。"""

    factor_id: str
    name: str
    definition: str                                    # 公式（表达 alpha 逻辑）
    params: Mapping[str, float]                        # 参数（window/threshold…）
    search_interval: Optional[Mapping[str, tuple[float, float]]] = None  # 参数合法搜索区间
    caliber: str = "前复权"                             # 口径绑定
    source: Optional[str] = None                       # 来源
    version: str = "v1"


def _bump(version: str) -> str:
    return f"{version}.1"


class FactorDict:
    """因子字典（Schema 注册表）。"""

    def __init__(self) -> None:
        self._factors: dict[str, Factor] = {}
        self._weights: dict[str, float] = {}            # 组合权重（reweight_factors 落库）

    # -- 查询 --
    def get(self, factor_id: str) -> Optional[Factor]:
        return self._factors.get(factor_id)

    def __contains__(self, factor_id: str) -> bool:
        return factor_id in self._factors

    def __len__(self) -> int:
        return len(self._factors)

    def list(self) -> tuple[Factor, ...]:
        return tuple(self._factors.values())

    def weights(self) -> dict[str, float]:
        return dict(self._weights)

    def register(self, factor: Factor) -> None:
        self._factors[factor.factor_id] = factor

    # -- 4 类动作 --
    def apply(self, action: Mapping) -> list[str]:
        """校验并应用一个进化动作；返回违规列表（空 = 已应用）。"""
        from protocol.evolution import validate_evolution_action

        errs = validate_evolution_action(action)
        if errs:
            return errs
        t = action["type"]

        if t == "add_factor":
            f = action["factor"]
            self._factors[f.factor_id] = f

        elif t == "remove_factor":
            self._factors.pop(action["factor_id"], None)

        elif t == "edit_factor_definition":
            fid = action["factor_id"]
            old = self._factors[fid]
            self._factors[fid] = Factor(
                factor_id=old.factor_id, name=old.name, definition=action["definition"],
                params=old.params, search_interval=old.search_interval,
                caliber=old.caliber, source=old.source, version=_bump(old.version),
            )

        elif t == "tune_factor_params":
            fid = action["factor_id"]
            old = self._factors[fid]
            new_params = dict(action["params"])
            for k, v in new_params.items():
                lo, hi = (old.search_interval or {}).get(k, (-float("inf"), float("inf")))
                if not (lo <= v <= hi):
                    return [f"参数 {k}={v} 超出搜索区间 [{lo}, {hi}]（前视防护）"]
            self._factors[fid] = Factor(
                factor_id=old.factor_id, name=old.name, definition=old.definition,
                params={**old.params, **new_params}, search_interval=old.search_interval,
                caliber=old.caliber, source=old.source, version=_bump(old.version),
            )

        elif t == "reweight_factors":
            weights = dict(action["weights"])
            unknown = [fid for fid in weights if fid not in self._factors]
            if unknown:
                return [f"权重引用未注册因子: {unknown}"]
            if abs(sum(weights.values()) - 1.0) > 1e-9:
                return [f"权重未归一化（和={sum(weights.values())}，应=1）"]
            self._weights = weights

        return []
