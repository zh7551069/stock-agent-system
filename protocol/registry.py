"""协议注册表 · 9 契约的版本化登记（治理工件参考表）。

protocol.md §契约的 9 条，逐条标注「谁定义 / 谁执行 / 谁校验 / 本仓校验入口」。
机械校验项指向本包的 validator；语义校验项标注由裁决面负责、此处不机械化。
"""

from __future__ import annotations

import dataclasses
from typing import Optional, Sequence


@dataclasses.dataclass(frozen=True)
class ProtocolContract:
    """一条协议契约的登记。"""

    name: str
    version: str
    content: str                 # 内容摘要
    check: Optional[str] = None  # 本仓机械校验入口（模块.函数）；None = 语义校验/待接


#: 9 契约（对齐 protocol.md §契约）。
PROTOCOLS: Sequence[ProtocolContract] = (
    ProtocolContract("消息信封", "v1", "四元 id + 来源/目标 + 消息类型 + schema 版本 + 时间戳 + 幂等键",
                     check="protocol.envelope.validate_envelope"),
    ProtocolContract("消息类型", "v1", "event / command / request_response / pub_sub，各带优先级与超时",
                     check="protocol.envelope.validate_envelope"),
    ProtocolContract("决策包契约", "v1", "strategy proposal 与决策包是机器可读 JSON Schema", check=None),
    ProtocolContract("数据口径契约", "v1", "复权基准/单位/日期/涨跌停/T+1/板块，带 id 与版本", check=None),
    ProtocolContract("写域隔离", "v1", "每个 Agent 只写自己的状态；裁决面只读生产", check="protocol.acl.violations"),
    ProtocolContract("异步/同步", "v1", "盘中同步低延迟；盘后/回测/对账/评估异步队列", check=None),
    ProtocolContract("Trace/Span 契约", "v1", "8 类 span + 三层语义 + 前缀白名单门禁", check="trace.gate.validate_attrs"),
    ProtocolContract("评估器 DSL 契约", "v1", "判定侧只声明变量，DSL 从 span 取值", check=None),
    ProtocolContract("进化动作契约", "v1", "4 类动作 + 每动作带归因证据 id", check="protocol.evolution.validate_evolution_action"),
)
