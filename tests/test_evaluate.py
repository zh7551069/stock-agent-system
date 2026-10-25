"""评测平台 · 评估器 + 三重门控 单测。"""

from evaluate.evaluator import RuleEvaluator, staged_judge
from evaluate.triple_gate import triple_gate


def _protocol_rule() -> RuleEvaluator:
    return RuleEvaluator(name="协议合规", rule=lambda ev: "bad" if ev.get("violation") else "待复核")


def _cost_rule() -> RuleEvaluator:
    def rule(ev):
        cost = ev.get("cost")
        return "bad" if (cost is not None and cost > 100) else "待复核"
    return RuleEvaluator(name="成本预算", rule=rule)


def test_staged_judge_rule_catches_bad():
    rules = [_protocol_rule(), _cost_rule()]
    v, src = staged_judge(rules, {"violation": True})
    assert v == "bad"
    assert src == "协议合规"


def test_staged_judge_falls_through_to_llm():
    rules = [_protocol_rule(), _cost_rule()]
    calls = []
    v, src = staged_judge(rules, {}, llm_judge=lambda ev: calls.append(1) or "good")
    assert v == "good"
    assert src == "llm"
    assert calls == [1]


def test_staged_judge_no_llm_review():
    rules = [_protocol_rule()]
    v, src = staged_judge(rules, {})
    assert v == "待复核"


def test_triple_gate_promote_when_all_ok():
    g = triple_gate(old_badcase_rate=0.2, new_badcase_rate=0.1, min_effect=0.01)
    assert g.decision == "promote"
    assert g.passed is True


def test_triple_gate_rollback_on_gain_fail():
    g = triple_gate(old_badcase_rate=0.1, new_badcase_rate=0.12, min_effect=0.01)
    assert g.decision == "rollback"
    assert g.gain_ok is False
    assert any("增益" in r for r in g.reasons)


def test_triple_gate_rollback_on_forget_fail():
    g = triple_gate(old_badcase_rate=0.2, new_badcase_rate=0.1, min_effect=0.01, recurrence=True)
    assert g.decision == "rollback"
    assert g.forget_ok is False


def test_triple_gate_rollback_on_safety_fail():
    g = triple_gate(old_badcase_rate=0.2, new_badcase_rate=0.1, min_effect=0.01, violations=["越权写判决库"])
    assert g.decision == "rollback"
    assert g.safety_ok is False


def test_triple_gate_min_effect_boundary():
    # 恰好达到最小效应量阈值不算通过（必须严格低于 old - min_effect）
    g = triple_gate(old_badcase_rate=0.2, new_badcase_rate=0.19, min_effect=0.01)
    assert g.gain_ok is False
