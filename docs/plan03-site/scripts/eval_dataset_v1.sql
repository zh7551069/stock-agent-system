-- ============================================================
-- 决策评测集落库 DDL v1（结果侧 7 表）
-- 依据: docs/plan03-site/docs/eval-dataset.md §6.3
-- 落库原则: ① 冻结快照保 GT 可复现 ② 分层可切片(regime 打散成列) ③ 口径版本绑定
-- 物理隔离: 评测平台是独立进程/独立代码仓/独立 DB，本 DDL 面向评测库，不写生产库。
-- 依赖: caliber_meta 已在 caliber_contract_v1.sql 建好（同一评测库内）。
-- ============================================================

-- ─────────────────────────────────────────
-- ① 口径元数据（复用 caliber_contract_v1.sql 的建表；此处仅注释对齐）
-- ─────────────────────────────────────────
-- CREATE TABLE IF NOT EXISTS caliber_meta (
--   caliber_id    VARCHAR PRIMARY KEY,   -- 'caliber:v1'
--   adjust        VARCHAR NOT NULL,      -- '前复权'
--   limit_caliber VARCHAR NOT NULL,      -- 'limit_price'
--   cost_rate     DOUBLE  NOT NULL,      -- 0.0015
--   code_format   VARCHAR NOT NULL,      -- 'sz000001'
--   eff_date      DATE    NOT NULL
-- );

-- ─────────────────────────────────────────
-- ② 决策事件（信号触发，T 日）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS decision_event (
  decision_id  VARCHAR PRIMARY KEY,      -- 四元 id 贯穿
  session_id   VARCHAR,
  strategy_id  VARCHAR,
  factor_ids   VARCHAR[],                -- 抓手因子
  signal_id    VARCHAR,                  -- 触发信号
  signal_date  DATE    NOT NULL,         -- T 日
  caliber_id   VARCHAR REFERENCES caliber_meta(caliber_id),
  trace_id     VARCHAR
);

-- ─────────────────────────────────────────
-- ③ regime 标签（决策时点打标，绑定口径版本）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS regime_label (
  decision_id  VARCHAR PRIMARY KEY REFERENCES decision_event(decision_id),
  limit_up_cnt VARCHAR,                  -- 涨停家数桶 '<30'/'30-60'/'60+'
  beta_bucket  VARCHAR,                  -- 大盘beta桶 '跌'/'平'/'涨'
  crowd_bucket VARCHAR,                  -- 拥挤度桶 '低'/'中'/'高'
  turnover_q   VARCHAR,                  -- 换手率分位 '低'/'中'/'高'
  news_level   VARCHAR,                  -- 消息面 '无'/'弱'/'强'/'待考证'
  regime_ver   VARCHAR                   -- 'regime:v1'
);
-- ⚠️ 缺口：6.2.2 的 8 个候选维度（市场宽度/情绪指数/市场周期/大盘闸门/C/r²/资金风格/多空阶段）
--    在 regime_label 里尚无列；待任务 16 验证通过后，用 ALTER TABLE ADD COLUMN 纳入并 +1 版本。

-- ─────────────────────────────────────────
-- ④ 样本篮子（当日合并篮子 + 超额）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sample_basket (
  decision_id  VARCHAR PRIMARY KEY REFERENCES decision_event(decision_id),
  entry_date   DATE    NOT NULL,         -- T+1
  exit_date    DATE,                     -- T+N
  n_days       INTEGER,                  -- N
  basket_ret   DOUBLE,                   -- 篮子收益
  bench_ret    DOUBLE,                   -- 同期沪深300
  excess_ret   DOUBLE,                   -- 剔 beta 超额
  cost_rate    DOUBLE,                   -- 实际成本率
  holdings     JSON,                     -- 个股明细（code/权重/entry/exit/收益）
  exit_events  JSON                      -- 出场事件（stop/tp/跌停封死顺延）
);

-- ─────────────────────────────────────────
-- ⑤ 配对对照（同天随机等规模篮子）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS paired_control (
  decision_id    VARCHAR REFERENCES decision_event(decision_id),
  control_date   DATE,
  control_ret    DOUBLE,
  control_excess DOUBLE,
  PRIMARY KEY (decision_id, control_date)
);

-- ─────────────────────────────────────────
-- ⑥ 判决结果（判决器输出，只读生产）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verdict (
  decision_id      VARCHAR PRIMARY KEY REFERENCES decision_event(decision_id),
  excess           DOUBLE,
  t_stat           DOUBLE,
  paired_t         DOUBLE,
  layered_win_rate DOUBLE,
  verdict          VARCHAR,              -- 'rejected'/'accepted'/'unknown'
  regime_slice     VARCHAR,              -- 切片标识
  judged_at        TIMESTAMP
);

-- ─────────────────────────────────────────
-- ⑦ 行情快照（冻结前复权，保证 GT 可复现）
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS price_snapshot (
  snapshot_id  VARCHAR,
  decision_id  VARCHAR REFERENCES decision_event(decision_id),
  trade_date   DATE,
  code         VARCHAR,
  open_adj     DOUBLE,                   -- 前复权开盘
  close_adj    DOUBLE,                   -- 前复权收盘
  high_adj     DOUBLE,
  low_adj      DOUBLE,
  limit_up     DOUBLE,                   -- 涨跌停价
  limit_down   DOUBLE,
  bench_close  DOUBLE,                   -- 沪深300 收盘
  PRIMARY KEY (snapshot_id, trade_date, code)
);

-- ─────────────────────────────────────────
-- 切片查询索引
-- ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_signal_date ON decision_event(signal_date);
CREATE INDEX IF NOT EXISTS idx_regime      ON regime_label(limit_up_cnt, beta_bucket, crowd_bucket, turnover_q);
CREATE INDEX IF NOT EXISTS idx_code_date   ON price_snapshot(code, trade_date);

-- ─────────────────────────────────────────
-- 读写分工（对齐 eval-dataset.md §6.3 结尾）
-- ─────────────────────────────────────────
-- 数据管家  写: caliber_meta / decision_event / regime_label / sample_basket / price_snapshot
-- 回测判决官 写: verdict / paired_control（判决，只读生产）
-- 资产登记官 读: 上述三类产出，蒸馏「意图-经验-效用」三元组（下游记忆视图）
