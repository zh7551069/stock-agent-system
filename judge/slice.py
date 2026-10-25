"""分层判决：在"涨停 → 次日开盘买"这个已证伪的规则里，找**是否存在正期望的子集**。

背景（判决器已给出的基线，879 个独立日 / 2023-2026 四年一致）：
    T+5 平均超额 涨停组 -1.20% vs 对照组 +0.22%，配对 t = -13.15
    → "涨停就上"是负期望。所以价值只能来自**选哪只**。

本脚本按下列维度切分，逐桶给出 T+5 / T+20 的剔 beta 超额与**按独立日的 t 值**：
    1. 连板高度       首板 / 2板 / 3板+
    2. 涨停时间       早盘 <=10:00 / 盘中 / 尾盘 >=13:30
    3. 封单额         当日横截面 低/中/高（三分位）
    4. 换手率         <5% / 5-15% / >15%
    5. 实际流通市值   当日横截面 小/中/大（三分位）
    6. 板块效应       当日同板块涨停家数 1 / 2-3 / 4+
    7. 昨日是否涨停   延续 vs 首日

⚠️ 已知偏差（必须随结果一起读）：封单/换手/市值字段仅约 43% 的行有值，
   因此 3/4/5 三个维度的样本是有选择性偏差的子集，不能当作全体结论。

用法：
    .venv/bin/python judge/slice.py --start 2023-01-01 --end 2026-08-25
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import re
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.bulk import BulkLibrary                      # noqa: E402
from judge.outcome import Decision, judge               # noqa: E402

HORIZONS = (5, 20)
ZT_COLS = ["交易时间", "代码", "状态（N连板）", "封单", "换手率%", "实际流通",
           "涨停时间", "板块", "成交额"]


def norm_board(state: str | None) -> str | None:
    """把 '首板' / '2连板' / '4天3板' / '新上市未开板' 归一到 首板 / 2板 / 3板+。"""
    if not state:
        return None
    if "新上市" in state or "未开板" in state:
        return "新上市未开板"          # 单列：新股上市连板，玩法完全不同
    if state.startswith("首板"):
        return "首板"
    m = re.findall(r"(\d+)", state)
    if not m:
        return None
    n = int(m[-1])                      # '4天3板' -> 3
    return "首板" if n <= 1 else ("2板" if n == 2 else "3板+")


def bucket_time(t: str | None) -> str | None:
    if not t:
        return None
    m = re.match(r"(\d{1,2}):(\d{2})", str(t))
    if not m:
        return None
    hm = int(m.group(1)) * 60 + int(m.group(2))
    if hm <= 10 * 60:
        return "早盘封板(<=10:00)"
    if hm < 13 * 60 + 30:
        return "盘中封板"
    return "尾盘封板(>=13:30)"


def tercile(values: list[float], v: float) -> str | None:
    xs = sorted(x for x in values if x is not None)
    if not xs or v is None:
        return None
    lo = xs[int(len(xs) * 0.33)]
    hi = xs[int(len(xs) * 0.67)]
    return "低" if v <= lo else ("中" if v <= hi else "高")


def turnover_bucket(v) -> str | None:
    """换手率在库里是 **VARCHAR**（实测），必须显式转数值再比大小。"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return "<5%" if v < 5 else ("5-15%" if v <= 15 else ">15%")


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def tstat(xs) -> float | None:
    if len(xs) < 5:
        return None
    sd = st.stdev(xs)
    if sd == 0:
        return None
    return mean(xs) / (sd / math.sqrt(len(xs)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-25")
    ap.add_argument("--exclude-new-listing", action="store_true", default=True)
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)

    with BulkLibrary() as lib:
        # 一次性取回区间内全部涨停池记录（含分层字段）
        cols = ", ".join(f'"{c}"' for c in ZT_COLS)
        rows = lib._con.execute(
            f"SELECT {cols} FROM zt_pool_limit_up WHERE 交易时间 >= ? AND 交易时间 <= ?",
            [start, end]).fetchall()
        print(f"涨停池记录 {len(rows):,} 条（{start} ~ {end}）")

        by_day: dict[dt.date, list[dict]] = defaultdict(list)
        for r in rows:
            d = dict(zip(ZT_COLS, r))
            T = d["交易时间"]
            stt = norm_board(d["状态（N连板）"])
            if args.exclude_new_listing and stt == "新上市未开板":
                continue
            by_day[T].append({
                "code": d["代码"], "board": stt,
                "seal": d["封单"], "turnover": d["换手率%"],
                "float_mv": d["实际流通"], "sector": d["板块"],
                "t_bucket": bucket_time(d["涨停时间"]),
            })

        cal = [x[0] for x in lib._con.execute("SELECT date FROM trade_cal ORDER BY date").fetchall()]
        cal_idx = {d: i for i, d in enumerate(cal)}
        zt_by_day = {T: {r["code"] for r in v} for T, v in by_day.items()}

        # 逐日：算横截面分位、板块家数、昨日涨停，然后判决
        recs: list[dict] = []
        for T in sorted(by_day):
            items = by_day[T]
            codes = [it["code"] for it in items]
            days_after = lib.trading_days_after(T, max(HORIZONS))
            if len(days_after) < max(HORIZONS):
                continue
            lib.prefetch_day(codes, days_after[0], days_after[-1])

            seals = [it["seal"] for it in items if it["seal"]]
            mvs = [it["float_mv"] for it in items if it["float_mv"]]
            sec_cnt: dict[str, int] = defaultdict(int)
            for it in items:
                if it["sector"]:
                    sec_cnt[it["sector"]] += 1
            i = cal_idx.get(T)
            prev_day = cal[i - 1] if i and i > 0 else None
            prev_zt = zt_by_day.get(prev_day, set()) if prev_day else set()

            for it in items:
                o = judge(Decision(it["code"], "buy", T, horizons=HORIZONS), lib)
                if not o.tradable:
                    continue
                recs.append({
                    "date": T.isoformat(), "code": it["code"],
                    "ex5": o.excess[5], "ex20": o.excess[20],
                    "ex5_net": o.excess_net[5], "ex20_net": o.excess_net[20],
                    "board": it["board"], "t_bucket": it["t_bucket"],
                    "seal_q": tercile(seals, it["seal"]),
                    "mv_q": tercile(mvs, it["float_mv"]),
                    "turn": turnover_bucket(it["turnover"]),
                    "sector_n": (sec_cnt.get(it["sector"]) if it["sector"] else None),
                    "y_zt": it["code"] in prev_zt,
                })
            if len(recs) % 20000 < len(items):
                print(f"  …{T} 累计可成交样本 {len(recs):,}")

    # ------------------------------------------------------------------ 汇总
    print(f"\n可成交样本 {len(recs):,} 笔 / {len({r['date'] for r in recs})} 个独立日")

    def report(dim: str, keyfn) -> dict:
        buckets: dict[str, list[dict]] = defaultdict(list)
        for r in recs:
            k = keyfn(r)
            if k is not None:
                buckets[str(k)].append(r)
        out = {}
        print(f"\n{'='*100}\n## 按「{dim}」分层\n")
        print(f"{'桶':>18} {'笔数':>7} {'日数':>5} {'T+5毛':>8} {'T+5净':>8} {'t值':>7} "
              f"{'胜率':>7} {'T+20毛':>8} {'T+20净':>8} {'t值':>7}")
        for k in sorted(buckets, key=lambda x: -len(buckets[x])):
            rs = buckets[k]
            per_day5: dict[str, list[float]] = defaultdict(list)
            per_day20: dict[str, list[float]] = defaultdict(list)
            per_day5n: dict[str, list[float]] = defaultdict(list)
            per_day20n: dict[str, list[float]] = defaultdict(list)
            for r in rs:
                if r["ex5"] is not None:
                    per_day5[r["date"]].append(r["ex5"])
                if r["ex20"] is not None:
                    per_day20[r["date"]].append(r["ex20"])
                if r["ex5_net"] is not None:
                    per_day5n[r["date"]].append(r["ex5_net"])
                if r["ex20_net"] is not None:
                    per_day20n[r["date"]].append(r["ex20_net"])
            d5 = [mean(v) for v in per_day5.values()]
            d20 = [mean(v) for v in per_day20.values()]
            dn5 = [mean(v) for v in per_day5n.values()]
            dn20 = [mean(v) for v in per_day20n.values()]
            m5, m20 = mean(d5), mean(d20)
            mn5, mn20 = mean(dn5), mean(dn20)
            hits = [x for x in (r["ex5"] for r in rs) if x is not None]
            win = sum(1 for x in hits if x > 0) / len(hits) if hits else None
            print(f"{k:>18} {len(rs):>7,} {len(d5):>5} "
                  f"{(f'{m5*100:+.2f}%' if m5 is not None else ''):>8} "
                  f"{(f'{mn5*100:+.2f}%' if mn5 is not None else ''):>8} "
                  f"{(f'{tstat(d5):+.2f}' if tstat(d5) is not None else ''):>7} "
                  f"{(f'{win*100:.1f}%' if win is not None else ''):>7} "
                  f"{(f'{m20*100:+.2f}%' if m20 is not None else ''):>8} "
                  f"{(f'{mn20*100:+.2f}%' if mn20 is not None else ''):>8} "
                  f"{(f'{tstat(d20):+.2f}' if tstat(d20) is not None else ''):>7}")
            out[k] = {"n": len(rs), "days": len(d5), "t5": m5, "t5_net": mn5, "t5_t": tstat(d5),
                      "win5": win, "t20": m20, "t20_net": mn20, "t20_t": tstat(d20)}
        return out

    res = {
        "by_board": report("连板高度", lambda r: r["board"]),
        "by_time": report("涨停时间", lambda r: r["t_bucket"]),
        "by_seal": report("封单额(当日三分位)", lambda r: r["seal_q"]),
        "by_turnover": report("换手率", lambda r: r["turn"]),
        "by_mv": report("实际流通市值(当日三分位)", lambda r: r["mv_q"]),
        "by_sector_n": report("同板块涨停家数", lambda r: (
            None if r["sector_n"] is None else
            ("1家" if r["sector_n"] == 1 else ("2-3家" if r["sector_n"] <= 3 else "4家+")))),
        "by_yesterday_zt": report("昨日是否涨停", lambda r: "昨日涨停(延续)" if r["y_zt"] else "昨日未涨停(首日)"),
    }

    out = pathlib.Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    p = out / f"slice_{args.start}_{args.end}.json"
    p.write_text(json.dumps({"n": len(recs), "res": res}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    print(f"\n明细已落盘：{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
