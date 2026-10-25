"""判决器共用统计口径。

刻意保持极小、无依赖：统计口径一旦分叉，跨假设的对比就不再成立。

## 一个真实踩过的 bug（本模块存在的理由）

最初的 `paired_t(a, b)` 用 `n = min(len(a), len(b))` 然后**按索引逐位相减**。
但 `a`、`b` 是"按独立日聚合的序列"，若某一组在某天没有有效记录，
该天就只出现在另一组里 —— 两个列表长度不同，**按索引配对会发生整体错位**。

实测后果：`limit_down` T+20 处理组 861 天 / 对照组 865 天，错位 4 天；
`new_low60` T+20 错位 2 天。错位会让"同日相减"变成"隔几天相减"，
配对检验的整个意义（剥离当日市场风格）就失效了。

修法：让日序列**自带日期**（:class:`DaySeries`），配对时先取日期交集再相减。
调用方无需改动 —— `DaySeries` 是 `list` 的子类，`mean`/`tstat`/`statistics.median` 照常可用。
"""
from __future__ import annotations

import math
import statistics as st


class DaySeries(list):
    """按**独立日**聚合的数值序列，并携带对应日期。

    独立样本单位是"日"而不是"笔"：同一天几十只票高度相关，
    必须先按日聚合成一个观测值，再对日序列做 t 检验，否则 t 值会被放大几十倍。
    """

    def __init__(self, days, values) -> None:
        super().__init__(values)
        self.days = list(days)

    def as_map(self) -> dict:
        return {d: v for d, v in zip(self.days, self)}


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def tstat(xs, min_n: int = 5) -> float | None:
    """单样本 t：mean / (sd / sqrt(n))。样本 < min_n 或零方差时返回 None。"""
    if len(xs) < min_n:
        return None
    sd = st.stdev(xs)
    if sd == 0:
        return None
    return mean(xs) / (sd / math.sqrt(len(xs)))


def paired_t(a, b, min_n: int = 5) -> tuple[float | None, float | None]:
    """配对 t：a - b 的均值与 t。

    若两边都是 :class:`DaySeries`，**按日期交集配对**（正确做法）；
    否则退化为按索引配对（仅适用于两侧日期集合必然相同的场景）。
    """
    if isinstance(a, DaySeries) and isinstance(b, DaySeries):
        ma, mb = a.as_map(), b.as_map()
        common = sorted(set(ma) & set(mb))
        if len(common) < min_n:
            return (None, None)
        d = [ma[k] - mb[k] for k in common]
        return (mean(d), tstat(d, min_n))
    n = min(len(a), len(b))
    if n < min_n:
        return (None, None)
    d = [a[i] - b[i] for i in range(n)]
    return (mean(d), tstat(d, min_n))


def paired_diff(a, b, min_n: int = 5) -> tuple[float | None, float | None, int]:
    """同 :func:`paired_t`，但额外返回**实际参与配对的共同日数**，便于诚实披露。"""
    if isinstance(a, DaySeries) and isinstance(b, DaySeries):
        common = len(set(a.days) & set(b.days))
    else:
        common = min(len(a), len(b))
    m, t = paired_t(a, b, min_n)
    return (m, t, common)


def day_series(records: list[dict], field: str) -> DaySeries:
    """把逐笔记录压成"按独立日的均值序列"（**携带日期**）。

    不可成交/缺失的记录不参与；某日若一条有效记录都没有，该日不会出现在序列里——
    这正是必须按日期配对的原因。
    """
    by_day: dict[str, list[float]] = {}
    for r in records:
        v = r.get(field)
        if v is not None:
            by_day.setdefault(r["date"], []).append(v)
    days = sorted(by_day)
    return DaySeries(days, [mean(by_day[d]) for d in days])
