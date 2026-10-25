"""Agent 清单 · roster 与 ACL 交叉校验 单测。"""

from agent.spec import AGENTS, validate_roster


def test_roster_has_thirteen_agents():
    assert len(AGENTS) == 13


def test_roster_valid_against_acl_and_facets():
    assert validate_roster() == []


def test_roster_covers_all_facets():
    facets = {a.facet for a in AGENTS}
    assert facets == {"门面", "决策面", "裁决面", "平台面"}


def test_roster_unique_ids():
    ids = [a.agent_id for a in AGENTS]
    assert len(ids) == len(set(ids))


def test_validate_catches_drift():
    # 手工构造一个写域与 ACL 不一致的 spec，应被校验出
    from agent.spec import AgentSpec, validate_roster
    bad = AgentSpec("commander", "主控", "门面", "Pro", ("verdict_db",), (), "#1")
    errs = validate_roster([bad])
    assert any("ACL" in e or "不一致" in e for e in errs)
