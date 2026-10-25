"""Trace 总线 · append-only 落盘 + 哈希链。

- **append-only**：只追加 JSONL 行，永不改写 / 截断。
- **哈希链**：每行 ``hash = sha256(prev_hash + 规范化自身)``，首行 ``prev_hash = 0*64``。
  复盘只能基于原始 trace；篡改任意一行，:meth:`TraceBus.verify` 即失败。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from trace.gate import validate_attrs
from trace.model import Span

#: 创世哈希（首行 prev_hash 的锚点）。
GENESIS_HASH = "0" * 64


def _canonical(obj: dict) -> str:
    """规范化 JSON（键排序、紧凑、保中文），保证同一记录哈希稳定。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_record(rec: dict) -> str:
    return hashlib.sha256(_canonical(rec).encode("utf-8")).hexdigest()


class TraceBus:
    """append-only Trace 总线：写 span → 一行 JSONL，行间哈希链。"""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._last_hash = GENESIS_HASH
        if self._path.exists():
            self._last_hash = _tail_hash(self._path)

    @property
    def path(self) -> Path:
        return self._path

    def append(self, span: Span) -> str:
        """校验门禁 → 落一行 → 返回该 span 的 hash（同时成为下一行的 prev_hash）。"""
        validate_attrs(span.attrs)
        rec = {**span.to_dict(), "prev_hash": self._last_hash}
        rec["hash"] = _hash_record(rec)
        line = _canonical(rec)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._last_hash = rec["hash"]
        return rec["hash"]

    @staticmethod
    def verify(path: Path) -> tuple[bool, str]:
        """校验整条哈希链；返回 ``(是否完整, 说明)``。"""
        prev = GENESIS_HASH
        p = Path(path)
        if not p.exists():
            return (False, f"文件不存在: {p}")
        n = 0
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                return (False, f"第 {i} 行 JSON 解析失败: {e}")
            if rec.get("prev_hash") != prev:
                return (False, f"第 {i} 行 prev_hash 断裂（期望 {prev[:8]}…，实得 {str(rec.get('prev_hash'))[:8]}…）")
            rec_no_hash = {k: v for k, v in rec.items() if k != "hash"}
            if _hash_record(rec_no_hash) != rec.get("hash"):
                return (False, f"第 {i} 行 hash 校验失败（内容被篡改）")
            prev = rec["hash"]
            n = i
        return (True, f"链完整（{n} 行）")


def _tail_hash(path: Path) -> str:
    """读最后一行取它的 hash；文件为空返回创世 hash。"""
    prev = GENESIS_HASH
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            prev = json.loads(line)["hash"]
    return prev
