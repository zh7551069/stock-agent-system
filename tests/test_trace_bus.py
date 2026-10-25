"""Trace 总线 · append-only 哈希链 + 门禁落盘单测。"""

import json

import pytest

from trace.bus import GENESIS_HASH, TraceBus
from trace.gate import GateError
from trace.model import Span, SpanType


def _span(span_id: str, session: str = "sesn_20260101_00000000") -> Span:
    return Span(
        span_id=span_id,
        span_type=SpanType.GUARD,
        name="limit_up_check",
        session_id=session,
        ts="2026-01-02T09:30:00",
        attrs={"a股.code": "sz000001", "trad.signal": "limit_up"},
    )


def test_append_two_spans_and_verify(tmp_path):
    bus = TraceBus(tmp_path / "trace.jsonl")
    h1 = bus.append(_span("s1"))
    h2 = bus.append(_span("s2"))
    assert h1 != h2

    lines = (tmp_path / "trace.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["prev_hash"] == GENESIS_HASH
    assert json.loads(lines[1])["prev_hash"] == h1

    ok, msg = TraceBus.verify(tmp_path / "trace.jsonl")
    assert ok, msg


def test_tamper_is_detected(tmp_path):
    path = tmp_path / "trace.jsonl"
    bus = TraceBus(path)
    bus.append(_span("s1"))
    bus.append(_span("s2"))
    # 用 round-trip 篡改第一行（而非字符串替换，避免与分隔符格式耦合）
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["name"] = "tampered"
    lines[0] = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    ok, msg = TraceBus.verify(path)
    assert not ok


def test_resume_keeps_chain(tmp_path):
    path = tmp_path / "trace.jsonl"
    TraceBus(path).append(_span("s1"))
    # 重新打开（模拟进程重启），链应延续且可校验
    TraceBus(path).append(_span("s2"))
    ok, msg = TraceBus.verify(path)
    assert ok, msg


def test_illegal_attr_blocked_at_append(tmp_path):
    path = tmp_path / "trace.jsonl"
    bus = TraceBus(path)
    bad = Span(
        span_id="s1", span_type=SpanType.DATA, name="x", session_id="sesn_x",
        ts="2026-01-01T00:00:00", attrs={"my_attr": 1},
    )
    with pytest.raises(GateError):
        bus.append(bad)
    # 门禁在开文件之前触发，非法 span 不应落盘（文件尚未创建）
    assert not path.exists()
    # 后续合法 span 应从创世哈希起链
    bus.append(_span("s1"))
    ok, msg = TraceBus.verify(path)
    assert ok, msg


def test_empty_file_is_verified(tmp_path):
    path = tmp_path / "trace.jsonl"
    path.write_text("")
    ok, msg = TraceBus.verify(path)
    assert ok, msg
