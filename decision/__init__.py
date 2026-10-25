"""决策面（decision）——P2 决策面各 Agent 的数据契约（确定性部分）。

P2 六个 LLM agent 里，「先写确定性代码」可落的部分是它们的**数据契约**（JSON Schema + 校验），
让策略师 proposal 能被回测判决官直接消费、主控任务清单能被调度器路由、因子工坊动作能被影子回放前校验。

模块：

- ``pack`` : 决策包契约（信号/进场/出场/仓位/风控门/抓手/依据）
- ``task`` : 主控任务清单（task_id/目标/派发面/依赖/预期产物）
"""

from decision.pack import DecisionPack, validate_pack
from decision.task import FACETS, Task, validate_task

__all__ = [
    "DecisionPack",
    "FACETS",
    "Task",
    "validate_pack",
    "validate_task",
]
