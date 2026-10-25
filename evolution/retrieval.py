"""自进化 · 效用检索 4 步的确定性部分（self-evolution.md §3）。

① 先找像的（语义召回：按 regime + 意图）→ ② 再挑值的（效用重排 Top-k）→
③ 现场验证（影子回放，依赖 judge，此处不落）→ ④ 更新价值（真实结果回填效用）。

本模块落 ① 召回 + ② 重排 + ④ 回填的确定性实现；① 的「语义」用精确匹配 regime/意图，
真·语义召回（embedding）由上层接模型实现。
"""

from __future__ import annotations

from typing import Optional, Sequence

from evolution.triplet import Triplet, Utility


def recall(triplets: Sequence[Triplet], *, intent: Optional[str] = None,
           regime: Optional[Sequence[str]] = None) -> list[Triplet]:
    """① 召回：按意图（精确）+ regime（标签交集非空）过滤。"""
    regime_set = set(regime) if regime is not None else None
    out: list[Triplet] = []
    for t in triplets:
        if intent is not None and t.intent != intent:
            continue
        if regime_set is not None and not (regime_set & set(t.utility.regime)):
            continue
        out.append(t)
    return out


def rerank(triplets: Sequence[Triplet], k: Optional[int] = None) -> list[Triplet]:
    """② 效用重排：按 excess 降序取 Top-k。"""
    s = sorted(triplets, key=lambda t: t.utility.excess, reverse=True)
    return s[:k] if k else s


def retrieve(triplets: Sequence[Triplet], *, intent: Optional[str] = None,
             regime: Optional[Sequence[str]] = None, k: Optional[int] = None) -> list[Triplet]:
    """①② 连起来：召回 → 效用重排 Top-k。"""
    return rerank(recall(triplets, intent=intent, regime=regime), k=k)


def backfill(triplet: Triplet, *, excess: Optional[float] = None,
             tstat: Optional[float] = None, win_rate: Optional[float] = None,
             verdict: Optional[str] = None) -> Triplet:
    """④ 更新价值：用判决器真实结果回填效用（只改传入的字段，其余保留）。"""
    u = triplet.utility
    nu = Utility(
        regime=u.regime,
        excess=u.excess if excess is None else excess,
        tstat=u.tstat if tstat is None else tstat,
        win_rate=u.win_rate if win_rate is None else win_rate,
        verdict=u.verdict if verdict is None else verdict,
    )
    return Triplet(intent=triplet.intent, experience=triplet.experience, utility=nu, provenance=triplet.provenance)
