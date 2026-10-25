"""数据管家（custodian）——数据维护的 agent 壳（确定性契约层）。

「先写确定性代码，再包 agent」：确定性核心 ``taobao_sync.py``（口径归一 + QC）已经存在，
本包补上**壳**——一份可机器校验的工具契约 + 幂等键 + 结构化 JSON 结果，让调度器/能力管家
能按契约调用、幂等、做契约测试。

设计原则：

1. **契约先行**：一个「能力」= 入参/出参 schema + 幂等键 + 副作用 + 超时，能力管家据此
   做契约测试与晋级/回滚（见 agent-prompts.md #12）。
2. **物理隔离**：本包不 import ``taobao_sync``（sync 函数经依赖注入传入），保持可测、
   可替换。
3. **唯一入口**：数据管家提示词（agent-prompts.md #10）规定「同步固定走 taobao_sync skill」，
   本包的 ``run_sync`` 即该 skill 的规范调用面。

模块：

- ``contract``   : 工具契约（ToolContract）+ taobao_sync 的契约定义
- ``sync_tool``  : 幂等键 + 同步工具壳（run_sync → SyncResult）
"""

from custodian.contract import SYNC_TOOL, ToolContract
from custodian.sync_tool import SyncResult, make_idempotency_key, run_sync

__all__ = [
    "SYNC_TOOL",
    "SyncResult",
    "ToolContract",
    "make_idempotency_key",
    "run_sync",
]
