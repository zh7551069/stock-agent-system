"""决策面 · 决策包契约 + 主控任务清单 单测。"""

from decision.pack import DecisionPack, validate_pack
from decision.task import Task, validate_task


def _pack(**kw) -> DecisionPack:
    base = dict(
        decision_id="dec_20260101_001", strategy_id="strat_rsi6@2.1",
        signal="rsi6<20 且 收盘站上 MA20", entry="T+1 开盘买入",
        exit="stop=-8% / TP=+12% / 持有至 T+20", position=0.3,
        risk="单票仓位≤30%，回撤≤5%",
        grips=("factor:rsi6_lt20", "caliber:v1"),
        bases=("rsi6 超卖反弹，口径前复权",),
    )
    base.update(kw)
    return DecisionPack(**base)


def test_pack_valid():
    assert validate_pack(_pack()) == []


def test_pack_catches_position_out_of_range():
    v = validate_pack(_pack(position=1.5))
    assert any("position" in x for x in v)
    v2 = validate_pack(_pack(position=-0.1))
    assert any("position" in x for x in v2)


def test_pack_requires_grips():
    v = validate_pack(_pack(grips=()))
    assert any("grips" in x for x in v)


def test_pack_requires_ids_and_rules():
    v = validate_pack(_pack(decision_id="", strategy_id="", signal="", entry="", exit=""))
    assert len(v) == 5   # 5 个缺失字段


def test_task_valid():
    t = Task(task_id="t1", goal="诊断账户近3日表现", facet="决策面", depends_on=(), deliverable="诊断报告")
    assert validate_task(t) == []


def test_task_rejects_bad_facet_and_missing_fields():
    v = validate_task(Task(task_id="", goal="", facet="随便", depends_on=(), deliverable=""))
    assert len(v) == 4
    assert any("facet" in x for x in v)
