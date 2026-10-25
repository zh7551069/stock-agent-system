"""能力管家（capability）——工具/Skill 契约测试 + 注册表（确定性核心）。

agent-prompts #12：能力管家的职责是「工具/Skill 注册、版本、契约测试；测试通过才晋级，
未通过回滚」。本包是它的确定性核心——契约测试跑正反例，全过晋级、任一失败回滚；
注册表记录每个能力的契约与状态。

设计原则：

1. **契约测试是晋级/回滚的唯一判据**：不做裸升级（对应自进化的三重门控在过程侧）。
2. **确定性**：同一契约 + 同一工具 + 同一组用例，结果恒定。
3. **只读判断**：本包不执行副作用，只判定「过/不过」。

模块：

- ``contract_test`` : 契约用例 + 契约测试 + 晋级/回滚判定
- ``registry``      : 能力注册表（注册 / 查询 / 状态）
"""

from capability.contract_test import (
    ContractCase,
    ContractTestResult,
    run_contract_test,
)
from capability.registry import CapabilityRegistry, RegistryEntry

__all__ = [
    "CapabilityRegistry",
    "ContractCase",
    "ContractTestResult",
    "RegistryEntry",
    "run_contract_test",
]
