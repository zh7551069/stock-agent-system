"""知识馆长（knowledge）——知识卡 + 证据分级 + 去重 + 降级（确定性核心）。

agent-prompts #11：知识馆长维护知识库，每条知识卡带「结论、证据等级（A/B/C）、出处
（书/报告/回测）、版本」；铁律：没有出处的知识只记不采信、证据不足标「待考证」；
被证伪或口径变更立即标注并降级。

本包是它的确定性核心——知识卡的值对象 + 知识库的去重/分级/降级操作。
（争议异源裁定用 GLM 交叉，是语义部分，不在本包。）

模块：

- ``card``  : 知识卡（KnowledgeCard）+ 构造约束（无出处不得标 A/B/C）
- ``store`` : 知识库（去重 / 查询 / 降级）
"""

from knowledge.card import VALID_GRADES, VALID_STATUS, KnowledgeCard, new_card
from knowledge.store import KnowledgeStore

__all__ = [
    "KnowledgeCard",
    "KnowledgeStore",
    "VALID_GRADES",
    "VALID_STATUS",
    "new_card",
]
