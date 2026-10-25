"""Trace 总线（trace）——可观测纵贯线的地基。

职责：把「每个 Agent 回合产出 span」变成类型化、可落库、不可篡改的事实流。
消费方：对账官（结果归因）、会话评估官（过程评估）、评测平台（采集层）、资产登记官。

设计原则：

1. **只做事实**：span 是结构化事实，不解释、不归因（归因是消费方的职责）。
2. **三层语义强制**：属性必须落在 ``trace.*`` / ``trad.*`` / ``a股.*`` 三前缀之下（前缀门禁）。
3. **append-only**：总线只追加，用哈希链防篡改；复盘只能基于原始 trace。

模块：

- ``model`` : ``Span`` 值对象 + ``SpanType``（8 类）+ 三层属性约定
- ``gate``  : 前缀白名单门禁（机械拦截非法属性）
- ``bus``   : append-only ``TraceBus`` + 哈希链 + 链完整性校验
- ``ids``   : 四元 id（session → decision → strategy → factor）生成
"""

from trace.bus import TraceBus
from trace.gate import GateError, validate_attrs
from trace.model import THREE_LAYER_PREFIXES, AttrValue, Span, SpanType

__all__ = [
    "AttrValue",
    "GateError",
    "Span",
    "SpanType",
    "THREE_LAYER_PREFIXES",
    "TraceBus",
    "validate_attrs",
]
