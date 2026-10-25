"""regime · DB 适配（单位归一 + 假连接）单测。"""

import datetime as dt

from regime.query import _to_prefix, market_regime, pct_to_decimal


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeCon:
    def __init__(self, limit_up, pct):
        self._limit_up, self._pct = limit_up, pct

    def execute(self, sql, params=None):
        if "count(*)" in sql:
            return _FakeResult([[self._limit_up]])
        if "index_daily" in sql:
            return _FakeResult([[self._pct]] if self._pct is not None else [])
        return _FakeResult([])


def test_pct_to_decimal():
    assert pct_to_decimal(-0.53) == -0.0053
    assert pct_to_decimal(1.2821) == 0.012821
    assert pct_to_decimal(0.0) == 0.0


def test_to_prefix():
    assert _to_prefix("000001.SZ") == "sz000001"
    assert _to_prefix("600519.SH") == "sh600519"
    assert _to_prefix("300750.SZ") == "sz300750"


def test_market_regime_two_dims():
    d = market_regime(_FakeCon(limit_up=86, pct=-0.53), dt.date(2026, 9, 1))
    assert d["limit_up_cnt"] == "60+"       # 86 只涨停
    assert d["beta_bucket"] == "跌"         # -0.53% → -0.0053 小数 → 跌
    assert d["crowd_bucket"] == "待考证"     # 分位未接
    assert d["turnover_q"] == "待考证"


def test_market_regime_beta_flat_when_missing():
    # 沪深300 缺数据 → bench 按 0 → 平
    d = market_regime(_FakeCon(limit_up=20, pct=None), dt.date(2026, 9, 1))
    assert d["beta_bucket"] == "平"
    assert d["limit_up_cnt"] == "<30"
