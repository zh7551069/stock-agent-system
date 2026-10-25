"""regime · 消息面打标框架单测。"""

from regime.news import NewsItem, classify_news


def _fake_classifier():
    """按内容关键字分类（模拟外部 LLM）。"""
    def cls(content):
        if "重大" in content or "涨停" in content:
            return "强"
        if "利好" in content or "公告" in content:
            return "弱"
        if "无" in content:
            return "无"
        return "待考证"
    return cls


def test_classify_news_aggregates_strongest():
    items = [
        NewsItem("2026-01-05", "东财", "利好公告"),
        NewsItem("2026-01-05", "公告", "重大合同"),
        NewsItem("2026-01-06", "新闻", "无重要消息"),
    ]
    out = classify_news(items, _fake_classifier())
    assert out["2026-01-05"] == "强"   # 弱 + 强 → 取强
    assert out["2026-01-06"] == "无"


def test_classify_news_unknown_when_only_uncertified():
    items = [NewsItem("2026-01-05", "x", "模糊内容")]
    out = classify_news(items, lambda c: "待考证")
    assert out["2026-01-05"] == "待考证"


def test_classify_news_skips_uncertified_in_aggregation():
    # 弱 + 待考证 → 弱（待考证不参与分层）
    def cls(c):
        return "弱" if "利好" in c else "待考证"
    items = [NewsItem("2026-01-05", "x", "利好"), NewsItem("2026-01-05", "y", "模糊")]
    assert classify_news(items, cls)["2026-01-05"] == "弱"
