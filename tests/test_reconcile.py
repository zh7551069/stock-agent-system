"""对账官 · 溯源图信用传播 + 对账结论单测。"""

from reconcile.graph import ProvenanceGraph
from reconcile.reconcile import reconcile


def _graph() -> ProvenanceGraph:
    """决策 dec → (因子 fac、知识卡 kb、skill sk)；fac → 口径 cal；kb → 来源书 book；sk → kb。"""
    return ProvenanceGraph([
        ("dec", "fac"),
        ("dec", "kb"),
        ("dec", "sk"),
        ("fac", "cal"),
        ("kb", "book"),
        ("sk", "kb"),
    ])


def test_credit_propagate_decays_by_distance():
    g = _graph()
    credit = g.credit_propagate("dec", blame=1.0, decay=0.5)
    assert credit["fac"] == 0.5          # 距离 1
    assert credit["kb"] == 0.5           # 距离 1
    assert credit["sk"] == 0.5           # 距离 1
    assert credit["cal"] == 0.25         # 距离 2
    assert credit["book"] == 0.25        # 距离 2（kb 与 sk→kb 两条路，取最短）
    assert "dec" not in credit           # 不含 root


def test_credit_propagate_shortest_path_wins():
    # fac 既被 dec 直接引用、又被 sk 间接引用 → 取最短距离 1
    g = ProvenanceGraph([("dec", "fac"), ("dec", "sk"), ("sk", "fac")])
    credit = g.credit_propagate("dec", decay=0.5)
    assert credit["fac"] == 0.5


def test_distance():
    g = _graph()
    assert g.distance("dec", "fac") == 1
    assert g.distance("dec", "book") == 2
    assert g.distance("dec", "dec") == 0
    assert g.distance("fac", "dec") is None  # 反向不可达


def test_reconcile_rejected_produces_blame_and_rollback():
    r = reconcile("dec", excess_net=-0.05, tstat=-3.0, graph=_graph())
    assert r.verdict == "rejected"
    assert r.blame["fac"] == 0.5
    # 回滚信号：信用 >= 0.25 的节点（fac/kb/sk 距离1=0.5，cal/book 距离2=0.25）
    assert set(r.rollback) == {"fac", "kb", "sk", "cal", "book"}
    assert r.rollback[:3] == ("fac", "kb", "sk")  # 距离 1 的信用最高且降序在前


def test_reconcile_accepted_produces_no_blame():
    r = reconcile("dec", excess_net=0.05, tstat=3.0, graph=_graph())
    assert r.verdict == "accepted"
    assert r.blame == {}
    assert r.rollback == ()


def test_reconcile_unknown_when_insignificant_or_missing():
    assert reconcile("dec", 0.0, 1.0, graph=_graph()).verdict == "unknown"
    assert reconcile("dec", None, None, graph=_graph()).verdict == "unknown"
    assert reconcile("dec", -0.05, None, graph=_graph()).verdict == "unknown"


def test_reconcile_rollback_threshold_filters():
    # 提高阈值：只回滚距离 1 的节点（0.5 >= 0.4），距离 2 的（0.25）被滤掉
    r = reconcile("dec", excess_net=-0.05, tstat=-3.0, graph=_graph(), rollback_threshold=0.4)
    assert r.rollback == ("fac", "kb", "sk")
