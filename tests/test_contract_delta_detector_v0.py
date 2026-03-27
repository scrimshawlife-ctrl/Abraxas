from __future__ import annotations

from pathlib import Path

import pytest

from abraxas.detectors.contract_delta_v0 import ContractDeltaError, detect_contract_deltas


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_contract_delta_detector_passes_known_fields(tmp_path: Path) -> None:
    sample = tmp_path / "test_sample_ok.py"
    _write(
        sample,
        """
from webpanel.models import RunState, AbraxasSignalPacket
run = RunState(run_id='id', created_at_utc='t', phase=1,
    signal=AbraxasSignalPacket(
        signal_id='sig', timestamp_utc='t', tier='psychonaut', lane='canon',
        payload={}, confidence={}, provenance_status='complete', invariance_status='pass',
        drift_flags=[], rent_status='paid', not_computable_regions=[]
    ),
    context={'context_id':'c','source_signal_id':'s','created_at_utc':'t',
        'stable_elements':[],'unstable_elements':[],'unknowns':[],
        'assumptions_inherited':[],
        'execution_lanes_allowed':['canon'],
        'risk_profile':{'risk_of_action':'low','risk_of_inaction':'low','risk_notes':'n'},
        'requires_human_confirmation':False,
        'recommended_interaction_mode':'present_options',
        'policy_basis':{}
    },
    requires_human_confirmation=False
)
packet = AbraxasSignalPacket(
    signal_id='sig', timestamp_utc='t', tier='psychonaut', lane='canon',
    payload={}, confidence={}, provenance_status='complete', invariance_status='pass',
    drift_flags=[], rent_status='paid', not_computable_regions=[]
)
_ = run.agency_enabled
_ = packet.signal_id
""",
    )

    detect_contract_deltas([sample])


def test_contract_delta_detector_flags_missing_field(tmp_path: Path) -> None:
    sample = tmp_path / "test_sample_bad.py"
    _write(sample, "state = RunState()\nstate.nonexistent_field\n")

    with pytest.raises(ContractDeltaError) as exc:
        detect_contract_deltas([sample])

    assert "missing_field:RunState.nonexistent_field" in str(exc.value)
