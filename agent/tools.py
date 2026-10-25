"""Agent 工具目录（再包 agent：确定性核心 → LLM 可调用工具的声明式目录）。

把本仓的确定性包登记成「工具目录」：每个工具带 name / 归属 Agent / 入参 / 出参 / 实现引用。
LLM 运行时据此绑定工具；能力管家据此做契约测试（capability.contract_test）。
确定性实现本身在各包里，本模块只做**声明式登记**（不 import 实现，保持轻量、无 DB 依赖）。
"""

from __future__ import annotations

import dataclasses
from typing import Mapping, Optional, Sequence


@dataclasses.dataclass(frozen=True)
class Tool:
    """一个确定性工具的登记。"""

    name: str
    agent: str                       # 归属 agent_id（对齐 agent.spec.AGENTS）
    description: str
    inputs: Mapping[str, str]        # 入参名 → 类型/说明
    outputs: str
    impl: str                        # 确定性实现引用（包.模块.函数）


#: 工具目录（覆盖 11 个 agent 的确定性核心）。
TOOLS: tuple[Tool, ...] = (
    Tool("sync_taobao", "data_custodian", "淘宝数据同步：CSV/zip → duckDB，口径归一 + QC",
         {"download_dir": "str（本地下载目录）", "db_path": "str（目标 duckDB）",
          "dry_run": "bool=False（只预览）", "verify": "bool=True（线上验证）"},
         "SyncResult（imported/unknown_count/qc/verify/removed）",
         "custodian.sync_tool.run_sync"),
    Tool("sync_base_data", "data_custodian",
         "同步《A股交易基础数据》（交易日历/停复牌/涨跌停/ST/股票列表），按表替换",
         {"base_dir": "str（基础数据目录）", "db_path": "str（目标 duckDB）",
          "dry_run": "bool=False（只预览）"},
         "SyncResult（imported 为各表行数）",
         "custodian.sync_tool.run_base_data"),
    Tool("sync_list_data", "data_custodian",
         "同步《A股_榜单数据》（涨停池/同花顺池/龙虎榜/连板天梯），按日期替换幂等",
         {"base_dir": "str（榜单数据目录）", "db_path": "str（目标 duckDB）",
          "dry_run": "bool=False（只预览）"},
         "SyncResult（imported 为各表行数）",
         "custodian.sync_tool.run_list_data"),
    Tool("judge", "backtest_judge", "对一条决策复算真实结果（独立日超额/剔beta/封板/成本）",
         {"code": "str", "side": "str(buy/sell)", "signal_date": "date", "horizons": "tuple[int]"},
         "Outcome（ret/excess 毛净 per horizon + tradable/reason）",
         "judge.outcome.judge"),
    Tool("tag_regime", "data_custodian", "给一个决策打市场级 regime 标签（涨停家数/beta/拥挤/换手/消息面）",
         {"code": "str(B套)", "day": "date", "news_level": "str|None"},
         "dict（regime_label 5 维 + regime_ver）",
         "regime.query.tag_decision"),
    Tool("run_regime_validation", "backtest_judge", "按 regime 维度切片 879 天独立日 → 三态结论",
         {"report": "dict（baseline 报告）", "con": "duckdb 只读连接"},
         "list[dict]（dim/state/reason/buckets/n）",
         "regime.run.run_validation"),
    Tool("reconcile", "reconciler", "对账 + 结果归因（信用传播）→ 回滚信号",
         {"decision_id": "str", "excess_net": "float|None", "tstat": "float|None",
          "graph": "ProvenanceGraph"},
         "Reconciliation（verdict/blame/rollback）",
         "reconcile.reconcile.reconcile"),
    Tool("validate_pack", "strategist", "校验决策包契约（信号/进出场/仓位∈[0,1]/抓手非空）",
         {"pack": "DecisionPack"},
         "list[str]（违规列表，空=合法）",
         "decision.pack.validate_pack"),
    Tool("apply_factor_action", "factor_lab", "因子工坊 4 类动作落库（add/remove/edit/tune/reweight）",
         {"action": "dict（type/evidence_id/…）"},
         "list[str]（违规列表，空=已应用）",
         "decision.factor.FactorDict.apply"),
    Tool("triple_gate", "process_evaluator", "三重门控（增益/遗忘/安全）→ 发布/回滚",
         {"old_badcase_rate": "float", "new_badcase_rate": "float",
          "regression_pass": "bool", "violations": "list[str]"},
         "GateResult（decision=promote/rollback）",
         "evaluate.triple_gate.triple_gate"),
    Tool("retrieve_experience", "asset_registrar", "效用检索：按意图/regime 召回 + 超额重排 Top-k",
         {"triplets": "list[Triplet]", "intent": "str|None", "regime": "list[str]|None", "k": "int|None"},
         "list[Triplet]（按效用降序）",
         "evolution.retrieval.retrieve"),
    Tool("contract_test", "capability_steward", "工具/Skill 契约测试 → 晋级/回滚",
         {"tool_id": "str", "version": "str", "tool_fn": "callable", "cases": "list[ContractCase]"},
         "ContractTestResult（passed/failures/decision）",
         "capability.contract_test.run_contract_test"),
    Tool("refute_knowledge", "knowledge_curator", "知识卡证伪降级（status=refuted + 证据回落待考证）",
         {"store": "KnowledgeStore", "card_id": "str", "version": "str"},
         "KnowledgeCard（降级后）",
         "knowledge.store.KnowledgeStore.refute"),
)


def get_tool(name: str) -> Optional[Tool]:
    """按名查工具。"""
    for t in TOOLS:
        if t.name == name:
            return t
    return None


def tools_of(agent_id: str) -> tuple[Tool, ...]:
    """某 Agent 名下的全部工具。"""
    return tuple(t for t in TOOLS if t.agent == agent_id)


def list_tools() -> tuple[str, ...]:
    """全部工具名。"""
    return tuple(t.name for t in TOOLS)
