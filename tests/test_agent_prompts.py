"""Agent 系统提示词加载单测。"""

from agent.prompts import all_prompt_ids, load_prompt
from agent.spec import AGENTS


def test_all_thirteen_agents_have_prompt():
    agent_ids = {a.agent_id for a in AGENTS}
    prompt_ids = set(all_prompt_ids())
    assert prompt_ids == agent_ids          # 13 个 agent 全有提示词，且无多余


def test_load_prompt_nonempty():
    for aid in all_prompt_ids():
        p = load_prompt(aid)
        assert p and len(p) > 20, f"{aid} 提示词为空/过短"


def test_load_prompt_unknown_none():
    assert load_prompt("nobody") is None
