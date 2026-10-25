"""数据管家 · 同步工具壳（taobao_sync 的可调用包装）。

把 ``taobao_sync.sync()`` 包成「带幂等键 + 结构化 JSON 结果」的 agent 可调用工具。
``sync_fn`` 经依赖注入传入，本模块不 import ``taobao_sync``（物理隔离、可测、可替换）。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
from typing import Any, Callable, Mapping, Optional, Sequence

from custodian.contract import SYNC_TOOL

#: sync 函数签名（taobao_sync.sync 的入参子集）。
SyncFn = Callable[..., Mapping[str, Any]]


@dataclasses.dataclass(frozen=True)
class SyncResult:
    """一次同步的结构化结果（对齐 SYNC_TOOL.outputs）。"""

    idempotency_key: str
    tool: str
    version: str
    imported: Mapping[str, int]
    unknown_count: int
    qc: Mapping[str, bool]
    verify_ok: bool
    verify_detail: str
    removed: int

    def to_dict(self) -> dict:
        """规范序列化（JSON 可序列化，供 agent 消费/落库）。"""
        return {
            "idempotency_key": self.idempotency_key,
            "tool": self.tool,
            "version": self.version,
            "imported": dict(self.imported),
            "unknown_count": self.unknown_count,
            "qc": dict(self.qc),
            "verify": {"ok": self.verify_ok, "detail": self.verify_detail},
            "removed": self.removed,
        }


def make_idempotency_key(download_dir: str, db_path: str, when: dt.date | None = None) -> str:
    """幂等键 = ``sha256(download_dir|db_path|date)``。

    同一目录 + 库 + 日重复同步应幂等（调度器据此去重、重试安全）。
    """
    d = (when or dt.date.today()).isoformat()
    return hashlib.sha256(f"{download_dir}|{db_path}|{d}".encode("utf-8")).hexdigest()


def run_sync(
    sync_fn: SyncFn,
    *,
    download_dir: str,
    db_path: str,
    dry_run: bool = False,
    verify: bool = True,
    keep_source: bool = False,
    csv_only: bool = False,
    only_tables: Optional[Sequence[str]] = None,
    when: dt.date | None = None,
) -> SyncResult:
    """调用 ``sync_fn`` 并把返回 dict 归一成结构化 :class:`SyncResult`。"""
    key = make_idempotency_key(download_dir, db_path, when)
    raw = sync_fn(
        download_dir,
        db_path,
        dry_run=dry_run,
        verify=verify,
        keep_source=keep_source,
        csv_only=csv_only,
        only_tables=only_tables,
    )
    return SyncResult(
        idempotency_key=key,
        tool=SYNC_TOOL.id,
        version=SYNC_TOOL.version,
        imported=raw.get("imported", {}),
        unknown_count=raw.get("unknown_count", 0),
        qc=raw.get("qc", {}),
        verify_ok=raw.get("verify", {}).get("ok", False),
        verify_detail=raw.get("verify", {}).get("detail", ""),
        removed=raw.get("removed", 0),
    )


# ── 基础数据 / 榜单数据（目录型同步，agent 可直接调用）──

def run_base_data(
    sync_fn: SyncFn,
    *,
    base_dir: str,
    db_path: str,
    dry_run: bool = False,
    when: dt.date | None = None,
) -> SyncResult:
    """同步《A股交易基础数据》目录（交易日历/停复牌/涨跌停/ST/股票列表）。

    ``sync_fn`` 需为 ``taobao_sync.sync_base_data(base_dir, con, dry_run)``（接受连接）。
    """
    import duckdb

    key = make_idempotency_key(base_dir, db_path, when)
    con = duckdb.connect(db_path, read_only=dry_run)
    try:
        raw = sync_fn(base_dir, con, dry_run=dry_run)
    finally:
        con.close()
    return SyncResult(
        idempotency_key=key,
        tool=SYNC_TOOL.id,
        version=SYNC_TOOL.version,
        imported=raw,
        unknown_count=0,
        qc={},
        verify_ok=True,
        verify_detail="base_data（目录型，无线上验证）",
        removed=0,
    )


def run_list_data(
    sync_fn: SyncFn,
    *,
    base_dir: str,
    db_path: str,
    dry_run: bool = False,
    when: dt.date | None = None,
) -> SyncResult:
    """同步《A股_榜单数据》目录（涨停池/同花顺池/龙虎榜/连板天梯等，增量幂等）。

    ``sync_fn`` 需为 ``taobao_sync.sync_list_data(base_dir, con, dry_run)``（接受连接）。
    """
    import duckdb

    key = make_idempotency_key(base_dir, db_path, when)
    con = duckdb.connect(db_path, read_only=dry_run)
    try:
        raw = sync_fn(base_dir, con, dry_run=dry_run)
    finally:
        con.close()
    return SyncResult(
        idempotency_key=key,
        tool=SYNC_TOOL.id,
        version=SYNC_TOOL.version,
        imported=raw,
        unknown_count=0,
        qc={},
        verify_ok=True,
        verify_detail="list_data（目录型，按日期替换幂等）",
        removed=0,
    )
