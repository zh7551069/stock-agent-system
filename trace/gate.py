"""Trace 总线 · 前缀白名单门禁（三层语义的机械断言）。

「未经严谨考证的数据不用于决策」在采集层的落点：
上报属性必须落在 ``trace.*`` / ``trad.*`` / ``a股.*`` 之下，否则直接拒绝，
进不了判决器 / 对账官 / 评估器。

- 硬门禁（默认）：键必须以下列三前缀之一开头。
- 严格模式（``strict=True``）：额外要求键在已知注册表内（防拼写漂移，如 ``trad.sigNal``）。
"""

from __future__ import annotations

from typing import Mapping

from trace.model import THREE_LAYER_PREFIXES, AttrValue


class GateError(ValueError):
    """前缀门禁拒绝异常：属性键不符合三层语义约定。"""


#: 三层已知属性注册表（文档 + strict 模式校验用，对齐 observability.md 三层语义表）。
#: L1 通用 · L2 交易域 · L3 口径。
KNOWN_ATTRS: dict[str, frozenset[str]] = {
    "trace.": frozenset({
        "trace.turn", "trace.model", "trace.tool", "trace.latency_ms",
        "trace.token_count", "trace.error", "trace.prompt_version", "trace.skill_version",
    }),
    "trad.": frozenset({
        "trad.decision_id", "trad.strategy_id", "trad.factor_id", "trad.signal",
        "trad.entry", "trad.exit", "trad.position", "trad.risk", "trad.verdict",
        "trad.excess", "trad.tstat", "trad.regime", "trad.provenance",
    }),
    "a股.": frozenset({
        "a股.adjust", "a股.code", "a股.unit", "a股.date", "a股.market",
        "a股.limit_up", "a股.limit_down", "a股.turnover", "a股.board",
        "a股.amount", "a股.volume", "a股.pct_chg", "a股.hfq_close",
    }),
}


def validate_attrs(attrs: Mapping[str, AttrValue], *, strict: bool = False) -> None:
    """校验 span 属性；非法键抛 :class:`GateError`。

    - 硬门禁：键必须以 ``trace.*`` / ``trad.*`` / ``a股.*`` 开头（任一层）。
    - ``strict``：额外要求键在 :data:`KNOWN_ATTRS` 注册表内。
    """
    for key in attrs:
        if not key.startswith(THREE_LAYER_PREFIXES):
            raise GateError(
                f"非法属性键 {key!r}：必须落在 "
                f"{'/'.join(THREE_LAYER_PREFIXES)} 前缀之下（三层语义门禁）"
            )
        if strict:
            layer = key.split(".", 1)[0] + "."
            if key not in KNOWN_ATTRS[layer]:
                raise GateError(f"未知属性键 {key!r}（strict 模式）：不在 {layer} 注册表内")
