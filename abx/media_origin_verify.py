from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from abx.providers.fetch_adapter import choose_adapter


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _domain_from_url(url: str) -> str:
    u = (url or "").strip()
    m = re.match(r"^https?://([^/]+)", u)
    return (m.group(1).lower() if m else "")


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _head_html_ts_hint(html: str) -> str:
    s = html or ""
    for pat in [
        r'property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
        r'name=["\']pubdate["\']\s+content=["\']([^"\']+)["\']',
        r'name=["\']publish-date["\']\s+content=["\']([^"\']+)["\']',
        r'name=["\']date["\']\s+content=["\']([^"\']+)["\']',
        r'<time[^>]+datetime=["\']([^"\']+)["\']',
    ]:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m:
            return str(m.group(1)).strip()
    return ""


def _extract_url(detail: str, artifacts: Dict[str, Any]) -> str:
    for k in ("url", "source_url", "anchor_url", "final_url"):
        v = artifacts.get(k)
        if isinstance(v, str) and v.strip().startswith("http"):
            return v.strip()
    m = re.search(r"(https?://[^\s\]]+)", detail or "")
    if not m:
        return ""
    return m.group(1).strip().rstrip(").,]")


def _fingerprint_from_response(
    url: str, headers: Dict[str, Any], body: bytes
) -> Tuple[str, Dict[str, Any]]:
    h = headers or {}
    etag = str(h.get("etag") or "")
    clen = str(h.get("content-length") or "")
    ctype = str(h.get("content-type") or "")
    if body:
        fp = _sha256_bytes(body)
        return fp, {
            "method": "sha256_body",
            "content_type": ctype,
            "content_length": len(body),
            "etag": etag,
        }
    surrogate = (url + "|" + clen + "|" + etag + "|" + ctype).encode(
        "utf-8", errors="ignore"
    )
    fp = _sha256_bytes(surrogate)
    return fp, {
        "method": "sha256_surrogate",
        "content_type": ctype,
        "content_length": clen,
        "etag": etag,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-98: verify media origin tasks (canonical url, headers, fingerprint, reupload storms)"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--in", required=True, help="acq_batch_*.json containing tasks")
    ap.add_argument("--provider", default="", help="provider hint; if empty, offline mode triggers")
    ap.add_argument(
        "--origin-ledger", default="out/ledger/media_origin_ledger.jsonl"
    )
    ap.add_argument(
        "--fp-index-ledger", default="out/ledger/media_fingerprint_index.jsonl"
    )
    ap.add_argument("--out", default="")
    ap.add_argument("--max", type=int, default=40)
    args = ap.parse_args()

    batch = _read_json(args.in)
    tasks = batch.get("tasks") if isinstance(batch.get("tasks"), list) else []
    vt = [
        t
        for t in tasks
        if isinstance(t, dict) and str(t.get("task_kind") or "") == "VERIFY_MEDIA_ORIGIN"
    ]
    vt = vt[: int(args.max)]

    fp_events = _read_jsonl(args.fp_index_ledger)
    fp_map: Dict[str, List[Dict[str, Any]]] = {}
    for e in fp_events:
        if e.get("kind") != "media_fingerprint_seen":
            continue
        fp = str(e.get("fingerprint") or "")
        if not fp:
            continue
        fp_map.setdefault(fp, []).append(
            {"domain": e.get("domain"), "anchor_id": e.get("anchor_id"), "url": e.get("url")}
        )

    adapter = choose_adapter(args.provider)

    items = []
    for t in vt:
        task_id = str(t.get("task_id") or "")
        detail = str(t.get("detail") or "")
        artifacts = t.get("artifacts") if isinstance(t.get("artifacts"), dict) else {}
        anchor_id = str(artifacts.get("anchor_id") or "")
        url = _extract_url(detail, artifacts)
        dom = _domain_from_url(url)

        if not url:
            ev = {
                "kind": "media_origin",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "task_id": task_id,
                "anchor_id": anchor_id,
                "url": "",
                "domain": "",
                "ok": False,
                "offline_required": True,
                "offline_required_reason": "no_url_found_in_task_detail",
                "notes": "WO-98: cannot verify without URL; request offline input.",
            }
            _append_jsonl(args.origin_ledger, ev)
            items.append(ev)
            continue

        resp = adapter.fetch(url)
        if not resp.ok:
            ev = {
                "kind": "media_origin",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "task_id": task_id,
                "anchor_id": anchor_id,
                "url": url,
                "domain": dom,
                "ok": False,
                "offline_required": bool(resp.offline),
                "offline_required_reason": str(resp.reason or ""),
                "notes": "WO-98: fetch failed; provenance limited.",
            }
            _append_jsonl(args.origin_ledger, ev)
            items.append(ev)
            continue

        final_url = str(resp.final_url or url)
        headers = resp.headers or {}
        body = resp.body or b""

        date_hdr = str(headers.get("date") or "")
        html_hint = ""
        try:
            if "text/html" in str(headers.get("content-type") or "").lower():
                html_hint = _head_html_ts_hint(body.decode("utf-8", errors="ignore"))
        except Exception:
            html_hint = ""

        fp, fp_meta = _fingerprint_from_response(final_url, headers, body)
        seen_before = fp_map.get(fp, [])
        domains = sorted({str(x.get("domain") or "") for x in seen_before if x.get("domain")})
        storm = len(domains) >= 2

        ev = {
            "kind": "media_origin",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "task_id": task_id,
            "anchor_id": anchor_id,
            "url": url,
            "final_url": final_url,
            "domain": _domain_from_url(final_url),
            "redirect_chain": list(
                resp.redirect_chain or ([url, final_url] if final_url != url else [url])
            ),
            "headers_subset": {
                "date": date_hdr,
                "content_type": str(headers.get("content-type") or ""),
                "content_length": str(headers.get("content-length") or ""),
                "etag": str(headers.get("etag") or ""),
                "last_modified": str(headers.get("last-modified") or ""),
            },
            "published_hint_ts": html_hint,
            "fingerprint": fp,
            "fingerprint_meta": fp_meta,
            "reupload_storm": bool(storm),
            "reupload_domains": domains[:12],
            "ok": True,
            "offline_required": False,
            "notes": "WO-98: origin traceability increased (fingerprint+headers+canonical). Not a truth verdict.",
        }
        _append_jsonl(args.origin_ledger, ev)
        items.append(ev)

        _append_jsonl(
            args.fp_index_ledger,
            {
                "kind": "media_fingerprint_seen",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "fingerprint": fp,
                "url": final_url,
            "domain": _domain_from_url(final_url),
            "anchor_id": anchor_id,
            "task_id": task_id,
            "meta": fp_meta,
        },
        )
        fp_map.setdefault(fp, []).append(
            {
                "domain": _domain_from_url(final_url),
                "anchor_id": anchor_id,
                "url": final_url,
            }
        )

    stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"media_origin_verify_{stamp}.json"
    )
    _write_json(
        out_path,
        {
            "version": "media_origin_verify.v0.1",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "batch_in": args.in,
            "n_tasks": len(vt),
            "n_items": len(items),
            "items": items,
            "notes": "Materialized report; full stream in media_origin_ledger.jsonl",
        },
    )
    print(f"[MEDIA_ORIGIN] wrote: {out_path} items={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
