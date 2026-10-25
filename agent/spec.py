"""Agent 清单 · 13 个 Agent 的机器可读规格（对齐 agent-roster.md + protocol.WRITE_DOMAINS）。"""

from __future__ import annotations

import dataclasses
from typing import Sequence


@dataclasses.dataclass(frozen=True)
class AgentSpec:
    """一个运行时 Agent 的规格。"""

    agent_id: str                 # 与 protocol.WRITE_DOMAINS 键一致
    name: str
    facet: str                    # 门面 / 决策面 / 裁决面 / 平台面
    model: str
    write_domains: tuple[str, ...]  # 写域（应与 protocol.WRITE_DOMAINS[agent_id] 一致）
    tools: tuple[str, ...]          # 绑定的确定性工具/包（本仓已实现）
    prompt_ref: str                 # agent-prompts.md 章节号


#: 13 个 Agent（对齐 agent-roster.md）。
AGENTS: tuple[AgentSpec, ...] = (
    AgentSpec("commander", "主控 Commander", "门面", "DeepSeek V4-Pro",
              ("task_plan",), (), "#1"),
    AgentSpec("orchestrator", "调度器 Orchestrator", "决策面", "DeepSeek V4.1-Flash",
              ("task_queue", "decision_pack"), ("decision.pack",), "#2"),
    AgentSpec("strategist", "策略师 Strategist", "决策面", "Flash 起草 · Pro 定稿",
              ("proposal",), ("decision.pack",), "#3"),
    AgentSpec("factor_lab", "因子工坊 Factor Lab", "决策面", "DeepSeek V4.1-Flash",
              ("factor_dict",), ("decision.factor",), "#4"),
    AgentSpec("macro_analyst", "大盘分析师 Macro Analyst", "决策面", "DeepSeek V4-Pro",
              ("macro_view",), ("decision.macro", "regime"), "#5"),
    AgentSpec("sentinel", "盘中哨兵 Sentinel", "决策面", "DeepSeek V4.1-Flash",
              ("event_stream",), ("decision.event",), "#6"),
    AgentSpec("backtest_judge", "回测判决官 Backtest Judge", "裁决面", "代码 + Flash",
              ("verdict_db",), ("judge",), "#7"),
    AgentSpec("reconciler", "对账官 Reconciler", "裁决面", "DeepSeek V4-Pro",
              ("reconcile_report",), ("reconcile",), "#8"),
    AgentSpec("process_evaluator", "会话评估官 Process Evaluator", "裁决面", "Pro + GLM",
              ("process_report",), ("evaluate",), "#9"),
    AgentSpec("data_custodian", "数据管家 Data Custodian", "平台面", "Flash + 代码",
              ("database", "caliber_registry"), ("custodian",), "#10"),
    AgentSpec("knowledge_curator", "知识馆长 Knowledge Curator", "平台面", "Flash + Pro + GLM",
              ("knowledge_base",), ("knowledge",), "#11"),
    AgentSpec("capability_steward", "能力管家 Capability Steward", "平台面", "DeepSeek V4.1-Flash",
              ("tool_registry",), ("capability",), "#12"),
    AgentSpec("asset_registrar", "资产登记官 Asset Registrar", "平台面", "Pro 蒸馏 + Flash",
              ("asset_db",), ("evolution",), "#13"),
)


def validate_roster(agents: Sequence[AgentSpec] = AGENTS) -> list[str]:
    """交叉校验 roster 与 protocol.WRITE_DOMAINS / decision.task.FACETS。返回违规列表。"""
    from decision.task import FACETS
    from protocol.acl import WRITE_DOMAINS

    v: list[str] = []
    ids = [a.agent_id for a in agents]
    if len(set(ids)) != len(ids):
        v.append("agent_id 重复")

    for a in agents:
        if a.facet not in FACETS:
            v.append(f"{a.agent_id} 的 facet 非法: {a.facet!r}")
        if a.agent_id not in WRITE_DOMAINS:
            v.append(f"{a.agent_id} 不在 protocol.WRITE_DOMAINS 中（ACL 缺该 Agent）")
            continue
        if set(a.write_domains) != set(WRITE_DOMAINS[a.agent_id]):
            v.append(f"{a.agent_id} 的写域与 ACL 不一致: {a.write_domains} vs {sorted(WRITE_DOMAINS[a.agent_id])}")
    return v
