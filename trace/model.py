"""Trace 总线 · Span 数据模型（可观测纵贯线的类型底座）。

四元 id：``session_id → decision_id → strategy_id → factor_id``，一条决策全链同串。
三层语义：``trace.*``（L1 通用）/ ``trad.*``（L2 交易域）/ ``a股.*``（L3 口径）。
前缀门禁在 :mod:`trace.gate`，本模块只定义类型与字段落点。
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Mapping, Optional

#: 三层语义前缀（顺序即 L1/L2/L3）。门禁据此判定属性合法性。
THREE_LAYER_PREFIXES: tuple[str, ...] = ("trace.", "trad.", "a股.")

#: 属性标量类型（JSON 可序列化；嵌套结构用 JSON 字符串，不做深层校验）。
AttrValue = str | int | float | bool | None


class SpanType(str, enum.Enum):
    """8 类 span（股票场景原生分类，见 overview.md「Span 类型」）。"""

    TURN = "turn"          # 回合：主控/调度器意图理解、规划、派单
    LLM = "llm"            # 模型调用：策略起草/定稿、复盘解读
    DATA = "data"          # 数据取数：行情/指标/口径取数
    TOOL = "tool"          # 工具调用：skill/工具
    RETRIEVE = "retrieve"  # 检索：知识卡/因子/历史经验
    GUARD = "guard"        # 风控校验：涨跌停/T+1/仓位/口径
    JUDGE = "judge"        # 判决：影子回放/对账/归因
    EVENT = "event"        # 事件：盘中异动/信号触发


@dataclasses.dataclass(frozen=True)
class Span:
    """一条结构化 span（frozen 值对象）。

    - ``span_type`` 必填；``decision_id`` / ``strategy_id`` / ``factor_id`` 可空
      （如纯数据取数可能无决策归属），但一旦属于某条决策，必须带 ``decision_id``。
    - ``attrs`` 是唯一放业务字段的地方，键必须通过 :func:`trace.gate.validate_attrs`
      的前缀门禁——这是「未经严谨考证的数据不用于决策」的机械断言落点。
    """

    span_id: str
    span_type: SpanType
    name: str
    session_id: str
    ts: str                                # ISO-8601 时间戳
    attrs: Mapping[str, AttrValue]         # 键必须通过前缀门禁
    decision_id: Optional[str] = None
    strategy_id: Optional[str] = None
    factor_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    def to_dict(self) -> dict:
        """规范序列化（键全集固定，供哈希链做 canonical 序列化）。"""
        return {
            "span_id": self.span_id,
            "span_type": self.span_type.value,
            "name": self.name,
            "session_id": self.session_id,
            "ts": self.ts,
            "attrs": dict(self.attrs),
            "decision_id": self.decision_id,
            "strategy_id": self.strategy_id,
            "factor_id": self.factor_id,
            "parent_span_id": self.parent_span_id,
        }
