"""判决器自校准：证明这把尺子**既能测出负、也能测出正**。

## 为什么必须有这一步

判决器如果只会输出负号，它和"永远说不操作"的旧系统没有本质区别——
负号可能全是判决器自身的偏差，而不是市场的真相。

三关：

1. **恒等检验**（纯函数，不需数据库）
   同一组自己减自己 → 配对差值必须**恒等于 0**。验证配对逻辑本身无偏。

2. **零假设检验**
   把同日随机票**随机劈成两半**：处理组 vs 对照组，走完全相同的判决路径。
   两边都没有任何信号 → 配对差值必须 **≈0 且不显著**。
   若这里出现显著非零，说明判决器会**凭空造出 alpha**。

3. **已知正 alpha 检验**（能力上限验证）
   用一个文献上稳健、且在 A 股被反复验证的**正向**因子当处理组：
   **低换手率**（换手率是 A 股最强的负向因子之一 → 低换手应跑赢）。
   若判决器**测不出正号**，说明它没有能力识别真机会，前面所有负结论都要作废。

用法：
    .venv/bin/python judge/calibrate.py --start 2023-01-01 --end 2026-08-25
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

HORIZONS = (1, 5, 20)
TURNOVER_LOOKBACK = 20          # 20 日平均换手
BUFFER_DAYS = 40                # 窗口缓冲


def judge_codes(lib, T: dt.date, codes: list[str]) -> list[dict]:
    days_after = lib.trading_days_after(T, max(HORIZONS))
    if len(days_after) < max(HORIZONS):
        return []
    lib.prefetch_day(codes, days_after[0], days_after[-1])
    out = []
    for c in codes:
        o = judge(Decision(c, "buy", T, horizons=HORIZONS), lib)
        if o.tradable:
            out.append({"date": T.isoformat(), **{f"ex{k}": o.excess[k] for k in HORIZONS}})
    return out


def show(title: str, rec_t: list[dict], rec_c: list[dict]) -> dict:
    print(f"\n{'='*100}\n## {title}\n")
    print(f"   可成交：处理组 {len(rec_t):,} 笔 / 对照组 {len(rec_c):,} 笔")
    print(f"   {'窗口':>5} {'处理组超额':>10} {'t':>7} {'对照组超额':>10} {'t':>7} "
          f"{'差值':>9} {'配对t':>8} {'共同日':>7}")
    res = {}
    for k in HORIZONS:
        a = day_series(rec_t, f"ex{k}")
        b = day_series(rec_c, f"ex{k}")
        m, t, common = paired_diff(a, b)
        ta, tb = tstat(a), tstat(b)
        ma, mb = mean(a), mean(b)
        print(f"   {'T+'+str(k):>5} "
              f"{(f'{ma*100:+.2f}%' if ma is not None else ''):>10} "
              f"{(f'{ta:+.2f}' if ta is not None else ''):>7} "
              f"{(f'{mb*100:+.2f}%' if mb is not None else ''):>10} "
              f"{(f'{tb:+.2f}' if tb is not None else ''):>7} "
              f"{(f'{m*100:+.2f}%' if m is not None else ''):>9} "
              f"{(f'{t:+.2f}' if t is not None else ''):>8} {common:>7}")
        res[str(k)] = {"treat_mean": ma, "treat_t": ta, "ctrl_mean": mb, "ctrl_t": tb,
                       "diff": m, "paired_t": t, "common_days": common}
    return res


def identity_check() -> bool:
    """恒等检验：同一序列自己减自己，差值必须恒为 0。"""
    from judge.stats import DaySeries
    days = [f"d{i}" for i in range(1, 11)]
    vals = [0.01 * i for i in range(1, 11)]
    s = DaySeries(days, vals)
    m, t, common = paired_diff(s, s)
    ok = (m == 0.0 and common == 10)
    print(f"\n## 恒等检验（同一组自减）\n   差值={m}  共同日={common}  -> {'✅ 通过' if ok else '❌ 失败'}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--per-side", type=int, default=200, help="零假设检验每侧抽多少只")
    ap.add_argument("--control", type=int, default=200)
    ap.add_argument("--quintile", type=float, default=0.20, help="低换手取最低多少比例")
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)

    report = {"start": args.start, "end": args.end}
    with BulkLibrary() as lib:
        cal = [r[0] for r in lib._con.execute("SELECT date FROM trade_cal ORDER BY date").fetchall()]
        idx = {d: i for i, d in enumerate(cal)}
        data_max = lib._con.execute("SELECT max(date) FROM tech_factor_qfq").fetchone()[0]

        # 可用信号日：之后有足够交易日，且数据已到
        rows = lib._con.execute(
            "SELECT DISTINCT date FROM tech_factor_qfq WHERE date >= ? AND date <= ? ORDER BY date",
            [start, end]).fetchall()
        days = [d for (d,) in rows
                if d in idx and idx[d] + max(HORIZONS) < len(cal)
                and cal[idx[d] + max(HORIZONS)] <= data_max]
        print(f"可用独立日 {len(days)} 个（{days[0]} ~ {days[-1]}）")

        # ---------------- 第 1 关：恒等 ----------------
        report["identity_ok"] = identity_check()

        # ---------------- 第 2 关：零假设 ----------------
        rec_t, rec_c = [], []
        for T in days:
            univ = lib.universe(T)
            if len(univ) < 2 * args.per_side:
                continue
            rng = random.Random(int(T.strftime("%Y%m%d")))
            picked = rng.sample(univ, 2 * args.per_side)
            half = args.per_side
            a_codes, b_codes = picked[:half], picked[half:]
            rec_t += judge_codes(lib, T, a_codes)
            rec_c += judge_codes(lib, T, b_codes)
        report["null_test"] = show(
            "第 2 关 · 零假设检验：同日随机票随机劈两半（两边都无信号）\n"
            f"   期望：配对差值 ≈ 0 且 t 不显著。若显著非零 = 判决器会凭空造 alpha",
            rec_t, rec_c)

        # ---------------- 第 3 关：已知正 alpha（低换手）----------------
        buf = cal[max(0, idx[start] - BUFFER_DAYS)] if start in idx else start
        turn = lib._con.execute(f"""
            WITH x AS (
              SELECT code, date, turnover,
                     AVG(turnover) OVER (PARTITION BY code ORDER BY date
                                         ROWS BETWEEN {TURNOVER_LOOKBACK-1} PRECEDING AND CURRENT ROW) AS t20,
                     ROW_NUMBER() OVER (PARTITION BY code ORDER BY date) AS rn
              FROM tech_factor_qfq WHERE date >= ? AND date <= ?)
            SELECT date, code, t20 FROM x WHERE rn >= {TURNOVER_LOOKBACK} AND date >= ?
        """, [buf, end, start]).fetchall()
        by_day: dict[dt.date, list[tuple[float, str]]] = {}
        for d, c, t20 in turn:
            if t20 is not None and t20 > 0 and c:
                by_day.setdefault(d, []).append((t20, c))
        print(f"\n   换手率数据：{len(turn):,} 行 / {len(by_day)} 个交易日")

        rec_t2, rec_c2 = [], []
        for T in days:
            lst = by_day.get(T)
            if not lst or len(lst) < 50:
                continue
            lst.sort()
            n = max(1, int(len(lst) * args.quintile))
            treat = [c for _, c in lst[:n]]                      # 最低换手
            univ = lib.universe(T)
            pool = [c for c in univ if c not in set(treat)]
            rng = random.Random(int(T.strftime("%Y%m%d")) + 7)
            ctrl = sorted(rng.sample(pool, min(args.control, len(pool))))
            rec_t2 += judge_codes(lib, T, sorted(set(treat)))
            rec_c2 += judge_codes(lib, T, ctrl)
        report["low_turnover"] = show(
            f"第 3 关 · 已知正 alpha：{args.quintile:.0%} 最低的 {TURNOVER_LOOKBACK} 日平均换手\n"
            "   期望：配对差值应为【正】。若测不出正号 = 判决器无能力识别真机会",
            rec_t2, rec_c2)

    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"calibrate_{args.start}_{args.end}.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n校准结果已落盘：{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
