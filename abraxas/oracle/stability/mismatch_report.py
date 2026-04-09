from __future__ import annotations

from typing import Sequence


def build_mismatch_report(
    *,
    input_hashes: Sequence[str],
    authority_hashes: Sequence[str],
    full_hashes: Sequence[str],
    authority_blobs: Sequence[str] | None = None,
    full_blobs: Sequence[str] | None = None,
) -> dict:
    report = {
        "status": "MISMATCH",
        "input_hashes": list(input_hashes),
        "authority_hashes": list(authority_hashes),
        "full_hashes": list(full_hashes),
    }
    if authority_blobs and len(set(authority_blobs)) > 1:
        report["authority_diff"] = {
            "left": authority_blobs[0],
            "right": next(x for x in authority_blobs if x != authority_blobs[0]),
        }
    if full_blobs and len(set(full_blobs)) > 1:
        report["full_diff"] = {
            "left": full_blobs[0],
            "right": next(x for x in full_blobs if x != full_blobs[0]),
        }
    return report
