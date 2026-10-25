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
    return None

def normalize_date(d):
    if isinstance(d, datetime.date): return d
    if isinstance(d, datetime.datetime): return d.date()
    s = str(d).strip()
    for f in ('%Y-%m-%d','%Y%m%d'):
        try: return datetime.datetime.strptime(s, f).date()
        except ValueError: pass
    return None

def normalize_market(c): return c[:2] if c else None

_UNIT = {"元":1.0,"千元":1e3,"万元":1e4,"亿元":1e8,"百万元":1e6,"万股":1e4,"手":100,"万笔":1e4}
def normalize_num(v, unit):
    if v is None or v == '' or v == '--' or v == 'None': return None
    try: return float(v) * _UNIT.get(unit, 1.0)
    except (ValueError, TypeError): return None

# ── SOURCE_MAP：表头签名 → (目标表, {源列:(目标列,单位)}) ──
# 签名 = 表头里能唯一区分该类型的关键列集合；匹配 = 签名 ⊆ 表头
# 单位 None 表示 code/date 专用归一
SOURCE_MAP = [
    # 日线行情
    (frozenset({"开盘价","最高价","最低价","收盘价","成交量(手)","成交额(千元)","市盈率"}), "daily", {
        "股票代码":"code","交易日期":"date","开盘价":"open","最高价":"high","最低价":"low","收盘价":"close",
        "成交量(手)":("volume","手"),"成交额(千元)":("amount","千元"),"涨跌幅":"pct_chg","换手率":("turnover","%"),
        "总市值(万元)":("total_mv","万元"),"流通市值(万元)":("circ_mv","万元")}),
    # 技术因子（前复权口径权威，code B 套）
    (frozenset({"复权因子","MA5","MA10","MA20"}), "tech_factor_qfq", {
        "股票代码":"code","交易日期":"date","开盘价":"open","最高价":"high","最低价":"low","收盘价":"close",
        "成交量(手)":("vol_hand","手"),"成交额(千元)":("amount_k","千元"),"涨跌幅(%)":"pct_chg","换手率(%)":"turnover"}),
    # 每日涨跌停价格
    (frozenset({"昨日收盘价","涨停价","跌停价"}), "limit_price", {
        "股票代码":"code","交易日期":"date","昨日收盘价":"prev_close","涨停价":"limit_up","跌停价":"limit_down"}),
    # 每日停复牌
    (frozenset({"停复牌时间段","停复牌类型"}), "suspension", {
        "股票代码":"code","交易日期":"date","停复牌时间段":"period","停复牌类型":"type"}),
    # 大盘资金流向
    (frozenset({"上证收盘点位","深证收盘点位"}), "market_flow_daily", {
        "交易日期":"date","上证收盘点位":"sh_close","上证涨跌幅(%)":"sh_pct","深证收盘点位":"sz_close","深证涨跌幅(%)":"sz_pct",
        "主力净流入(元)":("main_inflow","元")}),
    # 个股资金流（主力，今日主力净流入额）
    (frozenset({"今日主力净流入额（万元）","今日超大单净流入额（万元）"}), "moneyflow_stock", {
        "交易日期":"date","股票代码":"code","今日主力净流入额（万元）":("main_net","万元")}),
    # 个股资金流（明细，资金净流入+5日主力）
    (frozenset({"资金净流入(万元)","5日主力净额(万元)"}), "stock_flow", {
        "交易日期":"date","股票代码":"code","资金净流入(万元)":("net_inflow","万元"),"5日主力净额(万元)":("main_5d","万元")}),
    # 订单流（小单/中单/大单/特大单买卖）
    (frozenset({"小单买入量(手)","中单买入量(手)"}), "order_flow", {
        "股票代码":"code","交易日期":"date",
        "小单买入量(手)":("small_buy_vol","手"),"小单买入金额(万元)":("small_buy_amt","万元"),
        "中单买入量(手)":("mid_buy_vol","手"),"大单买入量(手)":("big_buy_vol","手"),"特大单买入量(手)":("xbig_buy_vol","手")}),
    # 行业资金流
    (frozenset({"行业代码","行业名称","领涨股票名称"}), "industry_flow", {
        "交易日期":"date","行业代码":"industry_code","行业名称":"industry_name",
        "流入资金(亿元)":("inflow","亿元"),"流出资金(亿元)":("outflow","亿元"),"净额(亿元)":("net","亿元")}),
    # 板块资金流（领涨股票名称 + 行业涨跌幅）
    (frozenset({"板块代码","板块名称","领涨股票名称","行业涨跌幅(%)"}), "board_flow", {
        "交易日期":"date","板块代码":"board_code","板块名称":"board_name",
        "流入资金(亿元)":("inflow","亿元"),"流出资金(亿元)":("outflow","亿元"),"净额(亿元)":("net","亿元")}),
    # 板块资金流细分（数据类型 + 主力净流入净额）
    (frozenset({"数据类型","板块代码","主力净流入净额(元)"}), "board_flow_detail", {
        "交易日期":"date","数据类型":"data_type","板块代码":"board_code","板块名称":"board_name",
        "主力净流入净额(元)":("main_net","元")}),
    # 涨停池
    (frozenset({"涨停原因","榜单类别","封单额(元)"}), "zt_pool", {
        "交易日期":"date","股票代码":"code","涨停原因":"reason","榜单类别":"category","涨停标签":"tag",
        "封单额(元)":("seal_amount","元"),"换手率%":"turnover"}),
    # 自然涨停（涨停时间/开板时间）
    (frozenset({"涨停时间","开板时间","最后涨停时间"}), "zt_pool_natural_up", {
        "代码":"code","交易时间":"date","涨停原因":"reason","标签":"tag","板块":"board"}),
    # 连板天梯
    (frozenset({"连板次数"}), "zt_ladder", {
        "股票代码":"code","股票名称":"name","交易日期":"date","连板次数":"ladder_count"}),
    # 涨停最强板块
    (frozenset({"上榜天数","连板高度","涨停家数"}), "zt_strong_board", {
        "板块代码":"board_code","板块名称":"board_name","交易日期":"date","涨停家数":"zt_count","连板高度":"ladder_height"}),
    # 龙虎榜明细
    (frozenset({"龙虎榜净买入额(元)","龙虎榜成交额(元)"}), "lhb_daily", {
        "交易日期":"date","股票代码":"code","龙虎榜净买入额(元)":("net_buy","元"),"龙虎榜成交额(元)":("total","元"),"上榜理由":"reason"}),
    # 龙虎榜机构明细
    (frozenset({"营业部名称","净成交额(元)"}), "lhb_inst", {
        "交易日期":"date","股票代码":"code","营业部名称":"dept","净成交额(元)":("net","元"),"买卖类型":"side"}),
    # 行业热度榜（热度值 + 上榜解读）
    (frozenset({"热度值","排行榜获取时间"}), "hot_rank", {
        "交易日期":"date","股票代码":"code","股票名称":"name","排行":"rank","热度值":"hot","标签":"tag"}),
    # ST 列表
    (frozenset({"ST类型"}), "st_stock", {
        "股票代码":"code","股票名称":"name","交易日期":"date","ST类型":"st_type"}),
    # 股票曾用名
    (frozenset({"更名日期","更名前简称"}), "stock_rename", {
        "代码":"code","名称":"name","更名日期":"date","更名前简称":"old_name","更名后简称":"new_name"}),
    # 退市股票列表
    (frozenset({"退市日期","实控人名称"}), "stock_delist", {
        "TS代码":"ts_code","股票代码":"code","股票名称":"name","上市日期":"list_date","退市日期":"delist_date"}),
    # ETF 基础信息
    (frozenset({"ETF代码","跟踪指数代码"}), "etf_info", {
        "ETF代码":"etf_code","ETF简称":"name","跟踪指数代码":"index_code","上市日期":"list_date","ETF类型":"etf_type"}),
    # 财务信息
    (frozenset({"流通股本","股东人数"}), "fin_company_snapshot", {
        "股票代码":"code","股票名称":"name","更新日期":"update_date","流通股本":"float_share","总股本":"total_share"}),
    # 沪深港通资金流向
    (frozenset({"北向资金(百万元)","南向资金(百万元)"}), "hk_connect_flow", {
        "交易日期":"date","北向资金(百万元)":("north","百万元"),"南向资金(百万元)":("south","百万元")}),
    # 港股通每日成交统计
    (frozenset({"买入成交金额(亿元)","卖出成交金额(亿元)"}), "hk_connect_daily", {
        "交易日期":"date","买入成交金额(亿元)":("buy_amt","亿元"),"卖出成交金额(亿元)":("sell_amt","亿元")}),
]

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
    out = {}
    for src, tgt in colmap.items():
        if src not in row: continue
        if tgt == "code": out[tgt] = normalize_code(row[src])
        elif tgt == "date": out[tgt] = normalize_date(row[src])
        elif isinstance(tgt, tuple): out[tgt[0]] = normalize_num(row[src], tgt[1])
        else: out[tgt] = row[src]
    return out

