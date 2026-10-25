"""假设检验流水线：同一套判决口径，换信号即可比较。

设计要点：
- **同一把尺子**：所有信号都用相同的入场（T+1 开盘）、相同的窗口（T+1/5/20）、
  相同的对照组（同日随机票）、相同的配对检验。这样跨信号的结果**才可比**。
- **独立样本单位是"日"不是"笔"**：同一天几十只票高度相关，必须先按日聚合成
  一个观测值，再对日序列做 t 检验。否则 t 值会被人为放大几十倍。
- **对照组同日同规则**：配对相减才能剥离当日市场风格。

内置信号（可扩展）：
    进攻侧：limit_up（T日涨停）
    恐慌侧：limit_down（T日跌停） / drop5（跌幅<=-5%） / drop3d（连跌3日）
            new_low60（创60日新低） / rsi6_lt20（RSI6<20）

用法：
    .venv/bin/python judge/probe.py --start 2023-01-01 --end 2026-08-25
    .venv/bin/python judge/probe.py --signals drop5,limit_down --control 100
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
from judge.stats import day_series, mean, paired_t, tstat  # noqa: E402

HORIZONS = (1, 5, 20)

#: 名称 -> (中文说明, 返回 (date, code) 的 SQL；占位符为 start,end 或 buf_start,end,start)
SIGNALS: dict[str, tuple[str, str]] = {
    "limit_up": (
        "T 日涨停（进攻侧基准）",
        "SELECT 交易时间 AS d, 代码 AS c FROM zt_pool_limit_up "
        "WHERE 交易时间 >= ? AND 交易时间 <= ?",
    ),
    "limit_down": (
        "T 日跌停（恐慌侧）",
        "SELECT 交易时间 AS d, 代码 AS c FROM zt_pool_limit_down "
        "WHERE 交易时间 >= ? AND 交易时间 <= ?",
    ),
    "drop5": (
        "T 日跌幅 <= -5%",
        "SELECT date AS d, code AS c FROM tech_factor_qfq "
        "WHERE date >= ? AND date <= ? AND pct_chg <= -5",
    ),
    "drop3d": (
        "连续 3 个交易日下跌",
        """
        WITH x AS (
          SELECT code, date, pct_chg,
                 LAG(pct_chg,1) OVER w AS p1,
                 LAG(pct_chg,2) OVER w AS p2
          FROM tech_factor_qfq WHERE date >= ? AND date <= ?
          WINDOW w AS (PARTITION BY code ORDER BY date))
        SELECT date AS d, code AS c FROM x
        WHERE pct_chg < 0 AND p1 < 0 AND p2 < 0 AND date >= ?
        """,
    ),
    "new_low60": (
        "收盘创 60 日新低",
        """
        WITH x AS (
          SELECT code, date, close,
                 MIN(close) OVER (PARTITION BY code ORDER BY date
                                  ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS mn,
                 ROW_NUMBER() OVER (PARTITION BY code ORDER BY date) AS rn
          FROM tech_factor_qfq WHERE date >= ? AND date <= ?)
        SELECT date AS d, code AS c FROM x
        WHERE close = mn AND rn >= 60 AND date >= ?
        """,
    ),
    "rsi6_lt20": (
        "RSI6 < 20（超卖）",
        "SELECT date AS d, code AS c FROM tech_factor_qfq "
        "WHERE date >= ? AND date <= ? AND rsi6 < 20",
    ),
}

#: 需要前置缓冲的信号（窗口函数要看历史） -> 缓冲天数
BUFFER_DAYS = {"drop3d": 30, "new_low60": 120}


#: 需要**按日横截面排序取分位**的信号：名称 -> (说明, 返回 (d,c,v) 的 SQL, 取多少比例, 是否取高)
#: 这类信号不能只筛代码，必须先按当日横截面排序——否则"资金流入最多"会变成"全样本最多"。
RANKED: dict[str, tuple[str, str, float, bool]] = {
    "flow_top": (
        "T 日主力净流入占比最高 10%（资金流入侧）",
        'SELECT strptime(CAST(交易日期 AS VARCHAR), \'%Y%m%d\')::DATE AS d, 股票代码 AS c, '
        '"今日主力净流入净占比（%）" AS v '
        "FROM stock_flow_em "
        "WHERE strptime(CAST(交易日期 AS VARCHAR), '%Y%m%d')::DATE >= ? "
        "AND strptime(CAST(交易日期 AS VARCHAR), '%Y%m%d')::DATE <= ?",
        0.10, True,
    ),
    "flow_bottom": (
        "T 日主力净流入占比最低 10%（资金流出侧）",
        'SELECT strptime(CAST(交易日期 AS VARCHAR), \'%Y%m%d\')::DATE AS d, 股票代码 AS c, '
        '"今日主力净流入净占比（%）" AS v '
        "FROM stock_flow_em "
        "WHERE strptime(CAST(交易日期 AS VARCHAR), '%Y%m%d')::DATE >= ? "
        "AND strptime(CAST(交易日期 AS VARCHAR), '%Y%m%d')::DATE <= ?",
        0.10, False,
    ),
    "lhb_net_top": (
        "T 日龙虎榜净买入额最高 10%",
        'SELECT 交易日期 AS d, 股票代码 AS c, "龙虎榜净买入额(元)" AS v '
        'FROM lhb_daily WHERE 交易日期 >= ? AND 交易日期 <= ? '
        'AND "龙虎榜净买入额(元)" IS NOT NULL',
        0.10, True,
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--control", type=int, default=200)
    ap.add_argument("--signals", default=",".join(SIGNALS))
    ap.add_argument("--max-treatment", type=int, default=400)
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    names = [s.strip() for s in args.signals.split(",") if s.strip()]

    results: dict[str, dict] = {}
    with BulkLibrary() as lib:
        cal = [r[0] for r in lib._con.execute("SELECT date FROM trade_cal ORDER BY date").fetchall()]
        idx = {d: i for i, d in enumerate(cal)}
        data_max = lib._con.execute("SELECT max(date) FROM tech_factor_qfq").fetchone()[0]

        for name in names:
            if name in RANKED:
                desc, sql, rank_frac, rank_high = RANKED[name]
            elif name in SIGNALS:
                desc, sql = SIGNALS[name]
                rank_frac, rank_high = None, True
            else:
                print(f"  跳过未知信号 {name}"); continue
            buf = BUFFER_DAYS.get(name, 0)
            buf_start = cal[max(0, idx[start] - buf)] if start in idx else start
            params = [buf_start, end, start] if buf else [start, end]
            sel = lib._con.execute(sql, params).fetchall()

            by_day: dict[dt.date, list[str]] = {}
            if name in RANKED:
                # 按日横截面排序，取分位；只保留有效数值
                by_val: dict[dt.date, list[tuple[float, str]]] = {}
                for d, c, v in sel:
                    if c and v is not None:
                        by_val.setdefault(d, []).append((float(v), c))
                for d, lst in by_val.items():
                    lst.sort(reverse=rank_high)
                    n = max(1, int(len(lst) * rank_frac))
                    by_day[d] = [c for _, c in lst[:n]]
            else:
                for d, c in sel:
                    if c:
                        by_day.setdefault(d, []).append(c)
            # 只保留"之后有足够交易日且数据已到"的日子
            use_days = []
            for d in sorted(by_day):
                i = idx.get(d)
                if i is None or i + max(HORIZONS) >= len(cal):
                    continue
                if cal[i + max(HORIZONS)] > data_max:
                    continue
                if d < start:
                    continue
                use_days.append(d)

            print(f"\n{'='*104}\n## {name} · {desc}\n   命中日 {len(use_days)} 个 / 命中记录 {len(sel):,} 条")
            if not use_days:
                print("   无可用样本"); continue

            rec_t, rec_c = [], []
            blocked: dict[str, int] = {}
            for T in use_days:
                treat = sorted(set(by_day[T]))[: args.max_treatment]
                univ = lib.universe(T)
                pool = [c for c in univ if c not in set(treat)]
                rng = random.Random(int(T.strftime("%Y%m%d")))
                ctrl = sorted(rng.sample(pool, min(args.control, len(pool))))
                days_after = lib.trading_days_after(T, max(HORIZONS))
                if len(days_after) < max(HORIZONS):
                    continue
                lib.prefetch_day(treat + ctrl, days_after[0], days_after[-1])
                for grp, codes, sink in (("t", treat, rec_t), ("c", ctrl, rec_c)):
                    for c in codes:
                        o = judge(Decision(c, "buy", T, horizons=HORIZONS), lib)
                        if not o.tradable:
                            key = f"{'处理' if grp == 't' else '对照'}:{o.reason}"
                            blocked[key] = blocked.get(key, 0) + 1
                            continue
                        sink.append({"date": T.isoformat(),
                                     **{f"ex{k}": o.excess[k] for k in HORIZONS},
                                     **{f"exn{k}": o.excess_net[k] for k in HORIZONS}})

            if blocked:
                print("   不可成交原因：" + "，".join(
                    f"{k} {v:,}" for k, v in sorted(blocked.items(), key=lambda x: -x[1])[:6]))

            row = {"desc": desc, "n_days": len(use_days),
                   "n_treat": len(rec_t), "n_ctrl": len(rec_c), "horizons": {}}
            print(f"   可成交：处理组 {len(rec_t):,} 笔 / 对照组 {len(rec_c):,} 笔")
            print(f"   {'窗口':>5} {'处理组毛':>9} {'处理组净':>9} {'t':>7} {'胜率':>7} "
                  f"{'对照组':>9} {'t':>7} {'差值':>9} {'配对t':>8}")
            for k in HORIZONS:
                a = day_series(rec_t, f"ex{k}")
                b = day_series(rec_c, f"ex{k}")
                an = day_series(rec_t, f"exn{k}")
                bn = day_series(rec_c, f"exn{k}")
                hits = [r[f"ex{k}"] for r in rec_t if r[f"ex{k}"] is not None]
                win = sum(1 for x in hits if x > 0) / len(hits) if hits else None
                pm, pt = paired_t(a, b)
                ta = tstat(a)
                print(f"   {'T+'+str(k):>5} {(f'{mean(a)*100:+.2f}%' if a else ''):>9} "
                      f"{(f'{mean(an)*100:+.2f}%' if an else ''):>9} "
                      f"{(f'{ta:+.2f}' if ta is not None else ''):>7} "
                      f"{(f'{win*100:.1f}%' if win else ''):>7} "
                      f"{(f'{mean(b)*100:+.2f}%' if b else ''):>9} "
                      f"{(f'{tstat(b):+.2f}' if tstat(b) is not None else ''):>7} "
                      f"{(f'{pm*100:+.2f}%' if pm is not None else ''):>9} "
                      f"{(f'{pt:+.2f}' if pt is not None else ''):>8}")
                row["horizons"][str(k)] = {
                    "treat_mean": mean(a), "treat_mean_net": mean(an),
                    "treat_t": ta, "ctrl_mean": mean(b), "ctrl_mean_net": mean(bn),
                    "paired_diff": pm, "paired_t": pt, "win_rate": win,
                    "n_days_treat": len(a), "n_days_ctrl": len(b)}
            results[name] = row

    # --------------------------------------------------------- 跨信号对照
    print(f"\n{'='*104}\n## 跨信号对照（T+5 / T+20，配对差值 vs 同日对照）\n")
    print(f"{'信号':>12} {'说明':>26} {'日数':>5} {'处理组笔数':>10} "
          f"{'T+5差值':>9} {'配对t':>8} {'T+20差值':>9} {'配对t':>8}")
    for name, r in results.items():
        f5 = r["horizons"].get("5", {})
        f20 = r["horizons"].get("20", {})
        d5 = f5.get("paired_diff")
        t5 = f5.get("paired_t")
        d20 = f20.get("paired_diff")
        t20 = f20.get("paired_t")
        s5 = f"{d5*100:+.2f}%" if d5 is not None else ""
        st5 = f"{t5:+.2f}" if t5 is not None else ""
        s20 = f"{d20*100:+.2f}%" if d20 is not None else ""
        st20 = f"{t20:+.2f}" if t20 is not None else ""
        print(f"{name:>12} {r['desc'][:24]:>26} {r['n_days']:>5} {r['n_treat']:>10,} "
              f"{s5:>9} {st5:>8} {s20:>9} {st20:>8}")

    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"probe_{args.start}_{args.end}.json"
    p.write_text(json.dumps({"start": args.start, "end": args.end, "signals": results},
                            ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n明细已落盘：{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
