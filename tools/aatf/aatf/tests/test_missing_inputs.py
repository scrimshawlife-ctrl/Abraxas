import pytest

from aatf.ingest.loaders import load_json_payload


def test_load_json_payload_requires_object(tmp_path):
    p = tmp_path / "payload.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_json_payload(str(p))
