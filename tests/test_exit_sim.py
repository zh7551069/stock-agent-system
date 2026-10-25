"""exit_sim.py 黑盒测试：simulate 出场模拟器。

第三方视角：只看输入（entry_px + bars/raw/lim + rule）→ 输出（退出价/持有天数/退出原因）。
这是「怎么走」结论的引擎，出场价/原因错一个，退出规则对比就全错。
"""
from __future__ import annotations

from judge.exit_sim import RULES, simulate

def bar(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c}

def test_no_data():
    px, day, why = simulate(10, [], [], [], RULES["sl5"])
    assert (px, day, why) == (None, None, "no_data")

def test_stop_loss():
    bars = [bar(10, 10.2, 9.4, 9.8)]
    px, day, why = simulate(10, bars, [{"high": 10.2}], [None], RULES["sl5"])
    assert why == "stop_loss" and px == 9.5 and day == 1    # min(9.5, open 10)

def test_stop_loss_gap_down_open():
    bars = [bar(9.0, 9.2, 8.8, 9.0)]          # 跳空低开，open < stop 9.5
    px, day, why = simulate(10, bars, [{"high": 9.2}], [None], RULES["sl5"])
    assert why == "stop_loss" and px == 9.0 and day == 1

def test_take_profit():
    bars = [bar(10, 11.5, 9.9, 11.0)]
    px, day, why = simulate(10, bars, [{"high": 11.5}], [None], RULES["tp10"])
    assert why == "take_profit" and px == 11.0 and day == 1   # max(11.0, open 10)

def test_take_profit_gap_up_open():
    bars = [bar(11.2, 11.5, 10.8, 11.0)]       # 跳空高开，open > tp 11.0
    px, day, why = simulate(10, bars, [{"high": 11.5}], [None], RULES["tp10"])
    assert why == "take_profit" and px == 11.2 and day == 1

def test_same_day_sl_and_tp_sl_first():
    # 同日 SL 和 TP 都触发 → 先止损（保守）
    bars = [bar(10, 11.5, 9.0, 11.0)]
    px, day, why = simulate(10, bars, [{"high": 11.5}], [None], RULES["sl5_tp10"])
    assert why == "stop_loss" and px == 9.5

def test_limit_down_locked_delays_to_next_day():
    # 第 1 天跌停封死（raw high 9.5 <= limit_down 9.5）→ 跳过；第 2 天正常触发止损
    bars = [bar(10, 9.5, 9.5, 9.5), bar(10, 10.2, 9.4, 9.8)]
    raw = [{"high": 9.5}, {"high": 10.2}]
    lim = [9.5, None]
    px, day, why = simulate(10, bars, raw, lim, RULES["sl5"])
    assert why == "stop_loss" and day == 2 and px == 9.5

def test_trailing_stop():
    # day1 high 11 → peak 11；day2 low 10.4 <= 11*0.95 = 10.45 → 跟踪止损
    bars = [bar(10, 11, 9.9, 11), bar(11, 11.2, 10.4, 10.5)]
    px, day, why = simulate(10, bars, [{"high": 11}, {"high": 11.2}], [None, None], RULES["trail5"])
    assert why == "trailing_stop" and px == 10.45 and day == 2

def test_time_stop():
    # time5：tstop=5, tthr=0.01；第 5 天 close < 10*1.01=10.1 → 时间止损
    bars = [bar(10, 10, 10, 10)] * 4 + [bar(10, 10, 10, 10.05)]
    px, day, why = simulate(10, bars, [{"high": 10}] * 5, [None] * 5, RULES["time5"])
    assert why == "time_stop" and day == 5 and px == 10.05

def test_max_hold():
    rule = dict(sl=None, tp=None, maxd=3, trail=None, tstop=None, tthr=None)
    bars = [bar(10, 10, 10, 10)] * 3
    px, day, why = simulate(10, bars, [{"high": 10}] * 3, [None] * 3, rule)
    assert why == "max_hold" and day == 3 and px == 10.0

def test_window_end():
    rule = dict(sl=None, tp=None, maxd=20, trail=None, tstop=None, tthr=None)
    bars = [bar(10, 10, 10, 10)] * 2
    px, day, why = simulate(10, bars, [{"high": 10}] * 2, [None] * 2, rule)
    assert why == "window_end" and day == 2 and px == 10.0
