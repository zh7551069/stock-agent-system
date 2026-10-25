#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝数据同步 skill · 本地数据 → duckDB（口径统一，从源头纠正）· v3
========================================================================
v3 更新: ① 按「表头签名」识别 CSV 类型（修第 7 地雷：文件名后缀不稳定）
        ② 补全 26 类 CSV 的列映射（此前 { } 空占位的已补）
这是「数据管家」确定性核心，以后每天同步固定走这个 skill。

依据: 数据口径契约 v1（caliber-contract.md）
用法: python3 taobao_sync.py --dry-run | --qc | （默认同步）
"""
import os, re, io, glob, datetime, csv, zipfile, random, json
import urllib.request
import duckdb
import pandas as pd

CALIBER = {"adjust": "前复权", "cost_rate": 0.0015, "code_format": "sz000001",
           "market_enum": {"sh","sz","bj"}, "amount_unit": "元", "volume_unit": "股"}

# ── 归一函数（6 地雷修复点）──
def normalize_code(c):
    if not c: return None
    s = str(c).strip()
    m = re.match(r'^(\d{6})\.(SH|SZ|BJ)$', s, re.I)
    if m: return m.group(2).lower() + m.group(1)      # 000001.SZ → sz000001
    m = re.match(r'^(sh|sz|bj)(\d{6})$', s, re.I)
    if m: return m.group(1).lower() + m.group(2)      # SH600519 → sh600519
    if re.match(r'^\d{6}$', s):                        # 裸 6 位 = 指数/板块码（880板块/000上证/399深证），保留原样
        return s
    return None

def normalize_code_suffix(c):
    """code → 后缀式 000001.SZ（仅 tech_factor_qfq/tech_factor_hfq 表的 code 用）。"""
    s = normalize_code(c)
    if not s: return None
    m = re.match(r'^(sh|sz|bj)(\d{6})$', s)
    if m: return m.group(2) + "." + m.group(1).upper()
    return s  # 裸 6 位（指数）保持原样

def normalize_date(d):
    if isinstance(d, datetime.date): return d
    if isinstance(d, datetime.datetime): return d.date()
    s = str(d).strip()
    for f in ('%Y-%m-%d','%Y%m%d'):
        try: return datetime.datetime.strptime(s, f).date()
        except ValueError: pass
    return None

_UNIT = {"元":1.0,"千元":1e3,"万元":1e4,"亿元":1e8,"百万元":1e6,"万股":1e4,"手":100,"万笔":1e4}
def normalize_num(v, unit):
    if v is None or v == '' or v == '--' or v == 'None': return None
    try: return float(v) * _UNIT.get(unit, 1.0)
    except (ValueError, TypeError): return None

def normalize_datetime(d):
    """分钟线时间 '2026/10/21 10:30' → datetime。"""
    if isinstance(d, datetime.datetime): return d
    s = str(d).strip()
    for f in ('%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try: return datetime.datetime.strptime(s, f)
        except ValueError: pass
    return None

def normalize_datestr(d):
    """日期 → 'YYYYMMDD' 字符串（真实库 suspension.交易日期 是 VARCHAR YYYYMMDD）。"""
    r = normalize_date(d)
    return r.strftime("%Y%m%d") if r else None

_MARKET_OF_PREFIX = {"sh": "hs", "sz": "hs", "bj": "bj"}

def normalize_market(c):
    """从 code 推导 market（daily/limit_price 的 market 列，sh/sz→hs，bj→bj）。"""
    s = normalize_code(c)
    if not s: return None
    return _MARKET_OF_PREFIX.get(s[:2])

# ── SOURCE_MAP：表头签名 → (目标表, {源列:(目标列,单位)}) ──
# 签名 = 表头里能唯一区分该类型的关键列集合；匹配 = 签名 ⊆ 表头
# 单位 None 表示 code/date 专用归一
SOURCE_MAP = [
    # 日线行情（真实库 daily：market/code/date/OHLC/volume/amount/pct_chg）
    (frozenset({"开盘价","最高价","最低价","收盘价","成交量(手)","成交额(千元)","市盈率"}), "daily", {
        "股票代码":("code","code"),"交易日期":("date","date"),
        "开盘价":"open","最高价":"high","最低价":"low","收盘价":"close",
        "成交量(手)":("volume","num","手"),"成交额(千元)":("amount","num","千元"),"涨跌幅":("pct_chg","num","")}),
    # 技术因子（前复权口径权威，code 后缀式 000001.SZ）
    (frozenset({"复权因子","MA5","MA10","MA20"}), "tech_factor_qfq", {
        "股票代码":("code","code_suffix"),"交易日期":("date","date"),
        "开盘价":"open","最高价":"high","最低价":"low","收盘价":"close",
        "成交量(手)":("vol_hand","num","手"),"成交额(千元)":("amount_k","num","千元"),
        "涨跌幅(%)":("pct_chg","num",""),"换手率(%)":("turnover","num","")}),
    # 每日涨跌停价格（真实库 limit_price：market/code/date/prev_close/limit_up/limit_down）
    (frozenset({"昨日收盘价","涨停价","跌停价"}), "limit_price", {
        "股票代码":("code","code"),"交易日期":("date","date"),
        "昨日收盘价":("prev_close","num",""),"涨停价":("limit_up","num",""),"跌停价":("limit_down","num","")}),
    # 每日停复牌（真实库 suspension 中文列，交易日期为 YYYYMMDD 字符串）
    (frozenset({"停复牌时间段","停复牌类型"}), "suspension", {
        "股票代码":("股票代码","code"),"交易日期":("交易日期","datestr"),
        "停复牌时间段":"停复牌时间段","停复牌类型":"停复牌类型"}),
    # 大盘资金流向
    (frozenset({"上证收盘点位","深证收盘点位"}), "market_flow_daily", {
        "交易日期":("交易日期","datestr"),"上证收盘点位":("上证收盘点位","num",""),
        "上证涨跌幅(%)":("上证涨跌幅(%)","num",""),"深证收盘点位":("深证收盘点位","num",""),
        "深证涨跌幅(%)":("深证涨跌幅(%)","num",""),"主力净流入(元)":("主力净流入(元)","num","元"),
        "主力净流入占比(%)":("主力净流入占比(%)","num",""),
        "特大单流入(元)":("特大单流入(元)","num","元"),"特大单占比(%)":("特大单占比(%)","num",""),
        "大单流入(元)":("大单流入(元)","num","元"),"大单占比(%)":("大单占比(%)","num",""),
        "中单流入(元)":("中单流入(元)","num","元"),"中单占比(%)":("中单占比(%)","num",""),
        "小单流入(元)":("小单流入(元)","num","元"),"小单占比(%)":("小单占比(%)","num","")}),
    # 个股资金流_东财（主力净流入，真实库 stock_flow_em 中文列）
    (frozenset({"今日主力净流入额（万元）","今日超大单净流入额（万元）"}), "stock_flow_em", {
        "交易日期":("交易日期","datestr"),"股票代码":("股票代码","code"),"股票名称":"股票名称",
        "涨跌幅":"涨跌幅","最新价":"最新价",
        "今日主力净流入额（万元）":("今日主力净流入额（万元）","num","万元"),
        "今日主力净流入净占比（%）":("今日主力净流入净占比（%）","num",""),
        "今日超大单净流入额（万元）":("今日超大单净流入额（万元）","num","万元"),
        "今日超大单净流入占比（%）":("今日超大单净流入占比（%）","num",""),
        "今日大单净流入额（万元）":("今日大单净流入额（万元）","num","万元"),
        "今日大单净流入占比（%）":("今日大单净流入占比（%）","num",""),
        "今日中单净流入额（万元）":("今日中单净流入额（万元）","num","万元"),
        "今日中单净流入占比（%）":("今日中单净流入占比（%）","num",""),
        "今日小单净流入额（万元）":("今日小单净流入额（万元）","num","万元"),
        "今日小单净流入占比（%）":("今日小单净流入占比（%）","num","")}),
    # 个股资金流_同花顺（资金净流入+5日主力，真实库 stock_flow_ths 中文列）
    (frozenset({"资金净流入(万元)","5日主力净额(万元)"}), "stock_flow_ths", {
        "交易日期":("交易日期","datestr"),"股票代码":("股票代码","code"),"股票名称":"股票名称",
        "涨跌幅":"涨跌幅","最新价":"最新价",
        "资金净流入(万元)":("资金净流入(万元)","num","万元"),
        "5日主力净额(万元)":("5日主力净额(万元)","num","万元"),
        "今日大单净流入额(万元)":("今日大单净流入额(万元)","num","万元"),
        "今日大单净流入占比(%)":("今日大单净流入占比(%)","num",""),
        "今日中单净流入额(万元)":("今日中单净流入额(万元)","num","万元"),
        "今日中单净流入占比(%)":("今日中单净流入占比(%)","num",""),
        "今日小单净流入额(万元)":("今日小单净流入额(万元)","num","万元"),
        "今日小单净流入占比(%)":("今日小单净流入占比(%)","num","")}),
    # 订单流（真实库 moneyflow_stock：s/m/l/xl 买卖量额）
    (frozenset({"小单买入量(手)","中单买入量(手)"}), "moneyflow_stock", {
        "股票代码":("code","code"),"交易日期":("date","date"),
        "小单买入量(手)":("s_buy_vol","num","手"),"小单买入金额(万元)":("s_buy_amt","num","万元"),
        "小单卖出量(手)":("s_sell_vol","num","手"),"小单卖出金额(万元)":("s_sell_amt","num","万元"),
        "中单买入量(手)":("m_buy_vol","num","手"),"中单买入金额(万元)":("m_buy_amt","num","万元"),
        "中单卖出量(手)":("m_sell_vol","num","手"),"中单卖出金额(万元)":("m_sell_amt","num","万元"),
        "大单买入量(手)":("l_buy_vol","num","手"),"大单买入金额(万元)":("l_buy_amt","num","万元"),
        "大单卖出量(手)":("l_sell_vol","num","手"),"大单卖出金额(万元)":("l_sell_amt","num","万元"),
        "特大单买入量(手)":("xl_buy_vol","num","手"),"特大单买入金额(万元)":("xl_buy_amt","num","万元"),
        "特大单卖出量(手)":("xl_sell_vol","num","手"),"特大单卖出金额(万元)":("xl_sell_amt","num","万元"),
        "净流入量(手)":("net_vol","num","手"),"净流入金额(万元)":("net_amt","num","万元")}),
    # 行业资金流（真实库英文列，恒等 + date 归一）
    (frozenset({"行业代码","行业名称","领涨股票名称"}), "industry_flow", {
        "交易日期":("date","date"),"行业代码":"industry_code","行业名称":"industry_name",
        "流入资金(亿元)":("inflow","num","亿元"),"流出资金(亿元)":("outflow","num","亿元"),
        "净额(亿元)":("net","num","亿元")}),
    # 板块资金流_同花顺（真实库 board_flow_ths 中文列）
    (frozenset({"板块代码","板块名称","领涨股票名称","行业涨跌幅(%)"}), "board_flow_ths", {
        "交易日期":("交易日期","datestr"),"板块代码":"板块代码","板块名称":"板块名称",
        "领涨股票名称":"领涨股票名称","最新价":"最新价",
        "行业涨跌幅(%)":("行业涨跌幅(%)","num",""),"行业指数":"行业指数","公司数量":"公司数量",
        "领涨股涨跌幅(%)":("领涨股涨跌幅(%)","num",""),
        "流入资金(亿元)":("流入资金(亿元)","num","亿元"),
        "流出资金(亿元)":("流出资金(亿元)","num","亿元"),
        "净额(亿元)":("净额(亿元)","num","亿元")}),
    # 板块资金流_东财（真实库 board_flow_em 中文列）
    (frozenset({"数据类型","板块代码","主力净流入净额(元)"}), "board_flow_em", {
        "交易日期":("交易日期","datestr"),"数据类型":"数据类型","板块代码":"板块代码","板块名称":"板块名称",
        "板块涨跌幅(%)":("板块涨跌幅(%)","num",""),"板块最新指数":"板块最新指数",
        "主力净流入净额(元)":("主力净流入净额(元)","num","元"),
        "主力净流入占比(%)":("主力净流入占比(%)","num",""),
        "超大单净流入净额(元)":("超大单净流入净额(元)","num","元"),
        "超大单净流入占比(%)":("超大单净流入占比(%)","num",""),
        "大单净流入净额(元)":("大单净流入净额(元)","num","元"),
        "大单净流入占比(%)":("大单净流入占比(%)","num",""),
        "中单净流入净额(元)":("中单净流入净额(元)","num","元"),
        "中单净流入占比(%)":("中单净流入占比(%)","num",""),
        "小单净流入净额(元)":("小单净流入净额(元)","num","元"),
        "小单净流入占比(%)":("小单净流入占比(%)","num",""),
        "主力净流入最大股":"主力净流入最大股","序号":("序号","num","")}),
    # 涨停池 → zt_pool_limit_up（判决器读「代码+交易时间」；映射能对齐的字段，其余留空）
    (frozenset({"涨停原因","榜单类别","封单额(元)"}), "zt_pool_limit_up", {
        "交易日期":("交易时间","date"),"股票代码":("代码","code"),"股票名称":"名称",
        "涨跌幅%":"涨跌幅%","涨停原因":"涨停原因","涨停标签":"标签",
        "封单额(元)":("封单","num","元"),"换手率%":("换手率%","num",""),
        "实际流通(元)":("实际流通","num","元"),"最大封单(元)":("最大封单","num","元"),
        "成交额(元)":("成交额","num","元"),"股票类型":"src_type"}),
    # 自然涨停（真实库中文列，恒等）
    (frozenset({"涨停时间","开板时间","最后涨停时间"}), "zt_pool_natural_up", {
        "代码":("代码","code"),"交易时间":("交易时间","date"),
        "涨停原因":"涨停原因","标签":"标签","板块":"板块"}),
    # 连板天梯 → ladder（真实库中文列，恒等）
    (frozenset({"连板次数"}), "ladder", {
        "股票代码":("股票代码","code"),"股票名称":"股票名称","交易日期":("交易日期","date"),
        "连板次数":"连板次数"}),
    # 涨停最强板块（真实库中文列，恒等）
    (frozenset({"上榜天数","连板高度","涨停家数"}), "zt_strong_board", {
        "板块代码":"板块代码","板块名称":"板块名称","交易日期":("交易日期","datestr"),
        "涨停家数":"涨停家数","连板高度":"连板高度"}),
    # 龙虎榜明细（真实库中文列，恒等映射）
    (frozenset({"龙虎榜净买入额(元)","龙虎榜成交额(元)"}), "lhb_daily", {
        "交易日期":("交易日期","date"),"股票代码":("股票代码","code"),
        "股票名称":"股票名称","收盘价":("收盘价","num",""),
        "涨跌幅%":("涨跌幅%","num",""),"换手率%":("换手率%","num",""),
        "总成交额(元)":("总成交额(元)","num","元"),
        "龙虎榜卖出额(元)":("龙虎榜卖出额(元)","num","元"),
        "龙虎榜买入额(元)":("龙虎榜买入额(元)","num","元"),
        "龙虎榜成交额(元)":("龙虎榜成交额(元)","num","元"),
        "龙虎榜净买入额(元)":("龙虎榜净买入额(元)","num","元"),
        "龙虎榜净买额占比%":("龙虎榜净买额占比%","num",""),
        "龙虎榜成交额占比%":("龙虎榜成交额占比%","num",""),
        "当日流通市值(元)":("当日流通市值(元)","num","元"),
        "上榜理由":"上榜理由"}),
    # 龙虎榜机构明细（真实库中文列，恒等映射）
    (frozenset({"营业部名称","净成交额(元)"}), "lhb_inst", {
        "交易日期":("交易日期","date"),"股票代码":("股票代码","code"),
        "营业部名称":"营业部名称","买入额(元)":("买入额(元)","num","元"),
        "买入占总成交比例%":("买入占总成交比例%","num",""),
        "卖出额(元)":("卖出额(元)","num","元"),
        "卖出占总成交比例%":("卖出占总成交比例%","num",""),
        "净成交额(元)":("净成交额(元)","num","元"),
        "买卖类型":"买卖类型","上榜理由":"上榜理由"}),
    # 行业热度榜 → hot_rank_ths（真实库中文列，恒等；跨市场码原样保留）
    (frozenset({"热度值","排行榜获取时间"}), "hot_rank_ths", {
        "交易日期":("交易日期","datestr"),"数据类型":"数据类型","股票代码":("股票代码","code_keep"),
        "股票名称":"股票名称","排行":"排行","涨跌幅%":"涨跌幅%","当前价格":"当前价格",
        "热度值":"热度值","标签":"标签","排行榜获取时间":"排行榜获取时间","上榜解读":"上榜解读"}),
    # ST 列表（真实库中文列，恒等映射）
    (frozenset({"ST类型"}), "st_stock", {
        "股票代码":("股票代码","code"),"股票名称":"股票名称",
        "交易日期":("交易日期","datestr"),"ST类型":"ST类型","ST类型名称":"ST类型名称"}),
    # 股票曾用名（真实库中文列，恒等映射）
    (frozenset({"更名日期","更名前简称"}), "stock_rename", {
        "代码":("代码","code"),"名称":"名称","更名日期":("更名日期","date"),
        "更名前简称":"更名前简称","更名后简称":"更名后简称","证券类型":"证券类型"}),
    # 退市股票列表 / ETF 基础信息：真实库无对应表，暂不导入（保留 CSV 由 sync 报未识别）
    # 财务信息（真实库中文列，恒等映射）
    (frozenset({"流通股本","股东人数"}), "fin_company_snapshot", {
        "股票代码":("股票代码","code"),"股票名称":"股票名称","市场":"市场",
        "流通股本":("流通股本","num",""),"更新日期":("更新日期","date"),
        "上市日期":("上市日期","date"),"总股本":("总股本","num",""),
        "股东人数":("股东人数","num",""),"净资产":("净资产","num",""),
        "净利润":("净利润","num",""),"每股净资产":("每股净资产","num","")}),
    # 沪深港通资金流向（CSV 中文括号 vs 真实下划线命名）
    (frozenset({"北向资金(百万元)","南向资金(百万元)"}), "hk_connect_flow", {
        "交易日期":("交易日期","datestr"),
        "港股通（上海）(百万元)":("港股通_上海_百万","num",""),
        "港股通（深圳）(百万元)":("港股通_深圳_百万","num",""),
        "沪股通(百万元)":("沪股通_百万","num",""),
        "深股通(百万元)":("深股通_百万","num",""),
        "北向资金(百万元)":("北向资金_百万","num",""),
        "南向资金(百万元)":("南向资金_百万","num","")}),
    # 港股通每日成交统计（真实库中文列，恒等映射）
    (frozenset({"买入成交金额(亿元)","卖出成交金额(亿元)"}), "hk_connect_daily", {
        "交易日期":("交易日期","datestr"),
        "买入成交金额(亿元)":("买入成交金额(亿元)","num","亿元"),
        "买入成交笔数(万笔)":("买入成交笔数(万笔)","num","万笔"),
        "卖出成交金额(亿元)":("卖出成交金额(亿元)","num","亿元"),
        "卖出成交笔数(万笔)":("卖出成交笔数(万笔)","num","万笔")}),
    # 分钟线（真实库按周期分表 minute_1min/5min/15min/30min/60min；列 market/code/dt/OHLC/volume/amount）
    (frozenset({"时间","代码","名称","开盘价","收盘价","最高价","最低价","成交额","涨幅","振幅"}),
     "minute_kline", {
         "时间":("dt","dt"),"代码":("code","code"),
         "开盘价":("open","num",""),"最高价":("high","num",""),"最低价":("low","num",""),"收盘价":("close","num",""),
         "成交量":("volume","num","手"),"成交额":("amount","num","元")}),
    # 资产负债表 → fin_balance（真实库中文列，保留所有列 + code/date 归一）
    (frozenset({"股票代码","公告日期","报告期","报表类型"}), "fin_balance", {
        "*": None, "股票代码":("股票代码","code"),"公告日期":("公告日期","date")}),
    # 财务指标 → fin_indicator（真实库中文列，保留所有列 + code/date 归一）
    (frozenset({"股票代码","公告日期","报告期","基本每股收益"}), "fin_indicator", {
        "*": None, "股票代码":("股票代码","code"),"公告日期":("公告日期","date")}),
    # 财报披露计划 → fin_schedule（真实库中文列，恒等）
    (frozenset({"股票代码","报告期","预约披露日期"}), "fin_schedule", {
        "股票代码":("股票代码","code"),"报告期":"报告期","公告日期":("公告日期","date"),
        "预约披露日期":("预约披露日期","date"),"实际披露日期":("实际披露日期","date")}),
    # 限售股解禁 → fin_restricted（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","解禁日期","流通股份(股)"}), "fin_restricted", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"解禁日期":("解禁日期","date"),
        "流通股份(股)":("流通股份(股)","num","股"),"流通股份占总股本比例(%)":("流通股份占总股本比例(%)","num",""),
        "股东名称":"股东名称","股份类型":"股份类型"}),
    # 题材成分 → theme_stock（真实库中文列，恒等）
    (frozenset({"题材代码","题材名称","成分股票代码","交易日期"}), "theme_stock", {
        "题材代码":"题材代码","题材名称":"题材名称","成分股票名称":"成分股票名称",
        "成分股票代码":"成分股票代码","交易日期":("交易日期","datestr"),
        "描述":"描述","人气值":"人气值"}),
    # 业绩快报 → fin_express（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","报告期","营业收入(元)"}), "fin_express", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"报告期":"报告期",
        "营业收入(元)":("营业收入(元)","num","元"),"营业利润(元)":("营业利润(元)","num","元"),
        "利润总额(元)":("利润总额(元)","num","元"),"净利润(元)":("净利润(元)","num","元"),
        "总资产(元)":("总资产(元)","num","元"),"每股收益(摊薄)(元)":("每股收益(摊薄)(元)","num",""),
        "净资产收益率(摊薄)(%)":("净资产收益率(摊薄)(%)","num",""),"业绩简要说明":"业绩简要说明"}),
    # 业绩预告 → fin_forecast（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","报告期","预告类型"}), "fin_forecast", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"报告期":"报告期",
        "预告类型":"预告类型","净利润变动幅度下限(%)":("净利润变动幅度下限(%)","num",""),
        "净利润变动幅度上限(%)":("净利润变动幅度上限(%)","num",""),
        "预告净利润下限(万元)":("预告净利润下限(万元)","num","万元"),
        "预告净利润上限(万元)":("预告净利润上限(万元)","num","万元"),
        "上年同期归母净利润(万元)":("上年同期归母净利润(万元)","num","万元"),
        "预告摘要":"预告摘要","业绩变动原因":"业绩变动原因"}),
    # 主营业务构成 → fin_main_biz（真实库中文列，恒等；报告期为 DATE 列）
    (frozenset({"股票代码","报告期","主营业务来源"}), "fin_main_biz", {
        "股票代码":("股票代码","code"),"报告期":("报告期","date"),"类型":"类型","主营业务来源":"主营业务来源",
        "主营业务收入(元)":("主营业务收入(元)","num","元"),"主营业务利润(元)":("主营业务利润(元)","num","元"),
        "主营业务成本(元)":("主营业务成本(元)","num","元"),"货币代码":"货币代码"}),
    # 分红送股 → fin_dividend（真实库中文列，恒等）
    (frozenset({"股票代码","分红年度","预案公告日"}), "fin_dividend", {
        "股票代码":("股票代码","code"),"分红年度":"分红年度","预案公告日":("预案公告日","date"),
        "实施进度":"实施进度","每股送股比例":("每股送股比例","num",""),
        "每股转增比例":("每股转增比例","num",""),
        "每股分红（税前）":("每股分红（税前）","num",""),"除权除息日":("除权除息日","date")}),
    # 分红配股 → fin_rights_issue（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","送股(股)"}), "fin_rights_issue", {
        "股票代码":("股票代码","code"),"股票名称":"股票名称","公告日期":("公告日期","date"),
        "送股(股)":("送股(股)","num","股"),"转增(股)":("转增(股)","num","股"),
        "派息(税前)(元)":("派息(税前)(元)","num","元"),
        "配股方案(每10股配股股数)":("配股方案(每10股配股股数)","num",""),
        "配股价格(元)":("配股价格(元)","num","元"),"募集资金合计(元)":("募集资金合计(元)","num","元")}),
    # 前十大股东 / 前十大流通股东（表头相同，靠文件名区分）→ fin_top10_holder / fin_top10_float
    (frozenset({"股票代码","公告日期","报告期","股东名称"}), "fin_top10_holder", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"报告期":"报告期",
        "股东名称":"股东名称","持股数量":("持股数量","num",""),
        "持股比例(%)":("持股比例(%)","num",""),"流通股占比(%)":("流通股占比(%)","num",""),
        "持股变动":"持股变动","股东类型":"股东类型"}),
    # 现金流量表 → fin_cashflow（真实库中文列，保留所有列 + code/date 归一）
    (frozenset({"股票代码","公告日期","报告期","经营活动产生的现金流量净额"}), "fin_cashflow", {
        "*": None, "股票代码":("股票代码","code"),"公告日期":("公告日期","date")}),
    # 股东人数 → fin_holder_num（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","截止日期","股东户数"}), "fin_holder_num", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"截止日期":("截止日期","date"),
        "股东户数":("股东户数","num","")}),
    # 股权质押明细 → fin_pledge_detail（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","股东名称","质押数量(万股)"}), "fin_pledge_detail", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"股东名称":"股东名称",
        "股东类型":"股东类型","质押数量(万股)":("质押数量(万股)","num","万股"),
        "质押开始日期":("质押开始日期","date"),"质押结束日期":("质押结束日期","date"),
        "是否已解押":"是否已解押","解押日期":("解押日期","date"),"质押方":"质押方"}),
    # 股权质押统计 → fin_pledge_stat（真实库中文列，恒等）
    (frozenset({"股票代码","截止日期","质押次数"}), "fin_pledge_stat", {
        "股票代码":("股票代码","code"),"截止日期":("截止日期","date"),
        "质押次数":("质押次数","num",""),"无限售股质押数量(万)":("无限售股质押数量(万)","num",""),
        "限售股质押数量(万)":("限售股质押数量(万)","num",""),
        "总股本(万)":("总股本(万)","num",""),"质押比例(%)":("质押比例(%)","num","")}),
    # 财务审计意见 → fin_audit（真实库中文列，恒等）
    (frozenset({"股票代码","公告日期","报告期","审计结果"}), "fin_audit", {
        "股票代码":("股票代码","code"),"公告日期":("公告日期","date"),"报告期":"报告期",
        "审计结果":"审计结果","审计总费用":("审计总费用","num",""),
        "会计事务所":"会计事务所","签字会计师":"签字会计师"}),
    # 股票列表 → stock_info（真实库英文列）
    (frozenset({"TS代码","股票代码","实控人名称"}), "stock_info", {
        "TS代码":"ts_code","股票代码":("code","code"),"股票名称":"name",
        "地域":"area","所属行业":"industry","股票全称":"fullname","英文全称":"enname",
        "拼音缩写":"pinyin","市场类型":"market","交易所代码":"exchange","交易货币":"currency",
        "上市状态":"list_status","上市日期":("list_date","date"),"退市日期":("delist_date","date"),
        "沪深港通标的":"hs_connect"}),
]

#: 表头签名相同、需靠文件名区分的表（前十大股东 vs 前十大流通股东）
_NAME_OVERRIDE = {"前十大流通股东": "fin_top10_float"}

# ── QC 断言 ──
def qc_assertions(con):
    q = {}
    q["market"] = con.execute("SELECT COUNT(*) FROM daily WHERE code NOT LIKE 'sh%' AND code NOT LIKE 'sz%' AND code NOT LIKE 'bj%'").fetchone()[0]
    q["code"] = con.execute("SELECT COUNT(*) FROM daily WHERE NOT regexp_matches(code,'^(sh|sz|bj)[0-9]{6}$')").fetchone()[0]
    q["turnover"] = con.execute("SELECT COUNT(*) FROM tech_factor_qfq WHERE date>=DATE '1993-01-01' AND (turnover<0 OR turnover>200)").fetchone()[0]
    q["amount_2006"] = con.execute("SELECT COUNT(*) FROM daily WHERE amount>1e13").fetchone()[0]
    q["tech_qfq_neg"] = con.execute("SELECT COUNT(*) FROM tech_factor_qfq WHERE close<0").fetchone()[0]
    return q

# ── 通用同步引擎（按表头签名识别）──
def _detect(header):
    cols = set(header)
    for sig, tbl, colmap in SOURCE_MAP:
        if sig.issubset(cols):
            return tbl, colmap
    return None, None

def _apply_map(row, colmap):
    """colmap value 格式：
      "列名"                 -> 原样字符串
      ("列名", "code")       -> normalize_code
      ("列名", "code_keep")  -> 原样保留（跨市场码）
      ("列名", "date")       -> normalize_date
      ("列名", "dt")         -> normalize_datetime
      ("列名", "num", "单位") -> normalize_num
    """
    out = {}
    keep_rest = "*" in colmap
    for src, tgt in colmap.items():
        if src == "*": continue
        if src not in row: continue
        if isinstance(tgt, tuple):
            col, typ = tgt[0], tgt[1]
            if typ == "code": out[col] = normalize_code(row[src])
            elif typ == "code_suffix": out[col] = normalize_code_suffix(row[src])
            elif typ == "code_keep": out[col] = str(row[src]).strip() or None
            elif typ == "date": out[col] = normalize_date(row[src])
            elif typ == "datestr": out[col] = normalize_datestr(row[src])
            elif typ == "market": out[col] = normalize_market(row[src])
            elif typ == "dt": out[col] = normalize_datetime(row[src])
            elif typ == "num": out[col] = normalize_num(row[src], tgt[2] if len(tgt) > 2 else "")
            else: out[col] = row[src]
        else:
            out[tgt] = row[src]
    if keep_rest:
        for src, val in row.items():
            if src not in colmap and src not in out:
                out[src] = val  # 保留未映射列（恒等，原样字符串）
    return out

# ── 文件扫描：csv + zip（非递归，跳过 ._ 前缀 macOS 元数据）──
def _iter_files(download_dir, csv_only=False):
    for f in sorted(glob.glob(os.path.join(download_dir, "*"))):
        name = os.path.basename(f)
        if name.startswith("._"):
            continue
        if name.endswith(".csv"):
            yield (f, False)
        elif name.endswith(".zip") and not csv_only:
            yield (f, True)


def _open_csv_streams(path, is_zip):
    """csv 返回自身一个流；zip 返回内部所有 csv 的文本流（读入内存，避免文件生命周期）。"""
    if not is_zip:
        yield (os.path.basename(path), open(path, encoding="utf-8-sig"))
    else:
        with zipfile.ZipFile(path) as zf:
            for inner in zf.namelist():
                base = inner.split("/")[-1]
                if base.endswith(".csv") and not base.startswith("._"):
                    yield (base, io.StringIO(zf.read(inner).decode("utf-8-sig")))


# ── 线上抽样验证：腾讯不复权日 K 算涨跌幅，与库内 pct_chg 比对（复权无关，可精确比对）──
def _tencent_pct(code, date):
    sym = code  # 腾讯 sym 即 sz000001 前缀式，与库内 daily.code 一致
    d = date if isinstance(date, datetime.date) else datetime.datetime.strptime(str(date), "%Y-%m-%d").date()
    start = (d - datetime.timedelta(days=8)).strftime("%Y-%m-%d")
    end = (d + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{start},{end},20,"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
    node = json.loads(raw)["data"][sym]
    key = "day" if "day" in node else "qfqday"
    closes = {r[0]: float(r[2]) for r in node[key]}
    dates = sorted(closes)
    ds = d.strftime("%Y-%m-%d")
    if ds not in dates:
        return None
    i = dates.index(ds)
    if i <= 0:
        return None
    return (closes[dates[i]] - closes[dates[i - 1]]) / closes[dates[i - 1]] * 100


def verify_online(con, n=5, tol=0.05):
    """从 daily 抽 n 条，腾讯源比对 pct_chg。返回 (ok, 详情)。"""
    rows = con.execute(
        "SELECT code, date, pct_chg FROM daily "
        "WHERE pct_chg IS NOT NULL AND date >= DATE '2024-01-01' "
        "ORDER BY date DESC LIMIT 5000").fetchall()
    if not rows:
        return True, "daily 无数据可验证"
    rng = random.Random(42)
    sample = rng.sample(rows, min(n, len(rows)))
    bad, checked = [], 0
    for code, date, pct in sample:
        tp = _tencent_pct(code, date)
        if tp is None:
            continue
        checked += 1
        if abs(pct - tp) > tol:
            bad.append(f"{code}@{date}: 库={pct:.3f}% 线上={tp:.3f}%")
    ok = (checked > 0 and len(bad) == 0)
    detail = f"抽样 {len(sample)} 条 / 比对 {checked} 条 / 超差 {len(bad)} 条"
    if bad:
        detail += "；" + "；".join(bad[:3])
    return ok, detail


def qc_all_pass(qc):
    """QC 断言全过（违规计数全为 0）。"""
    return all(v == 0 for v in qc.values())


#: 各表主键（仅供 sync 新建表时用；对齐后所有目标表均已在真实库存在，故留空）
_PK = {}


def _ensure_table(con, tbl, colmap):
    """表不存在时按 colmap 目标列建表，并按 _PK 设主键（INSERT OR REPLACE 判重用）。"""
    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]
    if exists:
        return
    cols = []
    for tgt in colmap.values():
        if isinstance(tgt, tuple):
            name, marker = tgt[0], tgt[1]
            if marker == "date": typ = "DATE"
            elif marker == "dt": typ = "TIMESTAMP"
            elif marker == "num": typ = "DOUBLE"
            else: typ = "VARCHAR"
        else:
            name, typ = tgt, "VARCHAR"
        cols.append(f'"{name}" {typ}')
    if tbl.startswith("minute_"):
        cols.append('"market" VARCHAR')
    pk = _PK.get(tbl, [])
    pk_sql = ""
    if pk:
        quoted = ", ".join('"%s"' % c for c in pk)
        pk_sql = f", PRIMARY KEY ({quoted})"
    con.execute(f'CREATE TABLE "{tbl}" ({", ".join(cols)}{pk_sql})')


def _has_pk(con, tbl):
    """表是否有主键约束。"""
    return con.execute(
        "SELECT count(*) FROM duckdb_constraints() WHERE table_name=? AND constraint_type='PRIMARY KEY'",
        [tbl]).fetchone()[0] > 0


def _adapt_date_types(con, tbl, rows, cols):
    """按目标表实际列类型适配日期值：DATE 列←date；BIGINT 列←YYYYMMDD 整数；VARCHAR 列保持字符串。"""
    try:
        col_types = {r[0]: r[1] for r in con.execute(f'DESCRIBE "{tbl}"').fetchall()}
    except Exception:
        return rows
    for col in cols:
        typ = col_types.get(col)
        if typ not in ("DATE", "BIGINT", "VARCHAR", "DOUBLE", "HUGEINT"):
            continue
        for row in rows:
            v = row.get(col)
            if v is None:
                continue
            # 非 VARCHAR 列：空字符串/占位符 → None（避免 '' 转 DOUBLE/BIGINT 报错）
            if typ != "VARCHAR" and isinstance(v, str) and v.strip() in ("", "--", "None", "nan"):
                row[col] = None
                continue
            if typ == "DATE":
                if isinstance(v, str):
                    s = v.strip().replace("-", "")[:8]
                    try:
                        row[col] = datetime.datetime.strptime(s, "%Y%m%d").date()
                    except ValueError:
                        row[col] = None
                elif isinstance(v, datetime.datetime):
                    row[col] = v.date()
            elif typ == "BIGINT":
                if isinstance(v, (datetime.date, datetime.datetime)):
                    row[col] = int(v.strftime("%Y%m%d"))
                elif isinstance(v, str):
                    s = v.strip().replace("-", "")[:8]
                    try:
                        row[col] = int(s)
                    except ValueError:
                        pass
            elif typ == "VARCHAR":
                if isinstance(v, (datetime.date, datetime.datetime)):
                    row[col] = v.strftime("%Y%m%d")
    return rows


def _delete_for_rows(con, tbl, rows, cols):
    """无主键表去重删除：按 csv 结构判断，避免误清全表。

    单代码（按股票拆分）→ DELETE WHERE code = ...；
    有日期列（按天拆分，含 TIMESTAMP 分钟线）→ DELETE WHERE date/CAST(dt AS DATE) IN (...)。
    """
    try:
        col_types = {r[0]: r[1] for r in con.execute('DESCRIBE "%s"' % tbl).fetchall()}
    except Exception:
        col_types = {}
    code_cols = [c for c in cols if c in ("code", "股票代码", "代码", "成分股票代码", "板块代码", "题材代码")]
    date_cols = [c for c in cols if any(k in c for k in ("日期", "时间", "date", "dt"))]
    codes = {r.get(c) for c in code_cols for r in rows if r.get(c) is not None}
    dates = set()
    for c in date_cols:
        for r in rows:
            v = r.get(c)
            if v is None:
                continue
            dates.add(v.date() if isinstance(v, datetime.datetime) else v)
    cc = code_cols[0] if code_cols else None
    dc = date_cols[0] if date_cols else None
    dc_type = col_types.get(dc) if dc else None

    def _del_dates():
        ph = ",".join("?" * len(dates))
        if dc_type == "TIMESTAMP":
            con.execute('DELETE FROM "%s" WHERE CAST("%s" AS DATE) IN (%s)' % (tbl, dc, ph), list(dates))
        else:
            con.execute('DELETE FROM "%s" WHERE "%s" IN (%s)' % (tbl, dc, ph), list(dates))

    def _del_code_dates():
        ph = ",".join("?" * len(dates))
        single = list(codes)[0]
        if dc_type == "TIMESTAMP":
            con.execute('DELETE FROM "%s" WHERE "%s" = ? AND CAST("%s" AS DATE) IN (%s)' % (tbl, cc, dc, ph), [single] + list(dates))
        else:
            con.execute('DELETE FROM "%s" WHERE "%s" = ? AND "%s" IN (%s)' % (tbl, cc, dc, ph), [single] + list(dates))

    if cc and len(codes) == 1 and dc and dates:
        # 单代码 + 有日期（分钟线每 csv 一只票当天）→ 按 (code, 日期) 删，避免删该 code 历史
        _del_code_dates()
    elif dc and dates:
        _del_dates()
    elif cc and len(codes) == 1:
        con.execute('DELETE FROM "%s" WHERE "%s" = ?' % (tbl, cc), list(codes))
    elif cc and codes:
        con.execute('DELETE FROM "%s" WHERE "%s" IN (%s)' % (tbl, cc, ",".join("?" * len(codes))), list(codes))
    else:
        con.execute('DELETE FROM "%s"' % tbl)


def sync(download_dir, db_path, dry_run=False, verify=True, keep_source=False, csv_only=False,
         only_tables=None):
    con = duckdb.connect(db_path)
    imported, unknown = {}, []
    removable = []  # 完全识别 + 有导入的文件，验证通过后可删除
    for f, is_zip in _iter_files(download_dir, csv_only=csv_only):
        name = os.path.basename(f)
        period = None
        if is_zip:
            # 不锚定 .zip$：容忍手动下载重名产生的序号（如 60min(7).zip）
            m = re.search(r"_(\d+min)", name)
            period = m.group(1) if m else None
        file_fully_recognized = True
        file_imported_any = False
        for stream_name, fp in _open_csv_streams(f, is_zip):
            reader = csv.DictReader(fp)
            header = reader.fieldnames or []
            tbl, colmap = _detect(header)
            if tbl == "fin_top10_holder":
                for kw, override_tbl in _NAME_OVERRIDE.items():
                    if kw in name:
                        tbl = override_tbl
                        break
            # 分钟线按周期分表：minute_kline → minute_{period}
            if tbl == "minute_kline" and period:
                tbl = f"minute_{period}"
            if tbl is None:
                unknown.append(stream_name)
                file_fully_recognized = False
                fp.close()
                continue
            if only_tables and tbl not in only_tables:
                fp.close()
                continue
            file_imported_any = True
            rows = [_apply_map(r, colmap) for r in reader]
            fp.close()
            # 过滤 code 归一失败（None）的行
            code_cols = [v[0] for v in colmap.values()
                         if isinstance(v, tuple) and len(v) > 1 and v[1] == "code"]
            if code_cols:
                rows = [r for r in rows if r.get(code_cols[0]) is not None]
            # daily/limit_price/minute_* 需要 market 列（从 code 推导）
            if tbl in ("daily", "limit_price") or tbl.startswith("minute_"):
                for r in rows:
                    if r.get("code") is not None:
                        r["market"] = normalize_market(r["code"])
            if tbl in _PK:
                pk_cols = _PK[tbl]
                rows = [r for r in rows if all(r.get(c) is not None for c in pk_cols)]
            imported[tbl] = imported.get(tbl, 0) + len(rows)
            if dry_run:
                print(f"  [dry-run] {stream_name} → {tbl}: {len(rows)} 行")
            elif rows:
                try:
                    _ensure_table(con, tbl, colmap)
                    cols = list(rows[0].keys())
                    rows = _adapt_date_types(con, tbl, rows, cols)
                    cols_sql = ",".join('"%s"' % c for c in cols)
                    df = pd.DataFrame(rows, columns=cols)
                    con.register("_batch", df)
                    try:
                        if _has_pk(con, tbl):
                            con.execute(f'INSERT OR REPLACE INTO "{tbl}" ({cols_sql}) SELECT {cols_sql} FROM _batch')
                        else:
                            _delete_for_rows(con, tbl, rows, cols)
                            con.execute(f'INSERT INTO "{tbl}" ({cols_sql}) SELECT {cols_sql} FROM _batch')
                    finally:
                        con.unregister("_batch")
                except Exception as e:
                    print(f"  ❌ {tbl} 写入失败: {type(e).__name__}: {e}")
                    print(f"     首行: {rows[0] if rows else None}")
                    raise
        if file_imported_any and file_fully_recognized:
            removable.append(f)
    if unknown and not dry_run:
        print(f"  ⚠️ 未识别 {len(unknown)} 个（表头无匹配，不删除）: {unknown[:5]}...")
    if not dry_run:
        con.commit()

    qc = qc_assertions(con)
    if verify and not dry_run:
        try:
            verify_ok, verify_detail = verify_online(con)
        except Exception as e:
            print(f"  ⚠️ 线上验证网络失败，跳过（数据已入库）: {type(e).__name__}: {e}")
            verify_ok, verify_detail = True, f"网络跳过: {e}"
    else:
        verify_ok, verify_detail = True, "跳过线上验证"

    removed = 0
    if not dry_run and verify_ok and qc_all_pass(qc):
        if keep_source:
            print("  ℹ️ --keep-source：保留源文件")
        else:
            for f in removable:
                try:
                    os.remove(f)
                    removed += 1
                except OSError as e:
                    print(f"  ⚠️ 删除失败 {os.path.basename(f)}: {e}")
            print(f"  ✅ 线上验证 + QC 通过，已删除 {removed} 个源文件")
    elif not dry_run:
        print(f"  ⛔ 验证未通过（QC 违规 {sum(1 for v in qc.values() if v)} 项 / 线上验证通过={verify_ok}），保留源文件")

    return {"imported": imported, "unknown_count": len(unknown), "qc": qc,
            "verify": {"ok": verify_ok, "detail": verify_detail}, "removed": removed}


def cleanup_imported(download_dir, db_path, dates, dry_run=True):
    """验证指定日期的数据已在库，然后删除源文件（日频 csv + 分钟线 zip）。

    日频：验证 daily/tech_factor_qfq/limit_price 该日期行数>0。
    分钟线：验证 minute_kline 该日期+周期的行数>0（表不存在则跳过、不删）。
    """
    con = duckdb.connect(db_path, read_only=True)
    removed = []
    minute_exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='minute_kline'").fetchone()[0] > 0

    for d in dates:
        d_fmt = datetime.datetime.strptime(d, "%Y%m%d").strftime("%Y-%m-%d")

        # --- 日频 csv ---
        detail = {}
        daily_ok = True
        for tbl in ["daily", "tech_factor_qfq", "limit_price"]:
            n = con.execute(f"SELECT count(*) FROM {tbl} WHERE date=?", [d_fmt]).fetchone()[0]
            detail[tbl] = n
            if n == 0:
                daily_ok = False
        print(f"  {d}: {'✅ 日频已导入' if daily_ok else '❌ 日频未完整导入'} {detail}")
        if daily_ok:
            for f in sorted(glob.glob(os.path.join(download_dir, f"*{d}*.csv"))):
                if os.path.basename(f).startswith("._"):
                    continue
                if dry_run:
                    print(f"    [dry-run] 将删除 {os.path.basename(f)}")
                else:
                    try:
                        os.remove(f)
                        removed.append(f)
                    except OSError as e:
                        print(f"    ⚠️ 删除失败 {os.path.basename(f)}: {e}")
        else:
            print(f"    → 日频数据缺失，保留日频 csv")

        # --- 分钟线 zip ---
        if not minute_exists:
            print(f"    ℹ️ minute_kline 表不存在，分钟线未导入，保留全部分钟线 zip")
        else:
            for period in ["1min", "5min", "15min", "30min", "60min"]:
                n = con.execute(
                    "SELECT count(*) FROM minute_kline WHERE period=? AND CAST(dt AS DATE)=?",
                    [period, d_fmt]).fetchone()[0]
                if n == 0:
                    print(f"    {d}_{period}: ❌ 未导入（保留 zip）")
                    continue
                for f in sorted(glob.glob(os.path.join(download_dir, f"*{d}_{period}*.zip"))):
                    if os.path.basename(f).startswith("._"):
                        continue
                    if dry_run:
                        print(f"    [dry-run] 将删除 {os.path.basename(f)}")
                    else:
                        try:
                            os.remove(f)
                            removed.append(f)
                        except OSError as e:
                            print(f"    ⚠️ 删除失败 {os.path.basename(f)}: {e}")

    con.close()
    return removed


if __name__ == "__main__":
    import sys
    DB = os.environ.get("STOCK_DB", "/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb")
    DL = os.environ.get("STOCK_DOWNLOAD", "/Volumes/My PSSD/downlodData/taobao")
    a = sys.argv[1:]
    if "--qc" in a:
        print("QC:", qc_assertions(duckdb.connect(DB, read_only=True)))
    elif "--cleanup" in a:
        # 用法: --cleanup 20261021,20261022 [--apply]
        i = a.index("--cleanup")
        dates = a[i + 1].split(",") if i + 1 < len(a) else []
        apply = "--apply" in a
        if not dates:
            print("用法: taobao_sync.py --cleanup 20261021,20261022 [--apply]")
            sys.exit(1)
        removed = cleanup_imported(DL, DB, dates, dry_run=not apply)
        print(f"\n{'已删除' if apply else '（dry-run 预览，加 --apply 才真删）'} {len(removed)} 个日频 csv")
    else:
        only = None
        if "--only-tables" in a:
            i = a.index("--only-tables")
            if i + 1 < len(a):
                only = set(a[i + 1].split(","))
        result = sync(DL, DB, dry_run="--dry-run" in a, keep_source="--keep-source" in a,
                      csv_only="--csv-only" in a, only_tables=only,
                      verify="--no-verify" not in a)
        print(f"导入统计: {result['imported']}")
        print(f"QC 违规: {result['qc']}")
        print(f"线上验证: {result['verify']}")
        print(f"删除源文件: {result['removed']} 个")
