# 旧系统与可复用代码资产 · 事实清单

> **重建说明**：本报告为重建版（原版在文件搬运中丢失）。
> **调研方式**：只读。全部结论来自 `find` / `ls` / `wc` / `grep` / `read` 的实际输出。
> **未执行任何测试**（按委托要求，pytest 会往工作区外写缓存）；未运行任何被调研目录内的代码。
> **未修改任何被调研目录**。
> **调研时间基准**：本机文件系统当前状态（`taobao_minute.duckdb` mtime = Oct 12 23:06）。
> **路径约定**：全部为绝对路径。行号为实际行号。
> **规模口径**：`.py` 行数一律**排除** `.venv/`、`.git/`、`__pycache__/`、`node_modules/`。

---

## 0. 一页速览

| 节 | 路径 | 形态 | py 文件 | py 行数 | 有测试 | 有 README | 有 git |
|---|---|---|---|---|---|---|---|
| A | `/Users/zenghui/Documents/quantInvest/` | AutoClaw 技能工作区（提示词 + 确定性脚本） | 23 | 3,710 | ✅ tests/ 34 例 | ❌ 无 README.md（有 初始化.md） | ❌ |
| B | `/Users/zenghui/Documents/code/TradingAgents-astock-main/` | 独立 Python 包（LangGraph 多 Agent 投研） | 121 | 20,244 | ✅ 32 文件 330 例 | ✅ 36.9 KB | ❌ |
| C | `/Users/zenghui/Documents/code/vibe-astock-main/` | 全栈应用（FastAPI + React19） | 66 | 23,677 | ✅ 1 文件 523 例 | ✅ 27.4 KB | ❌ |
| D | `/Users/zenghui/Documents/code/a-stock-data-main/` | **单个 SKILL.md 文件**（结构化 md + 内嵌 Python） | 1 | 314 | ✅ 1 文件（对 SKILL.md 内嵌代码做 exec 测试） | ✅ 28.0 KB | ❌ |
| E | `/Users/zenghui/Documents/code/alphadesk/` | 独立 Python 包（六层架构 + LangGraph） | 190 | 47,215 | ✅ 45 文件 658 例 | ✅ 7.2 KB | ⚠️ 有 `.git` 但**零 commit** |
| F1 | `/Users/zenghui/.duanxian-agents/` | 纯运行态数据（185 个 json，0 个 py） | 0 | 0 | — | — | — |
| F2 | `/Users/zenghui/.tradingagents/` | 纯运行态数据（18 文件） | 0 | 0 | — | — | — |
| G | `/Users/zenghui/.openclaw-autoclaw/` | 宿主运行目录，40 GB | 未统计（按委托只看顶层） | — | — | — | ❌（workspace 子目录有 `.git`） |

---

## A. `/Users/zenghui/Documents/quantInvest/`（旧 AutoClaw 形态）

### A.1 目录树（深度 ≤3）

```
/Users/zenghui/Documents/quantInvest/
├── AGENTS.md                 2,611 B   工作区宪法（启动流程 / 记忆分层 / 写入纪律）
├── IDENTITY.md               1,100 B   agent 身份（QuantAdvisor）
├── RULES-L0.md               4,478 B   L0 铁律 20 条（常驻注入）
├── USER.md                   1,936 B   用户画像「辉哥」+ 已确认口径
├── 初始化.md                 1,925 B   原始需求原文
├── data/
│   ├── decision_log.jsonl        0 B   L5 闭环日志（**空文件，0 行**）
│   ├── holdings.json           348 B   **holdings: [] —— 空数组**
│   ├── import_log.jsonl     21,308 B   91 行导入日志
│   └── scratch/                       工具输出卸载区（空）
├── docs/specs/
│   ├── 01-基础架构.md       11,566 B
│   ├── 02-业务架构.md       13,697 B
│   ├── 03-工作流设计.md     15,409 B
│   ├── 04-错误规避映射表.md 10,991 B
│   ├── 05-交易基础数据归档.md 6,658 B
│   └── 06-增量导入记录.md    4,454 B
├── memory/
│   ├── daily/                         **空目录**
│   └── stocks/                        **空目录**
├── scripts/
│   ├── import_delta.py         563 行  主导入器（幂等 + 逐表校验）
│   ├── import_specs.py         445 行  导入规格与列映射
│   ├── import_delisted.py      147 行  退市股 upsert
│   ├── verify_import.py        109 行  逐表行数与日期校验
│   ├── verify_memory.py        129 行
│   ├── verify_new_import.py    220 行  新导入数据专项验证
│   └── verify_online.py        133 行  线上接口抽样比价
├── skills/
│   ├── quant-advisor/
│   │   ├── SKILL.md          5,839 B   八步链路 + 铁律 + 输出模板
│   │   └── references/
│   │       ├── index.md      1,544 B   L1 战法索引
│   │       ├── signal-weights.md 2,601 B   30 信号 A/B/C/D
│   │       ├── reject-ladder.md  2,681 B   A/B/C 否决分级
│   │       ├── gate-rules.md     2,092 B   闸门七查 + 时间窗口表
│   │       ├── watchout-cases.md 3,166 B   v1.0.0 错误反例
│   │       ├── washout-end.md    1,473 B
│   │       └── data-dictionary.md 7,364 B  数据字典
│   ├── spec-gate/SKILL.md    7,036 B   工程工作流门禁（Spike/Bounded/Architectural）
│   └── memory/scripts/autoclaw-episodic-sync.sh
├── src/quant/
│   ├── config.py                70 行  路径常量收敛（唯一合法来源）
│   ├── contracts/advice.py     260 行  建议卡契约（纯数据结构 + 校验）
│   ├── data/store.py           116 行  DuckDB 只读访问 + 备份表白名单
│   ├── strategy/trading_rules.py 202 行 T+1 / 涨跌停 / 最小单位（确定性代码）
│   ├── agent/
│   │   ├── env_gate.py         205 行  启动自检（环境门禁）
│   │   ├── advice_gate.py      231 行  建议闸门（七查 + 四退出码）
│   │   ├── reject_ladder.py    133 行  否决分级校验
│   │   ├── evidence_audit.py    94 行  证据选择审计
│   │   └── decision_log.py     209 行  L5 闭环日志
│   └── (features/ **不存在**，见 A.7 断链)
└── tests/test_guards.py        444 行  34 个 test 函数
```

**注**：`.zwork/` 是运行产物目录（含 10 个 artifact 快照 + 5 个后台日志），内含一份 `test_guards.py` 副本。本报告统计**已排除** `.zwork/`。

### A.2 README / 设计文档的关键结论（逐条摘录）

**A.2.1 `RULES-L0.md`（4,478 B，硬上限 4k 字节）**

- 文件头：「本文件每次会话都会加载。**只放最高优先级、违反代价最大的铁律**。详细规则一律外置，此处只留索引。**体积超 18k 会被截断** → 会话中看不到。」
- 事实铁律：「**无数据不给结论**：取不到数据就置空并标注「未证实」，**禁止编造、禁止用默认值填充**。」
- 「**范围性结论必须先声明数据源边界**：说明「用了哪张表、覆盖到哪天、边界外还有什么没看」。**禁止用某张表的最早日期代表事情的最早日期。**」
- 「**数据缺失时 `action` 只能是 `watch`**，并说明缺什么。」
- 否决铁律：「**唯一合法否决依据（A 级）**：① 资金流反向 ② 量价结构坏 ③ 日线趋势坏（买入侧 +④ 大盘单边破位）。」「**B 级只能降级**，不得否决」「**C 级禁止作为理由**：板块不共振 / 组内最弱 / 跟风票 / 故事型独涨 / PE-PB / 破 BOLL / 日内已涨X% / 相对强度弱 / 「感觉」。」
- T+1：「**T+1（最重要，不可违）**：**当日买入的股票当日不可卖出**。……⚠️ **历史教训**：曾对当天买入的股票给出「当天卖出」建议 —— 这是不了解 T+1 制度，属无效建议。」
- 涨跌停幅度（**标注「已实测验证」**）：

  | 板别 | 幅度 | 实测家数 |
  |---|---|---|
  | 主板 | ±10% | 3046 |
  | 创业板 (300/301) / 科创板 (688) | ±20% | 2021 |
  | 北交所 (bj) | ±30% | 346 |
  | **ST / \*ST（风险警示板）** | **±5%** | 142 |

- 最小申报单位：「主板/创业板 100 股；**科创板 200 股**；北交所 100 股。减仓后剩余不得小于最小单位（否则全清）。」
- 退市整理期：「涨跌幅 ±10%，**仅可卖出**（不可买入）。」
- 「**遇阻塞必须停下问用户**，不得自行决定、将就执行、降级出具结论。」
- 「**每条建议必须落库**并登记对账；无追踪 = 任务未完成。」

**A.2.2 `AGENTS.md`（2,611 B）**

- 记忆六层：L0 铁律（`RULES-L0.md`，常驻，≤4k）/ L1 战法（`skills/quant-advisor/references/`，单文件 ≤15k）/ L2 观察（`memory/stocks/`，≤8k）/ L3 知识库（`~/Documents/baku_knowledge/`，永不整文件注入）/ L4 会话记忆（episodic-memory）/ L5 决策日志（`data/decision_log.jsonl`）。
- **实测数字（重要）**：「**为什么这样分层**：实测单文件注入上限约 20k 字节，超限被截断为头尾拼接（v1.0.0 实测：**TOOLS.md 27.4k 时只注入 19.9k，58% 内容决策时看不见** → 同一错误 24 小时内重犯）。」
- 「**不为了让校验变绿而删除或弱化测试**」
- 「**明确不做**：不自动下单、不接券商交易接口、不承诺收益、不覆盖可转债/期权/期货/两融。」

**A.2.3 `docs/specs/01-基础架构.md`（11,566 B）**

- 「**实测事实**（来自 v1.0.0 AGENTS.md 2026-09-10 固化记录）」：
  - 「单文件注入上限 ≈ **20k 字节**，超限被截断为头尾拼接」→「MEMORY.md 41.6k 时只注入 19.9k → **58% 内容决策时看不见**」
  - 「`memory/*.md` 日记**不注入**」→「**79 个日记文件**在会话中完全不可见，除非主动 read」
  - 「「规则写进文件」≠「决策时看得见」」→「这是 E-1 反复重犯 ≥6 次的直接机制」
- 核心原则：「**凡是决策时必须在场的，必须小到能常驻；凡是大的，必须按需检索而不是常驻。**靠「压缩」解决不了——压缩到 20k 以内仍是脆弱平衡，且每次新增规则都会把别的规则挤出去。**必须靠外置 + 分层 + 检索。**」
- L3 规模：「`~/Documents/baku_knowledge/` **61 个 md**（含 **1.27MB 大部头**）」
- 启动自检六项：PSSD 挂载 / 数据库可读 / 数据新鲜度 / 持仓数据 / L0 文件体积（`wc -c` < 18k 告警）/ 决策日志可写。
- 「§7 与 v2.0.0 的差异说明」表：v2.0.0 记忆方案是「「拆分 + 压缩到 12k」」，本设计改为「**外置 + 按需检索 + L0-L5 分层**」，理由「压缩仍是脆弱平衡；外置从机制上消除截断」。
- v2.0.0 的否决制被点名：「v2.0.0 自评承认会反向加剧 E-1」。

**A.2.4 `docs/specs/02-业务架构.md`（13,697 B）**

- 数据源实测表：
  - 路径 `/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb`
  - 「体积 | **124 GB / 71.2 亿行**」「表数 | **90 张**」
  - 「日线覆盖 | 2000-06-09 → 2026-09-24，6188 只，1691 万行」「分钟覆盖 | 1/5/15/30/60 min（1min **54.2 亿行**）」
- 已知数据风险：中文列名混杂（`lhb_daily` 列为「交易日期/股票代码」）/ 库在外置盘 / 路径含空格与中文 / **备份表混入 `bak_*` 表 20+ 张** / 数据新鲜度。
- 数据质量四道闸门：① 完整性（如全市场 ≥5000）阻塞 ② 一致性 告警 ③ 时点正确性（as-of）阻塞 ④ 边界声明 阻塞。
- 信号体系：
  - 「A 级（≥80，×1.0）: S16 旭日东升(91.3) / X10 高位换手(88.4) / S12 曙光初现(81.9)」
  - 「B 级（60-79，×0.7）: S13 启明星 / S18 星星相应 / S11 看涨吞没 / S10 底部长红K」
  - 「C 级（40-59，×0.3）: **17 个**」
  - 「D 级（<40，弃用）: 反向警示（X07 放量滞涨 → 出现即关注而非卖出）」
  - 「v1.0.0 的教训是「教科书结论被数据证伪」（「断头铡刀」实测无效、「放量滞涨」实测是洗盘）」
- 粗筛规模：「全市场 **5567 只**」→「候选池（50-200 只）」→「决策候选（≤10 只）」
- 建议卡字段级硬规则（原文）：`upside.reasons`/`downside.reasons` 各 ≥3 条；`signal_audit.against_conclusion` 为空 → 告警；`reject_levels.used_C` 非空 → 闸门 `exit_code=2`；`action=hold/reduce/watch` 必须给主动条件单；`gate.exit_code` 必须 0 才可交付；数据缺失时 `action` 只能是 `watch`。
- 九方智投战法 16 篇；实战纪律手册「自带 **4770 日 + 453 信号** 实证」。

**A.2.5 `docs/specs/03-工作流设计.md`（15,409 B）**

- 八步强制链路：0 环境自检 → 1 事实预检 → 2 数据源边界声明 → 3 证据收集（六类）→ 4 证据选择审计 → 5 否决分级校验 → 6 双向输出组装 → 7 闸门校验（七查）→ 8 交付 + 闭环。
- 阻塞清单 B-1~B-9；**用户强约束原文**：「遇到在每一步执行中，充分评估当前过程产生的结论、数据、可依赖的环境等是否具备足够条件进入下一步，遇到网络阻塞、数据不全时，必须寻求我的确认后再实施下一步，不要自己做决定。」
- 周报第 2 项：「★ **拦截错误率单列**（v1.0.0 的 **2/3 拦错率**是核心病灶）」
- §7 回测工作流：「统计口径输出（**多口径并列，不选最好看的**）：口径A 次日收盘 vs 信号日收盘 / 口径B 次日收盘 vs 次日开盘 / 口径C 含成本 vs 不含成本 / 分市场状态（牛/熊/震荡）」；「★ 标注样本区间、样本量、是否含成本（**禁止孤立报「年化 X%」**）」

**A.2.6 `docs/specs/04-错误规避映射表.md`（10,991 B）**

- 依据：「`v1.0.0` 审计（**166 条建议 / 151 条错误 / 6 组并行审计**）+ `v2.0.0` 自评报告的 9 个缺口」
- 覆盖度总表：A 类 51 条 / B 类 17 / C 类 34 / D 类 32 / E 类 17 = **合计 151**；本版完全覆盖 **97 (64%)**、部分 38 (25%)、不覆盖 16 (11%)。
- 「对比 v2.0.0 自评：**完全拦截 39% → 本版设计目标 64%**；含部分 73% → **89%**。」
- 「**诚实声明**：这是**设计覆盖率（机制是否存在）**，不是「实现后必然不发生」。」
- 四条根因：A 否决制无分级（E-1 重复 ≥6 次）/ B 规则加载不全（TOOLS.md 仅加载 **42%**，20k 截断）/ C 无闭环（**31% 建议无追踪**）/ D 证据选择审计缺失。
- D 类实测事故：「E-11 相关 | **无上界 DELETE 丢 233 万行** | 禁止无 WHERE 的 DELETE/UPDATE」「E-11 相关 | **整表替换删 1187 万行** | 写操作白名单 + 备份表只读」
- 「表数误报 | 表清单以 `SHOW TABLES` 实查为准」
- §9「反向加剧风险的消除」：v2.0.0「否决制做强但无双向输出 → 加剧 E-1」「「不操作合法」缺对称约束 → 加剧 E-7/E-14」。
- §10 明确不承诺：判断质量本身 / 复杂情境推理 / 全部 D 类脚本错误 / 「**胜率 ≥80% 的达成 | 本版只负责测出真实基线**」/ 自动下单。

**A.2.7 `docs/specs/05-交易基础数据归档.md`（6,658 B）**

- 触发原因：「用户指出「当天买入却建议当天卖出」的 T+1 违反错误」
- 外部数据源实测：`/Volumes/My PSSD/downlodData/taodaoDataUpdate/A股交易基础数据`（实测 **5.6GB**）
  - 交易日历.csv：1990-12-19 ~ 2026-12-31，**13,162 行**
  - 股票列表.csv：**5,534 只**
  - 涨跌停价格_每日更新/：**2007-01 ~ 2026-09（237 个月）**，每日 ~5,600 行
  - 停复牌_每日更新/：**2003-03 ~ 2026-09（283 个月）**
  - ST股票列表_每日更新/：2016-01 ~ 2026-09，每日 ~250 行
- 核心判断原文：「**我们把「交易规则」和「交易数据」混在一起管理了。**」「**v1.0.0 的错在哪**：T+1 这类**永不改变的铁律**，当时写在日记文件里（`memory/2026-08-25.md`），而日记**不注入会话**——等于没写。……**把不变的规则放进会变的存储里，必然忘记。**」
- §4「为什么不能把规则写成数据」：数据可缺失 / 数据可冲突 / 性能与可靠。「**规则**（制度事实）→ 常驻 L0，无条件生效；**数据**（逐日事实）→ 查询，缺失时**阻塞**（不给建议），而不是降级」
- §5 本轮修正的具体缺陷：「`advice_gate.py` | `tradability_ok` 由上游传入，**闸门本身不校验 T+1**」「契约层 | 无 `buy_date` / `sellable_shares` 字段」「**根因**：T+1 只作为「规则文本」存在，没有变成「代码校验」。**规则不落到代码上，等于没落。**」

**A.2.8 `docs/specs/06-增量导入记录.md`（4,454 B）**

- 数据源 `/Volumes/My PSSD/downlodData/taodaoDataUpdate`（**13GB，已删除释放**）
- 「导入结果（**21 张表**）」；逐表行数示例：minute_1min 3,829,866 / limit_price 11,213 / **stock_info 5,908（其中退市 339）**
- 「修复的 5 类缺陷」第 1 条：「**深市指数分片与个股撞码**（最严重）—— 分片 `(2)` 用**纯 6 位数字**命名，加前缀后与平安银行 sz000001 撞车 → 后果：**18,557 组重复行**，指数值（3925.32）混入股票分钟表」
- 第 5 条：「库内 `stock_info` 退市股 = **0**，而源有 **339 只**（1999-2026）…… 只用在市股票池会**系统性高估收益**」
- 验证结果：「价格交叉验证 | 5 只标的（跨四板）**全字段 0 偏差**」「资金流口径 | 已查清为定义差异（**主力口径 7,132 vs 东财 7,227 万，差 1.3%**）」

**A.2.9 `skills/quant-advisor/references/watchout-cases.md`（3,166 B）— 核心数字对照基线**

| 指标 | v1.0.0 实测 | 本版目标 |
|---|---|---|
| 建议总数 | 166 | — |
| 错误数 | 151 | — |
| **无追踪率** | **31%（52/166）** | ≤5% |
| 决策日志对账率 | **22%（6/27）** | ≥90% |
| C 级标签否决 | **6 次/单日** | **0** |
| 单边输出 | 反复 | **0** |
| 拦截错误率 | **2/3 拦错** | 0（拦截须附 A 级证据） |
| 有结果样本胜率 | **57%** | 先测基线再定目标 |

E-1 事故明细（原文表格）：9/11 一天内用禁用标签否决 6 次 —— 减仓亨通光电（「光纤组内最弱」）/ 减仓山东玻纤（「跟风票」）/ 减仓中兵红箭（「故事型独涨非资金认可型」）/ 卖山东玻纤（「板块不共振」）/ 减仓亨通光电（「组内最弱」）/ 卖亨通光电（「它最弱」）。**事后：山东玻纤 +4.05%、亨通 +1.02%**。

### A.3 代码规模

| 项 | 值 |
|---|---|
| `.py` 文件数（排除 `.zwork/ .venv/ .git/ __pycache__/`） | **23** |
| `.py` 总行数（同口径） | **3,710** |
| `.py` 文件数（**含** `.zwork/` artifact 副本） | 24 |
| `.py` 总行数（含 `.zwork/`） | 4,152 |
| `.md` 文件数 / 总字节（排除 `.zwork/`） | 21 / 111,898 B |
| 全仓文件数（排除 `.zwork/ __pycache__`） | 48 |
| 依赖清单（requirements.txt / pyproject.toml） | **不存在** |

单文件行数 Top 5：`scripts/import_delta.py` 563 / `scripts/import_specs.py` 445 / `tests/test_guards.py` 444 / `src/quant/contracts/advice.py` 260 / `src/quant/agent/advice_gate.py` 231。

### A.4 是否可运行

