from __future__ import annotations

from abx.boundary.types import AdapterTransformRecord


def build_transform_record(
    *,
    adapter_id: str,
    connector_id: str,
    transform_type: str,
    input_trust: str,
    output_trust: str,
    metadata: dict[str, object],
) -> AdapterTransformRecord:
    return AdapterTransformRecord(
        adapter_id=adapter_id,
        connector_id=connector_id,
        transform_type=transform_type,
        input_trust=input_trust,
        output_trust=output_trust,
        metadata=dict(metadata),
    )
