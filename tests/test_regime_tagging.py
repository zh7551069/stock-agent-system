"""regime · 市场级维度打标（确定性分桶）单测。"""

from regime.tagging import beta_bucket, breadth_bucket, cycle_stage, limit_up_bucket, quantile_three, tag_day


def test_limit_up_bucket():
    assert limit_up_bucket(12) == "<30"
    assert limit_up_bucket(30) == "30-60"
    assert limit_up_bucket(59) == "30-60"
    assert limit_up_bucket(60) == "60+"
    assert limit_up_bucket(120) == "60+"


def test_limit_up_bucket_custom_edges():
    assert limit_up_bucket(40, edges=(50, 100)) == "<50"
    assert limit_up_bucket(75, edges=(50, 100)) == "50-100"


def test_beta_bucket():
    assert beta_bucket(-0.02) == "跌"
    assert beta_bucket(0.03) == "涨"
    assert beta_bucket(0.001) == "平"
    assert beta_bucket(-0.001) == "平"


def test_quantile_three():
    assert quantile_three(0.1) == "低"
    assert quantile_three(0.5) == "中"
    assert quantile_three(0.9) == "高"


def test_breadth_bucket():
    assert breadth_bucket(0.2) == "<30%"
    assert breadth_bucket(0.3) == "30-70%"
    assert breadth_bucket(0.7) == "30-70%"
    assert breadth_bucket(0.71) == ">70%"


def test_cycle_stage():
    assert cycle_stage(110, 105, 100) == "上升趋势"       # close>ma20>ma60
    assert cycle_stage(90, 95, 100) == "下降趋势"          # close<ma20<ma60
    assert cycle_stage(80, 95, 100) == "恐慌超跌"          # 偏离 ma20 超 0.93
    assert cycle_stage(102, 100, 105) == "筑底反弹"        # close>ma20 但 <ma60
    assert cycle_stage(98, 100, 95) == "顶部转弱"          # close<ma20 但 >ma60


def test_tag_day_produces_regime_label_columns():
    d = tag_day(limit_up_count=45, bench_pct_chg=-0.02, crowd_pctile=0.2, turnover_pctile=0.8)
    assert d == {
        "limit_up_cnt": "30-60",
        "beta_bucket": "跌",
        "crowd_bucket": "低",
        "turnover_q": "高",
        "news_level": None,
        "regime_ver": "regime:v1",
    }


def test_tag_day_news_level_passthrough():
    d = tag_day(limit_up_count=10, bench_pct_chg=0.0, crowd_pctile=0.5,
                turnover_pctile=0.5, news_level="待考证")
    assert d["news_level"] == "待考证"
    assert d["limit_up_cnt"] == "<30"
    assert d["beta_bucket"] == "平"
