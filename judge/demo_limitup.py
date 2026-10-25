"""判决器真实数据演示：把「某日涨停池」当一批决策，看它们真实的 T+1/+3/+5/+20 结果。

这不是策略，是**判决器自检**——证明它能对真实决策算出真实结果。
用法：
    .venv/bin/python judge/demo_limitup.py 2026-10-08
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.outcome import Decision, Library, judge, summarize  # noqa: E402

HORIZONS = (1, 3, 5, 20)


def limit_up_codes(lib: Library, day: dt.date) -> list[str]:
    """东财涨停池（后缀式代码）。**注意**：这是"已经涨停"的事后名单，
    这里只当样本用；真实决策必须在 T 日收盘前产生。"""
    return lib.zt_limit_up_codes(day)


def fmt(x, pct=True, nd=2):
    if x is None:
        return "  缺失"
    return f"{x*100:+.{nd}f}%" if pct else f"{x:.{nd}f}"


def main() -> int:
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 10, 8)
    with Library() as lib:
        codes = limit_up_codes(lib, day)
        print(f"=== 样本：{day} 涨停池 {len(codes)} 只（东财口径）===")
        if not codes:
            print("  该日无样本"); return 1

        outcomes = [judge(Decision(c, "buy", day, horizons=HORIZONS), lib) for c in codes]
        q = summarize(outcomes, HORIZONS)

        print(f"\n决策数 {q.n_total} | 可成交 {q.n_tradable} | 不可成交 {q.n_untradable}"
              f" | 结果缺失 {q.n_missing}")
        blocked: dict[str, int] = {}
        for o in outcomes:
            if not o.tradable:
                blocked[o.reason] = blocked.get(o.reason, 0) + 1
        if blocked:
            print("  不可成交原因：" + "，".join(f"{k} {v} 例" for k, v in blocked.items()))

        print(f"\n{'窗口':>5} {'胜率(净>0)':>11} {'平均超额(毛)':>11} {'平均超额(净)':>11} {'盈亏比':>8}")
        for k in HORIZONS:
            print(f"{'T+'+str(k):>5} {fmt(q.hit_rate_net[k], False):>11} {fmt(q.avg_excess[k]):>11}"
                  f" {fmt(q.avg_excess_net[k]):>11} {fmt(q.payoff[k], False):>8}")
        print(f"\n平均最大浮盈 MFE {fmt(q.avg_mfe)} | 平均最大浮亏 MAE {fmt(q.avg_mae)}")

        out = pathlib.Path(__file__).parent / "reports" / f"limitup_{day}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(
            {"as_of": day.isoformat(), "quality": q.as_dict(),
             "outcomes": [o.as_dict() for o in outcomes]},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n逐笔明细已落盘：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
