#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测判决官 harness —— **已退役**（2026-10-25），现为兼容指针。

权威实现已迁至 `stock/judge/`（11 模块 · 18 测试全过 · 15 份 883 天校准报告）。
本文件此前是一套 212 行的独立重复实现，且收益口径有误（用 `daily` 原始价
相除，违反[数据口径契约]「收益率用 pct_chg」），并缺少停牌/涨跌停封板、
同日篮子合并（⑥）、配对对照（⑦）、最小样本 n≥5（⑧）。为消除「两套判决器
并存」，本文件不再独立计算，全部能力委托给权威包 `judge`。

旧 → 新 对应关系：
  load_data / build_calendar / _get        →  judge.outcome.Library（只读取数）
  simulate_exit（出场模拟）                →  judge.exit_sim（9 种退出规则，口径更完整）
  bench_return / excess（剔 beta 超额）    →  judge.outcome.judge(...).excess
  run_backtest（主回测）                    →  judge.outcome.judge + judge.bulk.BulkLibrary
  smoke_baseline / --smoke（涨停基线）      →  judge.baseline（涨停 vs 同日随机对照 + 配对 t）
  配对检验                                   →  judge.stats.paired_t / paired_diff

用法（保持旧 CLI 可运行）：
  python3 judge_harness.py --smoke            # 委托 judge.baseline 涨停基线回放
  python3 judge_harness.py --smoke --start 2023-01-01 --end 2026-08-25

如需直接使用权威实现：
  .venv/bin/python judge/baseline.py --start 2023-01-01 --end 2026-08-25
"""
from __future__ import annotations

import sys
from pathlib import Path

# 仓库根 = 本文件上三级（docs/plan03-site/scripts/ → stock/）
_ROOT = Path(__file__).resolve().parents[3]
if not (_ROOT / "judge" / "__init__.py").is_file():
    raise RuntimeError(f"找不到权威判决器包：{_ROOT / 'judge'}")
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 权威原语再导出（旧 import 不破；本包与选手物理隔离的纪律不变）
from judge.outcome import (                              # noqa: E402,F401
    DEFAULT_BENCH, DEFAULT_HORIZONS, DB_PATH,
    Decision, Library, Outcome, Quality,
    judge, summarize, to_prefix, to_suffix,
)
from judge.bulk import BulkLibrary                       # noqa: E402,F401
from judge.stats import (                                # noqa: E402,F401
    DaySeries, day_series, mean, paired_diff, paired_t, tstat,
)

__all__ = [
    "DB_PATH", "DEFAULT_BENCH", "DEFAULT_HORIZONS",
    "Decision", "Library", "Outcome", "Quality",
    "judge", "summarize", "to_prefix", "to_suffix",
    "BulkLibrary",
    "DaySeries", "day_series", "mean", "paired_diff", "paired_t", "tstat",
]


def main() -> int:
    """保持旧 CLI 可运行：`--smoke` 委托权威 `judge.baseline` 的涨停基线回放。"""
    from judge.baseline import main as baseline_main

    argv = sys.argv[1:]
    if "--smoke" in argv:
        argv = [a for a in argv if a != "--smoke"]
        print("⚠️  judge_harness.py 已退役 → 委托权威实现 judge.baseline（涨停基线回放）\n")
    sys.argv = [sys.argv[0], *argv]
    return baseline_main()


if __name__ == "__main__":
    raise SystemExit(main())