# ── 文件扫描：csv + zip（非递归，跳过 ._ 前缀 macOS 元数据）──
def _iter_files(download_dir):
    for f in sorted(glob.glob(os.path.join(download_dir, "*"))):
        name = os.path.basename(f)
        if name.startswith("._"):
            continue
        if name.endswith(".csv"):
            yield (f, False)
        elif name.endswith(".zip"):
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


def sync(download_dir, db_path, dry_run=False, verify=True, keep_source=False):
    con = duckdb.connect(db_path)
    imported, unknown = {}, []
    removable = []  # 完全识别 + 有导入的文件，验证通过后可删除
    for f, is_zip in _iter_files(download_dir):
        name = os.path.basename(f)
        file_fully_recognized = True
        file_imported_any = False
        for stream_name, fp in _open_csv_streams(f, is_zip):
            reader = csv.DictReader(fp)
            header = reader.fieldnames or []
            tbl, colmap = _detect(header)
            if tbl is None:
                unknown.append(stream_name)
                file_fully_recognized = False
                fp.close()
                continue
            file_imported_any = True
            rows = [_apply_map(r, colmap) for r in reader]
            fp.close()
            if "code" in colmap.values():
                rows = [r for r in rows if r.get("code") is not None]
            imported[tbl] = imported.get(tbl, 0) + len(rows)
            if dry_run:
                print(f"  [dry-run] {stream_name} → {tbl}: {len(rows)} 行")
            elif rows:
                cols = list(rows[0].keys())
                con.executemany(
                    f"INSERT OR REPLACE INTO {tbl} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])
        if file_imported_any and file_fully_recognized:
            removable.append(f)
    if unknown and not dry_run:
        print(f"  ⚠️ 未识别 {len(unknown)} 个（表头无匹配，不删除）: {unknown[:5]}...")
    if not dry_run:
        con.commit()

    qc = qc_assertions(con)
    verify_ok, verify_detail = verify_online(con) if (verify and not dry_run) else (True, "跳过线上验证")

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


if __name__ == "__main__":
    import sys
    DB = os.environ.get("STOCK_DB", "/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/duckdb/taobao_minute.duckdb")
    DL = os.environ.get("STOCK_DOWNLOAD", "/Volumes/My PSSD/downlodData/taobao")
    a = sys.argv[1:]
    if "--qc" in a:
        print("QC:", qc_assertions(duckdb.connect(DB, read_only=True)))
    else:
        result = sync(DL, DB, dry_run="--dry-run" in a, keep_source="--keep-source" in a)
        print(f"导入统计: {result['imported']}")
        print(f"QC 违规: {result['qc']}")
        print(f"线上验证: {result['verify']}")
        print(f"删除源文件: {result['removed']} 个")
