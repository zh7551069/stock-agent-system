# 总架构

主控门面 + 三面 + 双总线 + 外挂评测。**主视图是分层架构图**（业务驱动），另配**系统上下文图**（对外关系）与**容器图**（对内 C4 结构）。

## 分层架构图（业务驱动）

<div class="layer-arch">
  <div class="la-row biz">
    <div class="la-label">业务支持</div>
    <div class="la-cells">
      <span>策略生成</span><span>大盘分析</span><span>盘中监听</span><span>决策对账</span><span>风险告警</span>
    </div>
  </div>
  <div class="la-row ux">
    <div class="la-label">交互与呈现</div>
    <div class="la-cells">
      <span>意图对话（主控）</span><span>决策看板</span><span>回测报告</span><span>对账报告</span><span>协议接口</span>
    </div>
  </div>
  <div class="la-row agent">
    <div class="la-label vertical">Agent 业务生产能力层</div>
    <div class="la-body">
      <div class="la-subrow">
        <div class="la-sublabel">接入与会话</div>
        <div class="la-cells"><span>主控（意图/规划/派单）</span><span>调度器（路由/预算/幂等）</span><span>会话查询</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">指令与技能</div>
        <div class="la-cells"><span>协议契约</span><span>Skill 定义</span><span>角色约束</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">领域知识</div>
        <div class="la-cells"><span>知识馆长（知识卡+证据等级）</span><span>因子字典</span><span>Schema 注册表</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">记忆与历史</div>
        <div class="la-cells"><span>资产登记官（意图-经验-效用）</span><span>历史决策检索</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">业务与环境状态</div>
        <div class="la-cells"><span>数据管家（行情/口径）</span><span>盘中哨兵（事件流）</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">上下文组装</div>
        <div class="la-cells"><span>按 regime 检索</span><span>相关性筛选</span><span>上下文压缩</span><span>任务状态注入</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">Agent 决策</div>
        <div class="la-cells"><span>主控规划</span><span>策略师推理</span><span>因子工坊</span><span>大盘分析师</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">行动执行</div>
        <div class="la-cells"><span>能力管家（工具/Skill）</span><span>数据取数</span><span>回测回放</span><span>对账</span></div>
      </div>
      <div class="la-subrow">
        <div class="la-sublabel">业务资产</div>
        <div class="la-cells"><span>策略 proposal</span><span>因子字典</span><span>知识卡</span><span>过程资产</span></div>
      </div>
    </div>
  </div>
  <div class="la-row infra">
    <div class="la-label vertical">工具·约束·组件·基础设施</div>
    <div class="la-cells">
      <span>协议总线</span><span>Trace 总线</span><span>资产仓库</span><span>回测 harness</span><span>判决库</span>
    </div>
  </div>
</div>

> **两条纵贯线**：图中每个 Agent 回合都产出 span 写 Trace 总线（可观测）；裁决面输出 → 归因/评估 → 可进化层（自进化）。这两条线不是某一层，而是**贯穿所有层**——详见 [可观测平台设计](/observability.html) 与 [自进化设计](/self-evolution.html)。

## 系统上下文图 · System Context

![系统上下文图](/diagrams/overview-context.svg)

## 容器图 · Container

![容器图](/diagrams/overview-container.svg)

> **图例**：实线 = 正向执行流；**红色虚线 = 进化回路**——裁决面（对账官/会话评估官）输出 → 归因分析 → 换因子集/改定义/调参数/调权重/改出场（策略进化）与改 prompt/skill（过程进化）。这条回路就是系统的「自进化」过程，在 [自进化设计](/self-evolution.html) 页展开。

## 两条纵贯线：可观测 + 自进化

架构图里，这两条线不是某一块，而是**贯穿全图**：

- **可观测纵贯线**：图中每一条实线箭头（正向执行流）都同时是一条 span 写入 Trace 总线——决策面、裁决面、平台面的每个回合都产出带四元 id + 三层语义的 span。
- **自进化纵贯线**：图中红色虚线（进化回路）是可观测的「消费端」——裁决面读 trace → 归因 → 回灌可进化层。

所以图可以读成两层：**实线是「执行 + 观测」，虚线是「观测 → 进化」**。一条决策从触发到复盘，同时活在两层里。

## Span 类型（股票场景原生分类）

借鉴「统一 span 类型」这个思想，但**不照搬 OTel 的 9 类 Span 名**——按股票决策自身的环节分类：

| Span 类型 | 交易域含义 | 主要产出 Agent |
| --- | --- | --- |
| 回合 turn | 主控/调度器的意图理解、规划、派单回合 | 主控、调度器 |
| 模型调用 llm | 每次模型调用（策略起草/定稿、复盘解读） | 策略师、大盘分析师、对账官 |
| 数据取数 data | 行情/指标/口径取数（duckdb、行情 API） | 数据管家 |
| 工具调用 tool | 工具/skill 调用 | 能力管家 |
| 检索 retrieve | 知识卡/因子/历史经验检索 | 知识馆长、因子工坊、策略师 |
| 风控校验 guard | 涨跌停/T+1/仓位/口径校验 | 回测判决官、数据管家 |
| 判决 judge | 影子回放、对账、归因 | 回测判决官、对账官 |
| 事件 event | 盘中异动/信号触发 | 盘中哨兵 |

> 借鉴的是「统一 span 类型 + 分层语义」这个**思想**；类型名按股票场景自定，分层语义（`trace.*`/`trad.*`/`a股.*`）见 [可观测平台设计](/observability.html)。

## 四块怎么连

1. **入口** → **主控**：理解意图、拆任务、产出任务清单（含「派给哪个面」的规划决策）。
2. **主控 / 定时器 → 调度器**：调度器有两个触发源——主控（按需/会话）与定时器（盘后对账、盘前预热、定时复盘）。
3. **调度器 → 决策面 / 裁决面 / 平台面**：按任务类型路由到面内具体 agent，执行并发 / 预算 / 幂等 / 超时。
4. **共享基础设施**：协议总线（消息路由/幂等/ACL）、Trace 总线（append-only、哈希链）、Schema 注册表、资产仓库。
5. **评测平台**：从 Trace 总线订阅 trace；回灌只写「过程配置」（prompt / skill / 协议），**不写生产数据**。

## 三面的边界

| 面 | 职责 | 关键约束 |
| --- | --- | --- |
| 决策面 | 产生判断与动作（策略、因子、大盘、盘中） | 低延迟 · 高吞吐 · 无长推理 |
| 裁决面 | 回测 / 对账 / 会话评估 | 物理隔离 · 只读生产 · 只写判决库 |
| 平台面 | 数据 / 知识 / 工具 / 技能 / 过程资产 | 口径与证据分级 · 测试后晋级 |
