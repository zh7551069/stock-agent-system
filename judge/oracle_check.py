"""Oracle 检验：判决器的**能力下限测试**（决定性）。

## 为什么需要它

第 3 关用「低换手」当"已知正 alpha"失败了，但失败原因可能是：
  (a) 判决器测不出正 alpha（尺子坏了）→ 前面所有负结论作废
  (b) 低换手在样本内本就没有 alpha（超额全来自 beta）→ 尺子没问题

这两种解释无法靠"再换一个因子猜"来区分。所以用一个**不依赖任何因子先验**的测试：

**oracle 信号**：故意偷看未来 —— 每天选出实际 T+k 超额最高的 N 只当"处理组"。
一个正确的判决器**必然**对它给出巨大的正号。

- 若 oracle 显示强正（t 极大）→ **判决器有能力识别真机会**，之前的负结论可信。
- 若 oracle 都测不出正 → **判决器坏了**，全部结果必须重来。

用法：
    .venv/bin/python judge/oracle_check.py --start 2023-01-01 --end 2026-08-25
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.bulk import BulkLibrary                        # noqa: E402
from judge.outcome import Decision, judge                 # noqa: E402
from judge.stats import day_series, mean, paired_diff, tstat  # noqa: E402

HORIZONS = (5, 20)


def passes(report: dict) -> bool:
    """Oracle 判定阈值：每个窗口 diff > 2% 且 paired_t > 10 才判「有能力识别正 alpha」。"""
    return all(
        (report[str(k)]["diff"] or 0) > 0.02 and (report[str(k)]["paired_t"] or 0) > 10
        for k in HORIZONS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--sample", type=int, default=600, help="每日抽样评估的股票数")
    ap.add_argument("--top", type=int, default=150, help="oracle 取前多少只")
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)

    with BulkLibrary() as lib:
        cal = [r[0] for r in lib._con.execute("SELECT date FROM trade_cal ORDER BY date").fetchall()]
        idx = {d: i for i, d in enumerate(cal)}
        data_max = lib._con.execute("SELECT max(date) FROM tech_factor_qfq").fetchone()[0]
        rows = lib._con.execute(
            "SELECT DISTINCT date FROM tech_factor_qfq WHERE date >= ? AND date <= ? ORDER BY date",
            [start, end]).fetchall()
        days = [d for (d,) in rows
                if d in idx and idx[d] + max(HORIZONS) < len(cal)
                and cal[idx[d] + max(HORIZONS)] <= data_max]
        print(f"可用独立日 {len(days)} 个（{days[0]} ~ {days[-1]}）")

        # 每天：抽样评估 → 按真实结果排序 → 取 top 当处理组、随机当对照组
        rec = {k: {"top": [], "ctrl": []} for k in HORIZONS}
        for i, T in enumerate(days, 1):
            univ = lib.universe(T)
            if len(univ) < args.sample:
                continue
            rng = random.Random(int(T.strftime("%Y%m%d")))
            pool = rng.sample(univ, args.sample)
            days_after = lib.trading_days_after(T, max(HORIZONS))
            if len(days_after) < max(HORIZONS):
                continue
            lib.prefetch_day(pool, days_after[0], days_after[-1])

            scored = []
            for c in pool:
                o = judge(Decision(c, "buy", T, horizons=HORIZONS), lib)
                if o.tradable:
                    scored.append((c, o.excess[5], o.excess[20]))
            if len(scored) < args.top * 2:
                continue
            ctrl = scored[: args.top]                     # 抽样顺序已是随机的，取前 N 即随机组
            for k, pos in ((5, 1), (20, 2)):
                known = [x for x in scored if x[pos] is not None]
                known.sort(key=lambda x: -x[pos])          # 偷看未来：按真实超额倒序
                top = known[: args.top]
                rec[k]["top"] += [{"date": T.isoformat(), f"ex{k}": x[pos]} for x in top]
                rec[k]["ctrl"] += [{"date": T.isoformat(), f"ex{k}": x[pos]} for x in ctrl
                                   if x[pos] is not None]
            if i % 100 == 0 or i == len(days):
                print(f"  …{i}/{len(days)}  最新 {T}")

    report = {}
    print(f"\n{'='*100}\n## Oracle 检验：偷看未来选「实际最强」的票\n")
    print(f"   {'窗口':>5} {'oracle 组超额':>13} {'t':>8} {'随机组超额':>11} {'t':>8} "
          f"{'差值':>9} {'配对t':>8} {'共同日':>7}")
    for k in HORIZONS:
        a = day_series(rec[k]["top"], f"ex{k}")
        b = day_series(rec[k]["ctrl"], f"ex{k}")
        m, t, common = paired_diff(a, b)
        ta, tb = tstat(a), tstat(b)
        ma, mb = mean(a), mean(b)
        print(f"   {'T+'+str(k):>5} "
              f"{(f'{ma*100:+.2f}%' if ma is not None else ''):>13} "
              f"{(f'{ta:+.2f}' if ta is not None else ''):>8} "
              f"{(f'{mb*100:+.2f}%' if mb is not None else ''):>11} "
              f"{(f'{tb:+.2f}' if tb is not None else ''):>8} "
              f"{(f'{m*100:+.2f}%' if m is not None else ''):>9} "
              f"{(f'{t:+.2f}' if t is not None else ''):>8} {common:>7}")
        report[str(k)] = {"oracle_mean": ma, "oracle_t": ta, "ctrl_mean": mb,
                          "ctrl_t": tb, "diff": m, "paired_t": t, "common_days": common}

    ok = passes(report)
    print(f"\n   判定：{'✅ 判决器有能力识别正 alpha —— 之前的负结论可信' if ok else '❌ 判决器未能识别正 alpha —— 全部结果需重来'}")
    report["passed"] = ok

    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"oracle_{args.start}_{args.end}.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n明细已落盘：{p}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
