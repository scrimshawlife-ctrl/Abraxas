from __future__ import annotations
import sys, json
from .adapter import parse_request, handle

def main() -> int:
    raw = sys.stdin.read()
    try:
        req = parse_request(raw)
        resp = handle(req)
        sys.stdout.write(json.dumps({
            "ok": resp.ok,
            "overlay": resp.overlay,
            "phase": resp.phase,
            "request_id": resp.request_id,
            "output": resp.output,
            "error": resp.error,
        }, sort_keys=True))
        return 0
    except Exception as e:
        sys.stdout.write(json.dumps({
            "ok": False,
            "error": str(e),
        }, sort_keys=True))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
