"""协议注册表（protocol）——多 Agent 交互协议的确定性校验（治理工件）。

protocol.md：协议是**版本化治理工件**，由人一次定义、调度器执行、协议总线机械校验
（进总线即校验）、裁决面做语义校验；改协议只能走过程进化（三重门控），不能由 agent 临场改。

本包实现三条**可机械校验**的契约（其余契约是语义校验，由裁决面负责）：

- ``envelope``  : 消息信封（四元 id + 类型 + schema 版本 + 幂等键）
- ``acl``       : 写域隔离（每个 Agent 只写自己的状态）
- ``evolution`` : 进化动作契约（因子工坊 4 类动作 + 禁止裸动作）

模块：

- ``envelope``  : 消息信封校验
- ``acl``       : 写域隔离（ACL）
- ``evolution`` : 进化动作校验
- ``registry``  : 9 契约的版本化登记（含各自校验入口）
"""

from protocol.acl import WRITE_DOMAINS, is_write_allowed
from protocol.envelope import VALID_MSG_TYPES, Envelope, validate_envelope
from protocol.evolution import VALID_ACTIONS, validate_evolution_action

__all__ = [
    "Envelope",
    "VALID_ACTIONS",
    "VALID_MSG_TYPES",
    "WRITE_DOMAINS",
    "is_write_allowed",
    "validate_envelope",
    "validate_evolution_action",
]
