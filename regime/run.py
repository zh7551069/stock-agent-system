"""任务 16 跑数：按 regime 维度切片 879 天独立日 → 三态判定。

以「日」为独立样本（对齐 risks.md「用交易笔数当样本→自由度虚高」的对策）：
1. 从 baseline 报告的 per_day 取每日「涨停池 T+N 剔beta净超额」（独立日样本）。
2. 从主库查每日市场级维度（涨停家数 + 沪深300 beta）。
3. 按维度分桶聚合超额，用 :func:`regime.buckets.classify` 出三态结论。

依赖主库（只读）；查询为批量（879 天 2 次），非逐条。
"""

from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from typing import Callable, Mapping, Sequence

from regime.buckets import classify
from regime.tagging import beta_bucket, breadth_bucket, limit_up_bucket


def load_day_excess(report: Mapping, horizon: int = 20) -> dict[str, float]:
    """baseline 报告 per_day → ``{date: treat.avg_excess_net[horizon]}``（净超额）。"""
    out: dict[str, float] = {}
    for d in report.get("per_day", []):
        ex = d.get("treat", {}).get("avg_excess_net", {}).get(str(horizon))
        if ex is not None:
            out[d["date"]] = float(ex)
    return out


def load_limit_up_series(con, start: dt.date, end: dt.date) -> dict[str, int]:
    """每交易日 → 涨停家数（批量一次查）。"""
    rows = con.execute(
        """
        SELECT d.date, count(*) FROM daily d
        JOIN limit_price l ON d.code = l.code AND d.date = l.date AND d.market = l.market
        WHERE d.close >= l.limit_up AND d.pct_chg > 0 AND d.date BETWEEN ? AND ?
        GROUP BY d.date
        """,
        [start, end],
    ).fetchall()
    return {str(r[0]): int(r[1]) for r in rows}


def load_bench_series(con, start: dt.date, end: dt.date) -> dict[str, float]:
    """每交易日 → 沪深300 pct_chg（小数，批量一次查）。"""
    from regime.query import pct_to_decimal

    rows = con.execute(
        "SELECT date, pct_chg FROM index_daily WHERE code = 'sh000300' AND date BETWEEN ? AND ?",
        [start, end],
    ).fetchall()
    return {str(r[0]): pct_to_decimal(r[1]) for r in rows if r[1] is not None}


def load_breadth_series(con, start: dt.date, end: dt.date) -> dict[str, float]:
    """每交易日 → 市场宽度（站上 MA20 占比 [0,1]，批量一次查）。"""
    rows = con.execute(
        """
        SELECT date, avg(CASE WHEN close > ma20 THEN 1.0 ELSE 0.0 END)
        FROM tech_factor_qfq WHERE date BETWEEN ? AND ? AND close IS NOT NULL
        GROUP BY date
        """,
        [start, end],
    ).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}


