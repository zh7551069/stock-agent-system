"""知识馆长 · 知识卡（证据分级）。

agent-prompts #11 的「知识卡 JSON」：card_id、结论、证据等级、出处、regime 适用、版本。
铁律：没有出处的知识只记不采信（证据等级只能「待考证」）；被证伪/口径变更立即降级。
"""

from __future__ import annotations

import dataclasses
from typing import Optional

#: 证据等级枚举。
VALID_GRADES = frozenset({"A", "B", "C", "待考证"})

#: 知识卡状态。
VALID_STATUS = frozenset({"active", "refuted", "superseded"})


@dataclasses.dataclass(frozen=True)
class KnowledgeCard:
    """一张知识卡（frozen 值对象，覆盖不改写，改走新版）。"""

    card_id: str
    conclusion: str
    evidence_grade: str        # 'A' / 'B' / 'C' / '待考证'
    source: Optional[str]      # 出处（书 / 报告 / 回测）
    regime_scope: Optional[str]  # 适用 regime（如「涨停家数<30」）
    version: str
    status: str = "active"     # active / refuted / superseded


def new_card(
    card_id: str,
    conclusion: str,
    *,
    source: Optional[str] = None,
    evidence_grade: Optional[str] = None,
    regime_scope: Optional[str] = None,
    version: str = "v1",
) -> KnowledgeCard:
    """构造知识卡。

    - 无出处却标 A/B/C → 拒绝（只记不采信，须标「待考证」）。
    - 未给等级 → 默认「待考证」（证据不足）。
    """
    if not source and evidence_grade in ("A", "B", "C"):
        raise ValueError("无出处的知识卡不得给 A/B/C 证据等级（只记不采信，标「待考证」）")
    grade = evidence_grade or "待考证"
    if grade not in VALID_GRADES:
        raise ValueError(f"证据等级非法: {grade!r}（应 ∈ {sorted(VALID_GRADES)}）")
    return KnowledgeCard(
        card_id=card_id,
        conclusion=conclusion,
        evidence_grade=grade,
        source=source,
        regime_scope=regime_scope,
        version=version,
    )
