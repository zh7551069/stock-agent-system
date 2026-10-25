"""四元 id 生成单测。"""

import datetime as dt

from trace.ids import decision_id, factor_id, session_id, strategy_id


def test_session_id_format():
    sid = session_id(dt.date(2026, 1, 1))
    assert sid.startswith("sesn_20260101_")
    assert len(sid) == len("sesn_20260101_") + 8


def test_session_id_random_per_call():
    a = session_id(dt.date(2026, 1, 1))
    b = session_id(dt.date(2026, 1, 1))
    assert a != b  # 同一日期两次调用应不同（随机段）


def test_decision_id_format():
    assert decision_id("sesn_20260101_00000000", 3) == "dec_20260101_003"


def test_strategy_and_factor_id():
    assert strategy_id("rsi6", "2.1") == "strat_rsi6@2.1"
    assert factor_id("rsi6_lt20", "1") == "factor_rsi6_lt20@1"
