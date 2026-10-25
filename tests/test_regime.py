"""regime · 分桶三原则 + 三态判定单测。"""

from regime.buckets import (
    assign_bucket,
    bucket_stats,
    classify,
    find_flip,
    is_monotonic,
    min_n_violations,
    quantile_edges,
)


def test_quantile_edges_quartiles():
    # 0..99 均匀 100 个点，四分位断点应约 [25, 50, 75]
    edges = quantile_edges(list(range(100)), k=4)
    assert len(edges) == 3
    assert 24 <= edges[0] <= 26
    assert 49 <= edges[1] <= 51
    assert 74 <= edges[2] <= 76


def test_quantile_edges_k_lt_2_empty():
    assert quantile_edges([1, 2, 3], k=1) == []
    assert quantile_edges([], k=4) == []


def test_assign_bucket_bisect():
    edges = [25.0, 50.0, 75.0]
    assert assign_bucket(10, edges) == 0
    assert assign_bucket(25, edges) == 1       # bisect_right：等于断点归右桶
    assert assign_bucket(80, edges) == 3


def test_bucket_stats_skips_none():
    stats = bucket_stats([0, 0, 1, 1, 1], [1.0, 2.0, 4.0, None, 6.0])
    assert stats[0] == {"n": 2, "mean_excess": 1.5}
    assert stats[1] == {"n": 2, "mean_excess": 5.0}   # None 跳过，n=2


def test_min_n_violations():
    stats = {0: {"n": 3}, 1: {"n": 10}, 2: {"n": 2}}
    assert min_n_violations(stats, min_n=5) == [0, 2]


def test_is_monotonic():
    assert is_monotonic([-1.0, -0.5, 0.0]) is True      # 非降
    assert is_monotonic([0.5, 0.0, -0.2]) is True       # 非增
    assert is_monotonic([0.5, -0.1, 0.2]) is False      # 折返


def test_find_flip():
    pairs = [(10, 0.02), (30, 0.01), (50, -0.01), (70, -0.03)]
    assert find_flip(pairs) == 50        # 超额在 30→50 之间由正转负


def test_classify_include():
    stats = {0: {"n": 100, "mean_excess": -0.02},
             1: {"n": 100, "mean_excess": -0.04},
             2: {"n": 100, "mean_excess": -0.05}}
    assert classify(stats)[0] == "✅纳入"      # 单调递减


def test_classify_undetermined_when_small_n():
    stats = {0: {"n": 100, "mean_excess": -0.02},
             1: {"n": 3, "mean_excess": -0.04},
             2: {"n": 100, "mean_excess": -0.05}}
    assert classify(stats)[0] == "⚠️待定"      # 有桶 n<5


def test_classify_delete_when_no_relationship():
    stats = {0: {"n": 100, "mean_excess": -0.02},
             1: {"n": 100, "mean_excess": 0.01},
             2: {"n": 100, "mean_excess": -0.03}}
    assert classify(stats)[0] == "❌删除"      # 折返，无单调