def load_shanghai_gate(con, start: dt.date, end: dt.date) -> dict[str, str]:
    """每交易日 → 大盘闸门状态（上证 close vs 其 20 日均线：强/弱）。

    从 ``start-40`` 天起查，保证窗口首日的 MA20 有效；只返回 ``[start, end]`` 内状态。
    """
    q_start = start - dt.timedelta(days=40)
    rows = con.execute(
        """
        SELECT date, close, avg(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma20
        FROM index_daily WHERE code = 'sh000001' AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        [q_start, end],
    ).fetchall()
    out: dict[str, str] = {}
    for r in rows:
        d = r[0]
        if d < start:
            continue
        if r[2] is None:
            continue
        out[str(d)] = "强" if r[1] > r[2] else "弱"
    return out


def binary_compare(day_excess: Mapping[str, float], group_map: Mapping[str, str]) -> dict[str, dict]:
    """二组均值对比：``{group: {n, mean_excess}}``（用于二元闸门/信号，非单调桶）。"""
    agg: dict[str, list[float]] = defaultdict(list)
    for d, ex in day_excess.items():
        g = group_map.get(d)
        if g is not None:
            agg[g].append(ex)
    return {g: {"n": len(v), "mean_excess": sum(v) / len(v)} for g, v in agg.items()}


def slice_dimension(day_excess: Mapping[str, float], day_bucket: Mapping[str, str]) -> dict[str, dict]:
    """按维度桶分组，返回 ``{bucket: {n, mean_excess}}``。"""
    agg: dict[str, list[float]] = defaultdict(list)
    for date, ex in day_excess.items():
        b = day_bucket.get(date)
        if b is not None:
            agg[b].append(ex)
    return {b: {"n": len(v), "mean_excess": sum(v) / len(v)} for b, v in agg.items()}


def classify_labeled(bucket_stats: Mapping[str, dict], order: Sequence[str], *, min_n: int = 5) -> tuple[str, str]:
    """按显式桶序 → 三态判定（把标签桶映射到 0..k-1 再 classify）。"""
    stats = {i: bucket_stats[b] for i, b in enumerate(order) if b in bucket_stats}
    return classify(stats, min_n=min_n)


def run_validation(report: Mapping, con) -> list[dict]:
    """端到端：切 2 个市场维度（涨停家数 / 大盘 beta），返回每维三态结论。"""
    start = dt.date.fromisoformat(report["start"])
    end = dt.date.fromisoformat(report["end"])
    day_excess = load_day_excess(report)

    lu = load_limit_up_series(con, start, end)
    bench = load_bench_series(con, start, end)

    results = []

    # 维度 1：涨停家数
    lu_bucket = {d: limit_up_bucket(c) for d, c in lu.items()}
    lu_stats = slice_dimension(day_excess, lu_bucket)
    state, reason = classify_labeled(lu_stats, ["<30", "30-60", "60+"])
    results.append({"dim": "涨停家数", "state": state, "reason": reason,
                    "buckets": {b: round(s["mean_excess"], 4) for b, s in lu_stats.items()},
                    "n": {b: s["n"] for b, s in lu_stats.items()}})

    # 维度 2：大盘 beta
    beta_bucket_map = {d: beta_bucket(p) for d, p in bench.items()}
    beta_stats = slice_dimension(day_excess, beta_bucket_map)
    state, reason = classify_labeled(beta_stats, ["跌", "平", "涨"])
    results.append({"dim": "大盘 beta", "state": state, "reason": reason,
                    "buckets": {b: round(s["mean_excess"], 4) for b, s in beta_stats.items()},
                    "n": {b: s["n"] for b, s in beta_stats.items()}})

    # 维度 3：市场宽度（站上 MA20 占比）
    breadth = load_breadth_series(con, start, end)
    br_bucket = {d: breadth_bucket(f) for d, f in breadth.items()}
    br_stats = slice_dimension(day_excess, br_bucket)
    state, reason = classify_labeled(br_stats, ["<30%", "30-70%", ">70%"])
    results.append({"dim": "市场宽度", "state": state, "reason": reason,
                    "buckets": {b: round(s["mean_excess"], 4) for b, s in br_stats.items()},
                    "n": {b: s["n"] for b, s in br_stats.items()}})

    return results


def classify_slice_turnover(slice_report: Mapping) -> tuple[str, str, dict]:
    """换手率维度（slice 报告 ``res.by_turnover`` 桶，T+20 超额）→ 三态 + 桶统计。

    这是任务 16 第 5 项「换手率 <5% 的正式边界」的数据来源：slice 的 by_turnover 桶
    （涨停池个股换手率 <5% / 5-15% / >15%），桶序为换手率升序。
    """
    bt = slice_report["res"]["by_turnover"]
    order = ["<5%", "5-15%", ">15%"]
    stats = {b: {"n": bt[b]["n"], "mean_excess": bt[b]["t20"]} for b in order if b in bt}
    state, reason = classify_labeled(stats, order)
    return state, reason, stats


def _main() -> None:
    import duckdb
    import os
    from pathlib import Path

    report_path = Path(os.environ.get("STOCK_REPORT", "judge/reports/baseline_2023-01-01_2026-08-25.json"))
    db_path = os.environ.get("STOCK_DB", "/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb")
    report = json.loads(report_path.read_text())
    con = duckdb.connect(db_path, read_only=True)
    try:
        for r in run_validation(report, con):
            print(f"{r['dim']}: {r['state']}（{r['reason']}）")
            print(f"  桶超额: {r['buckets']}")
            print(f"  桶样本: {r['n']}")
    finally:
        con.close()


if __name__ == "__main__":
    _main()
