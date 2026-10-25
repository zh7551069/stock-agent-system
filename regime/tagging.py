"""regime · 市场级维度打标（确定性部分，0 LLM）。

eval-dataset 6.2 的 5 个基础 regime 维度里，涨停家数 / 大盘 beta / 板块拥挤度 / 换手率分位
是确定性代码（0 LLM，稳定可复现）；消息面强度是语义打标（LLM），本模块只留占位。

⚠️ 分桶边界是「占位待考证」：默认沿用文档示意（<30/30-60/60+、跌/平/涨、低/中/高），
正式边界应由 6.2.1 的「等频分位 + 已验证断点 + n≥5」从 883 天数据反推（见 regime.buckets）。
"""

from __future__ import annotations

#: 涨停家数占位断点（eval-dataset 6.2 示意，待任务 16 考证）。
LIMIT_UP_EDGES: tuple[int, int] = (30, 60)

#: 大盘 beta「平」的阈值（沪深300 单日 |pct_chg| 在此内算平；待任务 16 考证边界）。
BETA_NEUTRAL: float = 0.005


def limit_up_bucket(cnt: int, edges: tuple[int, int] = LIMIT_UP_EDGES) -> str:
    """涨停家数分桶 ``'<30' / '30-60' / '60+'``。"""
    lo, hi = edges
    if cnt < lo:
        return f"<{lo}"
    if cnt < hi:
        return f"{lo}-{hi}"
    return f"{hi}+"


def beta_bucket(pct_chg: float, neutral: float = BETA_NEUTRAL) -> str:
    """沪深300 单日涨跌 → ``跌 / 平 / 涨``。"""
    if pct_chg < -neutral:
        return "跌"
    if pct_chg > neutral:
        return "涨"
    return "平"


def quantile_three(pctile: float | None) -> str:
    """``[0,1]`` 分位 → ``低 / 中 / 高``（三分位）；None → ``待考证``（不参与分层）。"""
    if pctile is None:
        return "待考证"
    if pctile < 1 / 3:
        return "低"
    if pctile < 2 / 3:
        return "中"
    return "高"


def breadth_bucket(frac: float) -> str:
    """市场宽度（站上 MA20 占比）→ ``<30% / 30-70% / >70%``（占位断点，待考证）。"""
    if frac < 0.30:
        return "<30%"
    if frac <= 0.70:
        return "30-70%"
    return ">70%"


#: 恐慌超跌阈值：close 低于 MA20 达此比例记为恐慌（均线近似，占位待考证）。
PANIC_RATIO = 0.93


def cycle_stage(close: float, ma20: float, ma60: float) -> str:
    """市场周期六阶段（均线近似，仅用 close/MA20/MA60 三关系）。

    - 上升趋势：close > ma20 > ma60
    - 下降趋势：close < ma20 < ma60（恐慌超跌：偏离 MA20 超 :data:`PANIC_RATIO`）
    - 筑底反弹：close > ma20 但仍 < ma60（长期线下刚转强）
    - 顶部转弱：close < ma20 但仍 > ma60（长期线上刚转弱）
    """
    above20, above60 = close > ma20, close > ma60
    if above20 and above60:
        return "上升趋势"
    if not above20 and not above60:
        return "恐慌超跌" if close < PANIC_RATIO * ma20 else "下降趋势"
    if above20 and not above60:
        return "筑底反弹"
    return "顶部转弱"


def tag_day(
    *,
    limit_up_count: int,
    bench_pct_chg: float,
    crowd_pctile: float | None = None,
    turnover_pctile: float | None = None,
    news_level: str | None = None,
    regime_ver: str = "regime:v1",
) -> dict:
    """一个交易日的市场级 regime 标签（对齐 ``regime_label`` 表列）。

    - ``crowd_pctile`` / ``turnover_pctile`` 是 [0,1] 全市场分位；传 None → 桶记「待考证」。
    - ``news_level`` 语义打标（LLM），确定性侧传 None（= 待考证）。
    """
    return {
        "limit_up_cnt": limit_up_bucket(limit_up_count),
        "beta_bucket": beta_bucket(bench_pct_chg),
        "crowd_bucket": quantile_three(crowd_pctile),
        "turnover_q": quantile_three(turnover_pctile),
        "news_level": news_level,
        "regime_ver": regime_ver,
    }