- **有运行痕迹**：`src/quant/`、`scripts/`、`tests/` 下均存在 `__pycache__/*.cpython-314.pyc` → 曾用 **Python 3.14** 实际执行过。
- **解释器**：`AGENTS.md:7-8` 指定 `/opt/homebrew/opt/python@3.14/bin/python3.14 src/quant/agent/env_gate.py`，并注明「系统 python3.9 **无 duckdb 模块**」。实测该路径**存在**（`/opt/homebrew/opt/python@3.14/bin/python3.14`）。
- **数据盘**：`/Volumes/My PSSD` **当前已挂载**。
- **入口**：`src/quant/agent/env_gate.py`（启动自检）、`advice_gate.py`、`decision_log.py append|reconcile|report`。
- **无依赖清单**：仓库内没有 `requirements.txt` / `pyproject.toml` / `package.json`，依赖只能从 `AGENTS.md` 与 `data-dictionary.md` 的说明推断。
- **未运行验证**（按委托要求）。

### A.5 测试是否存在

- 目录：`/Users/zenghui/Documents/quantInvest/tests/`
- 唯一文件：`/Users/zenghui/Documents/quantInvest/tests/test_guards.py`（444 行）
- **test 函数数量：34**（`grep -c '^def test'`）
- 覆盖范围（从函数名读出）：双向输出必填、hold 需主动条件单、C 级否决拦截（含 variants）、A 级允许、B 级不得否决、闸门违规退出码、粗筛过滤守卫、选择性引用检测、编造信号检测、篡改检测、信号去重、缺数据强制 watch、无 SSD 阻断方向性动作、14:45 后禁新建仓、午休、禁用表述、时间型条件需 duration、决策日志往返、周报分错误类、中文列名翻译、备份表禁止、边界声明渲染、env_gate L0 体积、env_gate 无 SSD 阻断、T+1 同日卖出拦截、T+1 部分可卖、板别涨跌停、科创板 200 股最小单位、停牌不可交易、退市整理期仅可卖、涨跌停边界、闸门端到端拦同日卖出、可交易性未知时闸门阻断。
- **未运行**（按委托要求）。

### A.6 可复用组件清单（绝对路径 + 一句话用途）

**确定性代码（可直接搬，零外部服务依赖）**

| 绝对路径 | 行数 | 用途 |
|---|---|---|
| `/Users/zenghui/Documents/quantInvest/src/quant/contracts/advice.py` | 260 | **建议卡契约**：`AdviceCard` / `Side` / `Evidence` / `Action` / `Confidence` / `RejectLevel` / `GateExit(0/1/2/3)` / `BlockKind`；纯数据结构 + 校验，可独立单测 |
| `/Users/zenghui/Documents/quantInvest/src/quant/agent/advice_gate.py` | 231 | **风控闸门**：`run_gate()` 七查 + 退出码 0/1/2/3；`WINDOWS` 时间窗口表（11 段）；`NO_NEW_POSITION_WINDOWS`；`COMPLIANCE_FORBIDDEN` 合规禁用表述正则 |
| `/Users/zenghui/Documents/quantInvest/src/quant/strategy/trading_rules.py` | 202 | **A 股制度规则（纯代码）**：`classify_board()` / `limit_pct_of()` / `min_lot_of()` / `check_t_plus_1()` / `check_min_lot()` / `check_limit_price()` / `check_tradable()`；`ST_LIMIT_PCT=5.0`、`DELISTING_LIMIT_PCT=10.0` |
| `/Users/zenghui/Documents/quantInvest/src/quant/agent/reject_ladder.py` | 133 | **否决分级校验**：`classify_reject()` / `check_reject_ladder()` / `guard_screen_filters()`；A/B/C 三级清单写进代码，命中 C 级即判违规 |
| `/Users/zenghui/Documents/quantInvest/src/quant/agent/evidence_audit.py` | 94 | **证据选择审计**：`SignalBox` / `audit_evidence_selection()` / `assert_no_model_tampering()`（防确认偏误 + 防模型删改信号） |
| `/Users/zenghui/Documents/quantInvest/src/quant/agent/decision_log.py` | 209 | **决策闭环日志**：`DecisionRecord` / `append()` / `reconcile()` / `weekly_report()`（分类统计方向/时机/拦截错误） |
| `/Users/zenghui/Documents/quantInvest/src/quant/agent/env_gate.py` | 205 | **启动自检 / 环境门禁**：`check_ssd` / `check_duckdb` / `check_freshness` / `check_holdings` / `check_inject_sizes` / `check_decision_log_writable` / `run_env_gate` |
| `/Users/zenghui/Documents/quantInvest/src/quant/data/store.py` | 116 | **数据访问层**：`connect(read_only=True)` / `guard_table()`（`FORBIDDEN_PREFIXES = ("bak_", "rebuild_bak_")`）/ `translate_columns()` / `boundary_of()` → `BoundaryDeclaration` |
| `/Users/zenghui/Documents/quantInvest/src/quant/config.py` | 70 | **路径常量收敛**：`DUCKDB_PATH` / `DATA_VOLUME` / `KNOWLEDGE_BASE` / `INJECT_SOFT_LIMIT=18_000` / `INJECT_HARD_LIMIT=20_000`；含空格的 PSSD 路径只在此处出现 |

**数据源连接器（导入器）**

| 绝对路径 | 行数 | 用途 |
|---|---|---|
| `/Users/zenghui/Documents/quantInvest/scripts/import_delta.py` | 563 | 主导入器：幂等（先 DELETE 目标日期区间 → INSERT → 立即校验行数）+ 逐表校验 |
| `/Users/zenghui/Documents/quantInvest/scripts/import_specs.py` | 445 | 21+ 条导入规格 + 源→目标列名映射（ALIASES 别名机制） |
| `/Users/zenghui/Documents/quantInvest/scripts/import_delisted.py` | 147 | 退市股 / 股票列表按 `ts_code` upsert（**修「退市股 0 只」→ 339 只**，防幸存者偏差） |
| `/Users/zenghui/Documents/quantInvest/scripts/verify_import.py` | 109 | 逐表行数 + 最新日期校验 |
| `/Users/zenghui/Documents/quantInvest/scripts/verify_new_import.py` | 220 | 新导入数据专项（涨跌停一致性 / 分钟自洽性 / 资金流口径 / 线上比价） |
| `/Users/zenghui/Documents/quantInvest/scripts/verify_online.py` | 133 | 与线上接口抽样比价（含东财 secid 拼装） |

**提示词 / 方法论资产（markdown，可直接进新架构）**

