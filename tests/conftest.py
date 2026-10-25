"""pytest 共享配置（tests/ 下的 conftest 会被 pytest 自动加载）。

作用：
1. 仓库根加入 sys.path（与 pyproject 的 pythonpath 双保险，替代各测试文件的 sys.path.insert）
2. `sys.dont_write_bytecode = True` 禁用 .pyc 写入 —— 避免「变异测试/改完代码后
   脏 .pyc 缓存造成假失败」的坑（本项目实测踩过）
3. 统一 DB 路径：复用 `judge.outcome.DB_PATH`（可用环境变量 `STOCK_DB` 覆盖）
4. 提供 `db` / `db_path` fixture 与 `requires_db` marker
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 必须在导入被测模块之前设置，才能阻止它们写 .pyc
sys.dont_write_bytecode = True

import pytest  # noqa: E402

from judge.outcome import DB_PATH  # noqa: E402


@pytest.fixture(scope="session")
def db_path() -> pathlib.Path:
    """主库路径（可用环境变量 STOCK_DB 覆盖默认外接盘路径）。"""
    return DB_PATH


@pytest.fixture(scope="session")
def db():
    """只读 DuckDB 连接（session 级复用）；主库未挂载则 skip。"""
    import duckdb

    if not DB_PATH.exists():
        pytest.skip(f"主库未挂载（外接盘）：{DB_PATH}")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    yield con
    con.close()


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_db: 依赖主库（外接盘）的测试")
