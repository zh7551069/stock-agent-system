"""能力管家 · 工具契约（ToolContract）——数据管家 agent 壳的第一层。

一个「能力」= 一份可机器校验的契约：入参/出参 schema + 幂等键 + 副作用 + 超时。
能力管家据此做契约测试、晋级/回滚；调度器据此做幂等/预算/超时（见 protocol.md 的
「消息信封」与「写域隔离」）。

这里的 schema 用**简化形式**（字段名 → 类型/说明），够契约测试与文档用；
正式 JSON Schema 由能力管家在注册时展开。
"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Sequence


@dataclasses.dataclass(frozen=True)
class ToolContract:
    """一份工具/技能契约（能力注册表条目）。"""

    id: str                             # 能力注册表 id，如 'tool.data.sync_taobao'
    version: str
    description: str
    inputs: Mapping[str, str]           # 入参名 → 类型/说明
    outputs: Mapping[str, str]          # 出参名 → 类型/说明
    idempotency_fields: Sequence[str]   # 幂等键的构成字段（顺序敏感）
    side_effects: Sequence[str]         # 副作用（writes:/removes:...）
    timeout_s: int


#: taobao_sync v3 的契约（对齐 docs/plan03-site/scripts/taobao_sync.py 的 sync()）。
SYNC_TOOL = ToolContract(
    id="tool.data.sync_taobao",
    version="3",
    description="淘宝数据同步：本地 CSV/zip → duckDB，口径归一 + QC 门禁",
    inputs={
        "download_dir": "str（本地下载目录，含 CSV/zip）",
        "db_path": "str（目标 duckDB 路径）",
        "dry_run": "bool=False（只预览不写库不删源）",
        "verify": "bool=True（线上抽样验证）",
        "keep_source": "bool=False（验证通过后保留源文件）",
        "csv_only": "bool=False（只扫 CSV 不扫 zip）",
        "only_tables": "list[str]|None（只导入指定表）",
    },
    outputs={
        "imported": "dict[table, count]（各表导入行数）",
        "unknown_count": "int（表头无匹配、未识别数）",
        "qc": "dict[rule, bool]（QC 断言是否全过）",
        "verify": "dict[ok, detail]（线上验证结果）",
        "removed": "int（验证+QC 通过后删除的源文件数）",
    },
    idempotency_fields=("download_dir", "db_path", "date"),
    side_effects=("writes:duckdb", "removes:source_csv"),  # 删源仅当 verify+QC 通过
    timeout_s=3600,
)
