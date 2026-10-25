"""协议注册表 · 消息信封契约（进总线即校验）。

protocol.md：消息信封 = 四元 id + 来源/目标 + 消息类型 + schema 版本 + 时间戳 + 幂等键。
协议总线机械校验，违规即告警（不静默放行）。
"""

from __future__ import annotations

import dataclasses
from typing import Optional

#: 消息类型枚举（event / command / request_response / pub_sub）。
VALID_MSG_TYPES = frozenset({"event", "command", "request_response", "pub_sub"})


@dataclasses.dataclass(frozen=True)
class Envelope:
    """一条消息的信封（协议总线校验的最小字段集）。"""

    session_id: str
    msg_type: str
    schema_version: str
    idempotency_key: str
    decision_id: Optional[str] = None
    src_agent: Optional[str] = None
    dst_agent: Optional[str] = None
    ts: Optional[str] = None


def validate_envelope(env: Envelope) -> list[str]:
    """返回违规列表；空 = 合法。"""
    violations: list[str] = []
    if not env.session_id:
        violations.append("session_id 缺失")
    if env.msg_type not in VALID_MSG_TYPES:
        violations.append(f"msg_type 非法: {env.msg_type!r}（应 ∈ {sorted(VALID_MSG_TYPES)}）")
    if not env.schema_version:
        violations.append("schema_version 缺失")
    if not env.idempotency_key:
        violations.append("idempotency_key 缺失")
    return violations
