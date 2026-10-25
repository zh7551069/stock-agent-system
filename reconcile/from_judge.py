"""对账官 · 上游转换：judge 报告 JSON → JudgedSignal。

把 ``judge.baseline`` / ``judge.probe`` 的 ``by_horizon`` / ``signals`` 结构转成
对账官的输入。这是「判决器真实输出 → 对账官闭环」的接线；纯函数、不连库、不 import judge
（保持物理隔离）。

⚠️ 信号级 vs 决策级：baseline/probe 产出的是**信号级**汇总（跨多日聚合），此时
``JudgedSignal.decision_id`` 语义 = **归因主体 id**（= 信号名），是溯源图
（``signal → factor → caliber``）的根；只有 ``judge()`` 单决策级时才等于决策 id。
"""
from __future__ import annotations

from typing import Any

from reconcile.wire import JudgedSignal

#: 主观察窗（T+20，判决器默认的长期窗口）。
DEFAULT_HORIZON = 20

#: 基线报告的信号名（涨停 vs 同日随机对照）。
BASELINE_SIGNAL = "limit_up_baseline"


def from_baseline(
    report: dict[str, Any],
    *,
    horizon: int = DEFAULT_HORIZON,
    subject: str = BASELINE_SIGNAL,
    regime_slice: str = "全样本",
) -> JudgedSignal:
    """``judge.baseline`` 的 ``by_horizon`` → 单个 JudgedSignal。

    映射：excess = ``treat.mean_excess_net``（涨停篮净超额）、t_stat = ``treat.t``、
    paired_t = ``paired_t``（vs 同日随机对照）。
    """
    row = report["by_horizon"][str(horizon)]
    treat = row["treat"]
    return JudgedSignal(
        decision_id=subject,
        signal=BASELINE_SIGNAL,
        regime_slice=regime_slice,
        excess=treat.get("mean_excess_net"),
        t_stat=treat.get("t"),
        paired_t=row.get("paired_t"),
        layered_win_rate=None,
    )


def from_probe(
    report: dict[str, Any],
    signal: str,
    *,
    horizon: int = DEFAULT_HORIZON,
    regime_slice: str = "全样本",
) -> JudgedSignal:
    """``judge.probe`` 的 ``signals[signal]`` → 单个 JudgedSignal。

    映射：excess = ``treat_mean_net``（旧报告无 net 时回退 ``treat_mean``）、
    t_stat = ``treat_t``、paired_t = ``paired_t``、layered_win_rate = ``win_rate``。
    """
    s = report["signals"][signal]
    row = s["horizons"][str(horizon)]
    excess = row.get("treat_mean_net", row.get("treat_mean"))
    return JudgedSignal(
        decision_id=signal,
        signal=signal,
        regime_slice=regime_slice,
        excess=excess,
        t_stat=row.get("treat_t"),
        paired_t=row.get("paired_t"),
        layered_win_rate=row.get("win_rate"),
    )
