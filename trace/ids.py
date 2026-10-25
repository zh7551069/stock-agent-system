"""四元 id 生成（session → decision → strategy → factor）。

一条决策全链用同一串 id 串起来，评测平台可任意回放任意环节（见 eval-platform.md）。
本模块只提供**格式约定**，保证可读、可排序、可追溯；具体分配由调度器/主控执行。
"""

from __future__ import annotations

import datetime as dt
import uuid


def session_id(when: dt.date | None = None) -> str:
    """``sesn_YYYYMMDD_<8位随机>``。会话的唯一入口标识。"""
    d = when or dt.date.today()
    return f"sesn_{d:%Y%m%d}_{uuid.uuid4().hex[:8]}"


def decision_id(session: str, seq: int) -> str:
    """``dec_<session日期>_<序号>``。序号为同一 session 内递增（从 1 起）。

    ``session`` 形如 ``sesn_20260101_00000000``；本函数只取其日期段。
    """
    date_part = session.removeprefix("sesn_").split("_")[0]
    return f"dec_{date_part}_{seq:03d}"


def strategy_id(name: str, version: str) -> str:
    """``strat_<name>@<version>``。策略注册表条目引用。"""
    return f"strat_{name}@{version}"


def factor_id(name: str, version: str) -> str:
    """``factor_<name>@<version>``。因子字典条目引用。"""
    return f"factor_{name}@{version}"
