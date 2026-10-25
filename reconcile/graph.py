"""对账官 · 溯源图 + 信用传播（多步结构归因）。

信用传播（credit propagation）：当决策表现差（判决 rejected），把「责任」沿溯源图
的**依赖边**反向传播，每个上游节点的信用 = ``blame × decay^距离``，
距离 = 从决策节点出发的最短边数。这正是 self-evolution.md §4 的「沿依赖边做多步
结构归因，用图距离而非时间间隔」，以及 observability.md §5 的「定位因子失效/出场太慢」。

三层来源与图距离的对应（本实现按图距离衰减，比文档的「第0/1/2层」更精确）：
- 距离 1 = 本轮检索直接引用（决策 → 因子/知识卡/skill）
- 距离 2 = 直接祖先（因子 → 口径 / 知识卡 → 来源书）
- 距离 3 = 间接祖先（skill → 知识卡 → 来源书）
"""

from __future__ import annotations

import dataclasses
from collections import deque
from typing import Iterable, Optional


@dataclasses.dataclass(frozen=True)
class ProvenanceEdge:
    """溯源边：``src`` 引用 ``dst``（src 依赖 dst，如「决策 → 因子」「因子 → 口径」）。"""

    src: str
    dst: str


class ProvenanceGraph:
    """溯源图：节点为决策/因子/知识卡/skill/口径/来源，边为「谁引用了谁」。"""

    def __init__(self, edges: Iterable[ProvenanceEdge | tuple[str, str]]) -> None:
        self._edges = [e if isinstance(e, ProvenanceEdge) else ProvenanceEdge(*e) for e in edges]
        self._adj: dict[str, list[str]] = {}
        for e in self._edges:
            self._adj.setdefault(e.src, []).append(e.dst)

    def credit_propagate(self, root: str, *, blame: float = 1.0, decay: float = 0.5) -> dict[str, float]:
        """从 ``root``（决策节点）沿依赖边 BFS，``credit = blame × decay^距离``。

        返回 ``{节点: 信用}``（不含 root 本身；多路径取最短距离）。
        """
        credit: dict[str, float] = {}
        dist: dict[str, int] = {root: 0}
        queue: deque[str] = deque([root])
        while queue:
            node = queue.popleft()
            d = dist[node]
            for nxt in self._adj.get(node, []):
                nd = d + 1
                if nxt in dist and dist[nxt] <= nd:
                    continue  # 已按更短距离访问过
                dist[nxt] = nd
                credit[nxt] = blame * (decay ** nd)
                queue.append(nxt)
        return credit

    def distance(self, a: str, b: str) -> Optional[int]:
        """``a`` 沿引用链到 ``b`` 的最短边数；不可达返回 None。"""
        if a == b:
            return 0
        dist: dict[str, int] = {a: 0}
        queue: deque[str] = deque([a])
        while queue:
            node = queue.popleft()
            for nxt in self._adj.get(node, []):
                if nxt not in dist:
                    dist[nxt] = dist[node] + 1
                    if nxt == b:
                        return dist[nxt]
                    queue.append(nxt)
        return None
