"""自进化 · 三元组 + 效用检索/回填 单测。"""

from evolution.retrieval import backfill, recall, retrieve
from evolution.triplet import Experience, Triplet, Utility


def _t(intent, regime, excess, verdict="accepted", tstat=1.0, win_rate=0.5) -> Triplet:
    return Triplet(
        intent=intent,
        experience=Experience(decision_pack={}, grips=("factor:x",), bases=("依据",), trace_id="trace_1"),
        utility=Utility(regime=tuple(regime), excess=excess, tstat=tstat, win_rate=win_rate, verdict=verdict),
        provenance=("factor:x", "calib:v1"),
    )


def _triplets():
    return [
        _t("strategy_gen", ["涨停家数<30"], -0.05, verdict="rejected"),
        _t("strategy_gen", ["涨停家数<30"], 0.10, verdict="accepted"),
        _t("strategy_gen", ["大盘beta高"], 0.03, verdict="accepted"),
        _t("risk_reduce", ["涨停家数<30"], 0.20, verdict="accepted"),
    ]


def test_recall_by_intent_and_regime():
    ts = _triplets()
    r = recall(ts, intent="strategy_gen")
    assert len(r) == 3
    r2 = recall(ts, regime=["涨停家数<30"])
    assert len(r2) == 3
    r3 = recall(ts, intent="strategy_gen", regime=["大盘beta高"])
    assert len(r3) == 1


def test_retrieve_reranks_by_excess_desc():
    ts = _triplets()
    top = retrieve(ts, intent="strategy_gen", k=1)
    assert len(top) == 1
    assert top[0].utility.excess == 0.10   # 最高效用的排在前面


def test_retrieve_top_k():
    ts = _triplets()
    top = retrieve(ts, intent="strategy_gen", regime=["涨停家数<30"], k=2)
    assert [t.utility.excess for t in top] == [0.10, -0.05]


def test_backfill_updates_utility():
    t = _t("strategy_gen", ["涨停家数<30"], 0.05, verdict="accepted")
    t2 = backfill(t, excess=-0.03, tstat=-4.0, win_rate=0.2, verdict="rejected")
    assert t2.utility.excess == -0.03
    assert t2.utility.verdict == "rejected"
    assert t2.utility.tstat == -4.0
    assert t2.utility.regime == t.utility.regime   # regime 不回填，保留


def test_backfill_partial_keeps_rest():
    t = _t("strategy_gen", ["涨停家数<30"], 0.05, verdict="accepted")
    t2 = backfill(t, excess=-0.01)   # 只回填 excess
    assert t2.utility.excess == -0.01
    assert t2.utility.verdict == "accepted"   # 其余保留
    assert t2.utility.tstat == 1.0
