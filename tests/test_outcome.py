"""判决器测试。

分两类：
- 口径/契约测试：不依赖主库，随时可跑
- 真实数据测试：依赖主库，验证"入场价 = T+1 开盘"、"封板买不到记为缺失而非 0"等事实

运行：
    .venv/bin/python -m pytest tests/test_outcome.py -q
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.outcome import (  # noqa: E402
    Decision, Library, judge, summarize, to_prefix, to_suffix, split_prefix,
)

DB = pathlib.Path("/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb")
requires_db = pytest.mark.skipif(not DB.exists(), reason="主库未挂载（外接盘）")


# ---------------------------------------------------------------- 口径测试

def test_symbol_suffix_normalisation():
    assert to_suffix("000001.SZ") == "000001.SZ"
    assert to_suffix("000001.sz") == "000001.SZ"
    assert to_suffix("sz000001") == "000001.SZ"
    assert to_suffix("SZ000001") == "000001.SZ"
    assert to_suffix("1.SZ") == "000001.SZ"          # 补零


def test_symbol_prefix_normalisation():
    assert to_prefix("000001.SZ") == "sz000001"
    assert to_prefix("sz000001") == "sz000001"
    assert to_prefix("600000.SH") == "sh600000"
    assert split_prefix("sz000001") == ("sz", "000001")


def test_bare_code_is_rejected_not_guessed():
    """裸 6 位码在库中是歧义码（000001 是上证指数），必须拒绝而不是猜。"""
    with pytest.raises(ValueError):
        to_suffix("000001")


def test_side_and_horizon_validation():
    with pytest.raises(ValueError):
        Decision("000001.SZ", "hold", dt.date(2026, 9, 24))
    with pytest.raises(ValueError):
        Decision("000001.SZ", "buy", dt.date(2026, 9, 24), horizons=(0,))


# ---------------------------------------------------------------- 真实数据

@requires_db
def test_entry_price_is_next_trading_day_open():
    """入场价必须等于 T+1 的开盘价（前复权），不能是 T 日或收盘价。"""
    with Library() as lib:
        T = dt.date(2026, 9, 24)
        o = judge(Decision("000001.SZ", "buy", T), lib)
        assert o.entry_date is not None and o.entry_date > T
        bars = lib.qfq_bars("000001.SZ", o.entry_date, o.entry_date)
        assert bars, "入场日应有 K 线"
        assert o.entry_px == pytest.approx(bars[o.entry_date]["open"])
        # 且入场日确实是 T 之后第一个交易日
        assert o.entry_date == lib.trading_days_after(T, 1)[0]


@requires_db
def test_excess_equals_ret_minus_bench():
    with Library() as lib:
        o = judge(Decision("000001.SZ", "buy", dt.date(2026, 9, 24)), lib)
        assert o.tradable
        for k in (1, 3, 5, 20):
            if o.ret[k] is not None and o.bench_ret[k] is not None:
                assert o.excess[k] == pytest.approx(o.ret[k] - o.bench_ret[k], abs=1e-12)


@requires_db
def test_net_is_gross_minus_cost():
    """净超额 = 毛超额 − 往返成本 0.15%（基准不计成本，故成本只从个股侧扣一次）。"""
    with Library() as lib:
        o = judge(Decision("000001.SZ", "buy", dt.date(2026, 9, 24)), lib)
        assert o.tradable
        for k in (1, 3, 5, 20):
            if o.excess[k] is not None:
                assert o.excess_net[k] == pytest.approx(o.excess[k] - 0.0015, abs=1e-12)
                assert o.ret_net[k] == pytest.approx(o.ret[k] - 0.0015, abs=1e-12)


@requires_db
def test_blocked_decision_yields_missing_not_zero():
    """封板买不到时，收益必须是缺失，**绝不能是 0**——否则会把"没成交"算成"没赚没亏"。"""
    with Library() as lib:
        # 在真实库里找一例 T+1 开盘即涨停的标的（主体 hs/bj 行，非残留 sh/sz）
        row = lib._con.execute("""
            SELECT l.code, l.date FROM limit_price l
            JOIN daily d ON d.date = l.date AND d.code = l.code AND d.market = l.market
            WHERE d.open >= l.limit_up AND l.market IN ('hs','bj')
            ORDER BY l.date DESC LIMIT 1
        """).fetchone()
        if row is None:
            pytest.skip("库中未找到开盘即涨停样本")
        prefix, T = row[0], row[1]
        prev = lib._con.execute(
            "SELECT max(date) FROM trade_cal WHERE date < ?", [T]
        ).fetchone()[0]
        o = judge(Decision(prefix, "buy", prev), lib)
        assert o.tradable is False
        assert o.reason == "limit_up_on_open"
        assert all(v is None for v in o.ret.values()), "缺失必须保持 None，不得写 0"


@requires_db
def test_no_lookahead_window_is_respected():
    """只观察到 T+20；更远的数据不得进入计算（用 k 超过可用交易日验证）。"""
    with Library() as lib:
        T = dt.date(2026, 9, 24)
        o = judge(Decision("000001.SZ", "buy", T, horizons=(1, 500)), lib)
        assert o.ret[1] is not None
        assert o.ret[500] is None, "超出可用交易日必须缺失"


@requires_db
def test_market_column_means_different_things_per_table():
    """口径守卫：`daily.market` 与 `limit_price.market` **都是** 'hs'/'bj'（不是 'sh'/'sz'）。

    实测踩过的坑：曾误判「limit_price 用 sh/sz」，导致 limit_up_down() 用 sh/sz 查询
    静默取不到涨停价 → 封板判定失效（P0）。本测试钉死正确事实 + hs 覆盖率阈值。
    """
    with Library() as lib:
        daily_markets = {r[0] for r in lib._con.execute(
            "SELECT DISTINCT market FROM daily").fetchall()}
        limit_markets = {r[0] for r in lib._con.execute(
            "SELECT DISTINCT market FROM limit_price").fetchall()}
        assert "hs" in daily_markets and "bj" in daily_markets, \
            f"daily.market 期望含 hs/bj，实测 {daily_markets}"
        assert "sh" not in daily_markets and "sz" not in daily_markets, \
            f"daily.market 不应含 sh/sz，实测 {daily_markets}"
        # limit_price 主体也是 hs；sh/sz 只是 3 天历史残留（≈0.09%），不得当作主体
        total = lib._con.execute("SELECT count(*) FROM limit_price").fetchone()[0]
        hs_n = lib._con.execute("SELECT count(*) FROM limit_price WHERE market='hs'").fetchone()[0]
        assert hs_n / total > 0.9, f"limit_price.hs 占比异常：{hs_n/total:.3f}"


@requires_db
def test_raw_open_uses_daily_market_convention():
    """raw_open 必须能真的取到值（这正是上面那个坑的回归测试）。"""
    with Library() as lib:
        px = lib.raw_open("600743.SH", dt.date(2026, 9, 22))
        assert px is not None and px > 0, "raw_open 取不到值，说明 market 口径写错了"


@requires_db
def test_summarize_keeps_untradable_in_denominator():
    with Library() as lib:
        ds = [Decision(c, "buy", dt.date(2026, 9, 24)) for c in
              ("000001.SZ", "600000.SH", "000002.SZ")]
        q = summarize([judge(d, lib) for d in ds], (1, 3, 5, 20))
        assert q.n_total == 3
        assert q.n_tradable + q.n_untradable == 3
        assert set(q.hit_rate) == {1, 3, 5, 20}
