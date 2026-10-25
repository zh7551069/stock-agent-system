"""退出规则模拟器：在**同样的入场**下，比较不同退出规则的真实期望。

## 为什么做这个

判决器已证明（883 独立日 / 2023-2026，且经 oracle 检验校准）：
    「T+1 开盘买入 + 持有到 T+5/T+20」对 6 类信号**全部为负**。
但同批样本的 **MFE 平均 +19.05% / MAE 平均 −10.39%** —— 漂移是负的，**波动极大**。
固定持有必然吃满负漂移；若退出规则能截断 MAE、留住 MFE，期望可能被翻转。

所以：**机会可能不在"选什么"，而在"怎么走"。**

## 口径约定（全部取保守侧，宁可低估自己）

- 入场：T+1 **开盘价**（前复权）
- 止损：`low <= stop_px` → 成交价 `min(stop_px, open)`（跳空低开按开盘价，更差）
- 止盈：`high >= tp_px` → 成交价 `max(tp_px, open)`（跳空高开按开盘价，更好）
- **同日止损与止盈都触发 → 一律按"先止损"**（无分钟数据时的保守假设）
- **跌停封死卖不出**：当日 `raw_high <= limit_down` → 该日不可退出，顺延到下一日
  （用**原始价**判涨跌停，与前复权价严格分开——这是本项目踩过的口径坑）
- 超过最大持有天数 → 按当日收盘退出
- 基准：同口径持有期（基准开 → 基准收），超额 = 个股收益 − 基准收益

## 已知未建模项（如实标注）

- 未计交易成本与滑点（除上面已含的跳空）
- 未建模"涨停封死买不进"之外的买入限制
- 无分钟数据 → 同日内的路径顺序不可知，只能用保守假设

用法：
    .venv/bin/python judge/exit_sim.py --signal limit_up --start 2023-01-01 --end 2026-08-25
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.bulk import BulkLibrary                        # noqa: E402
from judge.outcome import _DAILY_MARKET_OF_EXCHANGE, to_suffix, to_prefix  # noqa: E402
from judge.stats import day_series, mean, paired_diff, tstat   # noqa: E402

MAX_HOLD = 20

#: 规则名 -> (止损%, 止盈%, 最大持有天数, 跟踪止损%, 时间止损天数, 时间止损阈值%)
#: 为 None 表示该规则该维度不生效
RULES: dict[str, dict] = {
    "hold20":      dict(sl=None, tp=None, maxd=20, trail=None, tstop=None, tthr=None),
    "sl5":         dict(sl=0.05, tp=None, maxd=20, trail=None, tstop=None, tthr=None),
    "sl8":         dict(sl=0.08, tp=None, maxd=20, trail=None, tstop=None, tthr=None),
    "tp10":        dict(sl=None, tp=0.10, maxd=20, trail=None, tstop=None, tthr=None),
    "sl5_tp10":    dict(sl=0.05, tp=0.10, maxd=20, trail=None, tstop=None, tthr=None),
    "sl5_tp15":    dict(sl=0.05, tp=0.15, maxd=20, trail=None, tstop=None, tthr=None),
    "trail5":      dict(sl=None, tp=None, maxd=20, trail=0.05, tstop=None, tthr=None),
    "sl5_trail5":  dict(sl=0.05, tp=None, maxd=20, trail=0.05, tstop=None, tthr=None),
    "time5":       dict(sl=None, tp=None, maxd=20, trail=None, tstop=5, tthr=0.01),
}


def simulate(entry_px: float, bars: list[dict], raw: list[dict], lim: list[Optional[float]],
             rule: dict) -> tuple[Optional[float], Optional[int], str]:
    """返回 (退出价, 持有天数, 退出原因)。bars/raw/lim 按日期升序，与持有窗口对齐。"""
    if not bars or entry_px is None or entry_px <= 0:
        return (None, None, "no_data")
    stop_px = entry_px * (1 - rule["sl"]) if rule["sl"] else None
    tp_px = entry_px * (1 + rule["tp"]) if rule["tp"] else None
    peak = entry_px

    for i, (b, r, ld) in enumerate(zip(bars, raw, lim)):
        day_no = i + 1
        # 跌停封死：整日最高价不高于跌停价 -> 卖不出，顺延
        locked = (r is not None and ld is not None and r.get("high") is not None
                  and r["high"] <= ld)
        if not locked:
            # 保守：先判止损
            if stop_px is not None and b["low"] is not None and b["low"] <= stop_px:
                return (min(stop_px, b["open"]), day_no, "stop_loss")
            if rule["trail"] is not None:
                trail_px = peak * (1 - rule["trail"])
                if b["low"] is not None and b["low"] <= trail_px:
                    return (min(trail_px, b["open"]), day_no, "trailing_stop")
            if tp_px is not None and b["high"] is not None and b["high"] >= tp_px:
                return (max(tp_px, b["open"]), day_no, "take_profit")
            if (rule["tstop"] is not None and day_no >= rule["tstop"]
                    and b["close"] is not None
                    and b["close"] < entry_px * (1 + (rule["tthr"] or 0))):
                return (b["close"], day_no, "time_stop")
        if b["high"] is not None:
            peak = max(peak, b["high"])
        if day_no >= rule["maxd"]:
            return (b["close"], day_no, "max_hold")
    last = bars[-1]
    return (last["close"], len(bars), "window_end")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", default="limit_up",
                    choices=["limit_up", "limit_down", "drop5", "new_low60"])
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--control", type=int, default=200)
    ap.add_argument("--max-treatment", type=int, default=300)
    ap.add_argument("--cost", type=float, default=0.0015,
                    help="单次往返总成本（佣金+印花税+过户费+滑点），默认 0.15%%。"
                         "压短持有=高换手，成本必须计入，否则结果失真")
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)

    SEL = {
        "limit_up": ("SELECT 交易时间 d, 代码 c FROM zt_pool_limit_up WHERE 交易时间>=? AND 交易时间<=?",
                     "T 日涨停"),
        "limit_down": ("SELECT 交易时间 d, 代码 c FROM zt_pool_limit_down WHERE 交易时间>=? AND 交易时间<=?",
                       "T 日跌停"),
        "drop5": ("SELECT date d, code c FROM tech_factor_qfq WHERE date>=? AND date<=? AND pct_chg<=-5",
                  "T 日跌幅<=-5%"),
        "new_low60": ("""WITH x AS (SELECT code,date,close,
                          MIN(close) OVER (PARTITION BY code ORDER BY date
                                           ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) mn,
                          ROW_NUMBER() OVER (PARTITION BY code ORDER BY date) rn
                          FROM tech_factor_qfq WHERE date>=? AND date<=?)
                        SELECT date d, code c FROM x WHERE close=mn AND rn>=60""",
                      "收盘创 60 日新低"),
    }
    sql, desc = SEL[args.signal]

    with BulkLibrary() as lib:
        cal = [r[0] for r in lib._con.execute("SELECT date FROM trade_cal ORDER BY date").fetchall()]
        idx = {d: i for i, d in enumerate(cal)}
        data_max = lib._con.execute("SELECT max(date) FROM tech_factor_qfq").fetchone()[0]
        if args.signal == "new_low60":
            # 注意：start 可能不是交易日（如 2023-01-01），必须先归到首个交易日
            first = next((d for d in cal if d >= start), None)
            if first is None:
                print("区间内无交易日"); return 1
            buf = cal[max(0, idx[first] - 130)]
            sel = lib._con.execute(sql + " AND date>=?", [buf, end, start]).fetchall()
        else:
            sel = lib._con.execute(sql, [start, end]).fetchall()
        by_day: dict[dt.date, list[str]] = {}
        for d, c in sel:
            if c:
                by_day.setdefault(d, []).append(c)

        use_days = [d for d in sorted(by_day)
                    if d >= start and d in idx and idx[d] + MAX_HOLD < len(cal)
                    and cal[idx[d] + MAX_HOLD] <= data_max]
        print(f"信号 {args.signal}（{desc}）：{len(use_days)} 个独立日，"
              f"命中 {sum(len(by_day[d]) for d in use_days):,} 条")

        # 逐日：一次取回全部需要的行情（前复权 + 原始 + 跌停价）
        sims: dict[str, list[dict]] = {name: [] for name in RULES}
        sims_ctl: dict[str, list[dict]] = {name: [] for name in RULES}
        for i, T in enumerate(use_days, 1):
            treat = sorted(set(by_day[T]))[: args.max_treatment]
            univ = lib.universe(T)
            pool = [c for c in univ if c not in set(treat)]
            rng = random.Random(int(T.strftime("%Y%m%d")))
            ctrl = sorted(rng.sample(pool, min(args.control, len(pool))))
            win = lib.trading_days_after(T, MAX_HOLD)
            if len(win) < MAX_HOLD:
                continue
            d0, d1 = win[0], win[-1]
            codes = treat + ctrl
            sfx = [to_suffix(c) for c in codes]
            pfx = [to_prefix(c) for c in codes]

            # ① 前复权 OHLC（收益与止损/止盈价都用它，口径内部一致）
            bars: dict[str, dict[dt.date, dict]] = {c: {} for c in sfx}
            for part in [sfx[i:i + 400] for i in range(0, len(sfx), 400)]:
                ph = ",".join("?" * len(part))
                for row in lib._con.execute(
                    f"SELECT code,date,open,high,low,close FROM tech_factor_qfq "
                    f"WHERE code IN ({ph}) AND date>=? AND date<=?", [*part, d0, d1]).fetchall():
                    bars[row[0]][row[1]] = {"open": row[2], "high": row[3],
                                            "low": row[4], "close": row[5]}
            # ② 原始价（判跌停封死用，绝不与前复权价混用）
            raw: dict[str, dict[dt.date, dict]] = {c: {} for c in pfx}
            for market in ("hs", "bj"):
                pm = [p for p in pfx if _DAILY_MARKET_OF_EXCHANGE[p[:2]] == market]
                for part in [pm[i:i + 400] for i in range(0, len(pm), 400)]:
                    ph = ",".join("?" * len(part))
                    for row in lib._con.execute(
                        f"SELECT code,date,high FROM daily WHERE market=? AND date>=? AND date<=? "
                        f"AND code IN ({ph})", [market, d0, d1, *part]).fetchall():
                        raw[row[0]][row[1]] = {"high": row[2]}
            # ③ 跌停价
            lim: dict[str, dict[dt.date, float]] = {c: {} for c in pfx}
            for part in [pfx[i:i + 400] for i in range(0, len(pfx), 400)]:
                ph = ",".join("?" * len(part))
                for row in lib._con.execute(
                    f"SELECT code,date,limit_down FROM limit_price "
                    f"WHERE date>=? AND date<=? AND code IN ({ph})", [d0, d1, *part]).fetchall():
                    if row[2] is not None:
                        lim[row[0]][row[1]] = row[2]

            bench = lib.bench_bars("sh000300", d0, d1)
            bench_open = bench.get(d0, {}).get("open")

            for codes_sfx, sink in ((treat, sims), (ctrl, sims_ctl)):
                for c in codes_sfx:
                    cs, cp = to_suffix(c), to_prefix(c)
                    bl = [bars.get(cs, {}).get(d) for d in win]
                    rw = [raw.get(cp, {}).get(d) for d in win]
                    lm = [lim.get(cp, {}).get(d) for d in win]
                    # 三个序列必须**按同一批交易日对齐**：任一缺失就整体剔除该日，
                    # 否则 前复权价 / 原始价 / 跌停价 会互相错位（本项目踩过的坑）
                    aligned = [(d, b, r, l) for d, b, r, l in zip(win, bl, rw, lm) if b is not None]
                    if not aligned or aligned[0][1]["open"] is None:
                        continue
                    entry = aligned[0][1]["open"]
                    bar_a = [x[1] for x in aligned]
                    raw_a = [x[2] for x in aligned]
                    lim_a = [x[3] for x in aligned]
                    for name, rule in RULES.items():
                        px, held, why = simulate(entry, bar_a, raw_a, lim_a, rule)
                        if px is None or held is None:
                            continue
                        ret = px / entry - 1
                        bd = aligned[min(held, len(aligned)) - 1][0]
                        br = (bench[bd]["close"] / bench_open - 1) if (bd in bench and bench_open) else None
                        ex = (ret - br) if br is not None else None
                        sink[name].append({"date": T.isoformat(),
                                           "ret": ret, "ex": ex,
                                           "exn": (ex - args.cost) if ex is not None else None,
                                           "held": held, "why": why})
            if i % 100 == 0 or i == len(use_days):
                print(f"  …{i}/{len(use_days)}  最新 {T}")

    # ------------------------------------------------------------- 汇总
    print(f"\n{'='*112}\n## 退出规则对比（信号 {args.signal}；超额 = 个股 − 基准，同持有期）")
    print(f"   往返成本 {args.cost*100:.2f}% 已计入「差值(净)」；「差值(毛)」为未计成本\n")
    print(f"{'规则':>13} {'处理组毛':>9} {'处理组净':>9} {'平均持有':>8} "
          f"{'对照组净':>9} {'差值(毛)':>9} {'配对t':>7} {'差值(净)':>9} {'配对t':>7}")
    report = {"signal": args.signal, "start": args.start, "end": args.end,
              "cost": args.cost, "rules": {}}
    for name in RULES:
        rg = [r for r in sims[name] if r["ex"] is not None]
        rn = [r for r in sims[name] if r["exn"] is not None]
        cg = [r for r in sims_ctl[name] if r["ex"] is not None]
        cn = [r for r in sims_ctl[name] if r["exn"] is not None]
        a, b = day_series(rg, "ex"), day_series(cg, "ex")
        an, bn = day_series(rn, "exn"), day_series(cn, "exn")
        mg, tg, _ = paired_diff(a, b)
        mn, tn, common = paired_diff(an, bn)
        ma, mb = mean(an), mean(bn)
        held = [r["held"] for r in sims[name]]
        print(f"{name:>13} "
              f"{(f'{mean(a)*100:+.2f}%' if a else ''):>9} "
              f"{(f'{ma*100:+.2f}%' if ma is not None else ''):>9} "
              f"{(f'{mean(held):.1f}d' if held else ''):>8} "
              f"{(f'{mb*100:+.2f}%' if mb is not None else ''):>9} "
              f"{(f'{mg*100:+.2f}%' if mg is not None else ''):>9} "
              f"{(f'{tg:+.2f}' if tg is not None else ''):>7} "
              f"{(f'{mn*100:+.2f}%' if mn is not None else ''):>9} "
              f"{(f'{tn:+.2f}' if tn is not None else ''):>7}")
        report["rules"][name] = {"treat_gross": mean(a), "treat_net": ma,
                                 "ctrl_net": mb, "diff_gross": mg, "paired_t_gross": tg,
                                 "diff_net": mn, "paired_t_net": tn, "common_days": common,
                                 "avg_held": mean(held), "n_treat": len(sims[name])}
    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"exit_{args.signal}_{args.start}_{args.end}.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n明细已落盘：{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