| 绝对路径 | 字节 | 用途 |
|---|---|---|
| `/Users/zenghui/Documents/quantInvest/RULES-L0.md` | 4,478 | L0 铁律 20 条（T+1 / 涨跌停实测家数 / 最小单位 / 交易时段 / 双向输出 / 否决分级） |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/signal-weights.md` | 2,601 | **30 信号 A/B/C/D 权重表**（738 万事件回测 + 10 日胜率/收益/超额 pp） |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/reject-ladder.md` | 2,681 | A/B/C 否决分级完整规则 + C 级标签清单 |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/gate-rules.md` | 2,092 | 闸门七查表 + A 股日内时间窗口表（11 段 + 允许动作） |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/watchout-cases.md` | 3,166 | v1.0.0 全部错误模式与反例 + 核心数字对照基线表 |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/data-dictionary.md` | 7,364 | 数据字典：高频表 / 中文列名表 / 特色表 / 已知缺口 / 口径要点 |
| `/Users/zenghui/Documents/quantInvest/docs/specs/01~06*.md` | 62,775 合计 | 六份设计文档（基础架构 / 业务架构 / 工作流 / 错误映射 / 数据归档 / 增量导入） |
| `/Users/zenghui/Documents/quantInvest/skills/spec-gate/SKILL.md` | 7,036 | **验证方法论**：Spike/Bounded/Architectural 三分类 + 达标才开工门禁 + 棘轮规则（只升不降） |

**signal-weights.md 关键数字（原文摘录）**：来源「`~/Documents/baku_knowledge/知识库量化验证体系-30信号权重.md`（2026-08-20）」；「回测基础：本地 duckDB 全历史，**738 万事件 / 30 信号全市场**」；口径「五维评分（样本量20 + 胜率偏移25 + 盈亏比20 + 显著性15 + 情境稳健20）」。

| ID | 信号 | 置信 | 10日胜率 | 10日收益 | 超额 pp |
|---|---|---|---|---|---|
| S16 | 旭日东升 | 91.3 | 60.3% | +3.73% | +2.16（全正） |
| X10 | 高位换手>20%（天量天价）| 88.4 | 67.9%下跌 | -4.33% | -3.91（全负） |
| S12 | 曙光初现 | 81.9 | 56.4% | +1.80% | +0.69（全正） |
| X07 | 放量滞涨 | **32.9** | — | 120日 **+10.27%** | **+3.67** —— 🔴 **反向警示**：「「出货」是假象，更像洗盘吸筹，出现→**关注而非卖出**」 |
| X06 | 断头铡刀 | 38.2 | — | 120日 **+4.99%** | 「彻底无效」 |

- 「⚠️ S10 由 A 降级：超额 -1.91 三情境全负 = **牛市 beta 虚高**，非真实 alpha。」
- 使用纪律第 4 条：「**恐慌日降级**：T-1 大盘跌 >2% 时，当天命中的底部信号降级使用，需次日缩量企稳确认（实证：**8/19 恐慌日 A 级信号次日 100% 失败，n=5，均值 -5.15%**）。」

### A.7 被明确否定的设计（原文摘录 + 出处）

1. **不做交易执行** —「**不自动下单、不接券商交易接口、不承诺收益、不覆盖可转债/期权/期货/两融。**」
   出处：`/Users/zenghui/Documents/quantInvest/AGENTS.md:48`

2. **否决制（无分级）被否** —「v1.0.0 的实际决策逻辑是「遇到一条不满足 → 默认不买 → 完」。但 A 股强势股的特征**恰恰是突破各种体系边界**——**否决制 = 系统性错过强势股**。实证：9/11 一天内用 6 次禁用标签否决（亨通/山东玻纤/中兵红箭），事后山东玻纤 +4.05%、亨通 +1.02%。而「禁用标签清单」当时已白纸黑字写在 TOOLS.md 里。**根因不是不知道，是决策时那段规则不在眼前。**」
   出处：`/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/reject-ladder.md:8-14`

3. **「压缩上下文」方案被否** —「靠「压缩」解决不了——压缩到 20k 以内仍是脆弱平衡，且每次新增规则都会把别的规则挤出去。**必须靠外置 + 分层 + 检索。**」
   出处：`/Users/zenghui/Documents/quantInvest/docs/specs/01-基础架构.md:30`（v2.0.0 的「拆分 + 压缩到 12k」方案被点名否定，见同文件 §7 表）

4. **「把规则写成数据」被否** —「一个自然但错误的想法是：「既然有逐日涨跌停数据，那 T+1 也可以通过查数据判断」。**这会失败**，因为：1. **数据可缺失**…… 2. **数据可冲突**…… 3. **性能与可靠**——每次决策都连库查制度规则，把「必然成立」降级为「依赖查询成功」」
   出处：`/Users/zenghui/Documents/quantInvest/docs/specs/05-交易基础数据归档.md:85-96`

5. **用无关指标否决资金验证通过的机会（E-1）被定为最贵错误** —「🥇 E-1：用无关指标否决资金验证通过的机会（**重复 ≥6 次**）**最贵的错误**。」
   出处：`/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/watchout-cases.md:6-8`

6. **C 级标签清单（明确禁止作为理由）** —「板块不共振 / 板块没共振（最常见复发项）｜组内最弱 / 板块内最弱（**9/11 用了 3 次**）｜跟风票｜故事型独涨（9/11 用了 1 次）｜PE / PB / 估值高｜破 BOLL 上轨｜日内已涨 X%｜相对强度弱｜「感觉」/ 直觉 / 心里没底」
   出处：`/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/reject-ladder.md:37-47`

7. **无上界 DELETE / 整表替换被禁** —「9/22 丢 **233 万行**、9/23 删 **1187 万行** —— 无上界 DELETE / 整表替换。**教训**：禁止无 WHERE 的 DELETE/UPDATE；备份表只读。」
   出处：`/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/watchout-cases.md:49-52`；同 `docs/specs/04-错误规避映射表.md:103-104`

8. **用事后择优 / 未来函数当实盘预期（E-8，≥4 次）被否** —「回测必须多口径并报，**不许挑最好看的那个**。」
   出处：`/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/watchout-cases.md:34-37`

9. **不做胜率承诺** —「**胜率 ≥80% 的达成** | **本版只负责测出真实基线**，80% 是否可达由基线数据决定」
   出处：`/Users/zenghui/Documents/quantInvest/docs/specs/04-错误规避映射表.md:166`；另 `USER.md:36`「胜率目标 | **先测基线再定目标**（80% 是长期追求，不预设）」

10. **v2.0.0 两处「反向加剧」设计被要求消除** —「**否决制做强但无双向输出 → 加剧 E-1** | 建议卡只有单一 `action` | `upside` 与 `downside` **均为必填**，任一为空校验失败」；「**「不操作合法」缺对称约束 → 加剧 E-7/E-14** | 「不买」可以是单边结论 | **给「不买」必须给「什么条件买」**」
    出处：`/Users/zenghui/Documents/quantInvest/docs/specs/04-错误规避映射表.md:146-151`

**实测数字附列**：`data/decision_log.jsonl` **0 行**（闭环日志是空的）；`data/holdings.json` 的 `holdings` 为 **空数组 `[]`**（虽已按 05 号文档补了 `buy_date` / `sellable` 字段说明）；`memory/daily/`、`memory/stocks/`、`data/scratch/` 均为**空目录**。
→ 即：**A 的代码骨架与规则体系完成度高，但从未真正跑过一次完整决策闭环**。

### A.8 A 的断链清单（设计文档指向但文件不存在）

| 被引用的路径 | 引用处 | 实际状态 |
|---|---|---|
| `skills/quant-advisor/references/youzi-playbook.md` | `references/index.md:11`、`RULES-L0.md:66`、`SKILL.md:106` | **不存在** |
| `skills/quant-advisor/references/intraday-t-sop.md` | `references/index.md:12`、`RULES-L0.md:67` | **不存在** |
| `skills/quant-advisor/references/jiufang/index.md` | `references/index.md:13`、`RULES-L0.md:68`、`docs/specs/03:245` | **不存在** |
| `skills/quant-advisor/scripts/env_gate.py` | `docs/specs/01:149-152`、`docs/specs/03:251-253` | **不存在**（实际在 `src/quant/agent/env_gate.py`） |
| `scripts/coverage_audit.py` | `docs/specs/04:184` | **不存在** |
| `src/quant/data/schema_map.py` | `docs/specs/02:64`（列名映射层） | **不存在**（实际在 `src/quant/data/store.py::COLUMN_ALIASES`） |
| `src/quant/features/` | `docs/specs/01:157`（特征层） | **不存在** |
| `memory/decisions/` | `docs/specs/01:163` | **不存在** |

另：`docs/specs/05:124` 断言「L0 总量 **8.9k** < 12k 预算」，但 `RULES-L0.md` 实际 **4,478 B**，且 `AGENTS.md:16` 写的是「≤4k」——**三处预算数字互不一致（8.9k / 12k / 4k）**。

---

## B. `/Users/zenghui/Documents/code/TradingAgents-astock-main/`

### B.1 目录树（深度 ≤3，排除 `.git/ __pycache__/ node_modules/ .venv/`）

```
/Users/zenghui/Documents/code/TradingAgents-astock-main/
├── main.py                   1,189 B   最小可运行示例（README 快速开始第 3 步）
├── main.py.bak               1,230 B
├── cli/                      入口包
│   ├── main.py              55,531 B   CLI 主体（Typer）
│   ├── utils.py             13,626 B
│   ├── announcements.py      1,507 B
│   ├── stats_handler.py      2,373 B
│   ├── config.py / models.py
│   └── static/welcome.txt
├── web/                      Streamlit Web UI（app.py / components / history.py / launch.py / pdf_export.py / progress.py / runner.py / stock_display.py）
├── tradingagents/            **核心包（10,093 行）**
│   ├── default_config.py
│   ├── performance.py          334 行  决策绩效统计
│   ├── dataflows/            数据层
│   │   ├── a_stock.py        2,463 行  **A 股数据 vendor（单文件最大）**
│   │   ├── interface.py        229 行  route_to_vendor() dispatch
│   │   ├── stockstats_utils.py 133 行  yf_retry 指数退避
│   │   ├── y_finance.py / yfinance_news.py   上游保留（美股）
│   │   └── alpha_vantage*.py                 上游保留（美股）
│   ├── agents/
│   │   ├── analysts/         market / social_media / news / fundamentals / policy / hot_money_tracker / lockup_watcher（**7 个**）
│   │   ├── researchers/      bull_researcher / bear_researcher
│   │   ├── risk_mgmt/        aggressive / conservative / neutral_debator
│   │   ├── managers/         research_manager / portfolio_manager
│   │   ├── trader/trader.py
│   │   ├── quality_gate.py    168 行  **质检闸门**
│   │   ├── schemas.py         211 行  结构化输出契约
│   │   └── utils/            agent_states / agent_utils / core_stock_tools / fundamental_data_tools / news_data_tools / signal_data_tools / technical_indicators_tools / memory.py(300 行) / rating.py(129 行) / structured.py
│   ├── graph/                trading_graph.py(756 行) / setup.py(225) / conditional_logic.py / propagation.py / reflection.py / signal_processing.py / checkpointer.py
│   └── llm_clients/          base / factory / openai / anthropic / google / azure / claude_agent_sdk(580 行) / capabilities / model_catalog / validators
├── tests/                    **32 个 .py（31 个 test_* + conftest）**
├── test.py / test_astock.py / test_data_quality.py   顶层裸测试
├── issues/                   001~005 共 5 份 issue 复盘 md
├── scripts/smoke_structured_output.py
├── examples/run_cases.py
├── pyproject.toml            3,353 B
├── README.md 36,891 B / README_en.md 37,322 B / CHANGELOG.md 88,006 B
├── CLAUDE.md 10,975 B / DEV_LOG.md 32,954 B / CHANGES_FROM_UPSTREAM.md 21,544 B
├── Dockerfile / docker-compose.yml / .env / .env.example / .streamlit/config.toml
├── assets/（11 png）  requirements.txt（内容仅 `.`）
└── .venv/
```

### B.2 README / 设计文档的关键结论（逐条摘录）

**B.2.1 `README.md`**

- 定位：「基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)（**65K ⭐**）的 A 股深度特化 fork」「全 Apache 2.0 开源 · pip install 即跑 · **零外部服务依赖**」
- 免责：「⚠️ 本项目是 TradingAgents 论文框架的工程实现与研究复现，面向研究与教学。**不构成任何投资建议，也不提供任何投资服务。**」
- 核心改造表（原文）：

  | 维度 | 原版 | 本 Fork |
  |---|---|---|
  | **Analyst 角色** | 4 个（市场/情绪/新闻/基本面） | **7 个**（+政策分析师/游资追踪/解禁监控） |
  | **交易规则** | 美股（T+0、无涨跌停） | A 股（T+1、涨跌停、最小手数、交易时段） |
  | **Alpha 基准** | SPY | **沪深 300（CSI 300）** |

- 架构四层：7 Analyst 研报生成 → Bull vs Bear 投研辩论（最多 N 轮）→ Research Manager 综合研判（深度思考 LLM）→ 三方风险辩论 + Portfolio Manager。

**B.2.2 `CLAUDE.md`（10,975 B）— 最有信息量的运维级结论**

- 版本纪律：「**当前版本**: 0.5.17（2026-09-05 发布）⚠️ 改版本号时**三处要一起改**：`pyproject.toml` / `CHANGELOG.md` / 这一行。漏了这行会让后续 agent 和发版流程读到旧版本（`tests/test_version_consistency.py` 会拦）。」
- **东财防封（v0.2.11 新增，移植自 a-stock-data v3.2）**：「`a_stock.py` 里所有指向 `eastmoney.com` 的请求（push2 / push2his / datacenter-web / search-api / np-weblist **共 7 个调用点**）统一走节流入口 `_em_get()`：模块级时间戳串行限流（默认间隔 `EM_MIN_INTERVAL=1.0s`，可用同名环境变量覆盖）+ 0.1~0.5s 随机抖动 + 复用 `requests.Session`（Keep-Alive）+ 默认 UA。……**仅东财限流**——mootdx(TCP) / 腾讯 / 新浪 / 同花顺 / 财联社 / 百度 等非东财源不受影响。批量场景可设 `EM_MIN_INTERVAL=1.5~2` 进一步降速。**新增东财端点时务必走 `_em_get` 而非裸 `requests.get`。**」
- **未来函数防护（v0.5.1）**：「历史日期上跑分析时，数据层**不得**把"今天"的数据当成分析日当天的事实——报告里完全看不出来，属于**静默失败**。」工具：`_is_historical(curr_date)` / `_snapshot_notice()`。「**新增任何收 `curr_date` 的接口，必须处理这两种情况之一，不能收了不用。**」
- **非 A 股代码防护（v0.5.3 / v0.5.5）**：「mootdx/腾讯/东财对不存在的代码常返回空值或**僵尸报价**而非报错，绕过就等于让模型拿别的市场的数据写报告。」
- **测试基线**：「干净 clone（`pip install -e .` 不带 `[agentsdk]`）跑 `pytest tests/` 应当是 **361 passed / 13 skipped / 0 failed**。出现 failed 就是真回归。」

**B.2.3 `DEV_LOG.md`（32,954 B）— 决策与选型记录（关键）**

- Fork 点 `7e9e7b8`，Fork 时间 2026-05-04，上游 Apache 2.0。
- 「**决策二:数据层用 EP11 的 a-stock-data 组合,不用 Tushare** —— **Why**:Tushare 核心接口要 **2000 积分**,免费数据残废;AKShare 高频调用易封 IP。」
- 「**决策三:不引入 MongoDB/Redis** —— CN 版的 git log 反复出现"MongoDB 迁移脚本""数据库隔离"等 fix,数据库依赖是累赘。我们要的是 `pip install + python main.py` 直接能跑。」
- 「**决策一:在原版上 fork,不在 CN 版上 fork** —— CN 版的 `app/` (FastAPI) + `frontend/` (Vue) 是商业闭源。」
- 「决策四:A 股特化角色是核心差异化」「决策五:T+1 / 涨跌停 / ST / 停牌等交易制度,在风控管理器层落地」

**B.2.4 `issues/`（5 份，一份一复盘）**

- `001-mootdx-missing-dependency.md`：「mootdx 锁死 httpx==0.25.2，与 langchain-google-genai 要求的 httpx>=0.28.1 冲突。」
- `002-chinese-ticker-crash.md`：「**复现人数 5+**」「`safe_ticker_component` 只允许 ASCII 字符……当 LLM 在 tool call 中返回中文股票名（如"福晶科技"）而不是 6 位代码时，直接报 ValueError。deepseek-v4-flash 等模型尤其容易触发，同一次分析中 news_analyst 正常但 policy_analyst 报错，说明**模型不一定每次都遵守工具描述中的格式要求**。」
- `005-docker-volume-permission.md`：Docker 命名卷权限真 bug（未预建目录 → 卷根 root:root → appuser 写入被拒）；「解析链路 `resolve_ticker()` → `_build_name_code_map()` → mootdx `client.stocks()`。实测 **0.11.7** 下 `stocks()` 正常返回 **2.7 万条**，非版本问题」

### B.3 代码规模

| 项 | 值 |
|---|---|
| `.py` 文件数（排除 `.venv/ .git/ __pycache__/`） | **121** |
| `.py` 总行数（同口径） | **20,244** |
| 其中 `tradingagents/` 包 | **10,093 行** |
| 其中 `cli/main.py` 单文件 | 55,531 B |
| 单文件最大 | `tradingagents/dataflows/a_stock.py` **2,463 行** |
| `.md` 文件数 / 总字节 | 12 / **233,494 B** |
| 其他 | 11 png / 7 txt / 2 toml / 2 example / 1 yml |
| `.git` | **不存在** |

### B.4 是否可运行

- **入口**：`main.py`（最小示例，`uv run python main.py <code> <date>`）；`cli/main.py`（Typer console command，注册于 `pyproject.toml [project.scripts]`）；`web/`（Streamlit）。
- **依赖清单完整**：`pyproject.toml` 有完整 `dependencies`（langchain-core / langgraph / langgraph-checkpoint-sqlite / pandas / mootdx>=0.11.7 / streamlit / fpdf2 等）；`requirements.txt` 内容只有 `.`（转 pyproject）。
- **运行环境**：`.venv` 目录存在；`.env` 存在（53 B）。
- **API key**：`.env.example` 约定（README 第 2 步）。
- **框架**：LangGraph + LangChain；`llm_clients/` 支持 OpenAI / Anthropic / Google / Azure / Claude Agent SDK / DeepSeek。
- **明确写明的依赖冲突**（`CLAUDE.md`）：「mootdx 钉死 `httpx>=0.25,<0.26`，与 langchain-google-genai 所需的 `httpx>=0.28.1` **结构性冲突**（该区间内每个 google-genai 版本都要 0.28.1，**无解**）。」
- **未运行验证**（按委托要求）。

### B.5 测试是否存在

- 目录：`/Users/zenghui/Documents/code/TradingAgents-astock-main/tests/`
- **32 个 `.py`**（`conftest.py` + 31 个 `test_*.py`），另有顶层 `test.py` / `test_astock.py` / `test_data_quality.py`
- **test 函数数量：330**（`grep -rho 'def test_'`，含顶层 3 个文件）
- `CLAUDE.md` 声称基线 **361 passed / 13 skipped / 0 failed**（差值来自 parametrize）
- 测试文件清单（31 个）：`test_agent_sdk_provider` / `test_astock_sina_supplement` / `test_capabilities` / `test_checkpoint_resume` / `test_cli_default_command` / `test_deepseek_reasoning` / `test_google_api_key` / `test_llm_config_persistence` / `test_lookahead_guard` / `test_market_guard` / `test_market_lookback` / `test_market_prefix_routing` / `test_memory_log` / `test_model_validation` / `test_mootdx_server_selection` / `test_news_data_tools` / `test_openai_compatible_provider` / `test_output_token_limit` / `test_partial_config` / `test_pdf_export` / `test_performance` / `test_progress_pause` / `test_role_llms` / `test_safe_ticker_component` / `test_sentiment_data_tools` / `test_signal_processing` / `test_stock_display` / `test_structured_agents` / `test_ticker_symbol_handling` / `test_version_consistency` / `test_web_history`
- **未运行**（按委托要求）。

### B.6 可复用组件清单（绝对路径 + 一句话用途）

| 绝对路径 | 行数 | 用途 |
|---|---|---|
| `/Users/zenghui/Documents/code/TradingAgents-astock-main/tradingagents/dataflows/a_stock.py` | **2,463** | **数据源连接器总入口**：`_get_prefix()`（板块前缀路由，含 920xxx 北交所修复）/ `_reject_non_a_share()` / `_normalize_ticker()` / `resolve_ticker()`（中文名→代码）/ `_get_mootdx_client()` + `_preserve_mootdx_bestip()` / `_tencent_quote()` / `_em_get()` + `_eastmoney_datacenter()` / `get_stock_data` / `get_indicators` / `get_fundamentals` / `get_balance_sheet` / `get_cashflow` / `get_income_statement` / `get_news` / `get_global_news` / `get_insider_transactions` / `get_profit_forecast` / `get_hot_stocks` / `get_northbound_flow` + 本地缓存 / `get_concept_blocks` / `get_fund_flow` / `get_dragon_tiger_board` / `get_lockup_expiry` |
| `.../tradingagents/dataflows/interface.py` | 229 | `route_to_vendor()` dispatch 模式（数据源可插拔） |
| `.../tradingagents/dataflows/stockstats_utils.py` | 133 | `yf_retry(func, max_retries=3, base_delay=2.0)` —— **只在限流时退避，其他异常直接冒泡** |
| `.../tradingagents/agents/quality_gate.py` | 168 | **质检闸门**（报告质量硬校验） |
| `.../tradingagents/agents/utils/rating.py` | 129 | **评级解析**：中文标签 + 英文评级词的边界判据 |
| `.../tradingagents/agents/utils/structured.py` | — | 结构化输出：失败后**重试一次自由文本** |
| `.../tradingagents/agents/utils/memory.py` | 300 | **决策记忆日志**（`TradingMemoryLog`，供绩效统计消费） |
| `.../tradingagents/agents/utils/signal_data_tools.py` | 163 | 信号类工具封装 |
| `.../tradingagents/agents/schemas.py` | 211 | 多 Agent 输出结构化契约 |
| `.../tradingagents/graph/trading_graph.py` | 756 | LangGraph 主编排 + 结果落库 |
| `.../tradingagents/graph/checkpointer.py` | — | 断点续跑（SqliteSaver） |
| `.../tradingagents/graph/reflection.py` | — | 反思闭环（历史结果回灌） |
| `.../tradingagents/performance.py` | 334 | **决策绩效统计**：`direction_accuracy`（方向正确率）/ `up_rate` / `outperform_rate`，零 LLM 调用 |
| `.../tradingagents/llm_clients/claude_agent_sdk_client.py` | 580 | Claude Agent SDK 客户端（走订阅额度） |
| `.../tradingagents/llm_clients/factory.py` / `capabilities.py` / `model_catalog.py` / `validators.py` | — | **多 provider 工厂 + 能力表 + 模型目录 + 校验**（新增 provider 的模板） |
| `.../tradingagents/agents/utils/rating.py` + `agents/utils/agent_utils.py` | — | 评级 + 通用 Agent 工具 |
| `.../tradingagents/agents/analysts/{policy_analyst,hot_money_tracker,lockup_watcher}.py` | — | **A 股特化三角色**（政策 / 游资 / 解禁） |
| `.../tradingagents/agents/utils/{core_stock_tools,fundamental_data_tools,news_data_tools,technical_indicators_tools}.py` | — | LangChain tool 定义（**给 LLM 的 Schema 层**） |
| `/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md` | 10,975 B | **可直接交给下一个 agent 的工程约束清单**（版本纪律 / 防封 / 未来函数 / provider 形状 / 测试基线 / 血的教训） |
| `/Users/zenghui/Documents/code/TradingAgents-astock-main/issues/*.md` | 5 份 | **issue 复盘模板**（问题 / 根因 / 修复 / 遗留） |

**`_em_get()` 实现（`a_stock.py:532-566`）**

```python
# 东财系 HTTP 接口（push2 / push2his / datacenter-web / search-api / np-weblist）
# 有风控：每秒 >5 次 / 单 IP 并发 ≥10 / 1 分钟 ≥200 次 / 5 分钟 ≥300 次 → 临时封 IP。
_EM_SESSION = _requests.Session()
_EM_SESSION.headers.update({"User-Agent": _UA})
_EM_MIN_INTERVAL = float(os.environ.get("EM_MIN_INTERVAL", "1.0"))
_em_last_call = [0.0]

def _em_get(url, params=None, headers=None, timeout=15, **kwargs):
    wait = _EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
    if wait > 0:
        time.sleep(wait + random.uniform(0.1, 0.5))
    try:
        return _EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    finally:
        _em_last_call[0] = time.time()
```

### B.7 被明确否定的设计（原文摘录 + 出处）

1. **Tushare 被否（积分墙）** —「**Why**:Tushare 核心接口要 **2000 积分**,免费数据残废;AKShare 高频调用易封 IP。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/DEV_LOG.md:44`

2. **MongoDB / Redis 被否** —「**Why**:CN 版的 git log 反复出现"MongoDB 迁移脚本""数据库隔离"等 fix,数据库依赖是累赘。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/DEV_LOG.md:50`

3. **CN 版 fork 路线被否** —「**Why**:CN 版的 `app/` (FastAPI) + `frontend/` (Vue) 是商业闭源,我们要做完全 Apache 2.0 开源,基础必须干净。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/DEV_LOG.md:38`

4. **akshare 被移除** —「**akshare 已移除（v0.2.5）** v0.2.5 起完全移除 akshare 依赖，所有数据通过直连 HTTP API 获取。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

5. **`[google]` extra 被移除（#87）** —「uv 构建覆盖所有 extra 的 universal lock，**extra 存在就让所有人的 `uv sync` 失败**。留空更糟（`pip install .[google]` 静默装空）。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`；同 `pyproject.toml:57`「NOTE: there is deliberately no `[google]` extra — see #87.」

6. **「一个卡点覆盖 15 个接口」这一自述被实测证伪** —「⚠️ v0.5.3 曾声称"一个卡点覆盖 15 个接口"，**实际漏了 3 个**（龙虎榜/解禁/行业对比直接调了 `safe_ticker_component`），拿 `00700` 调用会返回"近30日未上龙虎榜"这种**看起来完全正常的报告**。v0.5.5 补全。**改完这类防护要枚举所有 vendor 逐个实测，别从设计推断覆盖面。**」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

7. **截断告警「覆盖不全」被证伪（默认 provider 下从不触发）** —「`warn_if_truncated` 必须认全四种：Anthropic `stop_reason=max_tokens`、OpenAI 兼容 `finish_reason=length`、Gemini `finish_reason=MAX_TOKENS`（大写）、**OpenAI Responses API `status=incomplete`**……**最后一种最要紧**——`openai` 是默认 provider 且走 Responses API，v0.5.1 漏掉它导致**这个告警在默认配置下一次都不会触发**。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

8. **把 `direction_accuracy` 叫「胜率」是错的（v0.5.2 → v0.5.5 改）** —「⚠️ **指标命名即口径**：`direction_accuracy`（方向正确率）是唯一衡量判断准不准的——看多要跑赢、看空要跑输才算对，Hold 不计入。`up_rate` / `outperform_rate` 只描述标的怎么走，**与判断对错无关**。v0.5.2 曾把前者叫"胜率"，导致**给 Sell 之后股价下跌（判断正确）被记成失败**。」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

9. **评级边界规则「枚举允许标点」三轮全失败** —「这条规则前后被修了三轮才收敛——每轮都是往白名单加字符、每轮都漏：无边界→`Buyer interest`判 Buy；`(?![A-Za-z])`→`Sell-off`判 Sell；枚举收尾标点→`Buy（基于风险收益比）`**反被判成 Hold**。」「⚠️ **动这条规则必须整张跑 `test_rating_value_boundary_matrix`（22 例）**」
   出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

10. **mootdx 逐台探测覆写用户配置被否（v0.5.10 → v0.5.12 重构）** —「`StdQuotes.__init__` 里有 `config.set('BESTIP', {'HQ': self.server})`——**每建一次带 `server` 的 client 都会持久化写进 mootdx 配置文件**。逐台探测会把用户原本配好的服务器一路覆写，最后留下一台死的，还会连累同机其它用 mootdx 的程序。」「⚠️ **别改回手动调还原函数**——那样再加一条提前返回就会漏掉一处，而漏掉的后果是**静默给用户留下一台死服务器**。」
    出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

11. **CLI 裸跑被第二个子命令破坏（v0.5.9「血的教训」）** —「`@app.callback(invoke_without_command=True)` **不能删**。Typer 只注册一个命令时是"单命令模式"……一旦注册第二个子命令就切换成"命令组模式"，裸跑直接报 `Missing command` 退出——而 README 和所有文档写的都是裸跑，等于**每个现有用户升级后第一条命令就失败**。」
    出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

12. **占位类型用 `Exception` 基类导致护栏失效** —「⚠️ **占位类型绝不要用 `Exception` 基类**：`ClaudeSDKError` 曾被占位成 `Exception`，进 `_FALLBACK_ERRORS` 后让"订阅凭据失效不得降级到计费 provider"这条护栏彻底失效（v0.5.4 修）。」
    出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`

13. **外部 pyproject 修改被否** —「当前仓库的 pyproject.toml 已是最新，**无需采纳外部版本**。」
    出处：`/Users/zenghui/Documents/code/TradingAgents-astock-main/issues/004-pyproject-toml-dependencies.md`

---

## C. `/Users/zenghui/Documents/code/vibe-astock-main/`

### C.1 目录树（深度 ≤3，排除 `.git/ __pycache__/ node_modules/ .venv/`）

```
/Users/zenghui/Documents/code/vibe-astock-main/
├── main.py                    3,253 B   命令行入口（每日复盘，约 6 分钟一次）
├── server.py                 66,913 B   FastAPI Web 后端（**单文件 67 KB**）
├── pytest.ini                   117 B   testpaths=tests；markers=unit/integration
├── requirements.txt             889 B
├── .env.example                 685 B
├── README.md 27,408 B / README_en.md 33,904 B
├── assets/screenshots/        8 张界面截图
├── .deploy/
│   ├── 部署记录.md / 四件套部署记录.md
│   ├── review-0904.json
│   └── modes-v6-cards.png / portfolio-tradingdb.png / review-ai-narrative.png / review-dashboard.png
├── .claude/launch.json
├── duanxian/                  **后端核心包（49 个条目）**
│   ├── fetchers.py             628 行  **数据取数层**（自包含）
│   ├── analysts.py                    五分析师节点 + 降级报告
│   ├── review_graph.py                LangGraph 复盘编排
│   ├── roles.py / prompts.py / modes.py / synthesizer.py
│   ├── emotion_metrics.py             派生情绪指标
│   ├── breadth.py                     指数/市场宽度
│   ├── market_facts.py                盘面事实
│   ├── live_emotion.py / intraday.py  盘中快照
│   ├── backtest.py                    涨停样本统计
│   ├── stats_context.py / weekly.py / drift.py / excursion.py
│   ├── verification.py                **明日验证条件**
│   ├── archive.py                     **原始数据归档（原样返回，永不删除）**
│   ├── journal.py / positions.py / at_risk.py / attribution.py   **个人交易数据（严禁进 prompt）**
│   ├── review_store.py / preflight.py / config.py / helpers.py / util.py
│   ├── trade_calendar.py / theme_tree.py / llm_errors.py / structured.py
│   ├── cli_llm.py / tools.py / inbox.py / reflection.py / risk.py / overseas.py / sync_tradingdb.py
│   └── deepdive/               agents.py / data.py / graph.py / schemas.py / state.py
├── frontend/                  React 19 + Vite + TS + Tailwind
│   ├── src/{components,hooks,lib,pages,data}/ · router.tsx · main.tsx
│   ├── dist/                  已构建产物
│   └── package.json / vite.config.ts / tailwind.config.ts / tsconfig.json
├── vr/                        另一套并行前端/取数（含 vr/astock.py 东财客户端）
├── tests/
│   ├── conftest.py              845 B
│   └── test_core_logic.py   349,272 B   **523 个 test 函数，单文件**
└── .venv/
```

### C.2 README / 设计文档的关键结论（逐条摘录）

- 定位：「**A 股短线复盘看板 —— 打开就看清今天的短线情绪**」「派生情绪指标 · 全本地运行 · 可用本机 CLI 订阅免 key」
- 版本徽章：「tests-**533 passing**」「version-v0.2.1」
- 免责红线：「⚠️ 本项目只做公开盘面数据的整理、统计与市场层面研判，**不推荐个股、不预测涨跌、不给买卖时机。** 不构成任何投资建议」
- **不做什么**（原文）：「**它不做什么**：不推荐个股、不给参与倾向、不给买卖点位。个股一律只作客观陈述（属于哪个题材、几板、龙虎榜谁在买、技术位置如何）。**方向与情绪判断做到板块层面为止。**」
- 硬指标层设计：「所以屏幕上**九成是硬指标层**——赚钱效应 / 晋级率 / 梯队结构 / 情绪周期 / 亏钱效应 / 封板质量 / 题材事件树 / 历史统计位置——**全部纯计算、数据源直出，不经过 AI，打开就有**。」
- **明日验证条件**：「把今晚的判断变成明天能对账的东西：每条都带**今日基准值**和"**变动超过多少才算数**"的阈值。」
- 快照纪律：「⚠️ **快照过点就补不回来**（拿的是实时行情），所以由后台线程按点自动抓……⚠️ 更要紧的是：**过了那个点，系统不会拿此刻的实时值冒充当时的快照** —— 它会明说"09:25 快照缺失、现在距那个时点已超 8 分钟"，而不是给你一个看着正常的假数字。」
- **涨停样本统计的三层区分（原文表格）**：

  | 层级 | 是什么 | 本项目 |
  |---|---|---|
  | ① 市场现象统计 | 某类票在历史上的表现 | **就是这一层** |
  | ② 用户规则历史模拟 | 按你的规则回放，含成交概率与滑点 | 没做 |
  | ③ 用户真实成交统计 | 你实际下单成交的结果 | 见交易日志 |

  并附：「样本来自「前一日收盘时留在涨停池里的票」——这是**事后知道封住了**的名单，天然漏掉冲板没封住的、排队没成交的、一字板买不进的。**真实打法的期望必然低于这里的数字。**这段披露显示在页面顶部，不折叠。」
- **归档原则**：「**原始数据归档** —— 每天把数据源**原样返回的内容**存下来、永不删除（一天几百 KB）。缓存存的是派生结果、随时可删重建；归档是"口径改了之后还能把历史重算一遍"的唯一依据。⚠️ **存的必须是原始行**：归一化过的行既检不出字段漂移，也拿不回被丢掉的列。」
- **结构漂移三分类**：「把三件事分开：**数据源变了**（字段清单变化）/ **市场结构变了**（板块占比、涨停家数分布的窗口比较）/ **制度变了**（涨跌幅、920 号段、连板口径）。不分开就会把前两类读成第三类，然后基于一个假信号调整打法。⚠️ **制度事件只收人工登记，绝不从数据反推** —— 反推是猜，猜错会把市场波动当成制度事件。」
- 数据源表（原文，「要 key 吗」列）：

  | 来源 | 提供 | 要 key 吗 |
  |---|---|---|
  | akshare（东财涨停池 / 龙虎榜） | 涨停 · 炸板 · 跌停 · 连板梯队 · 龙虎榜席位 | 不要 |
  | 东财 `push2delay` clist | 板块 / 个股资金流、成交额榜 | 不要 |
  | akshare 昨日涨停池 | **定稿记录**：昨日涨停股在目标日的表现（赚钱效应 / 亏钱效应 / 连板溢价 / 反馈矩阵的主来源） | 不要 |
  | 腾讯财经 `qt.gtimg.cn` | 实时行情批量 | 不要 |
  | 腾讯 hist `stock_zh_a_hist_tx` | K 线与交易日历（**部分网络下东财 push2his 被封，故走腾讯**） | 不要 |
  | 同花顺问财 | 涨停原因题材串（→ 题材事件树） | **要** |

- 测试说明：「**533 个用例**，覆盖指标计算、口径边界与降级路径 —— 重点在那些**错了也看不出来**的地方：界面照常渲染、数字看着合理，但结论是错的。其中一组专门锁住个人交易数据的边界：账本损坏时必须报错而不是返回空表、并发写入不丢单、迁移老账本不反推计划止损、录入接口每个字段都要透传、以及**喂 prompt 的模块一律不得引用个人数据模块**。」
- 环境变量 `VIBE_MARKET_DIRECT`（README:438）：「相反方向：代理把东财挂掉、连取涨停池都失败时设 `1` 强行直连。⚠️ 它是**进程级**的，会一并关掉东财请求的代理回退」

### C.3 代码规模

| 项 | 值 |
|---|---|
| `.py` 文件数（排除 `.venv/ .git/ __pycache__/ node_modules/`） | **66** |
| `.py` 总行数（同口径） | **23,677** |
| 前端 | **31 个 `.tsx`** + **13 个 `.ts`** + 4 `.js` + 2 `.css` |
| `.md` 文件数 / 总字节 | 4 / **70,980 B** |
| 其他 | 13 png / 7 json / 2 svg / 2 html |
| 单文件最大 | `tests/test_core_logic.py` **349,272 B**；`server.py` 66,913 B；`duanxian/fetchers.py` 628 行 |
| `.git` | **不存在** |

### C.4 是否可运行

- **入口**：`main.py`（CLI 复盘，用法 `.venv/bin/python main.py [YYYY-MM-DD]`）；`server.py`（FastAPI 后端）；`frontend/`（Vite dev/build，`dist/` 已构建）。
- **依赖清单完整**：`requirements.txt` 分四段（编排引擎 / Web 后端 / 数据层 / 开发测试），含 langgraph>=0.6、fastapi>=0.110、uvicorn、akshare>=1.18、mini-racer>=0.12、pytest>=8。
- **Python 版本**：requirements 头注「需 Python 3.10+（akshare 新版语法）；**实测 3.12**」。
- **`.deploy/部署记录.md` 与 `四件套部署记录.md`** 存在（部署记录资产）。
- **外部依赖**：同花顺问财 `IWENCAI_API_KEY`（不配也能跑，题材事件树如实标不可用）。
- **未运行验证**（按委托要求）。

### C.5 测试是否存在

- 目录：`/Users/zenghui/Documents/code/vibe-astock-main/tests/`
- 文件：`conftest.py`（845 B）+ `test_core_logic.py`（**349,272 B**）
- **test 函数数量：523**（`grep -c 'def test'`）
- README 徽章与正文均称 **533 个用例**（差值来自 parametrize 或版本滞后）
- `pytest.ini` 定义两个 marker：`unit`（纯逻辑单测，不打网络）、`integration`（需要真实数据源）
- **未运行**（按委托要求）。

### C.6 可复用组件清单（绝对路径 + 一句话用途）

| 绝对路径 | 用途 |
|---|---|
| `/Users/zenghui/Documents/code/vibe-astock-main/duanxian/fetchers.py` | **数据源连接器**（628 行）：东财 `push2delay` clist + akshare 涨停池/炸板池/龙虎榜 + 腾讯实时 + 自研代理策略。含 `_direct_get()` / `_DIRECT_HOSTS` / `VIBE_MARKET_PROXY` / `VIBE_MARKET_DIRECT` |
| `.../duanxian/emotion_metrics.py` | **派生情绪指标**（纯计算）：赚钱效应 / 亏钱效应 / 晋级率 / 封板质量 |
| `.../duanxian/breadth.py` | 市场宽度（指数涨跌家数；含 `retries>=1` 参数校验，**不把参数错误伪装成请求失败**） |
| `.../duanxian/market_facts.py` | 盘面事实聚合（按日落盘缓存） |
| `.../duanxian/backtest.py` | **涨停样本统计**（封板时间曲线 / 分情绪环境表现 / 样本偏差声明） |
| `.../duanxian/verification.py` | **明日验证条件**（基准值 + 阈值，可对账） |
| `.../duanxian/archive.py` | **原始数据归档**（原样行、永不删除；空数据不归档） |
| `.../duanxian/review_store.py` | 复盘结果落盘（`~/.duanxian-agents/reviews/`） |
| `.../duanxian/review_graph.py` | **LangGraph 复盘编排**（五分析师 → 汇总） |
| `.../duanxian/analysts.py` | 五分析师节点 + **失败降级报告**（带 `[⚠️ … 已跳过：ExcType]` 标注） |
| `.../duanxian/reflection.py` | **反思闭环**：`get_past_context()` / `auto_evaluate_prior()`（历史命中回看） |
| `.../duanxian/preflight.py` | **体检门禁**：`check(date)` → 不 ok 直接 `sys.exit(3)`，**拒绝出报告** |
| `.../duanxian/positions.py` + `at_risk.py` + `attribution.py` + `journal.py` | **个人交易数据层**（账本 / 风险敞口 / 归因 / 日志）；⛔ 明令**不得进 prompt** |
| `.../duanxian/risk.py` | 个人仓位渲染（同上禁令） |
| `.../duanxian/drift.py` | **结构漂移检测**（数据源变 / 市场结构变 / 制度变 三分） |
| `.../duanxian/trade_calendar.py` | 交易日历 |
| `.../duanxian/theme_tree.py` | 题材事件树（同花顺问财题材串） |
| `.../duanxian/llm_errors.py` | **LLM 配置错误处理**：`LlmConfigError` 故意冒泡（**降级会让复盘"跑成功但内容全空"**） |
| `.../duanxian/structured.py` + `cli_llm.py` + `roles.py` | 结构化输出 + 本机 CLI 订阅 LLM 接入 + 角色定义 |
| `.../duanxian/modes.py` | 分析口径模式（cards.json） |
| `.../duanxian/weekly.py` | 周报（近 5 交易日热度趋势） |
| `.../duanxian/deepdive/graph.py` + `agents.py` + `schemas.py` + `state.py` + `data.py` | **个股深挖子图**：四分析师并行 → 正反论证 → 裁判结论 |
| `.../server.py` | FastAPI 全部 API（67 KB 单文件） |
| `.../frontend/src/` | React 19 + TS + Tailwind 看板（pages / components / hooks / lib） |
| `.../tests/test_core_logic.py` | **523 例单文件测试**（口径边界 + 降级路径 + 个人数据边界锁） |
| `.../requirements.txt` | **依赖坑留档**（mini-racer vs py_mini_racer 互覆盖的完整说明） |

### C.7 被明确否定的设计（原文摘录 + 出处）

1. **「模块顶层 pop 代理环境变量」被否（并写清为什么）** —「⛔ 这个模块在 server 启动时就被 import，所以**任何进程级的环境改动都会波及别人**：· 早先这里在模块顶层 pop 掉了 HTTP_PROXY / HTTPS_PROXY / ALL_PROXY —— 等于顺手废掉整个进程的代理，而同一进程里 LLM 调用可能正靠它出网，**表现只是"模型调不通"，没人会联想到取数模块**；· 改成"把 eastmoney.com 加进 NO_PROXY"也不行：`vr/astock.py` 的东财客户端本来就是**直连优先、失败自动回退系统代理**，而它的代理会话是 `trust_env=True`……往 NO_PROXY 里塞 eastmoney.com 会把那条自愈回退**静默废成"再直连一次"**。」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/fetchers.py:66-74`
   同上：「所以**默认什么都不改**。代价：akshare 内部自己 new requests（塞不进本模块的会话），在"系统代理挂掉东财"的机器上它会失败 —— 但**那是响亮的失败**：核心数据缺 → 体检拒跑 → 界面给一句能照着办的话，**而不是静默给错数**。」（`fetchers.py:76-79`）

2. **「只更新 NO_PROXY（大写）」被否（requests 小写优先）** —「🔴 大小写两个变量都要写。requests 取 no_proxy 时**小写优先**（`os.environ.get(k) or os.environ.get(k.upper())`），只更新 NO_PROXY 的话，凡是环境里已经有小写 no_proxy 的机器上这一整段就白做 —— 照样走代理、照样 **403**，而且**现象和"没改过"一模一样，看不出来**。」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/fetchers.py:95-98`

3. **`py_mini_racer`（旧包）被明确禁止** —「必须是改名后的 mini-racer，**不能装旧的 py_mini_racer**：两个包会装进同一个 `py_mini_racer/` 目录互相覆盖 —— 旧包的 Python 代码配上新包的二进制，调用时报 `dlsym(mr_eval_context): symbol not found`，表现是「板块资金 / 资金轮动」两块**静默空着**（接口 200、sectors: []）。已经装了旧包的：`pip uninstall py_mini_racer && pip install --force-reinstall mini-racer`」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/requirements.txt`

4. **个人交易数据严禁进 prompt（两处独立重复声明）** —「⛔ **不要接进任何 AI prompt** —— 同 `risk.render()`：个人仓位进 prompt……」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/at_risk.py:187`；`.../duanxian/attribution.py:178`「⛔ **不要把它接进任何 AI prompt。** 个人持仓与盈亏一旦进 prompt，模型的……」
   README 侧对应测试纪律：「**喂 prompt 的模块一律不得引用个人数据模块**」（`README.md:476`）

5. **「空数据归档」被禁（避免把取数失败固化成事实）** —「return {"ok": False, "reason": "**空数据不归档（避免把取数失败固化成'那天没有'）**"}」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/archive.py:81`

6. **「历史最大投入估账户规模」被否** —「⚠️ 没填就是 None，**不要拿历史最大投入之类的东西估一个** —— 估大了占比偏小，……」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/at_risk.py:48`

7. **「第二份实现」被否（防口径分叉）** —「⚠️ 这里**不要再写一份**：两份实现一旦分叉，回测与复盘……」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/duanxian/backtest.py:233`

8. **「拿此刻实时值冒充当时快照」被否** —「⚠️ 更要紧的是：**过了那个点，系统不会拿此刻的实时值冒充当时的快照** —— 它会明说"09:25 快照缺失、现在距那个时点已超 8 分钟"，而不是给你一个看着正常的假数字。」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/README.md:152-154`

9. **LLM 配置错误「降级」被否** —「它是**故意冒泡**上来的（降级会让复盘"跑成功但内容全空"，见 `duanxian/llm_errors.py`）」
   出处：`/Users/zenghui/Documents/code/vibe-astock-main/main.py:59-61`

10. **「制度事件从数据反推」被否** —「⚠️ **制度事件只收人工登记，绝不从数据反推** —— 反推是猜，猜错会把市场波动当成制度事件。」
    出处：`/Users/zenghui/Documents/code/vibe-astock-main/README.md:196`

**实测数字附列**：`duanxian/backtest.py:39` ——「只有 **116 只封住**，**18% 的失败样本完全不在统计里**」。

---

## D. `/Users/zenghui/Documents/code/a-stock-data-main/`

### D.1 目录树（深度 ≤3）

```
/Users/zenghui/Documents/code/a-stock-data-main/
├── SKILL.md                232,206 B / 4,552 行   **整个项目的本体**
├── README.md                28,005 B
├── README_en.md             23,071 B
├── CHANGELOG.md             59,840 B
├── LICENSE                  10,760 B   Apache 2.0
├── .gitignore                   38 B
├── .github/FUNDING.yml
├── docs/
│   └── source-integration-v3.8.0.md     88 行   V3.8 数据源整合记录（含候选取舍）
├── tests/
│   └── test_official_data.py           314 行   **对 SKILL.md 内嵌代码做 exec 测试**
├── assets/（2 png + .gitkeep）
└── （**没有 .venv、没有 .git、没有 setup.py / pyproject.toml**）
```

### D.2 README / 设计文档的关键结论（逐条摘录）

- 一句话：「**一个自包含的 Skill 文件**，把分散在 **22 个数据源**里的 A 股原始数据整合成 AI 编程助手直接能用的工具集。你不用再背 mootdx 的 K 线参数、东财的 PDF Referer 头、iwencai 的 X-Claw 鉴权——全部封装好了。**主源被封还有「备用源速查」可降级。**」
- 徽章：「12 层架构 · **60 个端点** · **22 个数据源** · 零鉴权」「Python-3.9+」
- `SKILL.md` 头部（version 3.8.0）：「十二层数据架构，**60 个能力端点（55 主端点 + 5 备胎）、22 个来源**。V3.8 新增的六个入口于 **2026-09-05** 实测」
- 「**V3.0 Breaking Change**：彻底移除 akshare 依赖，所有数据源改为直连 HTTP API（仅 mootdx 保留 TCP）。⚠️ V3.7 起 §6.5/§6.6 另需第三方客户端 `baostock`（TCP），因此「零第三方封装依赖」现仅适用于其余端点。」
- 使用方式：「将本文件放入 `~/.claude/skills/a-stock-data/SKILL.md`，Claude Code 会自动识别并在 A 股相关对话中激活。」
- 十二层：行情层 / 研报层 / 信号层 / 资金面·筹码层 / 新闻层 / 基础数据 / 公告 / 打板 / ETF期权 / 舆情互动 / 宏观 / 指数与交易日历
- `docs/source-integration-v3.8.0.md` 关键数字：「11→12 层，54→60 个能力入口，**19→22 个来源**（新增中证、国证、北交所）；无新增安装依赖，保留 Python 3.9。」「国证当前文件是**月末快照**；历史调样、集合竞价、需 Key 的同花顺增强 API 暂不算已支持。」

### D.3 代码规模

| 项 | 值 |
|---|---|
| `.py` 文件数（排除 `.venv/ .git/ __pycache__/ node_modules/`） | **1** |
| `.py` 总行数（同口径） | **314**（`tests/test_official_data.py`） |
| `SKILL.md` | **232,206 B / 4,552 行** |
| `SKILL.md` 内嵌 Python 函数数（`^def xxx(`） | **106** |
| `SKILL.md` 三级标题数（`^### `） | 83 |
| `.md` 文件数 / 总字节 | 5 / **350,145 B** |
| 全仓文件数 | 12 |
| `.git` / 依赖清单 | **不存在** |

### D.4 是否可运行

- **没有独立可运行程序**。形态是「**结构化 Markdown + 内嵌 Python**」，供支持上下文注入的 AI 助手（Claude Code / Codex / OpenClaw）读取。
- 内嵌代码的**可执行性由测试证明**：`tests/test_official_data.py:21` 的 `load_shipped_code()` 会
  1. 读 `SKILL.md`；
  2. 按 `<!-- official-data-core:start -->` / `<!-- official-data-backups:start -->` 标记切出区块；
  3. 用正则取 ```python 代码块；
  4. `exec(compile(block, "SKILL.md:official-data-core", "exec"), namespace)`。
- README：「Skill 文件本质是结构化 Markdown + 内嵌 Python，任何支持上下文注入的 AI 编程助手都能用。」
- Python 版本要求：3.9+（`SKILL.md` 内注释「3.9 兼容：不能写 `dict | None`（那是 3.10+ 语法）」）。
- 无依赖清单文件；依赖写在 SKILL.md 的 Prerequisites 段（mootdx / requests / pandas / baostock）。
- **未运行验证**（按委托要求）。

### D.5 测试是否存在

- 目录：`/Users/zenghui/Documents/code/a-stock-data-main/tests/`
- 唯一文件：`tests/test_official_data.py`（**314 行**）
- 两个 test class：`OfficialDataTests`（离线，mock HTTP）、`LiveOfficialDataTests`（联网，需 `ASTOCK_LIVE_TRADE_DATE` / `ASTOCK_LIVE_MARGIN_DATE` 环境变量）
- 文件头注释明确了测试理念：「Test the Python **shipped inside SKILL.md**, not a second implementation.」
- 运行方式（原文）：`Offline: python3 -m unittest discover -s tests -v`（用 unittest，非 pytest）
- **未运行**（按委托要求）。

### D.6 可复用组件清单（绝对路径 + 一句话用途）

`SKILL.md` 是单文件，组件以「章节 + 函数」为单位。**可复用价值最高的部分**：

| 位置（章节 / 函数） | 用途 |
|---|---|
| `/Users/zenghui/Documents/code/a-stock-data-main/SKILL.md` §「数据源优先级 & 东财防封」（行 ~231-294） | **限流铁律方法论**：四级优先级表 + 风控阈值表 + 实测封禁案例 + 防封铁律 5 条 + 降级路径表。**这是本仓最有价值的可复用资产** |
| 同文件「东财数据中心统一查询（共用 helper）」（行 ~600-670） | `em_get()` / `EM_SESSION` / `EM_MIN_INTERVAL` / `eastmoney_datacenter()` 的可直接抄的参考实现 |
| §「备用源速查 & 降级策略」 | `dragon_tiger_backup()`（沪深交易所官方，含营业部席位）/ `fund_flow_backup()`（新浪日度资金流）/ `announcements_backup()`（深交所官方 / 沪市东财公告+PDF） |
| §1 行情层 | `tdx_client()`（mootdx 服务器**真实取数验活** `_probe()`+`_validate()`）/ `tencent_quote()`（含 `is_stale`/`stale_reason` 僵尸报价标志）/ `norm_ticker()` / `get_prefix()`（前缀+后缀双路由）/ `em_market_code()` / `em_secid()` |
| §2 研报层 | `eastmoney_reports()` / `eastmoney_industry_reports()` / `ths_eps_forecast()` / `download_pdf()` |
| §3 信号层 | `board_fund_flow()`（板块资金流，行业/概念/地域 × 今日/5日/10日 + 四档明细）/ 行业板块排名 / `eastmoney_concept_blocks()` |
| §4 资金面 | 融资融券 / 大宗交易 / 股东户数 / 分红送转 / `eastmoney_fund_flow_minute()` |
| §5 新闻层 | 东财个股新闻（遍历 `cmsArticleWebOld` 列表本身）/ 财联社 `v1/roll/get_roll_list` + 本地签名 `sign=md5(sha1(排序query))` / 全球资讯 |
| §6 基础数据 | `_sina_stock_code()` / `_get_financial_report_sina()`（遍历 `report_list` 期次）/ 估值历史（PE/PB/PS/PCF + 换手率 + 停牌 + isST）/ **§6.4 新浪财报三表** / §6.5 估值历史 / §6.6 上市退市日 / §6.7 申万行业变迁史 |
| §7 公告层 | `_cninfo_orgid()`（动态查 `szse_stock.json`，6198 只，模块级缓存；硬编码 `gssx0{code}` 降为 fallback） |
| §8 打板层 | 涨停池 / 跌停池 / 炸板池 / 连板梯队 / 强势股 / `em_stock_monitor()`（重点监控池）/ `em_price_anomaly()`（日内异动，12 条规则码全解释）/ `ladder()` |
| §9-10 | ETF 期权 T 型报价 / 希腊字母 / IV / 舆情互动（互动易 / 热榜 / 人气榜） |
| §11 宏观层 | 社融（月度 12 列）/ PMI（注意全角括号内空格须整个删掉） |
| §12 指数与交易日历 | 中证/国证成分与权重 / 中证 PE 股息率 / 深交所整月日历 / 沪深官方两融 / 北交所行情 |
| §「筹码分布 CYQ」 | 用 OHLC + 换手率**本地推演**（东财无公开接口） |
| `/Users/zenghui/Documents/code/a-stock-data-main/docs/source-integration-v3.8.0.md` | **数据源取舍判据留档**（88 行，每条候选的接入/拒绝理由） |
| `/Users/zenghui/Documents/code/a-stock-data-main/CHANGELOG.md` | 59,840 B 逐版本变更（含每次实测数字） |
| `/Users/zenghui/Documents/code/a-stock-data-main/tests/test_official_data.py` | **「测试 SKILL.md 内嵌代码」的实现范式**（`load_shipped_code()`） |

### D.7 被明确否定的设计（原文摘录 + 出处）

1. **akshare 被彻底移除** —「**V3.0 Breaking Change**：彻底移除 akshare 依赖，所有数据源改为直连 HTTP API（仅 mootdx 保留 TCP）。」
   出处：`/Users/zenghui/Documents/code/a-stock-data-main/SKILL.md`（版本沿革段）

2. **百度 PAE 两个接口失效被替换** —「**§3.3 概念板块归属（#18）**：百度 PAE `getrelatedblock` 失效（`ResultCode 10003` + 空数组）→ 改用东财 `slist`（`spt=3`）」
   出处：同文件 V3.2.2 段；另 V3.1「百度 PAE 资金流→东财 push2」

3. **财联社旧 API 下线被弃用** —「**财联社快讯下线（#14）**：`cls.cn` 旧 API 全面 404，标注弃用并改用东财全球资讯。」
   出处：同文件 V3.2 段（V3.4.0 又用官方 `v1/roll/get_roll_list` 复活）

4. **东财 CYQ 接口被证不存在 → 改本地推演** —「**东财没有公开 CYQ 接口**（实测 `push2`/`push2his` 的 `cyq/get` 均 **404**），本端点用 OHLC + 换手率**本地推演**，零新增数据源。」
   出处：同文件 V3.7.0 段

5. **北交所老号段被判定为「僵尸数据」** —「🔴 **北交所老号段（43/83/87）会返回僵尸数据且不报错**：实测在市 342 只中 **336 只已迁至 `920xxx`**（锦波生物 `832982`→`920982`、贝特瑞 `835185`→`920185`），老码在东财研报静默返回 **0 篇**、在腾讯行情返回**定格报价**（成交量 0，价差达 **17%~100%+**）却仍是 **HTTP 200**。」
   出处：同文件 V3.6.0 段

6. **「同一份文件两套号段规则」被否** —「`get_prefix()` 用 `startswith(("4", "8"))` + `startswith("92")` 覆盖整个北交所号段——**同一份文件两套规则**（#51）。现统一为 `startswith(("4", "8", "92"))`。」
   出处：同文件 V3.7.2 段

7. **「未归一化原串直接喂 get_prefix」被否（静默返回错标的）** —「`000016.SH` 以 `0` 开头落到默认深市分支，secid 拼成 `0.000016`（深康佳A）而非 `1.000016`（上证50 指数），**静默返回另一只标的的数据**。」
   出处：同文件 V3.7.1 段

8. **外部项目 free-stockdb 被暂不接入** —「| [free-stockdb](https://github.com/hello245m/free-stockdb) | 本地存储和同步设计 | **上游数据出处不够清楚，暂不接入** |」
   出处：`/Users/zenghui/Documents/code/a-stock-data-main/docs/source-integration-v3.8.0.md:86`

9. **国证港股 5 位代码被拒** —「国证987008（港股科技指数）返回的腾讯代码为 `00700`；旧原型补零会错标成深市 `000700`。修复后**要求国证原始股票代码六位，拒绝五位港股**」
   出处：`docs/source-integration-v3.8.0.md:52`

10. **北交所「不截断成完整快照」** —「北交所分页期间总数变化、返回旧交易日、缺少盘口字段、重复标的**均拒绝**；匿名会话 302 仅重建一次，不循环跟随。」「上交所两融和北交所行情的分页总数**拒绝小数、布尔值等异常类型，不截断成"完整快照"**。」
    出处：`docs/source-integration-v3.8.0.md:54-55`

11. **`_probe()` 只做 TCP 握手被否** —「握手成功 ≠ 能取数——坏服务器可握手通过却回 2 字节空 body，导致**静默返回空 DataFrame 或连接崩溃**且走不到 fallback。新增 `_validate()`：每个候选 server 必须**真实拉一根 K 线成功**才采用」
    出处：`SKILL.md` V3.4.1 段

---

## E. `/Users/zenghui/Documents/code/alphadesk/`（最新、最完整）

### E.1 ⚠️ git 状态（实测，委托人特别关注项）

```
$ git -C /Users/zenghui/Documents/code/alphadesk log --oneline -15
fatal: your current branch 'main' does not have any commits yet
（exit code 128）

$ git -C /Users/zenghui/Documents/code/alphadesk log -1 --format='%H %ad %s'
fatal: your current branch 'main' does not have any commits yet

$ git -C /Users/zenghui/Documents/code/alphadesk branch -a
（无输出）

$ git -C /Users/zenghui/Documents/code/alphadesk status --porcelain | wc -l
18
```

**18 行全部为未跟踪（`??`）**：

```
?? .env.example        ?? .gitignore      ?? .openclaw/     ?? README.md
?? agent/              ?? backtest/       ?? cli.py         ?? config/
?? data/               ?? delivery/       ?? docs/          ?? eval/
?? features/           ?? ops/            ?? pyproject.toml ?? scripts/
?? strategy/           ?? tests/
```

**结论：`.git` 目录存在（2026-09-28 15:35 创建，分支 `main`），但仓库零 commit —— 47,215 行代码、38 份验收文档全部处于未跟踪状态，没有任何版本历史、没有任何回滚点。** 这是 E 相对其他项目最大的结构性风险。

### E.2 目录树（深度 ≤3，排除 `.git/ __pycache__/ node_modules/ .venv/ .pytest_cache/`）

```
/Users/zenghui/Documents/code/alphadesk/
├── cli.py                    20,352 B  命令行入口（doctor / tools / ask）
├── README.md                  7,241 B
├── pyproject.toml             2,244 B  扁平包结构（不依赖 pip install -e .）
├── .env.example               1,808 B
├── config/settings.py                 配置中心（.env + ALPHADESK_*）
├── data/                               **L0 数据层**
│   ├── sources/{base,market_duckdb,holdings_sqlite,news_online,industry_map}.py
│   ├── gates/quality.py               四道数据质量闸门
│   ├── meta.py                        BIG_TABLES 10 表 / guard_sql / guarded_query / meta_staleness
│   ├── ods/ · dwd/ · dws/ · ads/      （占位目录，ADR-009 决定不重建）
├── features/                           **L1 特征层**
│   ├── definitions/*.yaml             **27 个**声明式因子定义
│   ├── registry.py                    特征声明注册中心
│   ├── store.py                       as-of（Point-in-Time）读取契约
│   └── panel_fast.py                  面板向量化等价实现（T24/T32/T33）
├── strategy/                           **L2 策略层**
│   ├── factors/{flow,momentum,position,preprocess,trend,validate,volatility,volume_price,walkforward}.py
│   ├── signals/{compose,regime,regime_diag}.py
│   ├── portfolio/{constraints,optimize}.py
│   └── risk/{rules,sector}.py
├── backtest/{engine,checks,metrics}.py  回测引擎（61.6K）+ 五项可执行性检查 + 统一口径指标
├── agent/                              **L3 智能体层**
│   ├── llm/client.py                  httpx 直连 OpenAI 兼容（不引 LangChain）
│   ├── graph.py                       LangGraph 显式状态机（25,106 B）
│   ├── nodes/                         **八节点**：_common / recon / hypothesis / evidence / signal / portfolio / risk_gate / narrate / no_action / attribute
│   ├── specialists/                   **四专家 + Critic**：macro / sector_flow / technical / portfolio_view / critic / jurisdiction / prompts
│   ├── guards/{orchestrator,data_guard,review_guard,rule_guard,schema_guard}.py   四道防护
│   ├── context/{assembler,budget,memory,size_guard}.py   上下文工程（预算受控）
│   ├── prompts/{registry,templates,tool_docs,output_schemas}.py   版本化提示词
│   ├── schemas/advice.py              建议卡契约
│   └── tools/                         **13 工具**：advice_gate / backtest_tool / factors / holdings / kb / market / news / portfolio / registry / screen
├── delivery/                           **L4 交付层**
│   ├── card.py · pack.py · push.py · md_html.py · demo_run.py
│   └── out/                           真交付物：cards_2026-09-23.json / premarket_2026-09-23.{md,html} / postmortem_2026-09-23.{md,html} / trace_2026-09-23.jsonl
├── eval/{runner,assertions,loader,scripts/build_cases.py,golden/cases.jsonl,goldenset,report_golden.json}
├── ops/                                **L5 治理层**
│   ├── trace.py · log.py · audit.py · cost.py · lessons.py · scheduler.py · mock_push_demo.py
│   ├── traces/2026-09-26.jsonl · 2026-09-27.jsonl
│   └── out/                            审计/成本/教训/推送证据（含 push_records_s1~s6.db 六个场景库）
├── state/desk.db · state/trace.jsonl
├── scripts/{feishu_mock,fetch_news,verify_factor_equiv,verify_layered_equiv,verify_panel_equiv,verify_t25_parallel}.py
├── tests/                              **45 个 .py**（44 个 test_* + __init__）
├── docs/                               **38 个 md / 643,225 B**
│   ├── ADR-000-工程约定.md
│   ├── 任务清单与依赖关系.md（687 行，主索引）
│   ├── M0-验收记录.md / M1-数据与闸门验收记录.md
│   └── T04~T34 共 31 份验收记录
└── .openclaw/tmp/                      运行期临时与证据（~45 个文件：prof 日志 / A-B 脚本 / 回滚点快照）
```

### E.3 README / 设计文档的关键结论（逐条摘录）

**E.3.1 `README.md`（7,241 B）**

- 定位：「一个「**先有可信数据和可执行回测、再谈 Agent**」的 A 股策略建议系统。」
- 四条产品原则（原文）：
  - 「**一切结论强制绑定证据**：每个工具返回都带 `as_of` + `source`，无源数据不可用；」
  - 「**「不操作」是合法且被鼓励的输出**：凑一条建议不如诚实地报「今日不操作」；」
  - 「**硬约束下沉到确定性代码**（ADR-2）：T+1、涨跌停、最小申报单位、仓位上限由代码保证，不托付给 LLM 的概率性输出；」
  - 「**Critic 独立否决权**（ADR-3）：审查者与被审查者角色隔离，否决必须给可核查的理由。」
- 工具返回信封（全工具统一）：`{"ok": true, "data": {}, "error_code": null, "meta": {"source": "...", "as_of": "..."}}`；`error_code` 只允许 8 个枚举：`DATA_MISSING` / `DATA_STALE` / `NOT_TRADABLE` / `GATE_BLOCK` / `WINDOW_CLOSED` / `NO_EVIDENCE` / `DEGRADED` / `INTERNAL`。
- 快速开始：`cd /Users/zenghui/Documents/code/alphadesk` → `cp .env.example .env` → `.venv/bin/python cli.py doctor` → `cli.py tools` → `cli.py ask "长飞光纤今天冲高回落后，能不能做反T？"`
- 运行环境：「⚠️ 运行环境固定为仓库内的 `.venv`（**Python 3.11**）。**不要用系统 `python3`，也不要在 `.venv` 之外装依赖。**」
- 安全红线五条：只读（`read_only=True` / SQLite `mode=ro`）/ 密钥不入库 / 不动宿主运行目录（「不得修改 `/Users/zenghui/.openclaw-autoclaw/workspace/` 下任何文件（仅允许只读 `trading.db`）」）/ 合规边界（human-in-the-loop，ADR-7）/ 中文注释 + 英文标识符。
- ⚠️ **README 里程碑表已陈旧**：表内写 M1–M5 全为「⏳」，但 `docs/` 中已有 T04–T34 共 31 份验收记录、`任务清单与依赖关系.md` 记录验收进度 **34/35**。README 与 docs 的进度陈述不一致。

**E.3.2 `docs/任务清单与依赖关系.md`（687 行，主索引）**

- 生成日期 2026-09-27；工程根 `/Users/zenghui/Documents/code/alphadesk`；环境 `.venv`（Python **3.11.16**）；设计基准 `~/Documents/autoClawFiles/v2.0.1/`。
- **核心纪律**：「**不允许跳步 —— 上游未验收通过，下游不得开工。**」
- §0 现状基线（2026-09-27 实查）：
  - 「`cli.py doctor` → **10 项通过 / 0 警告 / 0 失败**（含 LLM 连通 `deepseek-chat` **499.5ms**）」
  - **数据库规模（原样摘录）**：「行情库 `DuckDB taobao_minute.duckdb` **124.4 GB / 92 表**；持仓库 `trading.db`（`holdings` **31 行**）；知识库 `kb_hits.duckdb`」
  - 「`pytest tests/ -q` → **129 passed**」
  - 「工具注册表 | 已注册 **7/13**」
- 六层 DAG：L0 数据层 D1–D4 / L1 特征层 F1–F3 / L2 策略层 S1–S7 / L3 智能体层 A1–A7 / L4 交付层 V1–V4 / L5 治理层 G1–G5。
- **验收进度 34/35**；「测试用例总数 **738**（0 失败；基线 423 → +T14 29 / T16 39 / T15 33 / T17 29 / T18 16 / T19 25 / T20 16 / T21 10 / T22 27 / T24 15 / T25 3 / T26 2 / T27 5 / T28 2 / T29 4 / T30 5 / T31 25 / T33 9 / T34 21）」
- 逐项验收数字（选摘）：
  - T05：「`features/definitions/*.yaml`（**27**）」；「**PIT 单测 3 例全过**（埋未来行 → 因子值双精度一致）」；「复权口径显式（**hfq 18 / raw 9 / qfq 0**）」
  - T06：「27 因子 / 6 大类」；「全市场 5555 只单日 **17.3s**（目标 ≤300s）」；「`pytest` **214 passed**」
  - T07：「端到端 **1044.5s** = 面板 90.4s + 验证 954.0s，预算 1800s」；「5555 只 / **4,237,953 面板行** / 训练 485 日 / 样本外 178 日 / 预热 133 日」；「最慢因子：`max_drawdown_60d` **420.3s**、`price_percentile_60d` **414.6s**（其余 ≤0.6s）」
  - T07-F1 性能优化：**1044.5s → 121.8s**
  - T08-L4b：regime 修复「旧（regime · 日频 · score）：年化 **−19.54%**｜夏普 −0.37｜回撤 −40.20%｜成本拖累 11.53%｜净值 0.8584」→「新（静态 · 每10日 · score）：年化 **+11.30%**｜夏普 +0.48｜回撤 −31.46%｜成本拖累 3.87%｜净值 1.0781」→「净提升 **+30.84pp**」
  - T09：「真库实跑 5555 只 → Top14、仓位 **94.94%**、成本 **1,227.94 元**」
  - T10：「**T+1 违规 0**（**1118 回合**）」；「真库实跑 178 日 **71.5s**（预算 15min）」
  - T12：「RISK_GATE 唯一收窄点：**exit_code=2 不重试**；{1,3} 回退 hypothesis **最多 2 次**；EVIDENCE→RECON **≤1 次**」
  - T16：「盘前包一屏守卫」；「负样本全被拦：依据截到 2 条 → `[NO_EVIDENCE]`；删 `qty_check` → `[DATA_MISSING]`；失效条件置空 → `[DATA_MISSING]`；`hold` 带数量 → 拒；**`hold` 只留被动条件单 → 「缺少『冲高减仓』主动条件单」**；补回主动单 → 通过」
- 补充 ADR：

  | # | 决策 | 理由（原文） |
  |---|---|---|
  | **ADR-009** | **不重建 ODS/DWD 分层**，改为**薄逻辑视图层**：用 SQL 视图把现有 92 张表映射为设计里的逻辑表名（`stock_daily / stock_minute / flow / adj_factor / calendar`），保留口径字典 | 「淘宝库已是人工整理后的准 DWD 形态；重建 ETL 收益低而踩坑成本极高（表结构/复权口径/备份表混杂）」 |
  | **ADR-010** | **复权口径显式化**：库内 `daily` 为不复权价 + `adj_factor` 提供因子；一切对外输出必须显式声明口径（默认 `hfq` 后复权） | 「历史教训：同名不同源、`技术因子_*.csv` 为后复权却当 qfq 用 → **结论全错**」 |
  | **ADR-011** | **性能守卫强制**：任何 DuckDB 查询前先查 `table_meta`；无过滤 `count(*) / max()` 一律禁止 | 「**124 GB / 54 亿行**库，无过滤全表扫描 **40 s+**」 |
  | **ADR-012** | **持仓与交易口径沿用现有权威源**：持仓 `/…/workspace/trading.db`（`holdings`/`broker_trades`），不新建副本 | 「已有 **31 行**真实持仓与对账单，重建=引入不一致」 |

- DOD 五条（每项结项必须同时满足）：「2. **`pytest` 全绿**（新增用例；**禁止改动已有用例来"通过"**）3. **真实数据实跑**：输出原样粘贴，**禁止造数**……5. 未通过项必须写「未通过 + 原因」，**禁止用"基本可用 / 大致正确"结项**」

**E.3.3 `docs/T04-性能守卫验收记录.md`** —— 「数据基线：行情库 `taobao_minute.duckdb`（**124 GB** / DuckDB，只读），数据边界 **2000-06-09 → 2026-09-24**（`daily` **16,910,750 行**）」；「规模：minute_1min ≈ **5,464,832,071 行（54.6 亿行）**」

**E.3.4 `docs/M0-验收记录.md:69`** —— 「✅ 行情库（只读）：market_db 存在且可读：`/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb`（**124.43 GB**）」；持仓库 `/Users/zenghui/.openclaw-autoclaw/workspace/trading.db`（0.00 GB）；知识库 `/Volumes/My PSSD/stock_data/data/kb_hits.duckdb`（0.00 GB）

**E.3.5 `docs/T05-T06-特征与因子验收记录.md:9`** —— 「行情库 `taobao_minute.duckdb`（**124.4 GB**，只读）；`daily` 2000-06-09 → 2026-09-24（**5555 只**）；资金流表 `stock_flow_em` 最新 **2026-09-22**」

**E.3.6 `docs/T11-工具补齐验收记录.md:324`** —— 「**`get_news` 主数据源缺失**：行情库 **92 张表无新闻表**；财联社接口**已挂**；未接其他免费源 | 默认无源时返回 `DATA_MISSING`（**不造假**）」；「走 `~/.openclaw-autoclaw/workspace/news.db`（**2209 行**，只读）。⚠️ 该库无情感标注列，`sentiment` 由**确定性词典 v1** 生成（非模型预测）」

**E.3.7 `docs/T11-工具补齐验收记录.md:323`** —— 「L1 | **`rag_query` 的结构化知识库为空**：`.../kb_hits.duckdb` 仅 1 张表 `kb_hits`，**0 行**且无文本列 → 该来源 `usable=false`」

**E.3.8 `docs/T33-SQL连接把join推进SQL验收记录.md:8`** —— 「T32 已证：在「分 5 张表取回 + 4 次 pandas merge」架构下，**4.29M 键的哈希成本不可消除**（Categorical 让单次 merge 快 2×，但 5 张表的键转换更贵）。唯一真杠杆 = 把 join 交给 [SQL]」

### E.4 代码规模

| 项 | 值 |
|---|---|
| `.py` 文件数（排除 `.venv/ .git/ __pycache__/ .pytest_cache/`） | **190** |
| `.py` 总行数（同口径） | **47,215** |
| `tests/` 内 `.py` 文件数 | 45 |
| `docs/` 内 `.md` 文件数 / 总字节 | **38 / 643,225 B** |
| `features/definitions/*.yaml` | **27** |
| `agent/nodes/` Python 模块 | 11（含 `__init__` / `_common`）→ **八节点** |
| `agent/tools/` Python 模块 | 11（含 `__init__` / `registry`）→ **13 个注册工具** |
| `agent/llm/` | 仅 `client.py` + `__init__.py`（**不引 LangChain 做 LLM 调用**） |
| `.git` | **存在但零 commit**（见 E.1） |

### E.5 是否可运行

- **运行环境**：`.venv`（Python **3.11.16**）；依赖已装（pydantic / polars / duckdb / pandas / numpy / httpx / structlog / yaml / pytest / apscheduler / langgraph / langchain-core 全部 `find_spec` OK）。
- **入口**：`cli.py doctor`（环境自检，含三库只读连接 + LLM 连通）、`cli.py tools`、`cli.py ask`（最多 5 轮工具循环）、`python -m delivery.demo_run --date 2026-09-23`、`python -m delivery.push`、`python -m strategy.factors.walkforward`。
- **依赖清单完整**：`pyproject.toml`（扁平包结构，**不依赖 `pip install -e .`**，`pythonpath = ["."]`）；唯一占位缺口：`ALPHADESK_LLM_PRICE_IN_PER_1M` / `_OUT_PER_1M` 默认 0 → 成本估算的 USD 维度「仅结构就绪」。
- **真库实跑已发生**（有证据）：`delivery/out/` 内 2026-09-23 的真交付物（cards / premarket / postmortem / trace）；`ops/out/` 内 6 个推送场景 DB + 审计/成本/教训输出；`ops/traces/` 两份 trace jsonl。
- **未运行验证**（按委托要求，**没有重跑 pytest / doctor**）。

### E.6 测试是否存在

- 目录：`/Users/zenghui/Documents/code/alphadesk/tests/`
- **45 个 `.py` 文件**（44 个 `test_*.py` + `__init__.py`）
- **test 函数数量：658**（`grep -rho 'def test_[a-zA-Z0-9_]*'`）；其中 47 处 `parametrize`
- **文档声称**：`任务清单与依赖关系.md:47`「测试用例总数 **738**（0 失败）」；`:685`「`pytest tests/ -q` → **RC=0 / 672 passed**（34 个测试文件；基线 423 例一字未改）」；`:679`「全量 **738 passed / rc=0**」
  → **三个数字（658 实测函数 / 672 / 738）互不一致**，原因未查明（parametrize 展开 + 文档编写时点不同是最可能解释，但**未验证**）
- 测试文件清单（44 个）：`test_adj_single_point` / `test_advice_gate` / `test_audit` / `test_backtest_checks` / `test_backtest_engine` / `test_context` / `test_cost` / `test_delivery` / `test_eval` / `test_factor_parallel` / `test_factor_perf` / `test_factor_perf2` / `test_factors` / `test_features` / `test_graph` / `test_guards` / `test_industry_map` / `test_kb_rag` / `test_lessons` / `test_lessons_concurrency` / `test_md_html` / `test_meta_guard` / `test_news_live` / `test_nodes` / `test_nodes_specialists` / `test_panel_fast_path` / `test_panel_ordering` / `test_panel_payload` / `test_panel_sql_join` / `test_portfolio` / `test_price_basis` / `test_prompts` / `test_push` / `test_push_cli` / `test_push_live_transport` / `test_regime_diag` / `test_rules` / `test_scheduler` / `test_sector_concentration` / `test_signals` / `test_sources` / `test_specialists` / `test_tools_extra` / `test_validate` / `test_walkforward`
- test 函数最多 5 个文件：`test_delivery.py` 39 / `test_nodes.py` 34 / `test_specialists.py` 29 / `test_meta_guard.py` 28 / `test_advice_gate.py` 28
- **未运行**（按委托要求）。

### E.7 可复用组件清单（绝对路径 + 一句话用途）

**L0 数据层**

| 绝对路径 | 用途 |
|---|---|
| `/Users/zenghui/Documents/code/alphadesk/data/sources/base.py` | 数据源抽象基类（统一 `connect()` / 边界声明接口） |
| `.../data/sources/market_duckdb.py` | **DuckDB 行情库适配器（只读）**；`latest_daily_raw()` 是「可交易价」唯一入口（T27） |
| `.../data/sources/holdings_sqlite.py` | **SQLite 持仓库适配器（只读，`mode=ro`）** |
| `.../data/sources/news_online.py` | 在线新闻抓取层（纯标准库，含 `FetchBudget` / `BackoffStop`，**429/403 退避**） |
| `.../data/sources/industry_map.py` | 行业分类适配层（T22，只读） |
| `.../data/gates/quality.py` | **四道数据质量闸门**（指纹对账 / 复权体检 / 派生一致性 / 完整性）+ `assert_gates_ok` |
| `.../data/meta.py` | **性能守卫**：`BIG_TABLES` 10 表 / `guard_sql` / `guarded_query` / `meta_staleness` / `stale_meta_report`（ADR-011 的落点） |

**L1 特征层 / L2 策略层**

| 绝对路径 | 用途 |
|---|---|
| `.../features/registry.py` | **特征声明注册中心**（YAML ↔ 实现一一对应校验：`declared=27 implemented=27 ok=True`） |
| `.../features/definitions/*.yaml`（27 个） | **声明式因子定义**（含 `output.direction` 供方向归一化消费） |
| `.../features/store.py` | **as-of（Point-in-Time）读取契约**（`AsOfViolation` 异常）+ 复权口径定式 |
| `.../features/panel_fast.py` | 面板加载向量化 / SQL 连接路线（T24/T32/T33 的成果所在） |
| `.../strategy/factors/validate.py` | **因子验证**（IC / RankIC / ICIR / t / 分层 10 组 / 多空含成本 / 样本外衰减） |
| `.../strategy/factors/preprocess.py` | 因子预处理（去极值 / 中性化） |
| `.../strategy/factors/walkforward.py` | **walk-forward 复验**（反数据窥探：A/B/C/C′/C⁗/C″ 多口径对照） |
| `.../strategy/signals/compose.py` | **信号合成**：方向归一化 → 因子筛选 → 加权合成 → 证据链（权重只用**训练段 IC**，缺 IC 直接抛错） |
| `.../strategy/signals/regime.py` | **状态自适应**：电风扇 / 弱轮动 / 主线确立 三态判定 |
| `.../strategy/portfolio/optimize.py` | **组合优化**（分数加权 + 迭代约束投影 + 股数取整，numpy 解析水填充，零新依赖、无 RNG） |
| `.../strategy/portfolio/constraints.py` | **组合硬约束（纯代码、零 IO、零依赖）**：最小单位 / 死仓 / T+1 / 仓位上限 |
| `.../strategy/risk/rules.py` | **硬规则风控引擎**（T+1 / 涨跌停 / 最小单位 / 停牌 / ST） |
| `.../strategy/risk/sector.py` | 行业集中度计算（纯函数） |

**回测引擎（可直接复用，与方法论绑定）**

| 绝对路径 | 用途 |
|---|---|
| `.../backtest/engine.py`（61.6 KB / 1325 行） | **事件驱动 + T+1 口径日频回测引擎**（信号 T 日 → T+1 开盘成交，禁当日了结；含成本 0.0015/单位换手 + 滑点可配） |
| `.../backtest/checks.py` | **五项可执行性检查**（`t_plus_1` / `limit_ok` / `lot_ok` / `universe_ok` / `cost_ok`） |
| `.../backtest/metrics.py`（12.9 KB / 340 行） | 统一口径指标：净值 / 年化 / 波动 / 夏普 / 回撤 / Calmar / 胜率 / 换手 / 成本拖累 / `blocked_summary()` / `compare_metrics()` / `format_report()` |

**L3 智能体层**

| 绝对路径 | 用途 |
|---|---|
| `.../agent/llm/client.py` | **LLM 调用**：httpx 直连 OpenAI 兼容接口，自实现退避；**「不缓存响应」**（ADR-000 明确：缓存会把旧数据当新数据） |
| `.../agent/tools/registry.py` | **工具注册表**（唯一接口件）：`ToolSpec` / `register` / `get_tool` / `all_schemas` / `TOOL_NAMES` + `ERROR_CODES` 8 枚举 + `load_errors()` |
| `.../agent/tools/advice_gate.py` | **建议闸门（决策链唯一收窄点）**：四退出码 0/1/2/3 |
| `.../agent/schemas/advice.py` | **建议卡契约**（App. A §A.2 的落点） |
| `.../agent/graph.py`（25,106 B） | **LangGraph 显式状态机**：八节点 + 回退边（闸门失败→HYPOTHESIS ≤2 次）+ 中断/恢复可持久化 |
| `.../agent/nodes/risk_gate.py` | ⑥ RISK_GATE（**唯一收窄点**：`exit_code=2` 不重试；`{1,3}` 回退 ≤2 次） |
| `.../agent/nodes/{recon,hypothesis,evidence,signal,portfolio,narrate,no_action,attribute}.py` | 八节点其余实现（每节点可单测、超时→「不操作」输出） |
| `.../agent/specialists/critic.py` | **Critic 风控 Agent（一票否决 + 必须给可核查理由）** |
| `.../agent/specialists/{macro,sector_flow,technical,portfolio_view,jurisdiction}.py` | **四专家 + 越权裁决**（职责互斥编成可执行规则） |
| `.../agent/specialists/prompts.py` + `.../agent/prompts/{registry,templates,tool_docs,output_schemas}.py` | **版本化提示词**（`PROMPT_VERSION` / `ROLE_PROMPT_VERSIONS` / `all_prompt_versions`） |
| `.../agent/guards/orchestrator.py` + `{data_guard,review_guard,rule_guard,schema_guard}.py` | **四道防护编排器**（越界提问被拒 / 无源数字标〔未证实〕/ 提示词版本化） |
| `.../agent/context/assembler.py` + `{budget,memory,size_guard}.py` | **上下文工程**：三层记忆拼成预算受控上下文 + 尺寸守卫 |

**L4 交付层 / L5 治理层 / 评测**

| 绝对路径 | 用途 |
|---|---|
| `.../delivery/card.py` | **建议卡数据类 / 构造器 / 校验器**（五段：动作 / 依据≥3 带来源时间戳与〔已验证\|推断\|未证实〕/ 执行参数 / 失效条件 / 风险与仓位） |
| `.../delivery/pack.py` | **盘前决策包 + 盘后复盘**（一屏守卫；复盘用**真实成交流水**逐条对齐） |
| `.../delivery/md_html.py`（7,647 B，纯标准库） | **Markdown → HTML 富格式渲染**（标题 / GFM 表格含对齐 / 列表 / 引用 / 行内码；**不放过原始 HTML**） |
| `.../delivery/push.py` | **多渠道推送**（飞书 app / webhook / 备用通道；`max_attempts` + 指数退避；**429 重试、400 不重试**；退出码 0/1/2/3 契约；`FeishuAppChannel.probe()`） |
| `.../delivery/demo_run.py` | 端到端演示（产出 md + html 两版） |
| `.../ops/scheduler.py` | **定时调度与准时率**（APScheduler） |
| `.../ops/trace.py` | **运行轨迹（RunTrace）**：每次运行落一条 JSONL，可审计 / 可回放 / 可统计（上下文管理器） |
| `.../ops/cost.py` | **成本追踪与降级（G4）**：token / 调用预算追踪，超预算自动降级为规则路径 |
| `.../ops/lessons.py` | **教训库（G5）**：入库 + 可检索 + 回灌「待应用建议」（不自动改代码）；含 `flock` 跨进程写锁 + `(size, mtime_ns)` 解析缓存 |
| `.../ops/audit.py` + `.../ops/log.py` | 审计留痕 + 结构化日志（structlog） |
| `.../eval/runner.py` + `.../eval/assertions.py` + `.../eval/loader.py` + `.../eval/golden/cases.jsonl` | **金标准集回归流水线**（规则断言 → 通过率 / 失败明细 / 耗时 / JSON 报告；golden **54/54**） |
| `.../scripts/verify_panel_equiv.py` / `verify_factor_equiv.py` / `verify_layered_equiv.py` / `verify_t25_parallel.py` | **等价性验证脚本**（400/5555 双路 + 逐列 sha256 指纹 A/B） |
| `.../ops/mock_push_demo.py` + `.../scripts/feishu_mock.py` | 推送的本地 mock（URL 注入 429/500/flaky/slow/badjson/tokenfail 六场景） |
| `.../docs/ADR-000-工程约定.md`（205 行） | **接口约定与工程纪律**（并行开发必读；含「M0 明确不做的事」清单） |
| `.../docs/任务清单与依赖关系.md`（687 行） | **主索引 + 每项验收的实测数字 + ADR + 收口结论** |
| `.../docs/T04~T34*.md`（31 份） | 每项验收的完整记录（含失败项与技术债「不粉饰」清单） |

### E.8 被明确否定的设计（原文摘录 + 出处 + 实测数字）

1. **⚠️ T32：两项「有理论依据」的 pandas 侧优化，实测全量都更慢 → 逐字节还原**（**本项目最有价值的负结果**）
   - 「**结论：未达标（已还原）** —— 两项「有理论依据」的 pandas 侧优化**全量实测都更慢**（等价性 ✅、性能 ❌），按「有收益才动」纪律**逐字节还原**」
   - 「① merge 键 object → **共享 categories 因子键**：✅ 全等 | 7.16s → **7.81s（−9.1%，更慢）**」
   - 「② `_finalize_panel`「去重+排序」→ **一次 int64 稳定 argsort**：✅ 全等 | 1.40s → **1.72s（−23.3%，更慢）**」
   - 「③ 合计：8.56s → **9.53s（−11.4%）**」
   - 根因：「**① 的失败不在 merge，而在「转换」本身**：每跑一次都要为 **5 张表**各做一次 `object → Categorical`（或等价的值哈希），**这份哈希成本和「object 键 merge 内部要做的哈希」是同一笔账**；4 次 merge 省下的 ~1.1s 被 5 次转换的 ~1.5s 吃掉，净亏 ~0.4s」
   - 「**关键认识**：在「分 5 张表取回 + 4 次 pandas merge」这个架构下，**4.29M 键的哈希成本不可消除**，只能换架构」
   - 出处：`/Users/zenghui/Documents/code/alphadesk/docs/T32-面板加载三轮-pandas侧微优化负结果.md:1-39`；复述于 `docs/任务清单与依赖关系.md:651-658`

2. **T30：倒排索引经实测**否决** ——「**倒排索引实测否决**：bigram/trigram build **43/46ms**、磁盘 **5.1MB**、load **17/29ms** —— 均**慢于现状**（扫描本身仅 **0.35ms**，成本全在重解析）；且**无进程内消费者** → **不做**。」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:639`；另 `:518`

3. **T26：三条优化路线被微基准否决** ——「**微基准否决 3 条路**：整数键 merge（仅快 **11%**）、`np.searchsorted`（**641ms**，比 merge 慢）、`Categorical.codes`（无差异）→ **都不做**。」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:606`

4. **T28：稠密 scatter/gather 被「够快但不够值」否决** ——「**附（候选①判决）**：稠密 scatter/gather 实测比 merge 快 **2.44×**（**0.145s vs 0.354s**），但折算端到端仅 **~2%** 且需重写连接层（**T24 有过静默污染前科**）→ **已量化，暂不做**。」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:625`

5. **T23：numpy 手写秩路径被自己实测证伪** ——「原「**手写 numpy 秩**」路径已被 T23 自己**实测证伪**（numpy **58ms** vs pandas **51ms**），**不再作为达标路径**」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:571`

6. **T33：三种 SQL 写法被否决留档** ——「**否决留档**：`split_part` 写法 **1.37s** 但 **346 码多匹配** ❌；OR 连接 **6.81s** ❌；CTE+顶层引用被 duckdb binder 拒 ❌。」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:668`

7. **T08-L4c：剔除 4 个「样本外翻转」因子被**明确否决**（数据窥探）**
   - 「🔴 **待决策（本轮未实施，且需要谨慎）**：4 个翻转因子是否同时从**静态池**剔除 → 实测 +11.30% → **+15.48%**（回撤 -31.46% → -24.17%）。⚠️ **但**：这 4 个因子「翻转」是在**同一段样本外**（2026 YTD）上测出来的，据此剔除 = **用样本外信息选因子**（数据窥探）……→ **建议不做一次性剔除，改为滚动重估 / 走 walk-forward 再验证**」
   - walk-forward 三/六口径实测：A 静态 18 全因子 **+11.30%** ｜ B 事后一次性剔 4 个（**不可执行**）**+15.48%** ← **窥探上限** ｜ C 可执行滚动剔除（min_abs_t=0）**−4.92%** ｜ C′ 要求 |t|≥2 **−30.53%** ｜ C⁗ 每次最多剔 4 个 **+2.13%** ｜ C″ 滚动子集+滚动权重 **−11.74%**
   - 「B−A=**+4.18pp**｜C−A=**−16.22pp**｜C⁗−A=**−9.17pp**｜C′−A=**−41.83pp**｜C″−A=**−23.04pp**」
   - 「**结论（采纳）**：🔴 **不剔那 4 个因子** —— 无窥探下真实增益恒为负；+4.18pp 全部来自「事后知道剔谁」。→ 维持现默认（静态全因子 **18** 个 · 每 **10** 日调仓 · scheme=score）；因子池**不做**滚动重估剔除。」
   - 反证：「主张「翻转」的 4 个因子在 C 口径 18 个信号日中被剔 12/9/9/7，而**未入选的** `dist_55d_low` 13 / `ma20_slope_5d` 13 / `momentum_20d` 13 / `price_percentile_60d` 12 / `ma_bull_align` 11 **更频繁** → 「**这 4 个因子特殊」不成立** ✅」
   - 出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:312-366`

8. **ADR-009：重建 ODS/DWD 分层被否** ——「**不重建 ODS/DWD 分层**，改为**薄逻辑视图层**……理由：淘宝库已是人工整理后的准 DWD 形态；**重建 ETL 收益低而踩坑成本极高**（表结构/复权口径/备份表混杂）」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:78`

9. **ADR-010：`技术因子_*.csv` 当 qfq 用被点名（结论全错）** ——「历史教训：同名不同源、`技术因子_*.csv` 为后复权却当 qfq 用 → **结论全错**」
   出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:79`
   实测延伸（T05/T06 遗留复核）：「`adj_factor.hfq_factor` 在 **2026-09-23 全市场口径切换**：9-22→9-23 比值≠1 的标的 **5135/5552（92.5%）**（长飞 `1.0068 → 1.0904`，跳 **8.30%**）；同期 `tech_factor_hfq.adj` 仅 **47/5552** 变化（真实除权）。→ 用 `tech_factor_hfq.adj` 正确，`adj_factor.hfq_factor` 派生会被污染。」（`:167`）
   另：「停牌日 `adj_factor` 基准异常：9-24 有 **139 行** `hfq_factor=1.0`（停牌票），直接做基准会造出假跳变。」（`:168`）
   T29 量化差异：「`_daily_row` 只用 `adj_factor.hfq_factor`（= workspace 速查卡**明令禁用**的源），与面板在 **9-23 之前**最多差 **+16.65%**（000001.SZ 9-16：**1897.25 vs 1626.39**）。」（`:630`）

10. **T27：定价口径错乱造成事故级 bug** ——「`state.positions[*].last_close` 名为「不复权」实为**后复权**……**实测后果**：002384 `pnl_pct` 显示 **+604%**（真实 −7.16%）、603986 显示 **+433%**（真实 −5.75%）；**卡片建议价位差 7.58 倍**。」
    出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:614-615`

11. **T24 的静默数据污染前科被反复引用为风险理由** ——「曾在 T24 造成**静默数据污染**（MaskedArray 掩码丢失 → **NULL 变 0.0**）的细节」
    出处：`/Users/zenghui/Documents/code/alphadesk/docs/T32-面板加载三轮-pandas侧微优化负结果.md:47`

12. **ADR-000：LLM 客户端「不缓存响应」** ——「**边界**：不做 Prompt 拼装、不执行工具、不做流式输出、**不缓存响应**（**缓存会把旧数据当新数据**）。」
    出处：`/Users/zenghui/Documents/code/alphadesk/docs/ADR-000-工程约定.md:158`

13. **ADR-000：禁止抛裸异常让模型瞎猜** ——「**理由**：§6.3「工具三条铁律」——失败必须结构化返回，**禁止抛裸异常让模型瞎猜**。」
    出处：`/Users/zenghui/Documents/code/alphadesk/docs/ADR-000-工程约定.md:133`

14. **README「M0 明确不做」** ——「**M0 明确不做**：Agent 状态机、业务工具、因子、回测、LangGraph 编排（**避免跳步**，见 §10「不允许跳步」）。」
    出处：`/Users/zenghui/Documents/code/alphadesk/README.md:126`

15. **工程纪律类否决（写进 DOD）** ——「**禁止改动已有用例来"通过"**」、「**真实数据实跑**：输出原样粘贴，**禁止造数**」、「**禁止用"基本可用 / 大致正确"结项**」、「**禁止**系统 python3，禁止在 `.venv` 之外装依赖」、「**禁止**把密钥写进 `meta`」
    出处：`/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:88-91`；`docs/ADR-000-工程约定.md:24,85`

### E.9 E 尚未闭合的已知缺口（`docs/任务清单与依赖关系.md:687`，原文「未闭合的已知缺口（不粉饰）」）

- ① 知识库空 / 无新闻源 → **T20 已闭合**（真库 140 行 + 153 个 md / **4,551 切块**可检索）
- ② **行业分类表缺失 → `sector_concentration_after` 恒 `None`（行业上限未做）**
- ③ T14 专家层未接线 → **T21 已闭合**（真实路径真调四专家 + Critic veto→`exit_code=2`）
- ④ **飞书线上实发待凭据**（T34 已闭环到凭据边界：`python -m delivery.push --send` + `--verify-online`）
- ⑤ **ngrok 外网仍 403（免费额度）**

另 `:518` 遗留：① LLM 叙述回放未做（非确定性）② 快照为派生粒度 ③ **真金成本校验未做**（`llm_price_in/out_per_1m` 默认 0 → USD 维度仅结构就绪）④ 回灌不自动改代码。

---

## F. `/Users/zenghui/.duanxian-agents/` 与 `/Users/zenghui/.tradingagents/`（纯运行态数据）

### F.1 `/Users/zenghui/.duanxian-agents/`（由 C `vibe-astock-main` 写入）

**总量与形态**

| 项 | 值 |
|---|---|
| 总大小 | **2.6 MB** |
| 文件总数 | **185** |
| 文件类型 | **全部 185 个都是 `.json`**；**0 个 `.py`** |
| 时间跨度 | 最早 `2026-09-05 23:11` → 最新 `2026-09-24 15:00` |

**一级子目录与体积**

| 绝对路径 | 体积 | 内容 |
|---|---|---|
| `/Users/zenghui/.duanxian-agents/cache/` | **1.9 M** | 派生缓存（**可删可重建**，与 `archive/` 相对） |
| `.../cache/bars/` | — | 31 个文件，命名 `<code>_<start>_<end>.json`（个股 K 线切片） |
| `.../cache/market_facts/` | — | 25 个文件，命名 `YYYY-MM-DD.json`（盘面事实日快照） |
| `.../cache/prev_pool/` | — | 15 个文件（昨日涨停池） |
| `.../cache/zt_summary/` | — | 15 个文件（涨停池摘要） |
| `.../cache/breadth/` | — | 1 个文件（2026-09-04.json） |
| `/Users/zenghui/.duanxian-agents/intraday/` | **336 K** | **14 个交易日**（2026-09-07 ~ 2026-09-24，每日 6 个时点快照） |
| `/Users/zenghui/.duanxian-agents/reviews/` | 120 K | `2026-09-04.json`（59,446 B）+ `latest.json`（59,446 B，同内容） |
| `/Users/zenghui/.duanxian-agents/journal/` | 68 K | `trades.json`（**59,559 B**）+ `synced_ids.json`（5,812 B） |
| `/Users/zenghui/.duanxian-agents/archive/` | 52 K | `archive/2026-09-04/` 下 4 文件：`dt_pool.json` / `prev_pool.json` / `zb_pool.json` / `zt_pool.json`（**原始行归档，永不删除**） |
| `/Users/zenghui/.duanxian-agents/backtest/` | 28 K | `last30.json` |
| `/Users/zenghui/.duanxian-agents/deepdive/` | 24 K | `300454.json`（9,313 B）+ `latest.json`（9,313 B） |
| `/Users/zenghui/.duanxian-agents/modes/` | 8 K | `cards.json`（8,134 B） |
| `/Users/zenghui/.duanxian-agents/weekly/` | 4 K | `latest.json`（3,044 B） |
| `/Users/zenghui/.duanxian-agents/leaders/` | 4 K | `20260904.json`（1,427 B） |

**`intraday/` 详情**：14 个日期目录 `2026-09-07` / `08` / `09` / `10` / `11` / `14` / `15` / `16` / `17` / `18` / `21` / `22` / `23` / `24`；每目录 **6 个时点**：`0925.json` / `0935.json` / `1000.json` / `1130.json` / `1400.json` / `1500.json` → 与 README「快照过点就补不回来，由后台线程按点自动抓」的设计一致。

**是否可复用**：**这是运行态数据，不是代码资产。** 但有**有价值的历史数据**：
- `/Users/zenghui/.duanxian-agents/archive/`（**52 K**，原始行归档，是唯一「口径改了还能重算历史」的依据）
- `/Users/zenghui/.duanxian-agents/journal/trades.json`（**59,559 B**，真实/模拟成交流水）
- `/Users/zenghui/.duanxian-agents/intraday/`（**336 K**，14 日 × 6 时点盘中快照，可用于事后验证「盘中判断 vs 实际」）
- `/Users/zenghui/.duanxian-agents/reviews/`（**120 K**，2 份完整复盘产物，594 KB 级的单份 JSON）
- 无 README / 配置说明类文本文件。

### F.2 `/Users/zenghui/.tradingagents/`（由 B `TradingAgents-astock-main` 写入）

**总量与形态**

| 项 | 值 |
|---|---|
| 总大小 | **2.4 MB** |
| 文件总数 | **18** |
| 文件类型 | 9 `.csv` / 8 `.json` / **1 `.md`**；**0 个 `.py`** |
| 时间跨度 | 最早 `2026-09-05 23:26` → 最新 `2026-09-08 01:49` |

**一级子目录与体积**

| 绝对路径 | 体积 | 内容 |
|---|---|---|
| `/Users/zenghui/.tradingagents/logs/` | **2.1 M** | 8 个代码目录（`000519` / `000876` / `002185` / `002714` / `300454` / `600519` / `600975` / `600988`），每目录下 `TradingAgentsStrategy_logs/full_states_log_<date>.json`（`600519` 那份 **299,308 B**）—— **完整 Agent 状态机全量日志** |
| `/Users/zenghui/.tradingagents/cache/` | 288 K | 8 个 `<code>-astock-daily.csv`（各 31,937 ~ 39,237 B）+ `northbound_daily.csv`（89 B，**3 行数据**：表头 + 2026-09-05/06/08） |
| `/Users/zenghui/.tradingagents/memory/` | 24 K | `trading_memory.md`（**138 行**） |

**`memory/trading_memory.md` 形态**：结构为 `[日期 | 代码 | 评级 | 状态]` 分块 + `DECISION:` 段（`**Rating**` / `**Executive Summary**` / `**Investment Thesis**` / `**Time Horizon**`）+ `<!-- ENTRY_END -->` 分隔符。摘要中提到：
- `[2026-09-04 | 600519 | Underweight | pending]`
- `[2026-09-04 | 600988 | Hold | pending]`
- `[2026-09-04 | 300454 | Underweight | ...]`
→ 与 B 的 `CLAUDE.md`「`TradingMemoryLog` 的标签格式会直接打断绩效统计（依赖 `[日期 | 代码 | 评级 | raw | alpha | holding]` 结构，且 holding 带 `d` 后缀）」部分吻合；**本机这份记忆文件里的标签只有 4 段（日期|代码|评级|pending），未见 `raw`/`alpha`/`holding` 字段**（该差异未查明，可能因写入时点为早期版本）。

**是否可复用**：**运行态数据，不是代码资产。** 有价值部分：
- `/Users/zenghui/.tradingagents/logs/<code>/TradingAgentsStrategy_logs/*.json`（**2.1 MB**，8 只标的的完整状态机全量日志 —— 是「Agent 每一步看到了什么、怎么辩论的」的原始证据，可用于复盘多 Agent 编排的真实行为）
- `/Users/zenghui/.tradingagents/memory/trading_memory.md`（**138 行**，决策记忆与绩效统计的输入）
- 无 README / 配置说明类文本文件。

---

## G. `/Users/zenghui/.openclaw-autoclaw/`（**只看顶层结构与配置文件名清单**）

> 按委托要求，**未读取其决策体系细节**（未打开 `openclaw.json` / `AGENTS.md` / `MEMORY.md` / `TOOLS.md` 等的内容）。

### G.1 总量

| 项 | 值 |
|---|---|
| 总大小 | **40 GB** |
| 顶层 `ls -la`（无 `.git`） | 73 个条目 |

### G.2 顶层一级子目录与体积

| 绝对路径 | 体积 |
|---|---|
| `/Users/zenghui/.openclaw-autoclaw/workspace/` | **33 G** |
| `.../agents/` | **4.9 G** |
| `.../media/` | **1.0 G** |
| `.../autoclaw/` | 213 M |
| `.../skills/` | 197 M |
| `.../state/` | 72 M |
| `.../browser/` | 63 M |
| `.../logs/` | 52 M |
| `.../internal-agent-runs/` | 9.0 M |
| `.../extensions/` | 2.6 M |
| `.../cron/` | 2.1 M |
| `.../skill-workshop/` | 792 K |
| `.../qqbot-data/` | 284 K |
| `.../sessions/` | 244 K |
| `.../memory/` | 68 K |
| `.../mcp-oauth/` · `.../office-plugin-tls/` · `.../npm/` · `.../workspace-attestations/` | 12–16 K 各 |
| `.../credentials/` · `.../devices/` · `.../hooks/` · `.../identity/` · `.../cache/` | 8 K 各 |
| `.../qqbot/` | 4.0 K |
| `.../plugin-skills/` | **0 B** |

### G.3 顶层配置文件文件名清单（**只报文件名 + 字节数**）

| 文件名（绝对路径 = `/Users/zenghui/.openclaw-autoclaw/<名>`） | 字节 |
|---|---|
| `service.log` | 28,428,403 |
| `service.log.1` | 19,215,508 |
| `expert-sop-last-known-good.json` | 30,404 |
| `session-goals.json` | 55,770 |
| `openclaw.json` | 20,225 |
| `openclaw.runtime.json` | 20,153 |
| `openclaw.runtime.json.last-good` | 20,153 |
| `openclaw.runtime.json.bak` | 20,156 |
| `openclaw.runtime.json.bak.1` | 20,153 |
| `openclaw.runtime.json.bak.2` | 20,006 |
| `openclaw.runtime.json.bak.3` | 18,683 |
| `openclaw.runtime.json.bak.4` | 18,588 |
| `openclaw.json.known-good` | 19,402 |
| `openclaw.json.bak-bind-20260816` | 16,125 |
| `openclaw.json.bak-qq-20260816` | 15,857 |
| `openclaw.json.bak_0816` | 15,805 |
| `openclaw.json.last-good` | 12,851 |
| `pending_result.json` | 12,896 |
| `expert-sop-im.txt` | 10,292 |
| `.DS_Store` | 12,292 |
| `session_pool.json` | 2,845 |
| `request-headers.json` | 2,363 |
| `browser_result_config_required.md` | 741 |
| `legal-jurisdictions.runtime.json` | 665 |
| `compact-threshold-config.json` | 271 |
| `compact-threshold-config.json.bak-20260820` | 271 |
| `agent-project-read-roots.json` | 250 |
| `exec-approvals.json` | 189 |
| `.pkulaw-proxy-capability.json` | 127 |
| `.qichacha-proxy-capability.json` | 129 |
| `config.json` | 117 |
| `.visible-browser-tool-access.json` | 77 |
| `.gateway-token` | 64 |
| `service_api_secret` | 64 |
| `skills-tombstones.json` | 55 |
| `agent-team-sessions.json` | 50 |
| `safety-approval-endpoint.json` | 48 |
| `goal-mode-sessions.json` | 36 |
| `client-sign.json` | 22 |
| `vault-roots.json` | 17 |
| `active_port` | 5 |
| `.session_pool.lock` / `service.lock` | 0 |

### G.4 二级配置文件文件名清单（`find -maxdepth 2`，**只报文件名 + 路径**）

```
./credentials/feishu-default-allowFrom.json
./credentials/feishu-pairing.json
./cron/jobs.json
./devices/paired.json
./devices/pending.json
./identity/device-auth.json
./identity/device.json
./logs/config-health.json
./skill-workshop/proposals.json
./mcp-oauth/connector-ima-f704f353d5b7a97b.json
./mcp-oauth/connector-lexiang-094cdba65a1e9a53.json
./mcp-oauth/connector-tianyancha-1f40f7185e0c4509.json
./mcp-oauth/tyc-mcp-8e3d90e67197a753.json
./workspace/.finance-tool-capability.json
./workspace/.jw-proxy-capability.json
./workspace/.legal-proxy-capability.json
./workspace/.tyc-proxy-capability.json
./workspace/openclaw-workspace-state.json
./workspace/stock-pool-break-box-0715.json
./workspace/stock-pool-break-box.json
./workspace/stock-pool.json
./workspace/watchlist.json
./internal-agent-runs/<uuid>.trajectory-path.json   × 多份
```

**`cron/` 目录的备份/迁移文件命名（只报文件名）**：`jobs.json.bak` / `jobs.json.bak-20260929-235012` / `jobs.json.bak-20261002-xianshou` / `jobs.json.bak-20261005-195844` / `jobs.json.bak-20261006` / `jobs.json.migrated` / `jobs.json.migrated.2` ~ `.migrated.16` / `.migrated.37` ~ `.migrated.39`；另有 `cron/_bak/` 子目录。

### G.5 委托关注的子目录

- **`skills/`**：**118 个一级子目录**（197 M）。名称抽样：`a-share-screener` / `a-stock-analysis` / `a-stock-data` / `akshare-finance` / `autoglm-stock-analysis` / `book-signal-library` / `book-to-skill` / `code-understand` / `claude-history-ingest` / `codex-history-ingest` …
- **`workspace/`**（**33 G**，71 个一级条目），与本次调研直接相关的事实：
  - `workspace/trading.db` = **167,936 B** ← **alphadesk / E 的红线引用对象**（M0 记录里写作「0.00 GB」，与 167 KB 一致）
  - `workspace/trading.db.bak_0902_cleanup` = 69,632 B
  - `workspace/news.db` = **3,448,832 B** ← alphadesk T11 引用的新闻源（文档称 2209 行）
  - `workspace/stock.db` = **0 B**
  - `workspace/holdings.json.deprecated` = 854 B（已弃用的旧持仓文件）
  - `workspace/` 内有 `AGENTS.md`（15,230 B）+ `AGENTS.md.bak_20261010_1531`、`IDENTITY.md`、`MEMORY.md`（14,200 B）、`SOUL.md`、`TOOLS.md`（**31,700 B**）、`USER.md`、`HEARTBEAT.md`（244 B）
  - `workspace/` 内含 **`baku_knowledge/`（47 个条目）** ← A 的 L3 知识库
  - `workspace/scripts/`（**387 个条目**）、`workspace/state/`（114）、`workspace/memory/`（202）、`workspace/reports/`（15）、`workspace/html/`（136）、`workspace/deliverables/`（28）
  - `workspace/.git` **存在**
- **`agents/`**（4.9 G）：16 个 agent 子目录，含 `main` / `stock` / `analyst` / `intel` / `scout` / `feishu-agent` / `auto-legal` / `auto-designer` / `auto-smb` / `agent-ej6h8` / `agent-kunuomi` / `cloud-*`
- **`memory/`**（68 K）、**`state/`**（72 M）、**`logs/`**（52 M）均存在
- **`plugin-skills/`** = **0 B**（空目录）

---

## H. 跨项目专项：数据库规模与表数的说法（**原样摘录，不合并不同来源**）

### H.1 所有出现过的数字（逐条标注出处）

| 出处（绝对路径:行） | 原文摘录 |
|---|---|
| `/Users/zenghui/Documents/quantInvest/USER.md:34` | 「数据源 \| 外置盘 PSSD 上的 duckDB（**124GB**，分钟+日线+财务全量）」 |
| `/Users/zenghui/Documents/quantInvest/docs/specs/02-业务架构.md:38` | 「PSSD duckDB（**90 表，71 亿行**）+ 列名映射 + 数据质量闸门」 |
| `/Users/zenghui/Documents/quantInvest/docs/specs/02-业务架构.md:51-52` | 「体积 \| **124 GB / 71.2 亿行**」「表数 \| **90 张**」 |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/data-dictionary.md:4` | 「实测：**124GB / 71.2 亿行 / 90 张表** ｜ 验证日期 2026-09-26」 |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/index.md:16` | 「查数据表结构 \| `data-dictionary.md` \| **92 张表** + 中文列名映射 + 外部数据源」 |
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/data-dictionary.md:80` | 「涨跌停幅度实测分布（2026-09-24，**5563 只**）：5%→142 只(ST) / 10%→3046(主板) / 20%→2021(创业板+科创板) / 30%→346(北交所)」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:15` | 「行情库 `DuckDB taobao_minute.duckdb` **124.4 GB / 92 表**；持仓库 `trading.db`（`holdings` **31 行**）」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:78` | 「用 SQL 视图把现有 **92 张表**映射为设计里的逻辑表名」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:80` | 「**124 GB / 54 亿行**库，无过滤全表扫描 40 s+」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/T04-性能守卫验收记录.md:6` | 「行情库 `taobao_minute.duckdb`（**124 GB** / DuckDB，只读），数据边界 2000-06-09 → 2026-09-24（`daily` **16,910,750 行**）」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/T04-性能守卫验收记录.md:38` | 「规模：minute_1min ≈ **5,464,832,071 行（54.6 亿行）**」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/T05-T06-特征与因子验收记录.md:9` | 「行情库 `taobao_minute.duckdb`（**124.4 GB**，只读）」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/M0-验收记录.md:69` | 「market_db 存在且可读：`.../taobao_minute.duckdb`（**124.43 GB**）」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/T11-工具补齐验收记录.md:324` | 「行情库 **92 张表无新闻表**」 |
| `/Users/zenghui/.dsh/im/assets/PLAN-02-agent-architecture.html:104` | 「主库规模 \| **133.6**GB \| **81 基表 + 48 视图** · 只读」 |
| `/Users/zenghui/.dsh/im/assets/PLAN-02-agent-architecture.html:156` | 「表/视图 \| `information_schema` **82**（基表 **81** + 视图 1）；`duckdb_tables()` **81**；`duckdb_views()` **48**；`bak_*` **9**」 |
| `/Users/zenghui/.dsh/im/assets/PLAN-02-agent-architecture.html:131` | 「PSSD taobao_minute.duckdb / **133.6 GB · 81 基表** / 分钟 **54.7 亿行**」 |

### H.2 ⚠️ 必读标注（按委托要求逐条附上）

> **上述所有 **124 GB / 124.4 GB / 124.43 GB / 90 表 / 92 表** 的说法，均源自 2026-09-26 ~ 2026-09-27 的文档记录。这些数字与 2026-10-12 实测（**133.6GB / 81 基表**）不一致，原因未查明。**

**本报告额外实测到的两点（供委托人判断，未据此修改上述标注）：**

1. **GB 数值的差异可以用单位制解释，但需委托人确认是否就是同一原因。**
   本报告以只读 `ls -la` 实测（未打开数据库）：
   ```
   /Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb
   133,608,517,632 bytes   mtime = Oct 12 23:06
   ```
   换算：
   - `133,608,517,632 / 1024³ = 124.43 GiB` ← 与文档中的 **124.43 GB / 124.4 GB / 124 GB** 吻合
   - `133,608,517,632 / 1000³ = 133.61 GB` ← 与 2026-10-12 的 **133.6 GB** 吻合
   → **即：两份数字极可能指向同一个文件，差异来自 GiB（1024 进制）与 GB（1000 进制）的混用。** 这一点**未被任何文档写明**，属本报告新增发现，**未经委托人确认**。
2. **表数差异（90 / 92 → 81 基表）无法用单位制解释，仍然原因未查明。** 可能的解释有三类（**均为未验证的推断**）：(a) 库在 9-27 ~ 10-12 之间被重建/清理过；(b) 90/92 的口径是「含视图/含 `bak_*`」，而 81 是 `duckdb_tables()` 的纯基表口径（注意 2026-10-12 记录本身写了「`bak_*` **9**」与「视图 **48**」——`81 + 9 = 90`，与 A 的「90 表」吻合；`81 + 9 + ...` 或 `information_schema` 口径 82 与 92 的关系不明确）；(c) 两次统计的库路径不同（A 的 `config.py` 写的是 `.../本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb`，2026-10-12 记录的是同一个路径）。
   **请委托人自行裁定，本报告不做合并。**

### H.3 分钟行数也不一致（同样不合并）

| 来源 | 数字 |
|---|---|
| `/Users/zenghui/Documents/quantInvest/skills/quant-advisor/references/data-dictionary.md:13` | `minute_1min` 「**54.2 亿行**」 |
| `/Users/zenghui/Documents/code/alphadesk/docs/T04-性能守卫验收记录.md:38` | 「minute_1min ≈ **5,464,832,071 行（54.6 亿行）**」 |
| `/Users/zenghui/.dsh/im/assets/PLAN-02-agent-architecture.html:131` | 「分钟 **54.7 亿行**」 |
| `/Users/zenghui/Documents/quantInvest/docs/specs/02-业务架构.md:54` | 「1min **54.2 亿行**」 |

### H.4 各项目对「是否有本地库」的定位

| 项目 | 是否有本地数据库 |
|---|---|
| A `quantInvest` | **有**（依赖外部 PSSD 上 124GB 级 DuckDB） |
| B `TradingAgents-astock-main` | **没有**。`CLAUDE.md`：「数据层（v0.2.5 全部直连 HTTP，**零第三方数据库依赖**）」 |
| C `vibe-astock-main` | **没有仓库内库**；只用 `~/.duanxian-agents/` 的 JSON 缓存/归档 + 外部 SQLite（`sync_tradingdb.py`） |
| D `a-stock-data-main` | **没有**。纯在线 API 工具包（22 个数据源全直连） |
| E `alphadesk` | **有**（三个只读库：market_db 124GB 级 DuckDB / holdings_db `trading.db` / kb_db `kb_hits.duckdb`） |

---

## I. 跨项目专项：东财接口限流阈值与「403 不重试」铁律的收敛情况

### I.1 出现位置一览（共 **5 处**，跨 **3 个项目**）

| # | 位置（绝对路径:行） | 形态 |
|---|---|---|
| 1 | `/Users/zenghui/Documents/code/a-stock-data-main/SKILL.md:250-260` | **阈值表**（权威来源，逐项列全 5 行） |
| 2 | `/Users/zenghui/Documents/code/a-stock-data-main/SKILL.md:282-292` | **防封铁律 5 条 + `em_get()` 说明** |
| 3 | `/Users/zenghui/Documents/code/a-stock-data-main/SKILL.md:607-618` | **代码注释 + `Retry` 配置**（含「403 不重试」原文） |
| 4 | `/Users/zenghui/Documents/code/TradingAgents-astock-main/tradingagents/dataflows/a_stock.py:539-546` | **代码注释**（阈值 + 口径，移植自 #2） |
| 5 | `/Users/zenghui/Documents/code/TradingAgents-astock-main/CLAUDE.md`（东财防封段） | **工程纪律**（v0.2.11 新增，移植自 a-stock-data v3.2） |

**未收敛的项目**：C `vibe-astock-main`（只用 `push2delay` 镜像规避，**无任何限流阈值**）、E `alphadesk`（**完全不碰东财**——数据全部来自本地 PSSD DuckDB + 本地 `trading.db` / `news.db`；`data/sources/news_online.py` 只对**新闻抓取**做 `FetchBudget` / `BackoffStop`）。

### I.2 阈值原文（**权威表**：`a-stock-data-main/SKILL.md:250-260`）

```
### 东财风控阈值（社区实测，2026-05）

| 行为 | 触发封禁的阈值 | 风险 |
|------|---------------|------|
| 每秒请求数 | > 5 次/秒 | 高 |
| 单 IP 并发连接 | ≥ 10 | 高 |
| 1 分钟请求总数 | ≥ 200 次 | 中高 |
| 5 分钟请求总数 | ≥ 300 次 | 触发封禁 |
| User-Agent | 空 UA / 无浏览器特征 | 中 |

被封表现：连续请求后 `403` / `429` / 连接超时 / 返回空数据。临时封禁通常几分钟到几小时。
```

### I.3 「403 不重试」铁律原文（`a-stock-data-main/SKILL.md:614-621`）

```python
# 连接级自动重试：瞬态连接错误 / 429 / 5xx 指数退避重试（住宅IP偶发风控更稳）。
# 注意：403 不重试（东财风控信号，重试无益反而加重；按下方 EM_MIN_INTERVAL 降频应对）。
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _em_adapter = HTTPAdapter(max_retries=Retry(
        total=3, connect=3, backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"]))
```

执行层面的一致性：`status_forcelist` **只含 `[429, 500, 502, 503, 504]`，不含 403** —— 代码与注释一致。

### I.4 防封铁律 5 条原文（`a-stock-data-main/SKILL.md:282-288`）

```
1. **串行，不并发**——绝不对东财开多线程/协程并发请求
2. **每次间隔 ≥ 1 秒 + 随机抖动**（QPS ≤ 2），批量筛选时调大到 1.5~2 秒
3. **复用 HTTP 会话**（Keep-Alive），不要每次新建连接
4. **带正常 UA + Referer**（本 SKILL 各端点已配好）
5. **批量场景每只股票之间 sleep**——AI 跑批量循环（如筛选 100 只股逐个拉龙虎榜/资金流）是被封的头号元凶
```

### I.5 实测封禁案例（`a-stock-data-main/SKILL.md:262-272`，一手数据）

- 「**触发方式**：选股脚本 **10 线程并发**、**完全不走 `em_get()` 限流**，1 小时内发出 **45000+ 请求**（三个版本的脚本同时跑全市场 5208 只）」
- 「**后果**：`push2` / `push2his` **全系列** `RemoteDisconnected`，**IP 级封禁持续 20+ 小时**——不是"几分钟到几小时"那种临时限速」
- 「**关键观察一**：`datacenter-web.eastmoney.com` **不受影响**——东财不同子域走不同 WAF」
- 「**关键观察二**：**腾讯 K 线（`web.ifzq.gtimg.cn`）连续 5000+ 次后会返回空**，但这是**限流不是封 IP**」
- 「**降级实测**：东财被封时，第一只股票花 **10.9s** 完成"检测被封 + 降级"，之后每只 **0.4s** 走腾讯」
- 「**这个案例正是「限流是铁律」的实证**：`em_get()` 的默认间隔（1s + 抖动、串行）下，1 小时最多约 **3000 次**请求，与踩坑者的 45000 次**差一个数量级**。」

### I.6 实现一致性（三处 `em_get` 对比）

| 实现 | 最小间隔 | 抖动 | 会话复用 | 默认 UA | 自动重试 |
|---|---|---|---|---|---|
| `a-stock-data-main/SKILL.md` `em_get()` | `EM_MIN_INTERVAL = 1.0` | `random.uniform(0.1, 0.5)` | `EM_SESSION` | `UA`（Mac Safari UA） | `Retry(total=3, connect=3, backoff_factor=0.6, status_forcelist=[429,500,502,503,504])` |
| `TradingAgents-astock-main/a_stock.py` `_em_get()` | `_EM_MIN_INTERVAL = float(os.environ.get("EM_MIN_INTERVAL", "1.0"))`（**可用环境变量覆盖**） | `random.uniform(0.1, 0.5)` | `_EM_SESSION` | `_UA`（**同一个 Mac Safari UA 字符串**） | **无**（只做节流，未挂 Retry adapter） |

→ **参数已收敛，实现有 1 处实质差异**：B 的 `_em_get()` **没有挂 `Retry` adapter**，所以 B 的东财请求**连 429/5xx 都不自动重试**。B 的 `CLAUDE.md` 未记录这一差异。

### I.7 ⚠️ 收敛情况的三个具体裂缝

1. **阈值清单在「表」与「代码注释」之间不完整收敛。**
   - `a-stock-data-main/SKILL.md:250-260` 表里是 **5 行**（含「5 分钟请求总数 ≥ 300 次」）。
   - 同文件 `:609` 的代码注释是 **3 项**：「每秒 >5 次 / 单 IP 并发 ≥10 / **1 分钟 ≥200 次** → 临时封 IP」—— **漏了「5 分钟 ≥300 次」这一行**。
   - 而 **B（`a_stock.py:539-541`）的代码注释反而是完整的 4 项**：「每秒 >5 次 / 单 IP 并发 ≥10 / 1 分钟 ≥200 次 / **5 分钟 ≥300 次** → 临时封 IP」。
   → 即：**下游（B）比上游（D 的代码注释）更准确**；D 的表格与自己的代码注释不一致。
2. **「1 分钟 ≥200 次」与「5 分钟 ≥300 次」在数学上互相冲突**（若严格满足前者，5 分钟上限应为 1000 次）。文档未解释两者关系，也未说明哪个优先。**未收敛。**
3. **C `vibe-astock-main` 完全没有采纳这套铁律**，它的应对是换域名（`push2delay` 而非 `push2`）：
   `duanxian/fetchers.py:5-6`「→ **push2delay.eastmoney.com** 的 clist 接口（**push2.eastmoney.com 在部分网络下被重置，故用 delay 镜像**）」；
   `README.md:451`「腾讯 hist `stock_zh_a_hist_tx` \| K 线与交易日历（**部分网络下东财 push2his 被封，故走腾讯**）」
   → 这是「换源」路线，与 D/B 的「限流」路线**并行且未交叉引用**。

### I.8 其他项目里出现的 403（语义不同，不要混为一谈）

| 位置 | 含义 |
|---|---|
| `/Users/zenghui/Documents/code/vibe-astock-main/duanxian/fetchers.py:97` | **本机代理把东财路由挂掉**导致的 403（环境问题，非风控封禁） |
| `/Users/zenghui/Documents/code/alphadesk/docs/任务清单与依赖关系.md:687` | 「⑤ **ngrok 外网仍 403**（免费额度）」——与本主题无关 |
| `/Users/zenghui/Documents/code/alphadesk/tests/test_push_live_transport.py:120-133` | **飞书推送**的 429 重试 / **400 不重试**（非东财） |

---

## J. 跨项目结论：资产盘点表

| 路径 | 形态 | 状态 | 可复用度 | 关键结论 |
|---|---|---|---|---|
| `/Users/zenghui/Documents/quantInvest/` | AutoClaw 技能工作区（提示词 + 确定性脚本，**无依赖清单**） | 骨架完成、**从未跑过一次完整决策闭环**（`decision_log.jsonl` 0 行 / `holdings` 空数组 / `memory/*` 空目录）；8 处文档指向的文件不存在 | **中高**（规则与方法论极高；代码需补断链） | 唯一一套写清了「A 股制度事实 → 确定性代码」的**契约级**资产（`advice.py` + `advice_gate.py` + `trading_rules.py` + `reject_ladder.py` + `evidence_audit.py` + `decision_log.py`，共 1,135 行）。设计文档六份 62.8 KB，含 151 条错误的机制映射表与覆盖率（**97/151 = 64%**）。**注意：否决分级 / 双向输出 / 证据审计 / 闭环对账这四件事，A 的设计最细，E 的实现最实。** |
| `/Users/zenghui/Documents/code/TradingAgents-astock-main/` | 独立 Python 包（LangGraph 多 Agent 投研，121 py / 20,244 行） | **可运行**（`main.py` + `cli/` + `web/`；pyproject 完整；`.venv` 就绪）；测试基线 **361 passed / 13 skipped**（自述，本次未跑）；无 `.git` | **高** | **A 股数据源连接器最完整的一份**（`dataflows/a_stock.py` **2,463 行**，覆盖 mootdx/腾讯/东财 7 个端点/新浪/同花顺/财联社/百度）。多 Agent 编排（7 Analyst + Bull/Bear + 三方风险辩论 + Portfolio Manager）、`quality_gate.py`、`rating.py`、`memory.py`、`performance.py`、`llm_clients/` 多 provider 工厂均可直接复用。**`CLAUDE.md`（10,975 B）是一份罕见的、可交给下一个 agent 的「血的教训 + 工程纪律」清单**（13 条实测否决记录）。已知硬伤：mootdx 钉死 `httpx<0.26`，与 Google Gemini 依赖**结构性冲突、无解**。 |
| `/Users/zenghui/Documents/code/vibe-astock-main/` | 全栈应用（FastAPI `server.py` 67 KB + React19/Vite/TS 前端，66 py / 23,677 行 + 44 个 ts/tsx） | **可运行**（`main.py` CLI 复盘 / `server.py` / `frontend/dist` 已构建）；**测试最厚**（单文件 349 KB / **523 例**，README 称 533）；无 `.git` | **高** | **边界纪律最严的一份**：「不推荐个股、不给参与倾向、不给买卖点位；方向与情绪判断做到板块层面为止」；「九成是硬指标层、纯计算、不经过 AI」。**可复用度最高的三样**：① `duanxian/fetchers.py`（628 行自包含取数层 + 罕见的「进程级代理改动会波及别人」反面教材 40 行注释）；② `archive.py` + `drift.py`（原样行归档 + 数据源变/市场结构变/制度变三分类）；③ `verification.py`（带基准值与阈值的可对账验证条件）。**它也是唯一把「个人交易数据一律不得进 prompt」写成两处代码注释 + 一组专项测试的项目。** |
| `/Users/zenghui/Documents/code/a-stock-data-main/` | **单个 `SKILL.md`（232 KB / 4,552 行，含 106 个内嵌 Python 函数）** + 28 KB README + 59 KB CHANGELOG | **可运行**（作为 skill 注入 AI 助手；`tests/test_official_data.py` 用 `exec()` 直接测 SKILL.md 内嵌代码，**说明内嵌代码是可执行的真代码**）；无 `.git`、无依赖清单 | **极高（作为数据源知识库）／中（作为代码）** | **12 层 · 60 端点 · 22 数据源 · 零鉴权** 的 A 股数据获取知识库。**最有价值的不是端点数量，而是「东财防封」这一整套工程规范**（阈值表 + 实测封禁案例 + 5 条铁律 + `em_get()` 参考实现 + 降级路径表 + `403 不重试` 原文）——已被 B 移植采纳。次要价值：`docs/source-integration-v3.8.0.md`（88 行数据源取舍判据，含「上游数据出处不够清楚，暂不接入」这类明确拒绝）。**注意：它是唯一有「测试 SKILL.md 内嵌代码」范式的项目。** |
| `/Users/zenghui/Documents/code/alphadesk/` | 独立 Python 包（六层架构 + LangGraph 八节点 + 四专家 + Critic；**190 py / 47,215 行**；38 份验收文档 / 643 KB） | **可运行且已真库实跑**（有 2026-09-23 的真交付物）；**测试 45 文件 / 658 个 test 函数**（文档自称 738 / 672，**三个数字不一致**）；**⚠️ git 零 commit，47,215 行全未跟踪** | **极高（本项目群最强）** | 六个项目里**唯一做到「工程闭环」**的：DOD 五条（`py_compile` + `pytest` 全绿 + **真实数据实跑、禁止造数** + 更新状态列 + **禁止「基本可用」结项**）、每项独立复跑、**不采信 Worker 自述**。**可复用清单最长的项目**（数据源适配器 / 四道质量闸门 / 性能守卫 / 27 声明式因子 / 因子验证 + walk-forward / 信号合成 + 三态 regime / 组合优化 + 硬约束 / 回测引擎 + 五查 / 13 工具 + 建议闸门 / 八节点状态机 / 四道防护 / 上下文工程 / 建议卡 + 决策包 + md_html 渲染 / 多渠道推送 + 调度 / trace + 成本降级 + 教训库 / 金标准集评测）。**并且留下了本项目群最有价值的一批「负结果」**（T32 / T30 / T26 / T23 / T28 / T33 六份实测否决，全部带数字）。**最大风险：没有一次 commit。** |
| `/Users/zenghui/.duanxian-agents/` | 纯运行态数据（**185 个 json，0 个 py，2.6 MB**，2026-09-05 → 09-24） | 由 C 写入；**不是代码资产** | **低（数据）／中（历史证据）** | 有**唯一一份「原样行归档」**（`archive/` 52 K）和 **14 日 × 6 时点的盘中快照**（`intraday/` 336 K）—— 是「盘中判断 vs 实际结果」事后归因的原始材料。`journal/trades.json`（59,559 B）是真实/模拟成交流水。 |
| `/Users/zenghui/.tradingagents/` | 纯运行态数据（**18 文件，2.4 MB**，2026-09-05 → 09-08） | 由 B 写入；**不是代码资产** | **低（数据）／中（编排证据）** | `logs/<code>/TradingAgentsStrategy_logs/full_states_log_*.json`（**2.1 MB / 8 只标的**）是多 Agent 状态机每一步的**全量原始日志**，可用于复盘多 Agent 编排的真实行为。`memory/trading_memory.md`（138 行）是绩效统计的输入（但其标签格式只有 4 段，与 B 文档描述的 `[日期\|代码\|评级\|raw\|alpha\|holding]` **不符**，未查明）。 |
| `/Users/zenghui/.openclaw-autoclaw/` | 宿主运行目录（**40 GB**） | 活跃运行中（`service.log` 28 MB，mtime Oct 12 23:23） | **低（作为资产）／关键（作为依赖）** | 与本次调研的三个硬关联：① `workspace/trading.db` = **167,936 B**，是 **E 的持仓权威源（只读红线）**；② `workspace/news.db` = **3,448,832 B**，是 **E 的新闻源兜底**；③ `workspace/baku_knowledge/`（47 项）是 **A 的 L3 知识库**（`~/Documents/baku_knowledge/` 亦存在）。**配置备份堆积严重**：顶层 5 份 `openclaw.json*` + 6 份 `openclaw.runtime.json*`；`cron/` 下 `jobs.json.migrated.*` 共 **19 份** + 5 份 `jobs.json.bak*`。`plugin-skills/` 为 **0 B 空目录**。 |

---

## K. 给下一步的三条硬提示

### 提示 1：先决定「哪一套契约做基线」，不要在六套之间再做一次横向对比

现状是**同一件事有 2–3 套并行实现，且各有一半对**：

- **建议卡契约**：A 的 `src/quant/contracts/advice.py`（260 行，含 `AdviceCard`/`Side`/`Evidence`/`GateExit`/`BlockKind`）**与** E 的 `agent/schemas/advice.py` + `delivery/card.py`（五段式 + 字段级校验 + `qty_check`）。
- **闸门**：A 的 `advice_gate.py`（七查 + 退出码 0/1/2/3 + 完整 A 股日内窗口表）**与** E 的 `agent/tools/advice_gate.py`（四查 + 同套退出码）。
- **A 股制度规则**：A 的 `trading_rules.py`（202 行，板别/最小单位/T+1/涨跌停/停牌/退市整理期，**带 34 例单测**）**与** E 的 `strategy/risk/rules.py` + `backtest/checks.py`。
- **否决分级**：A 的 `reject_ladder.py`（A/B/C 三级 + C 级代码禁用 + 粗筛前置守卫）**与** E 的 `agent/guards/rule_guard.py` + `specialists/critic.py`（Critic 一票否决 + 必须给可核查理由）。
- **证据审计**：A 的 `evidence_audit.py`（`SignalBox` + 篡改检测）**与** E 的 `agent/guards/orchestrator.py`（四道防护）。

→ **硬提示：先挑一套做「宪法」，另一套只作为「缺失字段的补充来源」入册；否则新架构会把 6 套不一致的字段名同时继承下来。** 优先建议以 **E 为工程基线**（唯一有真实数据实跑 + 738 例测试 + 完整 docs/ 验收链），以 **A 为规则文本基线**（`RULES-L0.md` + `reject-ladder.md` + `gate-rules.md` + `signal-weights.md` 是唯一条目化、带实测数字的规则资产）。

### 提示 2：把这六份「负结果 + 实测数字」先搬进新架构的决策层，再写一行代码

本项目群最贵的知识不是「怎么做」，而是**「试过、失败了、别再来」**。这些材料全带数字、可复核，且散落在三个项目的不同文件里：

| 结论 | 实测数字 | 出处 |
|---|---|---|
| pandas 侧微优化已穷尽 | merge 键 Categorical **7.16s→7.81s（更慢 9.1%）**；int64 argsort **1.40s→1.72s（更慢 23.3%）**；合计 **8.56s→9.53s** | `alphadesk/docs/T32-面板加载三轮-pandas侧微优化负结果.md` |
| 倒排索引不要做 | build **43/46ms**、load **17/29ms** > 现状 **0.35ms** 扫描 | `alphadesk/docs/任务清单与依赖关系.md:639` |
| 三条 merge 优化路线都不要做 | 整数键 +11%、`searchsorted` **641ms（更慢）**、Categorical.codes 无差异 | 同上 `:606` |
| 手写 numpy 秩不要做 | numpy **58ms** vs pandas **51ms** | 同上 `:571` |
| **用样本外 IC 选因子 = 数据窥探** | 事后剔除 **+15.48%** vs 可执行滚动剔除 **−4.92%**；**C−A = −16.22pp** | 同上 `:312-366` |
| 重建 ODS/DWD 不划算 | 「收益低而踩坑成本极高」 | 同上 `:78`（ADR-009） |
| `adj_factor.hfq_factor` 不可作派生源 | 9-23 口径切换致 **5135/5552（92.5%）** 标的比值异常；与面板最多差 **+16.65%** | 同上 `:167`、`:630` |
| 后复权当不复权用会造成事故级错价 | `pnl_pct` **+604%**（真实 −7.16%）、卡片价位差 **7.58 倍** | 同上 `:614-615` |
| 压缩上下文方案不可行 | 27.4k → 只注入 19.9k，**58% 内容看不见**；41.6k → 19.9k | `quantInvest/AGENTS.md:23-24`、`docs/specs/01:22` |
| 否决制（无分级）会系统性错过强势股 | 单日 6 次误否决，事后 **山东玻纤 +4.05% / 亨通 +1.02%** | `quantInvest/skills/.../reject-ladder.md:8-12` |
| 「一个卡点覆盖 15 个接口」是自述幻觉 | 实际漏 **3 个**（龙虎榜/解禁/行业对比），且失败时返回**看起来完全正常**的报告 | `TradingAgents-astock-main/CLAUDE.md` |
| 指标命名即口径 | 把 `direction_accuracy` 叫「胜率」→ **判断正确被记成失败** | 同上 |
| 评级边界不能枚举标点 | 三轮修复三轮漏（`Buyer interest` / `Sell-off` / `Buy（基于风险收益比）`） | 同上 |
| 代理不能在模块顶层 pop | 表现只是「模型调不通」，**没人会联想到取数模块** | `vibe-astock-main/duanxian/fetchers.py:66-74` |
| `NO_PROXY` 大写改了没用 | requests **小写优先**，「现象和"没改过"一模一样，看不出来」 | 同上 `:95-98` |
| 旧 `py_mini_racer` 会静默毁掉两块功能 | 接口 200、`sectors: []` | `vibe-astock-main/requirements.txt` |

→ **硬提示：这一步应该在写第一行新代码之前完成，并落成新仓库的 `docs/negative-results.md`（带数字 + 出处 + 可复现命令）。** E 的 `T32` 文件本身就是最好的模板（含「唯一剩余杠杆」与「为什么不在这轮做」）。

### 提示 3：先把三件「基础设施级事实」定死，否则新架构会重演同样的病

按「不解决就会必然复发」排序：

1. **外置盘的唯一入口 + 口径唯一入口。** 现在同时存在两条 PSSD 路径（`.../本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb` 与 `.../downlodData/taodaoDataUpdate/`）**以及三套数据获取哲学**（本地 DuckDB 全量 / 在线 API 直连 / 本地缓存 JSON）。A 已经写下结论「**同一份数据不直接替换 duckdb——避免两套数据源打架（E-11 教训：同名不同源）**」（`docs/specs/05:77`），E 已经写下 ADR-010「一切对外输出必须显式声明口径（默认 hfq 后复权）」。**新架构必须只有一个 `DUCKDB_PATH` 常量 + 一个「可交易价」函数入口（E 的 `latest_daily_raw()` 就是这个入口）。**
2. **东财限流阈值必须选一个口径并写明为什么，然后只在一处实现。** 现状：**1 分钟 ≥200 次** 与 **5 分钟 ≥300 次** 数学冲突且未解释；D 的表格（5 行）与自己的代码注释（3 行）不一致；B 引入了「5 分钟 ≥300 次」但**没有挂 Retry adapter**（连 429 都不重试）；C 用换镜像域名的完全另一条路线。**推荐：以 D 的表格为准（唯一有「社区实测 + 一手踩坑案例」双重来源），把「403 不重试 / 429 与 5xx 退避」写成单点实现 + 单测，并把「串行 + 1s + 抖动 + 复用会话」做成不可绕过的唯一请求出口。**
3. **先把「哪个数字是真的」测准并写死。** 数据库体量在文档里有 **6 个不同说法**（124 GB / 124.4 GB / 124.43 GB / 133.6 GB / 90 表 / 92 表 / 81 基表），分钟行数有 **4 个**（54.2 / 54.6 / 54.7 亿行）。本报告实测：文件 **133,608,517,632 B = 124.43 GiB = 133.61 GB**（GiB/GB 混用可解释体量差异），**但表数差异（90/92 vs 81 基表）无法用单位制解释，原因未查明**。新架构的第一份验收记录应该是「一条可复跑的命令 + 原始输出」，把所有后续文档的数字钉在这份记录上。顺带：A 的 `docs/specs/05:124` 写的「L0 总量 **8.9k** < 12k 预算」与 `AGENTS.md:16` 的「≤4k」与 `RULES-L0.md` 的实测 4,478 B —— **三个数字互不一致**，属于同一类问题。

---

## 附：本报告的统计口径与限制

1. **`.py` 行数**一律排除 `.venv/`、`.git/`、`__pycache__/`、`node_modules/`。A 额外排除了 `.zwork/`（运行产物，含 artifact 副本）。
2. **未运行任何测试**（委托要求）。所有测试数字来自 **`grep -c` / `grep -rho` 的口径**（只数 `def test_*`，**不展开 `parametrize`**），因此**与项目自述的「passed 数」必然有差**——本报告已逐项列出两套数字，**不做合并**。
3. **未修改任何被调研目录**。唯一写入的文件是本报告自身。
4. **未打开** `taobao_minute.duckdb` / `trading.db` / `news.db` / `kb_hits.duckdb`（只做 `ls -la` 体积与 mtime 读取）。
5. **G 节**按委托要求只看顶层结构与配置文件名清单，**未读取其决策体系内容**。
6. 凡是「推断」的结论均在文中显式标注「推断」；查不到的项写「未发现」或「不存在」。
7. 本报告为**重建版**：原版在文件搬运中丢失，因此无法逐字核对与原版的一致性；内容以本次实测为准。
