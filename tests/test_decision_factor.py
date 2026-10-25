"""决策面 · 因子工坊 4 类动作 + 大盘分析师 + 盘中哨兵 单测。"""

from decision.event import Event, validate_event
from decision.factor import Factor, FactorDict
from decision.macro import MacroView, validate_macro


def _f(**kw) -> Factor:
    base = dict(
        factor_id="rsi6_lt20", name="RSI6 超卖", definition="rsi6 < 20",
        params={"window": 6, "threshold": 20},
        search_interval={"window": (3, 20), "threshold": (10, 30)},
        caliber="前复权", source="回测:probe_2023",
    )
    base.update(kw)
    return Factor(**base)


def _d() -> FactorDict:
    d = FactorDict()
    d.register(_f())
    d.register(_f(factor_id="mom20", name="动量", definition="mom20 > 0",
                  params={"window": 20}, search_interval={"window": (10, 60)}))
    return d


def test_add_and_remove_factor():
    d = _d()
    assert d.apply({"type": "add_factor", "evidence_id": "e1", "factor": _f(factor_id="new_f")}) == []
    assert "new_f" in d
    assert d.apply({"type": "remove_factor", "evidence_id": "e2", "factor_id": "new_f"}) == []


def test_edit_definition_bumps_version():
    d = _d()
    old = d.get("rsi6_lt20").version
    assert d.apply({"type": "edit_factor_definition", "evidence_id": "e",
                    "factor_id": "rsi6_lt20", "definition": "rsi6 < 15"}) == []
    assert d.get("rsi6_lt20").definition == "rsi6 < 15"
    assert d.get("rsi6_lt20").version != old


def test_tune_params_within_interval_ok():
    d = _d()
    assert d.apply({"type": "tune_factor_params", "evidence_id": "e",
                    "factor_id": "rsi6_lt20", "params": {"threshold": 18}}) == []
    assert d.get("rsi6_lt20").params["threshold"] == 18


def test_tune_params_out_of_interval_rejected():
    d = _d()
    errs = d.apply({"type": "tune_factor_params", "evidence_id": "e",
                    "factor_id": "rsi6_lt20", "params": {"threshold": 99}})
    assert any("搜索区间" in x for x in errs)
    assert d.get("rsi6_lt20").params["threshold"] == 20   # 未被改动


def test_reweight_requires_normalized_and_registered():
    d = _d()
    errs = d.apply({"type": "reweight_factors", "evidence_id": "e",
                    "weights": {"rsi6_lt20": 0.7, "mom20": 0.2}})
    assert any("归一化" in x for x in errs)
    assert d.apply({"type": "reweight_factors", "evidence_id": "e",
                    "weights": {"rsi6_lt20": 0.7, "mom20": 0.3}}) == []
    assert d.weights() == {"rsi6_lt20": 0.7, "mom20": 0.3}


def test_action_requires_evidence_id():
    d = _d()
    errs = d.apply({"type": "remove_factor", "factor_id": "rsi6_lt20"})
    assert any("evidence_id" in x for x in errs)


def test_macro_view_valid_and_invalid():
    good = MacroView(date="2026-01-05", trend="震荡偏强", rotation=("题材", "资源"),
                     regime={"涨停家数": "30-60", "beta": "涨"}, confidence=0.7, bases=("依据A",))
    assert validate_macro(good) == []
    bad = MacroView(date="", trend="", rotation=(), regime={}, confidence=1.5, bases=())
    assert len(validate_macro(bad)) == 5


def test_event_valid_and_invalid():
    good = Event(event_id="evt1", symbol="000001.SZ", etype="signal", threshold="rsi6<20", ts="2026-01-05T10:00:00")
    assert validate_event(good) == []
    bad = Event(event_id="", symbol="", etype="bogus", threshold="", ts="")
    assert len(validate_event(bad)) == 4
