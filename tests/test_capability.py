"""能力管家 · 契约测试 + 注册表单测。"""

from capability.contract_test import ContractCase, run_contract_test
from capability.registry import CapabilityRegistry, STATUS_PROMOTED, STATUS_ROLLBACK
from custodian.contract import SYNC_TOOL


def _sync_tool_fn(ok=True):
    """模拟 taobao_sync.sync 返回结构的工具。"""
    def fn(download_dir, db_path, **kw):
        out = {
            "imported": {"daily": 1}, "unknown_count": 0, "qc": {"market": True},
            "verify": {"ok": ok, "detail": "x"}, "removed": 0,
        }
        if not ok:
            raise ValueError("QC 未过")
        return out
    return fn


def test_contract_test_all_pass_promotes():
    cases = [
        ContractCase(name="正常同步", inputs={"download_dir": "/d", "db_path": "/db"},
                     expect_keys=("imported", "unknown_count", "qc", "verify", "removed")),
    ]
    r = run_contract_test(SYNC_TOOL.id, SYNC_TOOL.version, _sync_tool_fn(), cases)
    assert r.passed is True
    assert r.decision == "promote"
    assert r.failures == ()


def test_contract_test_missing_key_fails():
    cases = [ContractCase(name="c", inputs={"download_dir": "/d", "db_path": "/db"}, expect_keys=("nope",))]
    r = run_contract_test("t", "1", _sync_tool_fn(), cases)
    assert r.passed is False
    assert any("nope" in f for f in r.failures)
    assert r.decision == "rollback"


def test_contract_test_expect_error_passes():
    cases = [ContractCase(name="反例", inputs={"download_dir": "/d", "db_path": "/db"}, expect_error=ValueError)]
    r = run_contract_test("t", "1", _sync_tool_fn(ok=False), cases)
    assert r.passed is True


def test_contract_test_expect_error_but_no_error_fails():
    cases = [ContractCase(name="反例", inputs={"download_dir": "/d", "db_path": "/db"}, expect_error=ValueError)]
    r = run_contract_test("t", "1", _sync_tool_fn(ok=True), cases)
    assert r.passed is False
    assert any("未抛" in f for f in r.failures)


def test_registry_register_promote_list():
    reg = CapabilityRegistry()
    reg.register(SYNC_TOOL)
    assert reg.get(SYNC_TOOL.id).status == "registered"
    assert reg.promoted(SYNC_TOOL.id) is False

    reg.set_status(SYNC_TOOL.id, STATUS_PROMOTED, SYNC_TOOL.version)
    assert reg.promoted(SYNC_TOOL.id) is True
    assert reg.get(SYNC_TOOL.id).tested_version == SYNC_TOOL.version
    assert len(reg.list()) == 1


def test_registry_rollback():
    reg = CapabilityRegistry()
    reg.register(SYNC_TOOL)
    reg.set_status(SYNC_TOOL.id, STATUS_ROLLBACK, "2")
    assert reg.promoted(SYNC_TOOL.id) is False
    assert reg.get(SYNC_TOOL.id).status == STATUS_ROLLBACK
