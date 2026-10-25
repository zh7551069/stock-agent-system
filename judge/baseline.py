"""基线回放：把「T 日收盘涨停 → T+1 开盘买入」当一条决策规则，跨多个**独立日**回放。

为什么要跨独立日：
同一天的 70 只票是高度相关的，等于 1 个样本。
按项目纪律，**独立日 >= 30 才有资格下结论**；本脚本就负责产出这个结论。

为什么要对照组：
"涨停后 T+5 超额 +5%" 可能只是这段时间的市场风格，不是"涨停"这件事的信息。
对照组 = **同一天**随机抽一批非涨停票，走完全相同的判决路径，
再做**配对检验**（同一天、两组相减），才能回答"涨停本身有没有信息"。

用法：
    .venv/bin/python judge/baseline.py --start 2023-01-01 --end 2026-08-25 --control 200
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.bulk import BulkLibrary          # noqa: E402
from judge.outcome import COST_RATE, Decision, judge, summarize   # noqa: E402
from judge.stats import DaySeries, mean, paired_t, tstat   # noqa: E402

HORIZONS = (1, 3, 5, 20)
MIN_DAYS_FOR_CONCLUSION = 30


# 统计口径统一委托 judge.stats（DaySeries 按日期配对、min_n=5）。
# 此处原本自带一份「索引配对 + min_n=2 + tstat 返回 tuple」的分叉实现（P1），已删除。


def candidate_days(lib: BulkLibrary, start: dt.date, end: dt.date,
                   min_samples: int, max_h: int) -> list[dt.date]:
    """候选独立日：当日涨停池样本足够，且**之后的 max_h 个交易日数据已经存在**。

    注意：日历必须取**全量**，不能按 --end 截断，否则"之后还有 N 个交易日"永远不成立。
    同时要用实际数据上界（tech_factor_qfq 的最大日期）兜底——日历有那天不代表数据有那天。
    """
    cal = [r[0] for r in lib._con.execute(
        "SELECT date FROM trade_cal ORDER BY date").fetchall()]
    idx = {d: i for i, d in enumerate(cal)}
    data_max = lib._con.execute("SELECT max(date) FROM tech_factor_qfq").fetchone()[0]
    rows = lib._con.execute(
        "SELECT 交易时间, count(*) FROM zt_pool_limit_up "
        "WHERE 交易时间 >= ? AND 交易时间 <= ? GROUP BY 1", [start, end]).fetchall()
    out = []
    for d, n in rows:
        if n < min_samples or d not in idx:
            continue
        need = idx[d] + max_h
        if need >= len(cal):
            continue
        if cal[need] > data_max:      # 结果窗口还没落到数据上
            continue
        out.append(d)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--control", type=int, default=200, help="每日对照组抽多少只")
    ap.add_argument("--min-samples", type=int, default=20, help="当日涨停池至少多少只")
    ap.add_argument("--max-treatment", type=int, default=300)
    args = ap.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    max_h = max(HORIZONS)

    with BulkLibrary() as lib:
        days = candidate_days(lib, start, end, args.min_samples, max_h)
        print(f"候选独立日 {len(days)} 个（{days[0] if days else '-'} ~ {days[-1] if days else '-'}）")
        if len(days) < MIN_DAYS_FOR_CONCLUSION:
            print(f"⚠️ 独立日不足 {MIN_DAYS_FOR_CONCLUSION}，结果不具备结论资格")

        per_day = []
        for i, T in enumerate(days, 1):
            treat = sorted(lib.zt_limit_up_codes(T))[: args.max_treatment]
            univ = lib.universe(T)
            pool = [c for c in univ if c not in set(treat)]
            rng = random.Random(int(T.strftime("%Y%m%d")))     # 确定性抽样
            ctrl = sorted(rng.sample(pool, min(args.control, len(pool))))

            days_after = lib.trading_days_after(T, max_h)
            if not days_after:
                continue
            lib.prefetch_day(treat + ctrl, days_after[0], days_after[-1])

            ot = [judge(Decision(c, "buy", T, horizons=HORIZONS), lib) for c in treat]
            oc = [judge(Decision(c, "buy", T, horizons=HORIZONS), lib) for c in ctrl]
            qt, qc = summarize(ot, HORIZONS), summarize(oc, HORIZONS)

            sh = lib._con.execute(
                "SELECT pct_chg FROM index_daily WHERE code='sh000001' AND date=?", [T]).fetchone()
            per_day.append({
                "date": T.isoformat(), "sh_pct": sh[0] if sh else None,
                "treat": qt.as_dict(), "ctrl": qc.as_dict(),
            })
            if i % 20 == 0 or i == len(days):
                print(f"  …{i}/{len(days)}  最新 {T}  可成交 {qt.n_tradable}/{qc.n_tradable}")

    # ------------------------------------------------------------------ 汇总
    def series(group: str, k: int, field: str) -> DaySeries:
        """按独立日聚合的序列（携带日期），配对时按日期交集对齐而非索引。"""
        days, vals = [], []
        for d in per_day:
            v = d[group][field].get(str(k))
            if v is not None:
                days.append(d["date"])
                vals.append(v)
        return DaySeries(days, vals)

    report = {"start": args.start, "end": args.end, "n_days": len(per_day),
              "cost": COST_RATE, "horizons": list(HORIZONS),
              "by_horizon": {}, "per_day": per_day}

    print(f"\n{'='*104}")
    print(f"基线回放结果  |  {len(per_day)} 个独立日  |  对照抽样 {args.control} 只/日  |  往返成本 {COST_RATE*100:.2f}%")
    print(f"{'='*104}")
    print(f"{'窗口':>5} {'组':>4} {'日数':>5} {'平均超额(毛)':>11} {'平均超额(净)':>11} "
          f"{'t值':>7} {'胜日占比':>9} {'日均胜率':>9} {'可成交':>7}")
    for k in HORIZONS:
        row = {}
        for g, label in (("treat", "涨停"), ("ctrl", "对照")):
            ex = series(g, k, "avg_excess")
            exn = series(g, k, "avg_excess_net")
            hit = series(g, k, "hit_rate")
            m, t = mean(ex), tstat(ex)
            mn = mean(exn)
            n_tr = sum(d[g]["n_tradable"] for d in per_day)
            win_day = (sum(1 for x in ex if x > 0) / len(ex)) if ex else None
            print(f"{'T+'+str(k):>5} {label:>4} {len(ex):>5} "
                  f"{('' if m is None else f'{m*100:+.2f}%'):>11} "
                  f"{('' if mn is None else f'{mn*100:+.2f}%'):>11} "
                  f"{('' if t is None else f'{t:+.2f}'):>7} "
                  f"{('' if win_day is None else f'{win_day*100:.1f}%'):>9} "
                  f"{('' if not hit else f'{mean(hit)*100:.1f}%'):>9} {n_tr:>7}")
        # 配对检验：同一天，涨停组 - 对照组（成本两侧同扣，配对差值不受影响）
        a, b = series("treat", k, "avg_excess"), series("ctrl", k, "avg_excess")
        pm, pt = paired_t(a, b)
        print(f"{'':>5} {'差值':>4} {'':>5} "
              f"{('' if pm is None else f'{pm*100:+.2f}%'):>11} {'':>11} "
              f"{('' if pt is None else f'{pt:+.2f}'):>7}   ← 配对 t（涨停 − 对照，成本抵消）")
        row["treat"] = {"mean_excess": mean(a), "mean_excess_net": mean(series("treat", k, "avg_excess_net")),
                        "t": tstat(a), "n_days": len(a)}
        row["ctrl"] = {"mean_excess": mean(b), "mean_excess_net": mean(series("ctrl", k, "avg_excess_net")),
                       "t": tstat(b), "n_days": len(b)}
        row["paired_diff"] = pm
        row["paired_t"] = pt
        report["by_horizon"][str(k)] = row

    # 分年，看是否依赖某段行情（"阳极必衰"这类问题的实证入口）
    print(f"\n{'-'*96}\n分年（T+5 平均超额）：")
    by_year: dict[str, dict[str, list[float]]] = {}
    for d in per_day:
        y = d["date"][:4]
        by_year.setdefault(y, {"treat": [], "ctrl": []})
        for g in ("treat", "ctrl"):
            v = d[g]["avg_excess"].get("5")
            if v is not None:
                by_year[y][g].append(v)
    for y in sorted(by_year):
        bt, bc = by_year[y]["treat"], by_year[y]["ctrl"]
        print(f"  {y}  日数 {len(bt):>3}  涨停 {mean(bt)*100:+.2f}%  "
              f"对照 {mean(bc)*100:+.2f}%  差值 {(mean(bt)-mean(bc))*100:+.2f}%")
    report["by_year"] = {y: {g: mean(v[g]) for g in v} for y, v in by_year.items()}

    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"baseline_{args.start}_{args.end}.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n明细已落盘：{p}")
    if len(per_day) < MIN_DAYS_FOR_CONCLUSION:
        print(f"⚠️ 独立日 {len(per_day)} < {MIN_DAYS_FOR_CONCLUSION}，**不得据此下结论**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
