"""知识馆长 · 知识库（去重 + 查询 + 降级）。

- 去重：同结论（归一化后）只保留一张卡。
- 降级：被证伪 → status=refuted 且证据等级回落「待考证」。
- 查询：按证据等级 / regime 适用切片。
"""

from __future__ import annotations

from typing import Optional

from knowledge.card import KnowledgeCard


class KnowledgeStore:
    """知识库（内存版；持久化由知识馆长接入时做）。"""

    def __init__(self) -> None:
        self._cards: dict[str, KnowledgeCard] = {}
        self._by_conclusion: dict[str, str] = {}  # 归一结论 -> card_id

    @staticmethod
    def _key(conclusion: str) -> str:
        return "".join(conclusion.split()).lower()

    def add(self, card: KnowledgeCard) -> str:
        """去重入库：同结论已存在则返回已有 ``card_id``，否则新增并返回新 ``card_id``。"""
        k = self._key(card.conclusion)
        if k in self._by_conclusion:
            return self._by_conclusion[k]
        self._cards[card.card_id] = card
        self._by_conclusion[k] = card.card_id
        return card.card_id

    def get(self, card_id: str) -> Optional[KnowledgeCard]:
        return self._cards.get(card_id)

    def refute(self, card_id: str, version: str) -> KnowledgeCard:
        """被证伪 → ``status=refuted`` 且证据等级降为「待考证」。"""
        c = self._cards[card_id]
        c2 = KnowledgeCard(
            card_id=c.card_id,
            conclusion=c.conclusion,
            evidence_grade="待考证",
            source=c.source,
            regime_scope=c.regime_scope,
            version=version,
            status="refuted",
        )
        self._cards[card_id] = c2
        return c2

    def by_grade(self, grade: str) -> tuple[KnowledgeCard, ...]:
        return tuple(c for c in self._cards.values() if c.evidence_grade == grade)

    def by_regime(self, regime: str) -> tuple[KnowledgeCard, ...]:
        return tuple(c for c in self._cards.values() if regime in (c.regime_scope or ""))

    def __len__(self) -> int:
        return len(self._cards)
