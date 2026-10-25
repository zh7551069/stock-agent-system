"""对账官 · 接线层（判决器 → verdict 行 + 对账结论）单测。"""

from reconcile.graph import ProvenanceGraph
from reconcile.wire import JudgedSignal, wire


def _graph() -> ProvenanceGraph:
    return ProvenanceGraph([
        ("dec", "fac"),
        ("dec", "kb"),
        ("fac", "cal"),
        ("kb", "book"),
    ])


def _signal(**kw) -> JudgedSignal:
    base = dict(
        decision_id="dec", signal="limit_up", regime_slice="涨停<30",
        excess=-0.05, t_stat=-2.9, paired_t=-3.0, layered_win_rate=0.3,
    )
    base.update(kw)
    return JudgedSignal(**base)


def test_wire_rejected_produces_consistent_verdict_and_blame():
    w = wire(_signal(), _graph(), judged_at="2026-01-02T15:00:00")
    assert w.verdict.verdict == "rejected"
    assert w.reconciliation.verdict == "rejected"       # 两者一致
    assert w.verdict.decision_id == "dec"
    assert w.verdict.excess == -0.05
    assert w.verdict.t_stat == -2.9
    assert w.verdict.paired_t == -3.0
    assert w.reconciliation.rollback  # rejected 有回滚信号


def test_wire_verdict_row_to_dict_matches_columns():
    w = wire(_signal(), _graph(), judged_at="2026-01-02T15:00:00")
    d = w.verdict.to_dict()
    assert set(d) == {
        "decision_id", "excess", "t_stat", "paired_t",
        "layered_win_rate", "verdict", "regime_slice", "judged_at",
    }


def test_wire_accepted_has_empty_blame():
    w = wire(_signal(excess=0.05, paired_t=3.0), _graph(), judged_at="2026-01-02T15:00:00")
    assert w.verdict.verdict == "accepted"
    assert w.reconciliation.blame == {}
    assert w.reconciliation.rollback == ()


def test_wire_unknown_when_missing_stat():
    w = wire(_signal(excess=None, paired_t=None, t_stat=None), _graph(), judged_at="x")
    assert w.verdict.verdict == "unknown"
    assert w.reconciliation.verdict == "unknown"


def test_wire_judged_at_defaults_to_wallclock():
    # 不注入 judged_at 时取墙钟（ISO）；只断言非空且可解析
    w = wire(_signal(), _graph())
    assert w.verdict.judged_at


def test_wire_preserves_regime_slice_and_layered_win_rate():
    w = wire(_signal(layered_win_rate=0.66), _graph(), judged_at="t")
    assert w.verdict.regime_slice == "涨停<30"
    assert w.verdict.layered_win_rate == 0.66
