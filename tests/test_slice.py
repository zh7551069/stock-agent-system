"""slice.py 黑盒测试：分层归一分桶纯函数。

第三方视角：只看输入 → 输出。这些函数把原始字段映射到 regime 桶标签，
桶标签错了，分层判决结论就全错，故必须钉死。
"""
from __future__ import annotations

from judge.slice import bucket_time, norm_board, tercile, turnover_bucket

def test_norm_board_映射连板状态():
    assert norm_board("首板") == "首板"
    assert norm_board("2连板") == "2板"
    assert norm_board("4天3板") == "3板+"       # 取末位数字 3
    assert norm_board("10连板") == "3板+"
    assert norm_board("新上市未开板") == "新上市未开板"
    assert norm_board("新上市") == "新上市未开板"

def test_norm_board_空值():
    assert norm_board(None) is None
    assert norm_board("") is None

def test_bucket_time_分桶边界():
    assert bucket_time("09:30") == "早盘封板(<=10:00)"
    assert bucket_time("10:00") == "早盘封板(<=10:00)"   # 边界含 10:00
    assert bucket_time("10:01") == "盘中封板"
    assert bucket_time("13:29") == "盘中封板"
    assert bucket_time("13:30") == "尾盘封板(>=13:30)"   # 边界含 13:30
    assert bucket_time("14:59") == "尾盘封板(>=13:30)"

def test_bucket_time_非法输入():
    assert bucket_time(None) is None
    assert bucket_time("") is None
    assert bucket_time("abc") is None

def test_tercile_三分位():
    vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # lo = xs[int(10*0.33)] = xs[3] = 4；hi = xs[int(10*0.67)] = xs[6] = 7
    assert tercile(vals, 1) == "低"
    assert tercile(vals, 4) == "低"       # 含 lo 边界
    assert tercile(vals, 5) == "中"
    assert tercile(vals, 7) == "中"       # 含 hi 边界
    assert tercile(vals, 8) == "高"

def test_tercile_空值与None():
    assert tercile([], 5) is None
    assert tercile([1, 2, 3], None) is None

def test_turnover_bucket_边界():
    assert turnover_bucket(4.9) == "<5%"
    assert turnover_bucket(5) == "5-15%"
    assert turnover_bucket(15) == "5-15%"
    assert turnover_bucket(15.1) == ">15%"

def test_turnover_bucket_字符串与非法():
    assert turnover_bucket("4.5") == "<5%"     # 库中换手率可能是字符串
    assert turnover_bucket("abc") is None
    assert turnover_bucket(None) is None
