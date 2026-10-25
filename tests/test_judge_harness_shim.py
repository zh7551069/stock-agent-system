"""判决器统一回归测试：judge_harness.py 必须已退役为委托 shim。

钉死「避免两套判决器并存」的决策：docs/plan03-site/scripts/judge_harness.py
不再是独立实现，必须指向权威包 judge 的原语，且带退役标记。
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

SHIM = (pathlib.Path(__file__).resolve().parents[1]
        / "docs" / "plan03-site" / "scripts" / "judge_harness.py")


def _load_shim():
    spec = importlib.util.spec_from_file_location("judge_harness_shim", SHIM)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_shim_is_marked_deprecated():
    mod = _load_shim()
    assert "退役" in (mod.__doc__ or ""), "shim 必须带退役标记"


def test_shim_reexports_authoritative_primitives():
    mod = _load_shim()
    assert mod.judge.__module__ == "judge.outcome"
    assert mod.Decision.__module__ == "judge.outcome"
    assert mod.BulkLibrary.__module__ == "judge.bulk"
    assert mod.paired_t.__module__ == "judge.stats"


def test_shim_exposes_smoke_cli_entrypoint():
    mod = _load_shim()
    assert callable(mod.main), "shim 需保留 --smoke CLI 入口"
