from __future__ import annotations

from typing import Mapping, Sequence

from abraxas.contracts.oracle_signal_layer_output_v2 import OracleSignalLayerOutputV2
from abraxas.core.canonical import canonical_json, sha256_hex


def build_output_envelope_v2(
    *,
    run_id: str,
    lane: str,
    authority: Mapping[str, object],
    advisory_attachments: Sequence[Mapping[str, object]],
    input_hash: str,
    not_computable_reasons: Sequence[str],
) -> dict:
    frozen_authority = dict(authority)
    frozen_advisory = [dict(x) for x in advisory_attachments]
    full_hash = sha256_hex(canonical_json({"authority": frozen_authority, "advisory": frozen_advisory, "run_id": run_id, "lane": lane}))
    computable = len(not_computable_reasons) == 0
    envelope = OracleSignalLayerOutputV2(
        run_id=run_id,
        lane=lane,
        authority=frozen_authority,
        advisory_attachments=frozen_advisory,
        boundary_enforced=True,
        provenance={
            "input_hash": input_hash,
            "authority_hash": str(frozen_authority.get("provenance", {}).get("authority_hash", "")),
            "full_hash": full_hash,
            "computable": computable,
            "status": "COMPUTABLE" if computable else "NOT_COMPUTABLE",
            "not_computable_reasons": list(not_computable_reasons),
        },
    )
    return envelope.to_dict()
