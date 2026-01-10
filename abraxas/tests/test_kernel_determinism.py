from __future__ import annotations
from abraxas.core.kernel import AbraxasKernel
from abraxas.core.context import UserContext


def test_kernel_deterministic_same_inputs():
    k = AbraxasKernel()
    u = UserContext(user_id="x", tier="psychonaut")
    signals = {"pressure": 5, "motifs": ["housing", "rates"]}

    a = k.run_oracle(user=u, input_signals=signals, overlays_requested=["aalmanac"])
    b = k.run_oracle(user=u, input_signals=signals, overlays_requested=["aalmanac"])

    assert a["run_id"] == b["run_id"]
    assert a["provenance"] == b["provenance"]
