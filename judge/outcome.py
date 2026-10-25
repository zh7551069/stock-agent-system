"""判决器 · 事实冻结（Outcome Freeze）

职责：给定一条**决策**，从主库复算它已经发生的**真实结果**。
这是整个系统唯一合法的验收标准来源——没有它，"好用"无法被证明。

## 设计原则（不可协商）

1. **与选手物理隔离**：本模块不 import 任何决策/引擎代码。
   若判决器与选手共享同一个 bug，判决就失效了（common-mode failure）。
2. **市场结果不可质疑**：本模块只记录事实，不做任何解释、不做归因。
3. **严格无未来函数**：计算 T+k 的结果时，只使用 <= T+k 的数据。
4. **确定性**：同一输入必得同一输出；不读墙钟、不用随机。

## 口径定义（写死，避免歧义）

- `T`  = 决策日（signal_date）：决策在 **T 日收盘后**产生
- 入场 = **T+1 日的开盘价**（前复权）。这与 A 股"收盘后决策、次日开盘执行"一致，
  也杜绝了"同一根 K 线内成交"的隐性作弊。
- `Ret(T+k)` = `close(T+k) / open(T+1) - 1`，其中 k 是 T 之后的第 k 个交易日（k >= 1）。
  - 例：T+1 = 入场当日收盘；T+20 = T 之后第 20 个交易日收盘。
- `Excess(T+k)` = `Ret(T+k) - BenchRet(T+k)`，基准同口径（基准开盘价 -> 基准收盘价）。
  这就是**剔 beta 超额**，用于回答"这笔决策到底是选股赚的还是大盘给的"。
- `MFE / MAE` = 入场后至最远观察日之间，相对入场价的**最大有利 / 最大不利偏移**。
  用于回答"我中途浮盈过多少、浮亏过多少"，而不是只看终值。

## 可交易性（fail-closed）

- T+1 停牌            -> 不可成交
- 买入 且 T+1 开盘即涨停 -> 不可成交（封死买不到）
- 卖出 且 T+1 开盘即跌停 -> 不可成交（封死卖不掉）

不可成交时，**不产生收益数字**（返回 None），而不是当作 0——
"缺失不等于 0" 是本项目的铁律。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import duckdb

DB_PATH = Path(
    "/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb"
)

#: 默认基准：沪深300（前缀式口径，实测 index_daily 用 sh000300）
DEFAULT_BENCH = "sh000300"

#: 默认观察窗口（T+k，k 为 T 之后的第 k 个交易日）
DEFAULT_HORIZONS: tuple[int, ...] = (1, 3, 5, 20)

#: 单次往返总成本（佣金+印花税+过户费+滑点）。
#: 与 exit_sim --cost 默认值、caliber_meta.cost_rate 一致（0.15% 往返合计）。
COST_RATE = 0.0015

#: 交易所后缀 -> 主库前缀
_EXCHANGE_OF_SUFFIX = {"SH": "sh", "SZ": "sz", "BJ": "bj"}

#: 交易所 -> **`daily` / `limit_price` 两张表**的 market 取值（实测二者一致，均为 hs/bj）。
#: ⚠️ 实测陷阱（2026-10-25 复现）：`daily.market` 与 `limit_price.market` 都用 `hs`（沪深合并）/ `bj`，
#: 而代码里 `split_prefix` 得到的是 `sh` / `sz` / `bj`。
#: 曾误判「limit_price 用 sh/sz」（2026-10-12），导致 `limit_up_down()` 用 sh/sz 查询、
#: 静默取不到涨停价 → 封板判定全线失效（P0，已修：见 limit_up_down 的市场映射）。
_DAILY_MARKET_OF_EXCHANGE = {"sh": "hs", "sz": "hs", "bj": "bj"}

MISSING = None  # 显式表达"缺失"，绝不写成 0


# --------------------------------------------------------------------------
# 代码口径转换（三套口径是首要工程风险）
# --------------------------------------------------------------------------

def to_suffix(code: str) -> str:
    """归一到后缀式 `000001.SZ`（tech_factor_qfq / suspension / stock_info 用）。"""
    c = code.strip().upper()
    if "." in c:
        num, ex = c.split(".", 1)
        return f"{num.zfill(6)}.{ex}"
    low = c.lower()
    if low[:2] in ("sh", "sz", "bj"):
        num, ex = low[2:], low[:2]
        return f"{num.zfill(6)}.{ex.upper()}"
    raise ValueError(f"无法判断交易所的代码: {code!r}（裸 6 位码在库中是歧义码：000001 是上证指数）")


def to_prefix(code: str) -> str:
    """归一到前缀式 `sz000001`（daily / limit_price / minute_1min 用）。"""
    sfx = to_suffix(code)
    num, ex = sfx.split(".", 1)
    return f"{_EXCHANGE_OF_SUFFIX[ex]}{num}"


def split_prefix(prefix: str) -> tuple[str, str]:
    """`sz000001` -> ("sz", "000001")，供 limit_price 的 market+code 双列查询。"""
    p = prefix.strip().lower()
    return p[:2], p[2:]


# --------------------------------------------------------------------------
# 值类型
# --------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Decision:
    """一条待判决的决策。字段刻意保持最小，且全部可观测。"""

    code: str
    side: str                      # "buy" | "sell"
    signal_date: dt.date           # 决策日 T（收盘后决策）
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    bench: str = DEFAULT_BENCH
    cost: float = COST_RATE        # 单次往返总成本，用于净收益/净超额

    def __post_init__(self) -> None:
        if self.side not in ("buy", "sell"):
            raise ValueError(f"side 只能是 buy/sell，收到 {self.side!r}")
        if not self.horizons or min(self.horizons) < 1:
            raise ValueError("horizons 必须是 >=1 的交易日偏移")


@dataclasses.dataclass(frozen=True)
class Outcome:
    """一条决策的真实结果。**只记录事实，不做解释。**"""

    code: str
    side: str
    signal_date: dt.date
    bench: str
    tradable: bool
    reason: str
    entry_date: Optional[dt.date]
    entry_px: Optional[float]
    ret: Mapping[int, Optional[float]]
    excess: Mapping[int, Optional[float]]
    bench_ret: Mapping[int, Optional[float]]
    ret_net: Mapping[int, Optional[float]]
    excess_net: Mapping[int, Optional[float]]
    mfe: Optional[float]
    mae: Optional[float]
    bars_observed: int

    def as_dict(self) -> dict:
        return {
            "code": self.code, "side": self.side,
            "signal_date": self.signal_date.isoformat(), "bench": self.bench,
            "tradable": self.tradable, "reason": self.reason,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "entry_px": self.entry_px,
            "ret": {str(k): v for k, v in self.ret.items()},
            "excess": {str(k): v for k, v in self.excess.items()},
            "bench_ret": {str(k): v for k, v in self.bench_ret.items()},
            "ret_net": {str(k): v for k, v in self.ret_net.items()},
            "excess_net": {str(k): v for k, v in self.excess_net.items()},
            "mfe": self.mfe, "mae": self.mae, "bars_observed": self.bars_observed,
        }


# --------------------------------------------------------------------------
# 只读连接与基础取数
# --------------------------------------------------------------------------

class Library:
    """主库只读访问。**本类不提供任何写入路径。**"""

    def __init__(self, path: Path = DB_PATH, *, read_only: bool = True) -> None:
        if not path.exists():
            raise RuntimeError(f"主库不可用（外接盘未挂载？）: {path}")
        self._con = duckdb.connect(str(path), read_only=read_only)
        # 基准序列在一批判决中是重复输入（同一基准、同一区间），缓存避免重复扫描
        self._bench_cache: dict[tuple[str, dt.date, dt.date], dict] = {}

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "Library":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def trading_days_after(self, day: dt.date, n: int) -> list[dt.date]:
        """严格晚于 `day` 的最近 n 个交易日（升序）。不足则返回现有的。"""
        rows = self._con.execute(
            "SELECT date FROM trade_cal WHERE date > ? ORDER BY date LIMIT ?",
            [day, n],
        ).fetchall()
        return [r[0] for r in rows]

    def qfq_bars(self, code: str, start: dt.date, end: dt.date) -> dict[dt.date, dict]:
        """前复权日线。用 `tech_factor_qfq`，**绝不自己拿 adj_factor 换算**
        ——该列存在负值且语义未验证。"""
        sfx = to_suffix(code)
        rows = self._con.execute(
            "SELECT date, open, high, low, close FROM tech_factor_qfq "
            "WHERE code = ? AND date >= ? AND date <= ? ORDER BY date",
            [sfx, start, end],
        ).fetchall()
        return {r[0]: {"open": r[1], "high": r[2], "low": r[3], "close": r[4]} for r in rows}

    def bench_bars(self, bench: str, start: dt.date, end: dt.date) -> dict[dt.date, dict]:
        key = (bench, start, end)
        hit = self._bench_cache.get(key)
        if hit is not None:
            return hit
        rows = self._con.execute(
            "SELECT date, open, high, low, close FROM index_daily "
            "WHERE code = ? AND date >= ? AND date <= ? ORDER BY date",
            [bench, start, end],
        ).fetchall()
        out = {r[0]: {"open": r[1], "high": r[2], "low": r[3], "close": r[4]} for r in rows}
        self._bench_cache[key] = out
        return out

    def limit_up_down(self, code: str, day: dt.date) -> Optional[tuple[float, float]]:
        """(涨停价, 跌停价)；库中无记录返回 None（**不猜测、不自算**）。"""
        market, num = split_prefix(to_prefix(code))
        # ⚠️ limit_price.market 与 daily.market 同为 'hs'/'bj'（非 'sh'/'sz'）。
        # 必须走 _DAILY_MARKET_OF_EXCHANGE 映射；code 保持前缀式（如 sz000001）。
        row = self._con.execute(
            "SELECT limit_up, limit_down FROM limit_price "
            "WHERE market = ? AND code = ? AND date = ?",
            [_DAILY_MARKET_OF_EXCHANGE[market], f"{market}{num}", day],
        ).fetchone()
        return None if row is None else (row[0], row[1])

    def zt_limit_up_codes(self, day: dt.date) -> list[str]:
        """东财涨停池的代码（后缀式）。

        ⚠️ 这是**事后**名单（收盘后才有的数据）。判决器用它做样本与复盘，
        但**决策层严禁在 T 日盘中使用它**——否则就是未来函数。
        """
        rows = self._con.execute(
            "SELECT DISTINCT 代码 FROM zt_pool_limit_up WHERE 交易时间 = ?", [day]
        ).fetchall()
        return [r[0] for r in rows]

    def raw_open(self, code: str, day: dt.date) -> Optional[float]:
        """**原始价**（未复权）开盘价，用于涨跌停判定。

        ⚠️ 为什么单独要有这个方法：
        `limit_price.limit_up/limit_down` 是**原始价**口径（由原始前收盘算出）。
        若拿 `tech_factor_qfq` 的**前复权**价去和它比较，跨除权日必然判错——
        实测已复现：600743.SH 原始价开盘即涨停，前复权价比较却判为"可成交"。
        规则：**涨跌停用原始价比较，收益用前复权价计算**，两者绝不混用。
        """
        market, num = split_prefix(to_prefix(code))
        # daily.market 是 'hs'/'bj'，不是 'sh'/'sz'（见模块顶部实测陷阱）
        row = self._con.execute(
            "SELECT open FROM daily WHERE market = ? AND code = ? AND date = ?",
            [_DAILY_MARKET_OF_EXCHANGE[market], f"{market}{num}", day],
        ).fetchone()
        return None if row is None else row[0]

    def is_suspended(self, code: str, day: dt.date) -> bool:
        """`suspension.交易日期` 是 VARCHAR 'YYYYMMDD'（实测）。"""
        sfx = to_suffix(code)
        row = self._con.execute(
            "SELECT 1 FROM suspension WHERE 股票代码 = ? AND 交易日期 = ? LIMIT 1",
            [sfx, day.strftime("%Y%m%d")],
        ).fetchone()
        return row is not None


# --------------------------------------------------------------------------
# 判决主逻辑
# --------------------------------------------------------------------------

def _pct(cur: Optional[float], base: Optional[float]) -> Optional[float]:
    """收益率；任一缺失即返回 None —— **缺失不等于 0**。"""
    if cur is None or base is None or base == 0:
        return None
    return cur / base - 1.0


def _blocked(decision: Decision, reason: str, entry_day, entry_px, observed: int) -> Outcome:
    """构造"不可成交"结果：收益一律 MISSING，绝不写 0。"""
    return Outcome(
        code=to_suffix(decision.code), side=decision.side,
        signal_date=decision.signal_date, bench=decision.bench,
        tradable=False, reason=reason, entry_date=entry_day, entry_px=entry_px,
        ret={k: MISSING for k in decision.horizons},
        excess={k: MISSING for k in decision.horizons},
        bench_ret={k: MISSING for k in decision.horizons},
        ret_net={k: MISSING for k in decision.horizons},
        excess_net={k: MISSING for k in decision.horizons},
        mfe=MISSING, mae=MISSING, bars_observed=observed,
    )


def judge(decision: Decision, lib: Library) -> Outcome:
    """复算一条决策的真实结果。纯读取，无副作用。"""
    T = decision.signal_date
    max_h = max(decision.horizons)
    days = lib.trading_days_after(T, max_h)
    if not days:
        return _blocked(decision, "no_trading_day_after_T", None, None, 0)

    entry_day, window_end = days[0], days[-1]
    bars = lib.qfq_bars(decision.code, entry_day, window_end)
    bench = lib.bench_bars(decision.bench, entry_day, window_end)
    observed = len(bars)

    if lib.is_suspended(decision.code, entry_day):
        return _blocked(decision, "suspended_on_entry", entry_day, None, observed)
    entry_bar = bars.get(entry_day)
    if entry_bar is None:
        return _blocked(decision, "no_bar_on_entry", entry_day, None, observed)

    entry_px = entry_bar["open"]
    lim = lib.limit_up_down(decision.code, entry_day)
    # 关键：涨跌停是**原始价**口径，必须用原始开盘价比较，不能用前复权价。
    # raw_open 兜底必须独立于 lim —— 即使查不到涨停价（新股无涨跌停 / 数据缺失），
    # 取不到原始价也应 fail-closed，而不是静默当"可成交"（P0：封板判定曾被一起跳过）。
    raw_open = lib.raw_open(decision.code, entry_day)
    if raw_open is None:
        # 无法核验可交易性 -> fail-closed，不谎报"可成交"
        return _blocked(decision, "no_raw_bar_on_entry", entry_day, entry_px, observed)
    if lim is not None:
        up, down = lim
        if decision.side == "buy" and raw_open >= up:
            return _blocked(decision, "limit_up_on_open", entry_day, entry_px, observed)
        if decision.side == "sell" and raw_open <= down:
            return _blocked(decision, "limit_down_on_open", entry_day, entry_px, observed)

    bench_open = bench[entry_day]["open"] if entry_day in bench else None

    ret: dict[int, Optional[float]] = {}
    excess: dict[int, Optional[float]] = {}
    bench_ret: dict[int, Optional[float]] = {}
    ret_net: dict[int, Optional[float]] = {}
    excess_net: dict[int, Optional[float]] = {}
    for k in decision.horizons:
        if k > len(days):
            ret[k] = excess[k] = bench_ret[k] = MISSING
            ret_net[k] = excess_net[k] = MISSING
            continue
        d = days[k - 1]
        bar, bb = bars.get(d), bench.get(d)
        r = _pct(bar["close"] if bar else None, entry_px)
        br = _pct(bb["close"] if bb else None, bench_open)
        ret[k], bench_ret[k] = r, br
        excess[k] = (r - br) if (r is not None and br is not None) else MISSING
        # 净 = 毛 − 往返成本（基准不计成本，故净超额 = 毛超额 − cost）
        ret_net[k] = (r - decision.cost) if r is not None else MISSING
        excess_net[k] = (excess[k] - decision.cost) if excess[k] is not None else MISSING

    held = [bars[d] for d in days if d in bars]
    mfe = (max(b["high"] for b in held) / entry_px - 1.0) if held else MISSING
    mae = (min(b["low"] for b in held) / entry_px - 1.0) if held else MISSING

    return Outcome(
        code=to_suffix(decision.code), side=decision.side,
        signal_date=T, bench=decision.bench, tradable=True, reason="",
        entry_date=entry_day, entry_px=entry_px,
        ret=ret, excess=excess, bench_ret=bench_ret,
        ret_net=ret_net, excess_net=excess_net,
        mfe=mfe, mae=mae, bars_observed=observed,
    )


# --------------------------------------------------------------------------
# 汇总：把一批结果压成**可对比**的质量指标
# --------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Quality:
    """一批决策的质量指标。这是验收新系统的唯一合法口径。"""

    n_total: int
    n_tradable: int
    n_untradable: int
    n_missing: int
    hit_rate: Mapping[int, Optional[float]]
    avg_ret: Mapping[int, Optional[float]]
    avg_excess: Mapping[int, Optional[float]]
    payoff: Mapping[int, Optional[float]]
    hit_rate_net: Mapping[int, Optional[float]]
    avg_ret_net: Mapping[int, Optional[float]]
    avg_excess_net: Mapping[int, Optional[float]]
    avg_mfe: Optional[float]
    avg_mae: Optional[float]

    def as_dict(self) -> dict:
        return {
            "n_total": self.n_total, "n_tradable": self.n_tradable,
            "n_untradable": self.n_untradable, "n_missing": self.n_missing,
            "hit_rate": {str(k): v for k, v in self.hit_rate.items()},
            "avg_ret": {str(k): v for k, v in self.avg_ret.items()},
            "avg_excess": {str(k): v for k, v in self.avg_excess.items()},
            "payoff": {str(k): v for k, v in self.payoff.items()},
            "hit_rate_net": {str(k): v for k, v in self.hit_rate_net.items()},
            "avg_ret_net": {str(k): v for k, v in self.avg_ret_net.items()},
            "avg_excess_net": {str(k): v for k, v in self.avg_excess_net.items()},
            "avg_mfe": self.avg_mfe, "avg_mae": self.avg_mae,
        }


def _mean(xs: Sequence[float]) -> Optional[float]:
    return (sum(xs) / len(xs)) if xs else MISSING


def summarize(outcomes: Iterable[Outcome], horizons: Sequence[int]) -> Quality:
    """统一口径汇总。**不可成交的决策不计入收益统计，但计入 n_untradable**，
    这样"因为封板买不到"这类事实不会被悄悄从分母里抹掉。"""
    os_ = list(outcomes)
    tradable = [o for o in os_ if o.tradable]
    hit: dict[int, Optional[float]] = {}
    avg: dict[int, Optional[float]] = {}
    avg_ex: dict[int, Optional[float]] = {}
    payoff: dict[int, Optional[float]] = {}
    hit_net: dict[int, Optional[float]] = {}
    avg_net: dict[int, Optional[float]] = {}
    avg_ex_net: dict[int, Optional[float]] = {}
    for k in horizons:
        rr = [o.ret.get(k) for o in tradable]
        ee = [o.excess.get(k) for o in tradable]
        rn = [o.ret_net.get(k) for o in tradable]
        en = [o.excess_net.get(k) for o in tradable]
        rr = [x for x in rr if x is not None]
        ee = [x for x in ee if x is not None]
        rn = [x for x in rn if x is not None]
        en = [x for x in en if x is not None]
        hit[k] = (sum(1 for x in ee if x > 0) / len(ee)) if ee else MISSING
        avg[k] = _mean(rr)
        avg_ex[k] = _mean(ee)
        hit_net[k] = (sum(1 for x in en if x > 0) / len(en)) if en else MISSING
        avg_net[k] = _mean(rn)
        avg_ex_net[k] = _mean(en)
        wins = [x for x in ee if x > 0]
        loss = [x for x in ee if x < 0]
        payoff[k] = ((sum(wins) / len(wins)) / abs(sum(loss) / len(loss))) if (wins and loss) else MISSING
    mfes = [o.mfe for o in tradable if o.mfe is not None]
    maes = [o.mae for o in tradable if o.mae is not None]
    return Quality(
        n_total=len(os_), n_tradable=len(tradable),
        n_untradable=sum(1 for o in os_ if not o.tradable),
        n_missing=sum(1 for o in tradable if all(o.ret.get(k) is None for k in horizons)),
        hit_rate=hit, avg_ret=avg, avg_excess=avg_ex, payoff=payoff,
        hit_rate_net=hit_net, avg_ret_net=avg_net, avg_excess_net=avg_ex_net,
        avg_mfe=_mean(mfes), avg_mae=_mean(maes),
    )
