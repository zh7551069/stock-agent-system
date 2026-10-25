"""批量判决：把"按天取数"合并成少数几条查询，但**计算路径与单条判决完全一致**。

为什么要单独一层：
单条判决对每只票各发 4~5 条查询，跑几百个交易日会退化成几万次查询。
这里按**信号日**把同一天所有标的的行情/涨跌停/停牌一次性取回并缓存，
再逐条调用同一个 `judge()` —— 保证批量与单条**结果必然一致**（同一计算路径）。

纪律：本层只做缓存与合并查询，**不改任何口径**。
"""
from __future__ import annotations

import datetime as dt
from typing import Iterable, Optional, Sequence

from .outcome import (
    Library, _DAILY_MARKET_OF_EXCHANGE, to_prefix, to_suffix,
)


def _chunks(seq: Sequence[str], n: int = 400) -> Iterable[Sequence[str]]:
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class BulkLibrary(Library):
    """带"按天预取"的只读库。缓存命中时不再发查询。"""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self._bars: dict[tuple[str, dt.date, dt.date], dict[dt.date, dict]] = {}
        self._raw: dict[tuple[str, dt.date], Optional[float]] = {}
        self._lim: dict[tuple[str, dt.date], Optional[tuple[float, float]]] = {}
        self._susp: set[tuple[str, dt.date]] = set()
        self._bars_done: set[tuple[dt.date, dt.date]] = set()
        #: 每个信号日**已预取过**的后缀式代码集合。
        #: 不能只用一个"这天取过了"的布尔标记——不同信号在同一天命中不同代码，
        #: 若第二个信号被提前返回，它会拿不到值且**不报错**，静默把可成交判成不可成交。
        self._day_codes: dict[dt.date, set[str]] = {}

    # ---------------------------------------------------------------- 预取
    def universe(self, day: dt.date) -> list[str]:
        """该日有前复权日线数据的全部标的（后缀式），用作对照组的抽样池。"""
        rows = self._con.execute(
            "SELECT DISTINCT code FROM tech_factor_qfq WHERE date = ? ORDER BY code", [day]
        ).fetchall()
        return [r[0] for r in rows]

    def prefetch_day(self, codes: Sequence[str], start: dt.date, end: dt.date) -> None:
        """把 codes 在 [start,end] 的行情、以及 start 日的原始开盘/涨跌停/停牌取回。

        **增量语义**：只取"这个信号日在之前没取过"的代码（同一天多个信号会累积）。
        这样跨信号复用缓存既不会漏，也不会重复查询。
        """
        known = self._day_codes.setdefault(start, set())
        new = [c for c in (to_suffix(x) for x in codes) if c not in known]
        if not new:
            return
        pfx_new = [to_prefix(c) for c in new]

        # 先占位：即使某只票在该区间没有任何 K 线，也标记为"已知"，避免反复回查
        for c in new:
            self._bars.setdefault((c, start, end), {})
        for part in _chunks(new):
            ph = ",".join("?" * len(part))
            for row in self._con.execute(
                f"SELECT code, date, open, high, low, close FROM tech_factor_qfq "
                f"WHERE code IN ({ph}) AND date >= ? AND date <= ?",
                [*part, start, end],
            ).fetchall():
                self._bars[(row[0], start, end)][row[1]] = {
                    "open": row[2], "high": row[3], "low": row[4], "close": row[5]}
        self._bars_done.add((start, end))

        # 原始开盘价（涨跌停判定用）—— 注意 daily.market 是 hs/bj，不是 sh/sz
        for market in ("hs", "bj"):
            codes_m = [p for p in pfx_new if _DAILY_MARKET_OF_EXCHANGE[p[:2]] == market]
            for part in _chunks(codes_m):
                ph = ",".join("?" * len(part))
                for row in self._con.execute(
                    f"SELECT code, open FROM daily WHERE market = ? AND date = ? AND code IN ({ph})",
                    [market, start, *part],
                ).fetchall():
                    self._raw[(row[0], start)] = row[1]

        for part in _chunks(pfx_new):
            ph = ",".join("?" * len(part))
            for row in self._con.execute(
                f"SELECT code, limit_up, limit_down FROM limit_price "
                f"WHERE date = ? AND code IN ({ph})",
                [start, *part],
            ).fetchall():
                self._lim[(row[0], start)] = (row[1], row[2])

        d8 = start.strftime("%Y%m%d")
        for part in _chunks(new):
            ph = ",".join("?" * len(part))
            for row in self._con.execute(
                f"SELECT 股票代码 FROM suspension WHERE 交易日期 = ? AND 股票代码 IN ({ph})",
                [d8, *part],
            ).fetchall():
                self._susp.add((row[0], start))

        known.update(new)

    # ------------------------------------------------- 命中缓存则不发查询
    #: 只有当"这只票在这个信号日确实被预取过"时，缓存里的缺失才代表真实缺失；
    #: 否则必须回落到单条查询——这是防止"静默判成不可成交"的关键。
    def _cached(self, code: str, day: dt.date) -> bool:
        return to_suffix(code) in self._day_codes.get(day, ())

    def qfq_bars(self, code: str, start: dt.date, end: dt.date) -> dict[dt.date, dict]:
        hit = self._bars.get((to_suffix(code), start, end))
        return hit if hit is not None else super().qfq_bars(code, start, end)

    def raw_open(self, code: str, day: dt.date) -> Optional[float]:
        if self._cached(code, day):
            return self._raw.get((to_prefix(code), day))
        return super().raw_open(code, day)

    def limit_up_down(self, code: str, day: dt.date) -> Optional[tuple[float, float]]:
        if self._cached(code, day):
            return self._lim.get((to_prefix(code), day))
        return super().limit_up_down(code, day)

    def is_suspended(self, code: str, day: dt.date) -> bool:
        if self._cached(code, day):
            return (to_suffix(code), day) in self._susp
        return super().is_suspended(code, day)
