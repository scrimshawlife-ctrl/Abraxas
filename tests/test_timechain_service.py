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
    # difficulty=2 deliberately, NOT the production 4.
    #
    # Mining to difficulty 4 needs 4k-56k hashes: measured 0.05s when lucky and 2.25s under
    # concurrent load, against a 3s client timeout. The tests then failed ~1 run in 4 with
    # `TimeoutError` -- and it was NOT the lock, NOT keep-alive, and NOT a socket race, all
    # of which I "fixed" first. It is simply that a variable-duration operation was given a
    # fixed, too-tight budget.
    #
    # difficulty 2 needs ~256x fewer hashes, so the behaviour under test (append, link,
    # verify, auth) is exercised without racing a hash-rate lottery. The difficulty-4
    # PROPERTY still has its own dedicated test below, where the cost is the point.
    srv = TimechainServer(host="127.0.0.1", port=0, api_key=None, difficulty=2)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    _wait_until_listening(srv.base_url)  # NOT a sleep: poll until the socket answers
    yield srv
    srv.shutdown()


def _wait_until_listening(base_url: str, attempts: int = 50) -> None:
    """Block until the server actually accepts connections.

    Without this the fixture raced: the thread was started but the socket might not be
    bound yet, so the first request occasionally hit a closed port and the test failed
    ~2 runs in 5. A fixed sleep would have hidden it behind a timeout instead of fixing
    it, and would slow every run. Poll the real readiness signal instead.
    """
    import time as _t
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=0.5):
                return
        except Exception:
            _t.sleep(0.02)
    raise RuntimeError(f"server at {base_url} never became ready")


def _get(url, key=None, timeout=3):
    req = urllib.request.Request(url, method="GET")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read() or b"{}")


def _post(url, payload, key=None, timeout=3):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
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

    def test_blocks_are_mined_to_the_configured_difficulty(self):
        """difficulty 4 means 4 leading hex zeros on the block hash.

        This one builds its OWN difficulty-4 server and does not share the fast fixture,
        because here the cost IS the property under test. The client timeout is sized to the
        measured worst case (2.25s under concurrent load) with headroom, rather than the 3s
        that made the fast tests flaky.
        """
        srv = TimechainServer(host="127.0.0.1", port=0, difficulty=4)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            _wait_until_listening(srv.base_url)
            # timeout=15, not the default 3: mining to difficulty 4 measured 2.25s under
            # concurrent load, so a 3s budget is a coin flip. The property being tested is
            # "4 leading zeros", not "fast" -- size the budget to the operation.
            _, created = _post(f"{srv.base_url}/blocks", {"data": {"mined": True}}, timeout=15)
            h = created["block"]["hash"]
            assert h.startswith("0" * 4), f"expected 4 leading zeros, got {h[:12]}"
            assert created["block"]["difficulty"] == 4
            assert srv.verify()[0] is True
        finally:
            srv.shutdown()

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
        srv = TimechainServer(host="127.0.0.1", port=0, api_key="secret", difficulty=2)
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
