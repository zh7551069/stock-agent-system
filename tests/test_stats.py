"""统计口径回归测试：配对检验必须按**日期**对齐，不能按索引。

注意：`tstat` 有 min_n=5 的样本下限，所以这里都用 >=5 个共同日，
否则返回 None（那是"样本不足"的正确行为，不是 bug）。
"""
from __future__ import annotations

from judge.stats import DaySeries, day_series, paired_diff, paired_t

def test_paired_t_aligns_by_date_not_index():
    """对照组缺第一天时，按索引配对会整体错位——本测试钉死正确行为。"""
    days_a = [f"d{i}" for i in range(1, 9)]           # d1..d8
    days_b = [f"d{i}" for i in range(2, 9)]           # d2..d8（缺 d1）
    a = DaySeries(days_a, [float(i) for i in range(1, 9)])
    b = DaySeries(days_b, [float(i) * 0.9 for i in range(2, 9)])

    m, t = paired_t(a, b)
    # 正确（按日期交集 d2..d8）：差值 = i - 0.9i = 0.1i → 均值 0.5
    assert abs(m - 0.5) < 1e-12, f"未按日期对齐，得到 {m}"
    # 错误做法（按索引）会得到 -0.5
    assert abs(m - (-0.5)) > 1e-9
    assert t is not None

def test_paired_diff_reports_common_days():
    days_a = [f"d{i}" for i in range(1, 9)]
    days_b = [f"d{i}" for i in range(4, 10)]          # 交集 d4..d8 = 5 天
    a = DaySeries(days_a, [float(i) for i in range(1, 9)])
    b = DaySeries(days_b, [1.0] * 6)
    m, t, common = paired_diff(a, b)
    assert common == 5, f"共同日数应为 5，得到 {common}"
    assert m == sum([4.0, 5.0, 6.0, 7.0, 8.0]) / 5 - 1.0
    assert t is not None

def test_day_series_carries_dates_and_skips_missing():
    recs = [
        {"date": "d1", "x": 1.0},
        {"date": "d1", "x": 3.0},
        {"date": "d2", "x": None},      # 缺失不参与
        {"date": "d3", "x": 5.0},
    ]
    s = day_series(recs, "x")
    assert isinstance(s, DaySeries)
    assert s.days == ["d1", "d3"], "缺失日不应出现"
    assert list(s) == [2.0, 5.0]

def test_day_series_is_list_compatible():
    """必须保持 list 兼容，否则调用方的 mean/tstat/median 会全部失效。"""
    import statistics as st
    s = day_series([{"date": "d1", "x": 1.0}, {"date": "d2", "x": 3.0}], "x")
    assert sum(s) == 4.0
    assert st.median(s) == 2.0
    assert len(s) == 2
    assert s.as_map() == {"d1": 1.0, "d2": 3.0}
