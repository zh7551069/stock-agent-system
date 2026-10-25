"""regime · 市场级维度的 DB 适配（主库查询）。

把每日市场级 regime 值从主库算出来，归一后喂给 :func:`regime.tagging.tag_day`。
2026-10-25 实库验证：涨停家数全窗 1~1276 / 日均 34.3；pct_chg 单位为百分数（÷100 转小数）。

依赖主库（124G duckdb，只读）；锁由外部同步进程间歇占用，测试需在锁释放时跑。
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "STOCK_DB",
        "/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb",
    )
)

#: 大盘基准：沪深300（index_daily 前缀式代码）。
BENCH_CODE = "sh000300"


def pct_to_decimal(pct: float) -> float:
    """百分数（如 ``-0.53`` = −0.53%）→ 小数（``-0.0053``），对齐判决器内部口径。"""
    return pct / 100.0


def limit_up_count(con, day: dt.date) -> int:
    """T 日涨停家数（``daily.close >= limit_price.limit_up`` 且 ``pct_chg > 0``）。"""
    row = con.execute(
        """
        SELECT count(*) FROM daily d
        JOIN limit_price l ON d.code = l.code AND d.date = l.date AND d.market = l.market
        WHERE d.date = ? AND d.close >= l.limit_up AND d.pct_chg > 0
        """,
        [day],
    ).fetchone()
    return int(row[0])


def bench_pct_chg(con, day: dt.date) -> float | None:
    """沪深300 当日 ``pct_chg``（百分数 → 小数）；缺失返回 None。"""
    row = con.execute(
        "SELECT pct_chg FROM index_daily WHERE code = ? AND date = ?",
        [BENCH_CODE, day],
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return pct_to_decimal(float(row[0]))


def market_regime(con, day: dt.date, *, crowd_pctile: float | None = None,
                  turnover_pctile: float | None = None) -> dict:
    """一个交易日的市场级 regime 标签（涨停家数 + 大盘 beta 已接；拥挤度/换手率分位待接）。

    - ``crowd_pctile`` / ``turnover_pctile``：全市场分位 [0,1]，暂由上层算好传入；
      传 None 时对应桶留「待考证」（不参与分层）。
    """
    from regime.tagging import tag_day

    return tag_day(
        limit_up_count=limit_up_count(con, day),
        bench_pct_chg=bench_pct_chg(con, day) or 0.0,   # 缺失按 0（平），避免 None 进分桶
        crowd_pctile=crowd_pctile,
        turnover_pctile=turnover_pctile,
    )


# --------------------------------------------------------------------------
# 个股级维度（换手率分位 / 板块拥挤度），需 code 为 B 套（如 000001.SZ）
# --------------------------------------------------------------------------

def _to_prefix(code_b: str) -> str:
    """B 套 ``000001.SZ`` → A 套 ``sz000001``（对齐 daily/limit_price 的 code）。"""
    num, ex = code_b.split(".", 1)
    return f"{ex.lower()}{num}"


def turnover_percentile(con, code_b: str, day: dt.date) -> float | None:
    """个股换手率的全市场分位 [0,1]（tech_factor_qfq.turnover，%）。"""
    row = con.execute(
        "SELECT turnover FROM tech_factor_qfq WHERE code = ? AND date = ?", [code_b, day]
    ).fetchone()
    if row is None or row[0] is None:
        return None
    t = row[0]
    row = con.execute(
        """
        SELECT count(*), count(*) FILTER (WHERE turnover < ?)
        FROM tech_factor_qfq WHERE date = ? AND turnover IS NOT NULL
        """,
        [t, day],
    ).fetchone()
    return row[1] / row[0] if row and row[0] else None


def _industry(con, code_b: str) -> str | None:
    row = con.execute("SELECT industry FROM stock_info WHERE ts_code = ?", [code_b]).fetchone()
    return row[0] if row else None


def sector_share(con, code_b: str, day: dt.date) -> float | None:
    """个股所在板块的当日成交额占全市场比例 [0,1]。"""
    ind = _industry(con, code_b)
    if not ind:
        return None
    row = con.execute(
        """
        SELECT
          (SELECT sum(amount) FROM daily d
           JOIN stock_info s ON d.code = lower(split_part(s.ts_code,'.',2)) || split_part(s.ts_code,'.',1)
           WHERE d.date = ? AND s.industry = ?) AS sector_amt,
          (SELECT sum(amount) FROM daily WHERE date = ?) AS total_amt
        """,
        [day, ind, day],
    ).fetchone()
    if row is None or not row[1]:
        return None
    return row[0] / row[1] if row[0] is not None else None


def sector_share_percentile(con, code_b: str, day: dt.date) -> float | None:
    """个股所在板块的成交占比在**所有板块**中的分位 [0,1]（拥挤度桶：低/中/高）。"""
    ind = _industry(con, code_b)
    if not ind:
        return None
    row = con.execute(
        """
        WITH sector_amt AS (
          SELECT s.industry AS ind, sum(d.amount) AS amt
          FROM daily d
          JOIN stock_info s ON d.code = lower(split_part(s.ts_code,'.',2)) || split_part(s.ts_code,'.',1)
          WHERE d.date = ? GROUP BY s.industry
        )
        SELECT avg(CASE WHEN amt < (SELECT amt FROM sector_amt WHERE ind = ?) THEN 1.0 ELSE 0.0 END)
        FROM sector_amt
        """,
        [day, ind],
    ).fetchone()
    return row[0] if row else None


def tag_decision(con, code: str, day: dt.date, *, news_level: str | None = None) -> dict:
    """一个决策（个股 + 交易日）的完整 5 维 regime 标签。

    - ``code``：B 套（如 ``000001.SZ``）。
    - 换手率分位 + 拥挤度分位从主库现算；消息面 ``news_level`` 待语义打标（传 None = 待考证）。
    """
    from regime.tagging import tag_day

    return tag_day(
        limit_up_count=limit_up_count(con, day),
        bench_pct_chg=bench_pct_chg(con, day) or 0.0,
        crowd_pctile=sector_share_percentile(con, code, day),
        turnover_pctile=turnover_percentile(con, code, day),
        news_level=news_level,
    )
