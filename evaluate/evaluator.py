"""评测平台 · 评估器（三要素 + 多阶段降本）。

evaluator.md §2：评估器 = 证据（只取必要 span）+ 边界（bad/good/待复核）+ 判定（规则 0 LLM
/ LLM 精判）。§5 多阶段降本：先规则粗筛（0 LLM），只有规则判不了的「异常」才上 LLM 精判。

本模块只落**规则评估器**与**多阶段判定**的确定性骨架；LLM 精判是语义部分，由会话评估官接
模型实现（这里以可注入的 ``llm_judge`` 占位）。
"""

from __future__ import annotations

import dataclasses
from typing import Callable, Mapping, Optional, Sequence

#: 判定三态。
VERDICT_BAD = "bad"
VERDICT_GOOD = "good"
VERDICT_REVIEW = "待复核"


@dataclasses.dataclass(frozen=True)
class RuleEvaluator:
    """规则评估器（0 LLM，能规则就用规则）。"""

    name: str
    rule: Callable[[Mapping], str]     # 输入证据 span → 'bad' / 'good' / '待复核'


def staged_judge(
    rules: Sequence[RuleEvaluator],
    evidence: Mapping,
    *,
    llm_judge: Optional[Callable[[Mapping], str]] = None,
) -> tuple[str, str]:
    """多阶段判定：规则粗筛能判（bad/good）就返回，判不了才上 LLM 精判。

    返回 ``(判定, 来源)``——来源是命中的规则名或 'llm' / '待复核'。
    """
    for r in rules:
        v = r.rule(evidence)
        if v in (VERDICT_BAD, VERDICT_GOOD):
            return v, r.name
    if llm_judge is not None:
        return llm_judge(evidence), "llm"
    return VERDICT_REVIEW, "待复核"
