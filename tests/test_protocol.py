"""协议注册表 · 消息信封 / 写域隔离 / 进化动作 单测。"""

from protocol.acl import is_write_allowed, violations
from protocol.envelope import Envelope, validate_envelope
from protocol.evolution import validate_evolution_action
from protocol.registry import PROTOCOLS


def _env(**kw) -> Envelope:
    base = dict(
        session_id="sesn_20260101_00000000", msg_type="command",
        schema_version="v1", idempotency_key="k1",
    )
    base.update(kw)
    return Envelope(**base)


def test_envelope_valid():
    assert validate_envelope(_env()) == []


def test_envelope_catches_violations():
    v = validate_envelope(_env(session_id="", msg_type="bogus", schema_version="", idempotency_key=""))
    assert len(v) == 4


def test_envelope_rejects_unknown_msg_type():
    v = validate_envelope(_env(msg_type="frobnicate"))
    assert any("msg_type" in x for x in v)


def test_acl_commander_cannot_write_verdict_db():
    assert is_write_allowed("commander", "task_plan") is True
    assert is_write_allowed("commander", "verdict_db") is False
    assert any("越权" in x for x in violations("commander", "verdict_db"))


def test_acl_backtest_judge_only_writes_verdict_db():
    assert is_write_allowed("backtest_judge", "verdict_db") is True
    assert is_write_allowed("backtest_judge", "database") is False


def test_acl_unknown_agent_fail_closed():
    assert is_write_allowed("nobody", "database") is False


def test_evolution_valid_action():
    a = {"type": "tune_factor_params", "evidence_id": "evt_1"}
    assert validate_evolution_action(a) == []


def test_evolution_rejects_bare_action():
    v = validate_evolution_action({"type": "reweight_factors"})
    assert any("evidence_id" in x for x in v)


def test_evolution_rejects_unknown_type():
    v = validate_evolution_action({"type": "smash_factor", "evidence_id": "e"})
    assert any("type" in x for x in v)


def test_registry_lists_nine_contracts():
    assert len(PROTOCOLS) == 9
    assert any(c.name == "写域隔离" for c in PROTOCOLS)
    # 三条机械校验契约有入口
    mechanical = [c for c in PROTOCOLS if c.check]
    assert len(mechanical) >= 3
