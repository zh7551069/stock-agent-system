"""能力管家 · 能力注册表（工具/Skill 注册 + 状态）。

记录每个能力的契约与状态（registered → promoted / rollback），调度器据此决定
「可调用清单」（只有 promoted 的进清单，对应 agent-prompts #12「契约测试不过，工具
不得进入调度器的可调用清单」）。落库/持久化由能力管家接入时做，这里是确定性内存版。
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from custodian.contract import ToolContract

#: 状态枚举语义。
STATUS_REGISTERED = "registered"
STATUS_PROMOTED = "promoted"
STATUS_ROLLBACK = "rollback"


@dataclasses.dataclass(frozen=True)
class RegistryEntry:
    """能力注册表条目。"""

    contract: ToolContract
    status: str                       # registered / promoted / rollback
    tested_version: Optional[str] = None


class CapabilityRegistry:
    """能力注册表（内存版）。"""

    def __init__(self) -> None:
        self._entries: dict[str, RegistryEntry] = {}

    def register(self, contract: ToolContract) -> None:
        self._entries[contract.id] = RegistryEntry(contract=contract, status=STATUS_REGISTERED)

    def get(self, tool_id: str) -> Optional[RegistryEntry]:
        return self._entries.get(tool_id)

    def set_status(self, tool_id: str, status: str, tested_version: str) -> None:
        e = self._entries[tool_id]
        self._entries[tool_id] = RegistryEntry(contract=e.contract, status=status, tested_version=tested_version)

    def promoted(self, tool_id: str) -> bool:
        e = self._entries.get(tool_id)
        return e is not None and e.status == STATUS_PROMOTED

    def list(self) -> tuple[RegistryEntry, ...]:
        return tuple(self._entries.values())
