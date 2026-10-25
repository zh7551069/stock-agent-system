"""对账官 · 上游转换（judge 报告 JSON → JudgedSignal）单测。

用与真实报告同构的合成 dict（字段名/结构取自 judge/reports/*.json 实测），
不连库、不 import judge。
"""

from reconcile.from_judge import from_baseline, from_probe


def _baseline_report() -> dict:
    """对齐 judge/reports/baseline_*.json 的 by_horizon 结构。"""
    return {
        "start": "2023-01-01", "end": "2026-08-25", "n_days": 879,
        "by_horizon": {
            "20": {
                "treat": {"mean_excess": -0.0343, "mean_excess_net": -0.0358, "t": -24.7, "n_days": 879},
                "ctrl": {"mean_excess": 0.0012, "mean_excess_net": 0.0003, "t": 0.5, "n_days": 879},
                "paired_diff": -0.0361, "paired_t": -18.89,
            }
        },
    }


def _probe_report() -> dict:
    """对齐 judge/reports/probe_*.json 的 signals 结构（含 net，当前代码 schema）。"""
    return {
        "start": "2023-01-01", "end": "2026-08-25",
        "signals": {
            "flow_top": {
                "desc": "主力净流入占比最高 10%",
                "n_days": 714, "n_treat": 281617, "n_ctrl": 142563,
                "horizons": {
                    "20": {
                        "treat_mean": 0.0041, "treat_mean_net": 0.0026,
                        "treat_t": 2.07, "ctrl_mean": 0.0083,
                        "paired_diff": -0.0042, "paired_t": -5.16,
                        "win_rate": 0.4648,
                    }
                },
            }
        },
    }


def test_from_baseline_maps_fields():
    js = from_baseline(_baseline_report())
    assert js.decision_id == "limit_up_baseline"
    assert js.excess == -0.0358          # treat.mean_excess_net
    assert js.t_stat == -24.7            # treat.t
    assert js.paired_t == -18.89         # paired_t
    assert js.layered_win_rate is None
    assert js.regime_slice == "全样本"


def test_from_probe_maps_fields():
    js = from_probe(_probe_report(), "flow_top")
    assert js.decision_id == "flow_top"
    assert js.excess == 0.0026           # treat_mean_net
    assert js.t_stat == 2.07
    assert js.paired_t == -5.16
    assert js.layered_win_rate == 0.4648


def test_from_probe_falls_back_to_gross_when_no_net():
    # 旧报告（10-13 schema）无 treat_mean_net → 回退 treat_mean
    rep = _probe_report()
    del rep["signals"]["flow_top"]["horizons"]["20"]["treat_mean_net"]
    js = from_probe(rep, "flow_top")
    assert js.excess == 0.0041           # 回退到 treat_mean


def test_from_probe_respects_horizon():
    rep = {
        "signals": {
            "s": {"horizons": {
                "5": {"treat_mean_net": 0.01, "treat_t": 1.0, "paired_t": -2.0, "win_rate": 0.5},
                "20": {"treat_mean_net": -0.02, "treat_t": -3.0, "paired_t": -5.0, "win_rate": 0.4},
            }},
        },
    }
    js = from_probe(rep, "s", horizon=5)
    assert js.excess == 0.01
    assert js.paired_t == -2.0
