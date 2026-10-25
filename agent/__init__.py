"""Agent 清单（agent）——13 个 Agent 的机器可读 roster（「再包 agent」第一步）。

把 agent-roster.md 的清单落成结构化 :class:`AgentSpec`，并把每个 Agent 绑定到：
- 写域（与 protocol.WRITE_DOMAINS 交叉校验，防漂移）
- 确定性工具（本仓已实现的包）
- 提示词出处（agent-prompts.md 章节）

这是「确定性核心 → 运行时壳」的中间层：确定性代码已立，本层把它们挂到对应 Agent。
"""

from agent.spec import AgentSpec, AGENTS, validate_roster

__all__ = ["AGENTS", "AgentSpec", "validate_roster"]
