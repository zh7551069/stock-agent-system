"""决策面 · 主控任务清单（agent-prompts #1）。

主控只规划整合、不落库：把意图拆成任务清单，每项含 task_id、目标、派发面、依赖、预期产物，
交给调度器执行。任务清单用 JSON（含 task_id、目标、派发面、依赖、预期产物）。
"""

from __future__ import annotations

import dataclasses
from typing import Sequence

#: 派发面（门面 + 三面）。
FACETS = frozenset({"门面", "决策面", "裁决面", "平台面"})


@dataclasses.dataclass(frozen=True)
class Task:
    """主控任务清单的一项。"""

    task_id: str
    goal: str
    facet: str                      # 派发面：门面 / 决策面 / 裁决面 / 平台面
    depends_on: tuple[str, ...]     # 依赖的任务 id（拓扑序）
    deliverable: str                # 预期产物


def validate_task(t: Task) -> list[str]:
    """返回违规列表；空 = 合法。"""
    v: list[str] = []
    if not t.task_id:
        v.append("task_id 缺失")
    if not t.goal:
        v.append("goal 缺失")
    if t.facet not in FACETS:
        v.append(f"facet 非法: {t.facet!r}（应 ∈ {sorted(FACETS)}）")
    if not t.deliverable:
        v.append("deliverable 缺失")
    return v
