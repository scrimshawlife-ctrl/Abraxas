from __future__ import annotations
import pytest
from abraxas.core.kernel import AbraxasKernel
from abraxas.core.context import UserContext


def test_tier_blocks_neon_genie_for_psychonaut():
    k = AbraxasKernel()
    u = UserContext(user_id="x", tier="psychonaut")
    with pytest.raises(PermissionError):
        k.run_oracle(user=u, input_signals={"pressure": 2}, overlays_requested=["neon_genie"])
