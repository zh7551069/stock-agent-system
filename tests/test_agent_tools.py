"""Agent 工具目录单测。"""

from agent.spec import AGENTS
from agent.tools import TOOLS, get_tool, list_tools, tools_of


def test_tools_have_unique_names():
    names = list_tools()
    assert len(names) == len(set(names))


def test_tools_reference_valid_agents():
    agent_ids = {a.agent_id for a in AGENTS}
    for t in TOOLS:
        assert t.agent in agent_ids, f"{t.name} 归属未知 agent {t.agent}"


def test_get_tool_and_tools_of():
    assert get_tool("sync_taobao").agent == "data_custodian"
    assert get_tool("nonexistent") is None
    assert {t.name for t in tools_of("backtest_judge")} == {"judge", "run_regime_validation"}


def test_every_agent_has_a_tool():
    # 11 个 agent 里除「门面 commander / 决策 orchestrator/sentinel/macro」外都有确定性工具
    tool_agents = {t.agent for t in TOOLS}
    assert "backtest_judge" in tool_agents
    assert "reconciler" in tool_agents
    assert "data_custodian" in tool_agents
    assert "factor_lab" in tool_agents
    assert "knowledge_curator" in tool_agents
