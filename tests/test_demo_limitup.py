"""demo_limitup.py 黑盒测试：fmt 格式化输出。

第三方视角：报告里展示的百分数/缺失占位必须稳定，否则读者会误读数字。
"""
from __future__ import annotations

def test_fmt_pct():
    from judge.demo_limitup import fmt
    assert fmt(0.0520) == "+5.20%"
    assert fmt(-0.0314) == "-3.14%"
    assert fmt(0.0) == "+0.00%"

def test_fmt_missing():
    from judge.demo_limitup import fmt
    assert fmt(None) == "  缺失"

def test_fmt_non_pct():
    from judge.demo_limitup import fmt
    assert fmt(0.5, pct=False, nd=2) == "0.50"
