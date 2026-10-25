"""regime（regime 维度验证的确定性方法）——任务 16 的前置。

实现 eval-dataset.md 6.2.1「分桶边界怎么确定」的三原则，作为确定性代码：

1. **等频分位（首选）**：连续量按样本量等分（如三分位），保证每桶 n≥5 可统计。
2. **已验证断点**：只在「超额收益翻转点」设断点；整数断点除非数据证明是转折点，否则禁用。
3. **n≥5 校验**：每桶 n<5 合并相邻桶，不报结论。

并落地 6.2.3 的三态判定（✅纳入 / ⚠️待定 / ❌删除）。
纯函数、不连库、可测；实际的 15 项维度打标与超额计算由上层接 judge 产出。
"""

from regime.buckets import (
    assign_bucket,
    bucket_stats,
    classify,
    find_flip,
    is_monotonic,
    min_n_violations,
    quantile_edges,
)
from regime.tagging import (
    beta_bucket,
    limit_up_bucket,
    quantile_three,
    tag_day,
)

__all__ = [
    "assign_bucket",
    "beta_bucket",
    "bucket_stats",
    "classify",
    "find_flip",
    "is_monotonic",
    "limit_up_bucket",
    "min_n_violations",
    "quantile_edges",
    "quantile_three",
    "tag_day",
]
