"""知识馆长 · 知识卡 + 知识库 单测。"""

import pytest

from knowledge.card import new_card
from knowledge.store import KnowledgeStore


def test_new_card_no_source_defaults_to_uncertified():
    c = new_card("kb1", "涨停家数<30 唯一正收益区")
    assert c.evidence_grade == "待考证"
    assert c.status == "active"


def test_new_card_with_source_and_grade():
    c = new_card("kb2", "拥挤度低桶超额更高", source="回测:slice_2023", evidence_grade="B",
                 regime_scope="拥挤度", version="v2")
    assert c.evidence_grade == "B"
    assert c.version == "v2"


def test_new_card_no_source_rejects_abc_grade():
    with pytest.raises(ValueError):
        new_card("kb3", "无出处却标 A", evidence_grade="A")


def test_new_card_rejects_bad_grade():
    with pytest.raises(ValueError):
        new_card("kb4", "x", source="s", evidence_grade="D")


def test_store_dedup_by_conclusion():
    s = KnowledgeStore()
    id1 = s.add(new_card("kb1", "涨停家数<30 唯一正收益区"))
    id2 = s.add(new_card("kb2", "  涨停家数 <30 唯一正收益区 "))  # 归一后同结论
    assert id1 == id2
    assert len(s) == 1


def test_store_refute_downgrades():
    s = KnowledgeStore()
    s.add(new_card("kb1", "某论断", source="回测", evidence_grade="B"))
    c = s.refute("kb1", version="v2")
    assert c.status == "refuted"
    assert c.evidence_grade == "待考证"
    assert s.get("kb1").status == "refuted"


def test_store_by_grade_and_regime():
    s = KnowledgeStore()
    s.add(new_card("a", "结论A", source="书", evidence_grade="A", regime_scope="涨停家数<30"))
    s.add(new_card("b", "结论B", source="回测", evidence_grade="B", regime_scope="拥挤度"))
    s.add(new_card("c", "结论C", evidence_grade="待考证", regime_scope="涨停家数<30"))
    assert {c.card_id for c in s.by_grade("待考证")} == {"c"}
    assert {c.card_id for c in s.by_regime("涨停家数<30")} == {"a", "c"}
