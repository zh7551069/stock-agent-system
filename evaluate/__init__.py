"""评测平台（evaluate）——评估器 + 发布门禁的确定性核心。

P3 评测平台 = 采集 / 评测 / 反馈三层；本包落**评测层**的评估器与**反馈层**的三重门控：

- ``evaluator``   : 评估器三要素（证据/边界/判定）+ 多阶段降本（规则粗筛 → LLM 精判）
- ``triple_gate`` : 三重门控（增益/遗忘/安全）→ 发布/回滚

对应 evaluator.md §2/§5 与 self-evolution.md §5。
"""

from evaluate.evaluator import VERDICT_BAD, VERDICT_GOOD, VERDICT_REVIEW, RuleEvaluator, staged_judge
from evaluate.triple_gate import GateResult, triple_gate

__all__ = [
    "GateResult",
    "RuleEvaluator",
    "VERDICT_BAD",
    "VERDICT_GOOD",
    "VERDICT_REVIEW",
    "staged_judge",
    "triple_gate",
]
