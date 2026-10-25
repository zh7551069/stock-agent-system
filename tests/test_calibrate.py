"""calibrate.py 黑盒测试：恒等检验必须恒过。

第三方视角：同一序列自己减自己，配对差值必须恒等于 0 —— 这是「判决器无偏」的第一关。
"""
from __future__ import annotations

def test_identity_check_always_passes():
    from judge.calibrate import identity_check
    assert identity_check() is True, "恒等检验（自己减自己=0）必须恒过"
