"""baseline.py 黑盒测试：统计口径必须与 judge.stats 共享。

第三方视角：baseline 的配对 t / t 值必须是「按日期对齐 + n≥5」的正确口径，
不允许再出现一份自带的「索引配对 + min_n=2 + 返回 tuple」分叉实现（P1）。
"""
from __future__ import annotations

def test_statistical_helpers_are_shared_with_stats():
    import judge.baseline as bl
    import judge.stats as st
    assert bl.mean is st.mean, "baseline.mean 应指向 judge.stats.mean"
    assert bl.tstat is st.tstat, "baseline.tstat 应指向 judge.stats.tstat（返回 float, min_n=5）"
    assert bl.paired_t is st.paired_t, "baseline.paired_t 应指向 judge.stats.paired_t（按日期对齐）"
    assert bl.DaySeries is st.DaySeries
