from __future__ import annotations

from typing import Any, Mapping

from abraxas.oracle.runtime.input_normalizer import normalize_input_v2
from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service
from abraxas.oracle.stability.canonicalize import canonical_authority_blob, canonical_full_blob
from abraxas.oracle.stability.digests import compute_digest_triplet
from abraxas.oracle.stability.mismatch_report import build_mismatch_report


def run_invariance_v2(raw_envelope: Mapping[str, Any], *, repeats: int = 12) -> dict:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    input_hashes: list[str] = []
    authority_hashes: list[str] = []
    full_hashes: list[str] = []
    authority_blobs: list[str] = []
    full_blobs: list[str] = []

    for _ in range(repeats):
        normalized = normalize_input_v2(raw_envelope)
        out = run_oracle_signal_layer_v2_service(raw_envelope)
        hashes = compute_digest_triplet(normalized=normalized, output=out)
        input_hashes.append(hashes["input_hash"])
        authority_hashes.append(hashes["authority_hash"])
        full_hashes.append(hashes["full_hash"])
        authority_blobs.append(canonical_authority_blob(out))
        full_blobs.append(canonical_full_blob(out))

    stable = len(set(input_hashes)) == 1 and len(set(authority_hashes)) == 1 and len(set(full_hashes)) == 1
    report = {
        "schema_id": "OracleSignalInvarianceReport.v2",
        "repeats": repeats,
        "status": "PASS" if stable else "BLOCKED",
        "input_hash": input_hashes[0],
        "authority_hash": authority_hashes[0],
        "full_hash": full_hashes[0],
    }
    if not stable:
        report["mismatch"] = build_mismatch_report(
            input_hashes=input_hashes,
            authority_hashes=authority_hashes,
            full_hashes=full_hashes,
            authority_blobs=authority_blobs,
            full_blobs=full_blobs,
        )
    return report
