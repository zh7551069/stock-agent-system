"""Trace 总线 · 前缀门禁 + Span 模型单测。"""

from trace.gate import GateError, validate_attrs
from trace.model import SpanType


def test_span_type_covers_eight_types():
    assert {t.value for t in SpanType} == {
        "turn", "llm", "data", "tool", "retrieve", "guard", "judge", "event",
    }


def test_valid_three_layer_attrs_pass():
    # L1 / L2 / L3 各一层，都应放行
    validate_attrs({
        "trace.model": "deepseek-flash",
        "trad.signal": "limit_up",
        "a股.code": "sz000001",
    })


def test_illegal_prefix_rejected():
    try:
        validate_attrs({"my_attr": 1})
    except GateError as e:
        assert "my_attr" in str(e)
    else:
        raise AssertionError("应抛 GateError")


def test_bare_prefix_is_still_illegal_in_strict():
    # 硬门禁放行（前缀合法），strict 拒绝（未注册）
    validate_attrs({"trace.": 1})  # 不抛
    try:
        validate_attrs({"trace.": 1}, strict=True)
    except GateError:
        pass
    else:
        raise AssertionError("strict 应拒绝未注册键")


def test_strict_mode_rejects_unknown_key():
    try:
        validate_attrs({"trace.unknowwn": 1}, strict=True)
    except GateError:
        pass
    else:
        raise AssertionError("strict 应拒绝未注册键")


def test_strict_mode_accepts_registered_key():
    validate_attrs({"trad.excess": -0.42}, strict=True)
