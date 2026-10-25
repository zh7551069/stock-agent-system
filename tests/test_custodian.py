"""数据管家 · agent 壳（工具契约 + 幂等键 + 结构化结果）单测。"""

import datetime as dt
import importlib.util
import inspect
import json
import pathlib

import pytest

from custodian.contract import SYNC_TOOL
from custodian.sync_tool import make_idempotency_key, run_sync


def _fake_sync(**over):
    def fn(download_dir, db_path, **kw):
        return {
            "imported": {"daily": 100, "limit_price": 50},
            "unknown_count": 2,
            "qc": {"market": True, "code": False},
            "verify": {"ok": True, "detail": "抽样通过"},
            "removed": 3,
            **over,
        }
    return fn


def test_contract_fields():
    assert SYNC_TOOL.id == "tool.data.sync_taobao"
    assert SYNC_TOOL.version == "3"
    assert "writes:duckdb" in SYNC_TOOL.side_effects
    assert SYNC_TOOL.idempotency_fields == ("download_dir", "db_path", "date")


def test_idempotency_key_deterministic_and_date_sensitive():
    a = make_idempotency_key("/d", "/db", when=dt.date(2026, 1, 1))
    b = make_idempotency_key("/d", "/db", when=dt.date(2026, 1, 1))
    c = make_idempotency_key("/d", "/db", when=dt.date(2026, 1, 2))
    assert a == b
    assert a != c


def test_run_sync_normalizes_result():
    r = run_sync(_fake_sync(), download_dir="/d", db_path="/db", when=dt.date(2026, 1, 1))
    assert r.tool == "tool.data.sync_taobao"
    assert r.imported == {"daily": 100, "limit_price": 50}
    assert r.unknown_count == 2
    assert r.qc == {"market": True, "code": False}
    assert r.verify_ok is True
    assert r.removed == 3
    # 幂等键含日期
    assert r.idempotency_key == make_idempotency_key("/d", "/db", dt.date(2026, 1, 1))


def test_run_sync_result_is_json_serializable():
    r = run_sync(_fake_sync(), download_dir="/d", db_path="/db", when=dt.date(2026, 1, 1))
    json.dumps(r.to_dict())  # 不抛即通过
    d = r.to_dict()
    assert d["verify"] == {"ok": True, "detail": "抽样通过"}


def test_run_sync_passes_flags_through():
    seen = {}
    def fn(download_dir, db_path, **kw):
        seen.update(kw)
        return {"imported": {}, "unknown_count": 0, "qc": {}, "verify": {"ok": True, "detail": ""}, "removed": 0}
    run_sync(fn, download_dir="/d", db_path="/db", dry_run=True, only_tables=["daily"], when=dt.date(2026, 1, 1))
    assert seen["dry_run"] is True
    assert seen["only_tables"] == ["daily"]


def test_contract_matches_real_sync_signature():
    """契约入参 ⊆ 真实 taobao_sync.sync() 的参数（防契约漂移）。"""
    p = pathlib.Path(__file__).resolve().parents[1] / "docs" / "plan03-site" / "scripts" / "taobao_sync.py"
    spec = importlib.util.spec_from_file_location("taobao_sync_under_test", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"taobao_sync 导入失败（环境缺 duckdb/pandas？）: {type(e).__name__}")
    params = list(inspect.signature(mod.sync).parameters)
    assert set(SYNC_TOOL.inputs) <= set(params)
