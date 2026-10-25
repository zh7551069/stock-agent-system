"""评测集设计 · 覆盖率 + 优先级 单测。"""

from evalds import (
    coverage,
    coverage_gaps,
    priority_bucket,
    priority_score,
)


def test_priority_score_is_product():
    assert priority_score(10, 2) == 20.0
    assert priority_score(0.5, 0.2) == 0.1


def test_priority_bucket():
    assert priority_bucket(20) == "P0"
    assert priority_bucket(5) == "P1"
    assert priority_bucket(0.5) == "P2"
    assert priority_bucket(0.01) == "P3"


def test_coverage_counts():
    cases = [
        {"能力": "策略", "场景": "涨停", "难度": "简单", "目标": "效果"},
        {"能力": "策略", "场景": "暴跌", "难度": "复杂", "目标": "安全"},
        {"能力": "因子", "场景": "涨停", "难度": "简单", "目标": "效果"},
    ]
    cov = coverage(cases)
    assert cov["能力"] == {"策略": 2, "因子": 1}
    assert cov["场景"] == {"涨停": 2, "暴跌": 1}


def test_coverage_gaps_finds_uncovered():
    cases = [{"能力": "策略", "场景": "涨停", "难度": "简单", "目标": "效果"}]
    gaps = coverage_gaps(cases)
    assert "因子" in gaps["能力"]
    assert "横盘" in gaps["场景"]
    assert "安全" in gaps["目标"]
