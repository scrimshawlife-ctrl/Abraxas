from __future__ import annotations


def classify_compression(*, compression_state: str, omitted_context: str) -> str:
    if compression_state in {"NOT_COMPUTABLE", "BLOCKED", "COMPRESSION_UNSAFE"}:
        return compression_state
    if compression_state in {
        "COMPRESSED_WITH_PRESERVATION",
        "COMPRESSED_WITH_NOTED_LOSS",
        "COMPRESSED_WITH_HIDDEN_LOSS_RISK",
        "NO_COMPRESSION_NEEDED",
    }:
        return compression_state
    if omitted_context not in {"NONE", ""}:
        return "COMPRESSED_WITH_NOTED_LOSS"
    return "COMPRESSED_WITH_PRESERVATION"
