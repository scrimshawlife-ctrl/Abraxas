from __future__ import annotations

import pytest

from abraxas.oracle.runtime.schema_guard import validate_oslv2_input, validate_oslv2_output


def test_validate_oslv2_input_rejects_missing_schema_id() -> None:
    with pytest.raises(ValueError):
        validate_oslv2_input({"signal_sources": ["mda"], "payload": {}, "context": {}, "metadata": {}})


def test_validate_oslv2_output_rejects_missing_provenance() -> None:
    with pytest.raises(ValueError):
        validate_oslv2_output({"schema_id": "OracleSignalLayerOutput.v2", "run_id": "x", "lane": "shadow"})
