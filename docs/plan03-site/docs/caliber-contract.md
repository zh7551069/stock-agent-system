# 数据口径契约 v1（实库校准）

> 依据实库 `/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb`（78 表，daily 覆盖 2000-06-09 ~ 2026-10-22，关键表更新到 2026-10-22）逐字段核实。这是「可验证性地基」的**第一刀**——数据管家「口径注册表」的 v1 依据。**未经本契约归一的数据，不用于决策。**

## 一、五个口径地雷（已逐字段核实）

### 1.1 market 语义：同一字段名，三种含义

| 表 | 实际取值 | 真实含义 | 样本 |
| --- | --- | --- | --- |
| `daily.market` | `{hs, bj}` | `hs`=沪深合并（含 sh+sz，靠 code 前缀区分），`bj`=北交所 | hs→sh600000~sz302132；bj→bj920000~bj920992 |
| `limit_price.market` | `{hs, bj, sz, sh}` | 混乱：`hs` 合并（16.69M 行）+ `bj`（277K）+ `sz`（8.7K）+ `sh`（6.9K），疑似重复 | — |
| `stock_info.market` | `{主板, 创业板, …}` | **板块**，不是交易所！ | 主板 / 创业板 / 科创板 |

### 1.2 code 格式：两套体系并存（实跑修正：不是三种，是两套）

| 套系 | 格式 | 样本 | 覆盖表 |
| --- | --- | --- | --- |
| A 套 | 小写 2 字母 + 6 位 | `sz002640` | `daily` / `limit_price` / `adj_factor` / `daily_mv` / `index_daily` |
| B 套 | 6 位 + `.SZ/.SH` 大写 | `000001.SZ` / `601100.SH` | `stock_info.ts_code` / `tech_factor_qfq.code` / `tech_factor_hfq.code` / `zt_pool.代码` |

> 🔴 **第 6 个地雷（QC 断言 6 实跑发现）**：`tech_factor_qfq` 用 B 套格式（`000001.SZ`），与 `daily` 的 A 套（`sz000001`）不同——**因子表直接 join 行情表会失败**。归一规则必须覆盖两张 tech_factor 表。

### 1.3 date 格式：三种并存

| 表 | 类型 | 样本 |
| --- | --- | --- |
| `daily.date` / `limit_price.date` / `index_daily.date` | DATE | 2026-10-22 |
| `market_flow_daily.交易日期` | BIGINT | 20261022 |
| `suspension.交易日期` | VARCHAR | 待核实具体格式 |

### 1.4 金额/成交量单位：至少四种

| 字段 | 单位 | 验证依据 |
| --- | --- | --- |
| `daily.amount` | **元** | 茅台 600519 日成交 5,576,216,964（约 55.76 亿） |
| `daily.volume` | **手**（100 股） | 55.76 亿 ÷ 1318 元 ≈ 423 万股 = 42300 手 ✓ |
| `tech_factor_qfq.amount_k` | **千元** | 字段名后缀 `_k` |
| `tech_factor_qfq.vol_hand` | **手** | 字段名后缀 `_hand` |
| `daily_mv.total_mv_yi` / `circ_mv_yi` | **亿元** | 字段名后缀 `_yi` |
| `zt_pool.主力净额(元)` / `成交额` | **元** | 字段名带 `(元)` |

### 1.5 换手率：不在 daily_basic，在 tech_factor_qfq

- `daily_basic` 只有 `total_mv / pe_ttm / pb`，**无换手率**。
- `tech_factor_qfq.turnover` 直接有换手率（%），且带全 `ma5/10/20/60、ema、macd、rsi6/12/24、kdj、boll、atr、obv、up_days/new_high_days` 等预计算技术因子（前复权口径）。
- 结论：**换手率与技术因子统一从 `tech_factor_qfq` 取**，不再从 daily_basic 找。

## 二、归一规则（canonical form）

统一后的规范口径，所有下游表只认这一套：

