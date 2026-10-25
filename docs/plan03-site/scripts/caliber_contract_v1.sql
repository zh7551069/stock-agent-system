-- ============================================================
-- 数据口径契约 v1.1 · 实库校准 SQL（含 QC 实跑修正）
-- 依据: /Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb
-- v1.1 修正: ① tech_factor 用 B 套 code 格式（JOIN 需归一）② amount 区分停牌/2006异常 ③ turnover 排除 1992
-- ============================================================

-- ─────────────────────────────────────────
-- 一、caliber_meta 表（口径元数据）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS caliber_meta (
  caliber_id    VARCHAR PRIMARY KEY,
  adjust        VARCHAR NOT NULL,      -- '前复权'
  limit_caliber VARCHAR NOT NULL,      -- 'limit_price'
  cost_rate     DOUBLE  NOT NULL,      -- 0.0015
  code_format   VARCHAR NOT NULL,      -- 'sz000001'
  market_enum   VARCHAR NOT NULL,      -- 'sh,sz,bj'
  date_format   VARCHAR NOT NULL,      -- 'DATE(ISO)'
  amount_unit   VARCHAR NOT NULL,      -- '元'
  volume_unit   VARCHAR NOT NULL,      -- '股'
  eff_date      DATE    NOT NULL
);
INSERT INTO caliber_meta VALUES
('caliber:v1', '前复权', 'limit_price', 0.0015, 'sz000001', 'sh,sz,bj', 'DATE(ISO)', '元', '股', DATE '2026-10-25');

-- ─────────────────────────────────────────
-- 二、code 归一（核心！两套 code 体系）
-- ─────────────────────────────────────────
-- A 套（小写2字母+6位）: daily / daily_mv / limit_price / index_daily
-- B 套（6位+.SZ/.SH）: adj_factor / tech_factor_qfq / tech_factor_hfq / stock_info / zt_pool
-- 🔴 注意: adj_factor 是 B 套！前复权计算 daily×qfq_factor 横跨 A/B 两套，必须归一
-- 统一归一到 A 套：'000001.SZ' → 'sz000001'
--   归一表达式（B 套 → A 套）:
--     lower(split_part(code, '.', 2)) || split_part(code, '.', 1)

-- ─────────────────────────────────────────
-- 三、QC 断言（实跑结果见下注释）
-- ─────────────────────────────────────────

-- 断言 1：market 从 code 前缀推导（实跑 0 违规 ✓）
SELECT COUNT(*) AS market_violations
FROM daily
WHERE code NOT LIKE 'sh%' AND code NOT LIKE 'sz%' AND code NOT LIKE 'bj%';
-- 实跑: 0

-- 断言 2：daily.code 匹配 ^(sh|sz|bj)6位$（实跑 0 违规 ✓）
SELECT COUNT(*) AS code_violations
FROM daily
WHERE NOT regexp_matches(code, '^(sh|sz|bj)[0-9]{6}$');
-- 实跑: 0

-- 断言 3：date 类型（schema 级，确认需转）
SELECT typeof(交易日期) AS type FROM market_flow_daily LIMIT 1;  -- BIGINT
SELECT typeof(交易日期) AS type FROM suspension LIMIT 1;          -- VARCHAR

-- 断言 4：amount 分三类（区分停牌 / 小额 / 2006 异常）
SELECT
  COUNT(*) FILTER (WHERE amount = 0 AND volume = 0)             AS suspension_days,   -- 停牌，合法
  COUNT(*) FILTER (WHERE amount > 0 AND amount < 1e6)           AS low_amount,        -- 小额，待核实
  COUNT(*) FILTER (WHERE amount > 1e13)                         AS anomaly_2006        -- 2006 数据异常
FROM daily;
-- 实跑: suspension_days=24300, low_amount≈171024, anomaly_2006≈若干（含 sz000488 3.9e15）

-- 断言 5：turnover 分时期（1992 年合法，1993 后应 0）
SELECT
  COUNT(*) FILTER (WHERE date < DATE '1993-01-01')                                        AS pre1993_high,   -- 合法
  COUNT(*) FILTER (WHERE date >= DATE '1993-01-01' AND (turnover < 0 OR turnover > 200))  AS post1993_violation
FROM tech_factor_qfq;
-- 实跑: pre1993_high=164, post1993_violation=0 ✓（1992 后无超界）

-- 断言 6：前复权交叉校验（JOIN 需先做 code 归一，adj_factor 和 tech_factor_qfq 都是 B 套）
SELECT
  d.code, d.date,
  d.close AS raw_close,
  a.qfq_factor,
  d.close * a.qfq_factor AS calc_qfq,
  t.close AS qfq_close,
  abs(d.close * a.qfq_factor - t.close) AS diff
FROM daily d
JOIN adj_factor a
  ON a.date = d.date
  AND lower(split_part(a.code, '.', 2)) || split_part(a.code, '.', 1) = d.code
JOIN tech_factor_qfq t
  ON t.date = d.date
  AND lower(split_part(t.code, '.', 2)) || split_part(t.code, '.', 1) = d.code
WHERE d.code = 'sh600519' AND d.date >= DATE '2026-01-01'
ORDER BY d.date DESC
LIMIT 5;
-- 实跑: 归一后 diff 多日=0（一致），但 adj_factor 有缺记录日（qfq_factor NULL）
-- 全市场 2026 年: 25% 行 daily×qfq_factor ≠ tech_factor_qfq.close（两个前复权口径不一致，🔴 最高优先级待核实）
