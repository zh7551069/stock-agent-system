"""自进化（evolution）——意图-经验-效用三元组 + 效用检索的确定性核心。

self-evolution.md §1/§3：资产登记官把决策蒸馏成「意图-经验-效用 + 溯源」三元组；策略师/
主控按当前 regime 检索历史上表现最好的经验（先找像的 → 再挑值的 → 现场验证 → 更新价值）。

本包落确定性部分：三元组值对象、效用检索（召回 + 效用重排 Top-k）、效用回填。
「现场验证」= 影子回放（依赖 judge，待接）；「更新价值」= 效用回填（判决器真实结果，非模型自评）。

模块：

- ``triplet``   : 意图-经验-效用三元组（+ provenance 溯源边）
- ``retrieval`` : 效用检索（召回 + 重排）+ 效用回填
"""

from evolution.retrieval import backfill, recall, rerank, retrieve
from evolution.triplet import Experience, Triplet, Utility

__all__ = [
    "Experience",
    "Triplet",
    "Utility",
    "backfill",
    "recall",
    "rerank",
    "retrieve",
]
