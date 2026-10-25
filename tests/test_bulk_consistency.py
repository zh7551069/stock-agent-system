"""批量缓存一致性回归测试。

背景（真实踩过的 bug）：`BulkLibrary` 最初用一个"这个信号日取过了"的布尔标记做短路。
同一天跑第二个信号时，它带着**不同的代码集合**再次调用 `prefetch_day`，
被短路后这些代码在缓存里查不到 → `raw_open()` 返回 None
→ 判决器判为 `no_raw_bar_on_entry`（不可成交）。
**不报错、只静默把可成交的票算成买不到**，直接污染所有统计。

本测试就是钉死这条：**预取顺序不得改变任何判决结果**。
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.bulk import BulkLibrary            # noqa: E402
from judge.outcome import Decision, judge     # noqa: E402

DB = pathlib.Path("/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb")
requires_db = pytest.mark.skipif(not DB.exists(), reason="主库未挂载（外接盘）")

T = dt.date(2026, 8, 25)
A = ["600519.SH", "000001.SZ"]                  # 第一批
B = ["300750.SZ", "601869.SH", "600743.SH"]     # 第二批（不同集合）


def _judge_all(lib, codes):
    return {c: judge(Decision(c, "buy", T, horizons=(1, 5, 20)), lib).as_dict() for c in codes}


@requires_db
def test_prefetch_order_does_not_change_results():
    """先预取 A 再预取 B，与只预取 B，结果必须逐位相同。"""
    with BulkLibrary() as lib1:
        days = lib1.trading_days_after(T, 20)
        lib1.prefetch_day(A, days[0], days[-1])      # 先灌一批"无关"代码
        lib1.prefetch_day(B, days[0], days[-1])      # 再灌目标代码
        after = _judge_all(lib1, B)

    with BulkLibrary() as lib2:
        days = lib2.trading_days_after(T, 20)
        lib2.prefetch_day(B, days[0], days[-1])      # 直接灌目标代码
        fresh = _judge_all(lib2, B)

    assert after == fresh, "预取顺序改变了判决结果（缓存串扰）"


@requires_db
def test_uncached_codes_fall_back_to_single_query():
    """未被预取的代码也必须能正确判决（回落到单条查询），不得静默判为不可成交。"""
    with BulkLibrary() as lib:
        days = lib.trading_days_after(T, 20)
        lib.prefetch_day(A, days[0], days[-1])       # 只预取 A
        for c in B:                                   # 直接判 B，不做预取
            o = judge(Decision(c, "buy", T, horizons=(1, 5, 20)), lib)
            assert o.reason != "no_raw_bar_on_entry", f"{c} 未预取却被判为取不到原始价"


@requires_db
def test_bulk_matches_plain_library():
    """批量缓存版与无缓存版，结果必须逐位相同。"""
    from judge.outcome import Library
    with Library() as plain, BulkLibrary() as bulk:
        days = bulk.trading_days_after(T, 20)
        bulk.prefetch_day(A + B, days[0], days[-1])
        for c in A + B:
            x = judge(Decision(c, "buy", T, horizons=(1, 5, 20)), plain).as_dict()
            y = judge(Decision(c, "buy", T, horizons=(1, 5, 20)), bulk).as_dict()
            assert x == y, f"{c} 批量版与单条版结果不一致"
