"""probe.py 黑盒测试：信号定义完整性。

第三方视角：每个内置信号必须能提供「说明 + 可执行的 SELECT」；RANKED 类还要有
合法的分位比例与方向，否则探针跑出来的结论不可信。
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


def test_signals_well_formed():
    from judge.probe import RANKED, SIGNALS
    assert len(SIGNALS) >= 6, "内置信号至少 6 个"
    for name, (desc, sql) in SIGNALS.items():
        assert isinstance(desc, str) and desc, f"{name} 缺说明"
        assert "SELECT" in sql.upper(), f"{name} SQL 非 SELECT"


def test_ranked_signals_well_formed():
    from judge.probe import RANKED
    for name, (desc, sql, frac, high) in RANKED.items():
        assert isinstance(desc, str) and desc, f"{name} 缺说明"
        assert "SELECT" in sql.upper(), f"{name} SQL 非 SELECT"
        assert 0 < frac <= 1, f"{name} 分位比例非法：{frac}"
        assert isinstance(high, bool), f"{name} 方向标志应为 bool"
