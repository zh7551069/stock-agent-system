"""oracle_check.py 黑盒测试：Oracle 判定阈值。

第三方视角：Oracle 是判决器的能力下限测试，判定阈值（diff>2% 且 paired_t>10）
一旦松动，就会把「测不出正 alpha 的坏尺子」误判成「可信」。
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.oracle_check import HORIZONS, passes  # noqa: E402


def test_horizons_contract():
    assert HORIZONS == (5, 20)


def test_passes_true_when_all_windows_strong():
    report = {str(k): {"diff": 0.073, "paired_t": 106.5} for k in HORIZONS}
    assert passes(report) is True


def test_passes_false_when_diff_below_threshold():
    report = {"5": {"diff": 0.073, "paired_t": 106.5},
              "20": {"diff": 0.01, "paired_t": 107.4}}   # T+20 diff 1% < 2%
    assert passes(report) is False


def test_passes_false_when_paired_t_below_threshold():
    report = {"5": {"diff": 0.073, "paired_t": 106.5},
              "20": {"diff": 0.15, "paired_t": 5.0}}     # T+20 paired_t 5 < 10
    assert passes(report) is False


def test_passes_treats_missing_as_false():
    report = {"5": {"diff": None, "paired_t": None}, "20": {"diff": None, "paired_t": None}}
    assert passes(report) is False