| 维度 | 规范值 | 归一规则 |
| --- | --- | --- |
| market | `{sh, sz, bj}` | 从 code 前缀推导：`sh6xxxxx`→sh、`sz0/3xxxxx`→sz、`bj8/9xxxxx`→bj；`stock_info.market` 改字段名为 `board`，不与交易所混用 |
| code | `sz002640`（小写2字母+6位） | `000001.SZ`↔`sz000001`；`601100.SH`↔`sh601100` |
| date | DATE | BIGINT→`strptime(cast(x AS varchar),'%Y%m%d')`；VARCHAR 待核实后转 |
| amount | 元 | `amount_k×1000`→元；`*_yi×1e8`→元 |
| volume | 股 | `手×100`→股 |
| turnover | % | 统一取 `tech_factor_qfq.turnover` |

## 三、QC 断言（机器可校验，进不了下游）

每条口径配一条可机械执行的断言，采集层/QC 门禁直接拦：

1. `market ∈ {sh, sz, bj}` —— 非法值直接拒绝。
2. `code` 匹配正则 `^(sh|sz|bj)\d{6}$` —— 不匹配拒绝。
3. `date` 为 DATE 类型 —— BIGINT/VARCHAR 必须先转再入库。
4. `amount` 单位 = 元 —— 量级校验：大盘股日成交 1e8~1e10 元，超界告警。
5. `turnover ∈ [0, 200]` —— 单位 %，超界告警。
6. `qfq` 价格 = `daily.close × adj_factor.qfq_factor` —— 交叉校验前复权。

## 四、映射到 caliber_meta 表

| caliber_meta 字段 | 取值（v1） |
| --- | --- |
| adjust | 前复权（`adj_factor.qfq_factor`） |
| limit_caliber | 涨跌停口径（`limit_price.limit_up/limit_down/limit_pct`） |
| cost_rate | 0.0015 |
| code_format | `sz000001`（小写2字母+6位） |
| market_enum | `{sh, sz, bj}` |
| date_format | DATE（ISO） |
| amount_unit | 元 |
| volume_unit | 股 |

## 五、待核实项（v1 遗留 → 已消化 6 项，剩 1 项）

- [x] **🔴 前复权口径（已权威验证，结论修正）**：经 tushare + 腾讯双源验证——① 前复权价负值（茅台 2001 年 -314）是「前复权」真实数学性质（累计分红超股价），**不是 bug**；② `adj_factor` 表（hfq=6.25）与权威源（8.6463）不一致，是**真的错表**，弃用；③ 判决器核心是「收益率 pct_chg」，复权不影响收益率，pct_chg 已验证 4/4 与 tushare 一致。**结论：收益率用 `pct_chg`（已验证）；技术指标用后复权价 `tech_factor_hfq.close`（正值单调）；`adj_factor` 表弃用。**
- [x] **🔴 第 7 个地雷：文件名后缀不稳定（已修复）**：`(2)` 后缀不同日含义漂移。**结论：同步 skill v3 改为按「表头签名」识别，不按文件名。**
- [x] `limit_price.market` 混乱（已消化）：历史 1669 万行用 `hs` 合并，近期 1.5 万行才用 `sz/sh` 单独。**归一从 code 前缀推导，忽略源 market 字段。**
- [x] `suspension.交易日期`（已消化）：VARCHAR 存 `'19990528'`（8 位 YYYYMMDD），`normalize_date` 的 `%Y%m%d` 分支已能处理。
- [x] `market_flow_daily`（已消化）：只有 2023-04-17 之后（851 行）。**情绪指数维度只能回测 2023 之后，更早无两融数据。**
- [x] `zt_pool` 主表滞后（已消化）：`zt_pool` 到 2026-09-17，但 `zt_pool_limit_up/down` 到 10-21。**涨停池主表没持续导入，需补导或改用 limit_up/down 表。**
- [x] `adj_factor` 缺记录（已确认根因）：下载包「复权因子_前复权.zip」里茅台 10-21 **数据源本身就缺**（最后一行是 10-20）。且「前复权因子负值」不是 bug（腾讯权威源前复权价也是 -314）。**结论：adj_factor 表弃用（hfq=6.25 与权威源 8.6463 不一致）；收益率用 pct_chg，技术指标用 tech_factor_hfq.close。**

## 六、结论

数据地基「料」够格，但要立住，第一步就是**把上面 5 个地雷 + 4 个待核实项写成 `caliber_meta` 表 + QC 断言**。这份契约 v1 已经把它们从「经验预判」变成了「实库实证」。下一步：数据管家照此建 `caliber_meta` 表 + 写 QC 门禁，回测判决官 harness 才能拿到可靠输入。
