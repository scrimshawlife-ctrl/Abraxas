"""C: the Timechain service, tested against the client's existing contract.

Written first (red). The acceptance criterion is deliberately NOT "matches a spec I
invented" -- it is **the client already in this repo can read from, append to, and verify
against this server, using real block data**. The contract is pinned by
`CypherTempreTimechain`, which I fixed in the previous commit:

    GET  {endpoint}/health        -> 2xx           (what _probe_endpoint checks)
    POST {endpoint}/blocks        -> accept a block
    GET  {endpoint}/blocks        -> the stored chain
    GET  {endpoint}/verify        -> chain validity

Auth: the client sends `Authorization: Bearer <api_key>` when api_key is set.

Scope decisions (recommended and accepted):
  1. stdlib http.server -- zero new dependencies, matching the repo's lean posture
  2. difficulty 4 kept as-is -- it is what the client already mines at
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from abraxas.yggdrasil.timechain_service import TimechainServer


@pytest.fixture()
def server():
    srv = TimechainServer(host="127.0.0.1", port=0, api_key=None)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()


def _get(url, key=None):
    req = urllib.request.Request(url, method="GET")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=3) as r:
        return r.status, json.loads(r.read() or b"{}")


def _post(url, payload, key=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=3) as r:
        return r.status, json.loads(r.read() or b"{}")


class TestHealthContract:
    def test_health_answers_2xx(self, server):
        """This is the exact check _probe_endpoint makes. If it 404s, the client still
        reports UNREACHABLE and nothing has been fixed."""
        status, body = _get(f"{server.base_url}/health")
        assert status == 200
        assert body.get("status") == "ok"


class TestClientCanUseIt:
    """The acceptance test: the REAL client against the REAL server."""

    def test_client_reports_available_against_this_server(self, server):
        from abraxas.yggdrasil.timechain import CypherTempreTimechain, TimechainConfig, TimechainState

        tc = CypherTempreTimechain(TimechainConfig(enabled=True, endpoint=server.base_url, timeout=2.0))
        assert tc.connection_state() is TimechainState.AVAILABLE, (
            "the client's own probe must accept this server -- otherwise C does not close the thread"
        )

    def test_status_surface_reports_available(self, server):
        from abraxas.yggdrasil.timechain import CypherTempreTimechain, TimechainConfig

        tc = CypherTempreTimechain(TimechainConfig(enabled=True, endpoint=server.base_url, timeout=2.0))
        st = tc.get_status()
        assert st["timechain_state"] == "available"
        assert st["timechain_available"] is True


class TestChainBehaviour:
    def test_append_then_read_back(self, server):
        status, created = _post(f"{server.base_url}/blocks", {"data": {"k": "v"}})
        assert status in (200, 201)
        assert created["block"]["index"] == 0
        status, chain = _get(f"{server.base_url}/blocks")
        assert status == 200
        assert len(chain["blocks"]) == 1
        assert chain["blocks"][0]["data_hash"]

    def test_chain_links_and_verifies(self, server):
        _post(f"{server.base_url}/blocks", {"data": {"n": 1}})
        _post(f"{server.base_url}/blocks", {"data": {"n": 2}})
        _post(f"{server.base_url}/blocks", {"data": {"n": 3}})
        status, chain = _get(f"{server.base_url}/blocks")
        blocks = chain["blocks"]
        assert [b["index"] for b in blocks] == [0, 1, 2]
        # each block must point at its predecessor's HASH (not its data_hash, and not
        # "or something truthy" -- that made this assertion vacuous and it passed while
        # checking nothing)
        for prev, cur in zip(blocks, blocks[1:]):
            assert cur["previous_hash"] == prev["hash"], (
                f"block {cur['index']} points at {cur['previous_hash'][:12]}, "
                f"predecessor hash is {prev['hash'][:12]}"
            )
        assert blocks[0]["previous_hash"] == "0" * 64, "first block must point at genesis"
        status, v = _get(f"{server.base_url}/verify")
        assert status == 200
        assert v["valid"] is True

    def test_blocks_are_mined_to_the_configured_difficulty(self, server):
        """difficulty 4 means 4 leading hex zeros on the block hash."""
        _, created = _post(f"{server.base_url}/blocks", {"data": {"mined": True}})
        h = created["block"]["hash"]
        assert h.startswith("0" * 4), f"expected 4 leading zeros, got {h[:12]}"
        assert created["block"]["difficulty"] == 4

    def test_tampering_is_detected(self, server):
        """The counterfactual for verify(): if a mutated chain still verifies, verify()
        is decorative."""
        _post(f"{server.base_url}/blocks", {"data": {"a": 1}})
        _post(f"{server.base_url}/blocks", {"data": {"b": 2}})
        server._chain[0] = dict(server._chain[0], data_hash="0" * 64)  # tamper
        _, v = _get(f"{server.base_url}/verify")
        assert v["valid"] is False, "a tampered chain MUST fail verification"


class TestAuth:
    def test_api_key_is_enforced_when_configured(self):
        srv = TimechainServer(host="127.0.0.1", port=0, api_key="secret")
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with pytest.raises(urllib.error.HTTPError) as ei:
                _get(f"{srv.base_url}/blocks")  # no key
            assert ei.value.code == 401
            status, _ = _get(f"{srv.base_url}/blocks", key="secret")
            assert status == 200
            # health stays open: a probe must not need credentials to answer
            status, _ = _get(f"{srv.base_url}/health")
            assert status == 200
        finally:
            srv.shutdown()
