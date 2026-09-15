"""Keep output digest for spec v1.1.

Keeper stores this string. It does not compute it.
Payload is binding_hash + weave attachment payloads + ward_post.hash.
Herald is excluded (Herald points at the ledger entry).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from abx_familiar.ir.delivery_pack_v0 import AttachmentRef
from abx_familiar.ir.ward_report_v0 import WardReport


def compute_keep_output_hash(
    binding: dict[str, Any],
    weave: list[AttachmentRef],
    ward_post: WardReport,
) -> str:
    payload = {
        "binding_hash": binding.get("binding_hash"),
        "binding_status": binding.get("status"),
        "weave": [a.to_payload() for a in weave],
        "ward_post_hash": ward_post.hash(),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
