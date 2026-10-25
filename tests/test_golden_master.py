"""黄金样例（golden master）测试：钉住判决器输出 + 独立源交叉验证 pct_chg。

第三方视角：这 8 个样本的 pct_chg 已用独立源（腾讯 ifzq）交叉验证（涨跌幅复权无关、
可精确比对），判决器的完整输出（超额/可成交/原因）则作为「当前正确输出」钉住。
任何「数据漂移」或「代码/口径回归」都会让重跑结果偏离 golden 而失败——即数据漂移哨兵。

为何只交叉验证 pct_chg：前复权价（tech_factor_qfq）不同源口径有 0.3~0.6% 差异，
不能精确比对；而 pct_chg（涨跌幅）复权无关，实测与腾讯源 0.000 差异。
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

import duckdb
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from judge.outcome import DB_PATH, Decision, Library, judge  # noqa: E402

DB = DB_PATH
GOLDEN = pathlib.Path(__file__).parent / "golden" / "golden_samples.json"
requires_db = pytest.mark.skipif(not DB.exists(), reason="主库未挂载（外接盘）")


def _golden():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@requires_db
def test_golden_master_judge_outputs_stable():
    """判决器对固定样本的输出必须逐位复现（数据漂移 / 口径回归都会触发失败）。"""
    golden = _golden()
    with Library() as lib:
        for s in golden["samples"]:
            o = judge(Decision(s["code"], s["side"], dt.date.fromisoformat(s["signal_date"]),
                               horizons=tuple(s["horizons"])), lib)
            g = s["judge"]
            assert o.tradable == g["tradable"], f"{s['id']} tradable 漂移"
            assert o.reason == g["reason"], f"{s['id']} reason 漂移：{o.reason!r} != {g['reason']!r}"
            assert o.entry_date.isoformat() == g["entry_date"], f"{s['id']} entry_date 漂移"
            if g["entry_px"] is not None:
                assert o.entry_px == pytest.approx(g["entry_px"], abs=1e-5), \
                    f"{s['id']} entry_px 漂移：{o.entry_px} vs {g['entry_px']}"
            for k in s["horizons"]:
                gv = g["excess"].get(str(k))
                ov = o.excess.get(k)
                if gv is not None:
                    assert ov is not None, f"{s['id']} T+{k} 超额应为非空"
                    assert ov == pytest.approx(gv, abs=1e-6), \
                        f"{s['id']} T+{k} 超额漂移：{ov} vs {gv}"
                else:
                    assert ov is None, f"{s['id']} T+{k} 超额应为空（不可成交）"


@requires_db
def test_golden_master_pct_chg_not_drifted():
    """淘宝库 pct_chg 必须与独立源（腾讯 ifzq）交叉验证值一致（数据漂移哨兵）。"""
    golden = _golden()
    con = duckdb.connect(str(DB), read_only=True)
    try:
        checked = 0
        for s in golden["samples"]:
            if s["pct_chg_golden"] is None:
                continue  # 独立源未拉到该样本，跳过
            row = con.execute(
                "SELECT pct_chg FROM tech_factor_qfq WHERE code=? AND date=?",
                [s["code"], s["signal_date"]]).fetchone()
            assert row is not None, f"{s['id']} 淘宝库缺 pct_chg"
            assert abs(row[0] - s["pct_chg_golden"]) < 0.05, \
                f"{s['id']} pct_chg 漂移：库={row[0]} 独立源={s['pct_chg_golden']}"
            checked += 1
        assert checked >= 5, f"至少 5 个样本做过独立源交叉验证，实际 {checked}"
    finally:
        con.close()
