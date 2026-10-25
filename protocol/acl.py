"""协议注册表 · 写域隔离（ACL）。

protocol.md：每个 Agent 只写自己的状态；裁决面只读生产；评测平台只写过程配置仓。
这是「主控越权直接写生产」反模式（risks.md）的机械拦截。
"""

from __future__ import annotations

from typing import Mapping

#: 13 个 Agent + 外挂评测平台的写域（对齐 agent-roster.md 的写域列）。
WRITE_DOMAINS: Mapping[str, frozenset[str]] = {
    "commander":          frozenset({"task_plan"}),
    "orchestrator":       frozenset({"task_queue", "decision_pack"}),
    "strategist":         frozenset({"proposal"}),
    "factor_lab":         frozenset({"factor_dict"}),
    "macro_analyst":      frozenset({"macro_view"}),
    "sentinel":           frozenset({"event_stream"}),       # 只发不落库
    "backtest_judge":     frozenset({"verdict_db"}),          # 只读生产、只写判决库
    "reconciler":         frozenset({"reconcile_report"}),
    "process_evaluator":  frozenset({"process_report"}),      # 只读 trace
    "data_custodian":     frozenset({"database", "caliber_registry"}),
    "knowledge_curator":  frozenset({"knowledge_base"}),
    "capability_steward": frozenset({"tool_registry"}),
    "asset_registrar":    frozenset({"asset_db"}),
    "eval_platform":      frozenset({"process_config"}),      # 外挂评测平台：只写过程配置仓
}


def is_write_allowed(agent: str, domain: str) -> bool:
    """``agent`` 是否允许写 ``domain``。未知 agent 一律拒绝（fail-closed）。"""
    return domain in WRITE_DOMAINS.get(agent, frozenset())


def violations(agent: str, domain: str) -> list[str]:
    """返回越权描述；空 = 允许。"""
    if is_write_allowed(agent, domain):
        return []
    allowed = sorted(WRITE_DOMAINS.get(agent, ()))
    return [f"{agent} 越权写 {domain}（其写域 = {allowed}）"]
