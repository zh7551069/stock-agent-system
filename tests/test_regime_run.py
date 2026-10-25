"""任务 16 跑数 · 纯函数单测（不连主库）。"""

from regime.run import binary_compare, classify_labeled, load_day_excess, slice_dimension


def _report() -> dict:
    return {
        "start": "2023-01-03", "end": "2023-01-06",
        "per_day": [
            {"date": "2023-01-03", "treat": {"avg_excess_net": {"20": -0.05}}},
            {"date": "2023-01-04", "treat": {"avg_excess_net": {"20": -0.03}}},
            {"date": "2023-01-05", "treat": {"avg_excess_net": {"20": -0.01}}},
            {"date": "2023-01-06", "treat": {"avg_excess_net": {"20": None}}},  # 缺失日跳过
        ],
    }


def test_load_day_excess_skips_none():
    d = load_day_excess(_report())
    assert d == {"2023-01-03": -0.05, "2023-01-04": -0.03, "2023-01-05": -0.01}


def test_slice_dimension_groups_and_means():
    excess = {"d1": -0.05, "d2": -0.03, "d3": -0.01}
    bucket = {"d1": "<30", "d2": "30-60", "d3": "30-60"}
    s = slice_dimension(excess, bucket)
    assert s["<30"] == {"n": 1, "mean_excess": -0.05}
    assert s["30-60"]["n"] == 2
    assert s["30-60"]["mean_excess"] == -0.02


def test_classify_labeled_monotonic_include():
    stats = {"<30": {"n": 100, "mean_excess": -0.037},
             "30-60": {"n": 100, "mean_excess": -0.032},
             "60+": {"n": 100, "mean_excess": -0.018}}
    state, reason = classify_labeled(stats, ["<30", "30-60", "60+"])
    assert state == "✅纳入"


def test_binary_compare_two_groups():
    excess = {"d1": -0.04, "d2": -0.03, "d3": -0.02, "d4": -0.01}
    gate = {"d1": "弱", "d2": "弱", "d3": "强", "d4": "强"}
    c = binary_compare(excess, gate)
    assert c["弱"] == {"n": 2, "mean_excess": -0.035}
    assert c["强"] == {"n": 2, "mean_excess": -0.015}
