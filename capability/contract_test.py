"""能力管家 · 契约测试（工具/Skill 晋级/回滚的确定性判据）。

一个契约用例 = 给工具一组入参，断言输出至少含某组键、或按预期抛某异常。
一组用例全过 → 晋级（promote），任一失败 → 回滚（rollback）。
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Mapping, Sequence, Type


@dataclasses.dataclass(frozen=True)
class ContractCase:
    """一个契约测试用例（正例或反例）。"""

    name: str
    inputs: Mapping[str, Any]                          # 工具入参（kwargs）
    expect_keys: Sequence[str] = ()                    # 期望输出至少含这些键（正例）
    expect_error: Type[BaseException] | None = None    # 期望抛出的异常类型（反例）


@dataclasses.dataclass(frozen=True)
class ContractTestResult:
    """契约测试结果 + 晋级/回滚判定。"""

    tool_id: str
    version: str
    passed: bool
    failures: tuple[str, ...]

    @property
    def decision(self) -> str:
        return "promote" if self.passed else "rollback"


def run_contract_test(
    tool_id: str,
    version: str,
    tool_fn: Callable[..., Any],
    cases: Sequence[ContractCase],
) -> ContractTestResult:
    """跑契约用例；全过 → ``passed=True``，任一失败 → 记录失败原因。"""
    failures: list[str] = []
    for c in cases:
        try:
            out = tool_fn(**c.inputs)
        except Exception as e:  # noqa: BLE001 —— 反例可能抛任意异常，按类型判定
            if c.expect_error is not None and isinstance(e, c.expect_error):
                continue  # 按预期抛错 = 通过
            failures.append(f"{c.name}: 意外异常 {type(e).__name__}: {e}")
            continue
        if c.expect_error is not None:
            failures.append(f"{c.name}: 期望抛 {c.expect_error.__name__} 但未抛")
            continue
        missing = [k for k in c.expect_keys if k not in out]
        if missing:
            failures.append(f"{c.name}: 输出缺键 {missing}")
    return ContractTestResult(tool_id=tool_id, version=version, passed=not failures, failures=tuple(failures))
