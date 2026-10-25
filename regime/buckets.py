"""regime · 分桶三原则 + 三态判定（eval-dataset.md 6.2.1 / 6.2.3）。

- 等频分位：``quantile_edges`` + ``assign_bucket``。
- 已验证断点：``find_flip``（超额正负翻转点）。
- n≥5 校验：``min_n_violations``。
- 三态判定：``classify``（✅纳入 / ⚠️待定 / ❌删除）。
"""

from __future__ import annotations

import statistics
from bisect import bisect_right
from collections import defaultdict
from typing import Iterable, Mapping, Optional, Sequence


def quantile_edges(values: Sequence[float], k: int) -> list[float]:
    """``k`` 分位断点（``k-1`` 个）。``k < 2`` 或样本空返回 ``[]``。"""
    data = [float(v) for v in values]
    if k < 2 or not data:
        return []
    return list(statistics.quantiles(data, n=k))


def assign_bucket(value: float, edges: Sequence[float]) -> int:
    """把 ``value`` 分到 ``0..len(edges)`` 桶（bisect_right 语义）。"""
    return bisect_right(edges, value)


def bucket_stats(bucket_ids: Iterable[int], excesses: Iterable[Optional[float]]) -> dict[int, dict]:
    """每桶 ``{n, mean_excess}``（跳过 None = 缺失，缺失≠0）。"""
    agg: dict[int, dict] = defaultdict(lambda: {"n": 0, "sum": 0.0})
    for b, e in zip(bucket_ids, excesses):
        if e is None:
            continue
        agg[b]["n"] += 1
        agg[b]["sum"] += float(e)
    return {b: {"n": v["n"], "mean_excess": v["sum"] / v["n"]} for b, v in agg.items()}


def min_n_violations(stats: Mapping[int, dict], min_n: int = 5) -> list[int]:
    """返回 ``n < min_n`` 的桶号（升序）。"""
    return sorted(b for b, s in stats.items() if s["n"] < min_n)


def is_monotonic(means: Sequence[float]) -> bool:
    """桶号升序的均值是否单调（全非降或全非增）。"""
    diffs = [means[i + 1] - means[i] for i in range(len(means) - 1)]
    return all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs)


def find_flip(pairs: Sequence[tuple[float, float]]) -> Optional[float]:
    """按维度值排序后，找超额正负翻转点（第一个相邻异号处的维度值）。

    返回「超额由正转负（或负转正）」的临界维度值 = 候选断点（6.2.1 第 2 条）。
    """
    s = sorted(pairs, key=lambda p: p[0])
    for i in range(len(s) - 1):
        if s[i][1] * s[i + 1][1] < 0:  # 异号
            return s[i + 1][0]
    return None


def classify(stats: Mapping[int, dict], *, min_n: int = 5) -> tuple[str, str]:
    """三态判定，返回 ``(态, 理由)``。

    - 有桶 ``n < min_n`` → ⚠️待定（数据不足，不删除、不纳入）。
    - 全桶 ``n ≥ min_n`` 且均值单调 → ✅纳入。
    - 全桶 ``n ≥ min_n`` 但无单调关系 → ❌删除。
    """
    if not stats:
        return ("⚠️待定", "无样本")
    bad = min_n_violations(stats, min_n)
    if bad:
        return ("⚠️待定", f"桶 {bad} 的 n<{min_n}，数据不足")
    ordered = sorted(stats)
    means = [stats[b]["mean_excess"] for b in ordered]
    if is_monotonic(means):
        return ("✅纳入", "超额与维度桶单调（可翻转）")
    return ("❌删除", "无单调/可翻转关系")
