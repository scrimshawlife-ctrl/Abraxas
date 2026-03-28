from __future__ import annotations

from abx.explanation.types import CompressionLossRecord


def build_compression_loss_records() -> tuple[CompressionLossRecord, ...]:
    return (
        CompressionLossRecord("loss.exec", "executive.summary", "COMPRESSION_LOSS_ACTIVE", "uncertainty"),
        CompressionLossRecord("loss.card", "dashboard.card", "COMPRESSION_LOSS_ACTIVE", "counterevidence"),
        CompressionLossRecord("loss.ops", "operator.writeup", "NO_MATERIAL_LOSS", "none"),
    )
