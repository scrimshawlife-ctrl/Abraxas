"""A minimal Timechain service, implementing the contract `CypherTempreTimechain` expects.

Scope decisions (recommended and accepted):
  1. stdlib only -- `http.server` + `json` + `hashlib`. Zero new dependencies, matching
     this repo's lean posture. No framework, no ORM, no async runtime for a service whose
     actual job is "append a hashed block and answer three questions about it".
  2. difficulty 4 kept as-is -- it is what the client already mines at, so changing it
     here would silently change what the client accepts.
  3. The stored shape matches the client's `blocks.json` (index / data_hash /
     previous_hash / merkle_root / nonce / difficulty), so an existing file is readable
     and a server chain is portable back to disk.

What this is NOT: not a distributed ledger, not Byzantine-tolerant, not a consensus
protocol. One process, one chain, append-only, hash-linked, PoW-mined, verifiable. That
is what the client's contract asks for and nothing more.

Run:
    python -m abraxas.yggdrasil.timechain_service --port 8332 --storage .abraxas/timechain
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64


def _canonical_hash(obj: Any) -> str:
    """Hash a value by its stable JSON form.

    sort_keys + separators: the same dict must hash identically regardless of insertion
    order, or a re-serialized block would fail its own verification. This is the same
    discipline `abraxas.util.canonical_hash` enforces (which forbids floats for exactly
    this reason); kept local and simple because this module must not depend on the wider
    package to be runnable as a standalone service.
    """
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _merkle_root(leaves: List[str]) -> str:
    """Merkle root over the data leaves. Single leaf hashes itself; empty is genesis."""
    if not leaves:
        return GENESIS_HASH
    level = list(leaves)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else level[i]
            nxt.append(hashlib.sha256((a + b).encode()).hexdigest())
        level = nxt
    return level[0]


class TimechainServer(ThreadingHTTPServer):
    """Threaded HTTP server holding one append-only chain."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host: str = "127.0.0.1", port: int = 8332,
                 api_key: Optional[str] = None, difficulty: int = 4,
                 storage: Optional[str] = None):
        self.difficulty = difficulty
        self.api_key = api_key
        self._lock = threading.RLock()
        self._chain: List[Dict[str, Any]] = []
        self._storage = Path(storage) if storage else None
        super().__init__((host, port), _TimechainHandler)
        if self._storage:
            self._load()

    # ---- properties -------------------------------------------------------

    @property
    def base_url(self) -> str:
        host, port = self.server_address[0], self.server_address[1]
        return f"http://{host}:{port}"

    # ---- chain ------------------------------------------------------------

    def _last_hash(self) -> str:
        return self._chain[-1]["hash"] if self._chain else GENESIS_HASH

    def _mine(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Proof of work: increment nonce until the block hash has `difficulty` leading
        zeros. Deliberately naive -- this is a verifiable-log primitive, not a
        hash-rate competition."""
        target = "0" * self.difficulty
        while True:
            h = _canonical_hash({k: block[k] for k in
                                 ("index", "timestamp", "data_hash", "previous_hash",
                                  "merkle_root", "nonce", "difficulty")})
            if h.startswith(target):
                block["hash"] = h
                return block
            block["nonce"] += 1

    def append(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Append a block.

        The mine loop runs OUTSIDE the lock, deliberately. Mining takes 4k-56k hashes
        (measured 0.05-1.2s) and the previous version held self._lock for the whole of it,
        so any concurrent verify()/list read starved until the client's timeout fired. That
        is what made the test suite fail ~1 run in 4 with
        `TimeoutError` in socket.recv_into -- and it reproduced under a concurrent-load
        harness at trial 4.

        Only the append itself needs the lock, and it is O(1).
        """
        # Snapshot what mining needs, under the lock, then release it.
        with self._lock:
            index = len(self._chain)
            previous_hash = self._last_hash()
            difficulty = self.difficulty

        data_hash = _canonical_hash(data)
        block = {
            "index": index,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_hash": data_hash,
            "previous_hash": previous_hash,
            "merkle_root": _merkle_root([data_hash]),
            "nonce": 0,
            "difficulty": difficulty,
            "data": data,
            "metadata": metadata or {},
        }

        # Mining: no lock held. This is the slow part.
        block = self._mine(block)

        with self._lock:
            # Another writer may have appended while we mined. Re-link onto the real tip
            # rather than the snapshot, or the chain forks silently.
            if self._last_hash() != block["previous_hash"]:
                block["index"] = len(self._chain)
                block["previous_hash"] = self._last_hash()
                block = self._mine(block)
            self._chain.append(block)
            self._save()
            return block

    def verify(self) -> Tuple[bool, List[str]]:
        """Recompute and check. Each block must hash to its recorded hash, point at its
        predecessor, and meet difficulty."""
        errors: List[str] = []
        prev = GENESIS_HASH
        target = "0" * self.difficulty
        for i, b in enumerate(self._chain):
            if b["index"] != i:
                errors.append(f"block {i}: index is {b['index']}")
            if b["previous_hash"] != prev:
                errors.append(f"block {i}: previous_hash mismatch")
            if not b["hash"].startswith(target):
                errors.append(f"block {i}: hash does not meet difficulty {self.difficulty}")
            recomputed = _canonical_hash({k: b[k] for k in
                                          ("index", "timestamp", "data_hash", "previous_hash",
                                           "merkle_root", "nonce", "difficulty")})
            if recomputed != b["hash"]:
                errors.append(f"block {i}: hash does not match its contents (tampered)")
            if _canonical_hash(b.get("data")) != b["data_hash"]:
                errors.append(f"block {i}: data_hash does not match data (tampered)")
            prev = b["hash"]
        return (not errors), errors

    # ---- persistence ------------------------------------------------------

    def _save(self) -> None:
        if not self._storage:
            return
        self._storage.mkdir(parents=True, exist_ok=True)
        payload = {"blocks": self._chain, "index": len(self._chain),
                   "last_hash": self._last_hash()}
        (self._storage / "blocks.json").write_text(json.dumps(payload, indent=2))

    def _load(self) -> None:
        f = self._storage / "blocks.json"
        if not f.exists():
            return
        try:
            data = json.loads(f.read_text())
            self._chain = data.get("blocks", [])
            logger.info("Loaded %d blocks from %s", len(self._chain), f)
        except Exception as exc:  # a corrupt store must not prevent startup
            logger.warning("Could not load %s: %s", f, exc)
            self._chain = []


class _TimechainHandler(BaseHTTPRequestHandler):
    server: TimechainServer
    # HTTP/1.0 deliberately. With HTTP/1.1 the handler advertises keep-alive and holds the
    # socket open, but a SECOND request on the reused connection times out reading the
    # status line -- reproduced directly:
    #
    #     http.client: /health (200, will_close=False) then POST on the SAME conn
    #     -> TimeoutError in _read_status -> socket.recv_into
    #
    # urlopen hides it by opening a fresh connection per call, which is why a standalone
    # probe passed 15/15 while pytest failed 1-in-4 on the same server. A verifiable-log
    # service does not need connection reuse, and correctness beats a saved handshake.
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt, *args):  # quieter default logging
        logger.debug("%s - %s", self.address_string(), fmt % args)

    # ---- helpers ----------------------------------------------------------

    def _json(self, status: int, body: Dict[str, Any]) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        # Explicit, so behaviour does not depend on the protocol_version default.
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def _authed(self, path: str) -> bool:
        """Health is deliberately open: the client's reachability probe must be able to
        answer without credentials, or a misconfigured key would look like an outage."""
        if path.rstrip("/").endswith("/health"):
            return True
        if not self.server.api_key:
            return True
        return self.headers.get("Authorization") == f"Bearer {self.server.api_key}"

    def _read_body(self) -> Dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return {}

    # ---- routes -----------------------------------------------------------

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if not self._authed(path):
            return self._json(401, {"error": "unauthorized"})
        if path.rstrip("/").endswith("/health"):
            valid, errors = self.server.verify()
            return self._json(200, {"status": "ok", "blocks": len(self.server._chain),
                                    "chain_valid": valid, "errors": errors})
        if path.rstrip("/").endswith("/blocks"):
            return self._json(200, {"blocks": self.server._chain,
                                    "index": len(self.server._chain),
                                    "last_hash": self.server._last_hash()})
        if path.rstrip("/").endswith("/verify"):
            valid, errors = self.server.verify()
            return self._json(200, {"valid": valid, "errors": errors,
                                    "blocks": len(self.server._chain)})
        return self._json(404, {"error": "not found", "path": path})

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if not self._authed(path):
            return self._json(401, {"error": "unauthorized"})
        if path.rstrip("/").endswith("/blocks"):
            body = self._read_body()
            if "data" not in body:
                return self._json(400, {"error": "missing 'data'"})
            block = self.server.append(body["data"], body.get("metadata"))
            return self._json(201, {"block": block})
        return self._json(404, {"error": "not found", "path": path})


def main() -> int:
    ap = argparse.ArgumentParser(description="Minimal Timechain service.")
    ap.add_argument("--host", default="127.0.0.1",
                    help="interface to bind (default 127.0.0.1; pass 0.0.0.0 to expose)")
    ap.add_argument("--port", type=int, default=8332)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--difficulty", type=int, default=4)
    ap.add_argument("--storage", default=None,
                    help="directory to persist blocks.json (omit for in-memory)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    srv = TimechainServer(host=args.host, port=args.port, api_key=args.api_key,
                          difficulty=args.difficulty, storage=args.storage)
    logger.info("Timechain serving on %s (difficulty=%d, auth=%s, storage=%s)",
                srv.base_url, args.difficulty, bool(args.api_key), args.storage or "in-memory")
    print(f"Timechain listening on {srv.base_url}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
