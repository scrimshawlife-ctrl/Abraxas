from __future__ import annotations

import pytest

from abraxas.acquisition.reason_codes import CACHE_POLICY_OFFLINE_ONLY
from abraxas.acquisition.transport import acquire_cache_only


class _DummyCAS:
    def lookup_url(self, url: str):  # pragma: no cover - should not be reached in this test
        raise AssertionError("lookup_url should not be called when policy_reason is missing")


def test_acquire_cache_only_requires_explicit_policy_reason() -> None:
    with pytest.raises(RuntimeError, match="policy_reason"):
        acquire_cache_only(url="https://example.com/data.json", cas_store=_DummyCAS(), policy_reason="")


class _Entry:
    def __init__(self, path: str) -> None:
        self.path = path
        self.content_hash = "hash123"
        self.subdir = "raw"
        self.suffix = ".bin"


class _CASWithEntry:
    def __init__(self, entry: _Entry) -> None:
        self._entry = entry

    def lookup_url(self, url: str):
        return self._entry


def test_acquire_cache_only_returns_policy_reason(tmp_path) -> None:
    payload_path = tmp_path / "cached.bin"
    payload_path.write_bytes(b"hello-cache")
    cas = _CASWithEntry(_Entry(str(payload_path)))

    result = acquire_cache_only(
        url="https://example.com/data.json",
        cas_store=cas,
        policy_reason=CACHE_POLICY_OFFLINE_ONLY,
    )

    assert result is not None
    assert result.policy_reason == CACHE_POLICY_OFFLINE_ONLY
    assert result.method == "cache_only"


def test_acquire_cache_only_rejects_unknown_policy_reason() -> None:
    with pytest.raises(RuntimeError, match="invalid cache-only policy_reason"):
        acquire_cache_only(
            url="https://example.com/data.json",
            cas_store=_DummyCAS(),
            policy_reason="ad_hoc_reason",
        )
