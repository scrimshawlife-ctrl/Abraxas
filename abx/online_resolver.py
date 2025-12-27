from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from abx.task_ledger import task_event
from abx.relation_classifier import classify_relation


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def _sha8(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:8]


def _http_get(url: str, timeout: int = 14, headers: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "abx/online_resolver"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        # capture minimal headers
        hdrs = {k.lower(): v for k, v in r.headers.items()}
    # best-effort decode
    try:
        txt = raw.decode("utf-8", errors="ignore")
    except Exception:
        txt = raw.decode("latin-1", errors="ignore")
    return txt, hdrs


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    t = re.sub(r"\s+", " ", m.group(1)).strip()
    return t[:180]


def _extract_meta_date(html: str) -> str:
    # common meta tags
    pats = [
        r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="pubdate"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="publishdate"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="date"[^>]+content="([^"]+)"',
    ]
    for p in pats:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            return m.group(1)[:64]
    return ""


def _canonicalize(url: str) -> str:
    """
    Basic canonicalization: strip common tracking params; keep deterministic.
    """
    try:
        u = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
        q2 = [(k, v) for (k, v) in q if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
        nq = urllib.parse.urlencode(q2)
        nu = u._replace(query=nq, fragment="")
        return urllib.parse.urlunparse(nu)
    except Exception:
        return (url or "").strip()


def _dedupe_urls(urls: List[str], limit: int = 12) -> List[str]:
    seen = set()
    out = []
    for u in urls:
        cu = _canonicalize(u)
        if not cu or cu in seen:
            continue
        seen.add(cu)
        out.append(cu)
        if len(out) >= limit:
            break
    return out


def _parse_rss_urls(xml_text: str, limit: int = 12) -> List[str]:
    urls = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    # RSS: item/link ; Atom: entry/link[@href]
    for link in root.findall(".//item/link"):
        if link.text:
            urls.append(link.text.strip())
    for link in root.findall(".//{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}link"):
        href = link.attrib.get("href")
        if href:
            urls.append(href.strip())
    return _dedupe_urls(urls, limit=limit)


def _extract_links(html: str, limit: int = 20) -> List[str]:
    # very simple href extraction (we're not doing full HTML parsing)
    hrefs = re.findall(r'href="([^"]+)"', html, re.IGNORECASE)
    out = []
    for h in hrefs:
        h = h.strip()
        if not h or h.startswith("#") or h.startswith("javascript:"):
            continue
        out.append(h)
        if len(out) >= limit:
            break
    return out


def _resolve_relative(base: str, hrefs: List[str]) -> List[str]:
    out = []
    for h in hrefs:
        out.append(urllib.parse.urljoin(base, h))
    return out


def make_anchor(
    *,
    url: str,
    provider: str,
    content_hint: str,
    fetched_title: str = "",
    fetched_date: str = "",
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    cu = _canonicalize(url)
    dom = _domain(cu)
    anchor_id = f"anc_{_sha8(provider)}_{_sha8(cu)}_{int(time.time())}"
    return {
        "kind": "anchor_added",
        "ts": _utc_now_iso(),
        "anchor_id": anchor_id,
        "url": cu,
        "domain": dom,
        "provider": provider,
        "title": fetched_title or "",
        "published_at": fetched_date or "",
        "content_hint": (content_hint or "")[:160],
        "headers": headers or {},
        "hashes": {
            "url_sha16": hashlib.sha256(cu.encode("utf-8")).hexdigest()[:16],
        },
        "notes": "Anchor created by WO-78 online_resolver. Content is referenced by URL; no claim is asserted without edges.",
    }


def link_anchor_to_claim(
    *,
    run_id: str,
    claim_id: str,
    anchor: Dict[str, Any],
    relation: str,
    evidence_graph_ledger: str,
) -> None:
    _append_jsonl(evidence_graph_ledger, {
        "kind": "anchor_claim_link",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "claim_id": claim_id,
        "anchor_id": anchor.get("anchor_id"),
        "url": anchor.get("url"),
        "domain": anchor.get("domain"),
        "relation": relation,  # SUPPORTS/CONTRADICTS/REFRAMES
        "notes": "Edge added by WO-78 online_resolver.",
    })


def resolve_routing_to_urls(routing: Dict[str, Any]) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Returns (provider, urls, meta)
    """
    provider = str(routing.get("provider") or "none")
    if provider == "direct_http":
        res = routing.get("results") if isinstance(routing.get("results"), list) else []
        urls = [str(r.get("url") or "") for r in res if isinstance(r, dict)]
        return provider, _dedupe_urls(urls, limit=12), {"note": "direct_http urls"}
    if provider == "search_lite":
        res = routing.get("results") if isinstance(routing.get("results"), list) else []
        urls = [str(r.get("url") or "") for r in res if isinstance(r, dict)]
        return provider, _dedupe_urls(urls, limit=12), {"query": routing.get("query")}
    if provider == "rss":
        res = routing.get("results") if isinstance(routing.get("results"), list) else []
        urls = [str(r.get("url") or "") for r in res if isinstance(r, dict)]
        return provider, _dedupe_urls(urls, limit=12), {"note": "rss feed urls"}
    if provider == "decodo":
        # Decodo execution lives elsewhere; here we only return stub.
        return provider, [], {"request": routing.get("request")}
    return provider, [], {"error": "unsupported_or_empty_routing"}


def execute_task_routing(
    *,
    run_id: str,
    task: Dict[str, Any],
    routing: Dict[str, Any],
    anchor_ledger: str,
    evidence_graph_ledger: str,
    relation_default: str = "REFRAMES",
    max_fetch: int = 8,
) -> Dict[str, Any]:
    """
    For non-decodo providers: fetch minimal metadata and emit anchors + edges.
    For RSS: fetch feeds, extract item urls, then fetch those.
    For search_lite: fetch candidate URLs directly (no search re-fetch).
    For direct_http: fetch provided URLs.
    """
    claim_id = str(task.get("claim_id") or "")
    term = str(task.get("term") or "")
    task_id = str(task.get("task_id") or "")
    mode = str(task.get("mode") or "")
    task_kind = str(task.get("task_kind") or "")

    provider, urls, meta = resolve_routing_to_urls(routing)
    created = []
    errors = []

    # Pull claim text (best effort) for relation classification
    claim_text = ""
    try:
        for e in _read_jsonl(evidence_graph_ledger):
            if str(e.get("kind") or "") == "claim_added" and str(e.get("claim_id") or "") == claim_id:
                claim_text = str(e.get("text") or "") or str(e.get("claim_handle") or "") or ""
                break
    except Exception:
        claim_text = ""

    if provider == "decodo":
        return {
            "status": "DEFERRED",
            "provider": "decodo",
            "created_anchors": [],
            "errors": [],
            "notes": "Decodo execution is handled by a separate operator (WO-78D).",
        }

    # RSS special: urls are feeds; fetch feeds and expand into item links
    expanded_urls: List[str] = []
    if provider == "rss":
        for feed in urls[:max_fetch]:
            try:
                xml_text, hdrs = _http_get(feed, timeout=14, headers={"User-Agent": "abx/online_resolver (rss)"})
                item_urls = _parse_rss_urls(xml_text, limit=12)
                expanded_urls.extend(item_urls)
            except Exception as e:
                errors.append({"feed": feed, "error": str(e)})
        urls = _dedupe_urls(expanded_urls, limit=12)

    # Fetch pages and create anchors
    for u in urls[:max_fetch]:
        try:
            html, hdrs = _http_get(u, timeout=14, headers={"User-Agent": f"abx/online_resolver ({provider})"})
            title = _extract_title(html)
            pub = _extract_meta_date(html)
            snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:600]

            rr = classify_relation(
                claim_text=claim_text or term,
                anchor_title=title or "",
                anchor_snippet=snippet or "",
            )

            # minimal hint: term + title
            hint = f"{term} | {title}".strip(" |")
            anc = make_anchor(url=u, provider=provider, content_hint=hint, fetched_title=title, fetched_date=pub, headers={"content-type": hdrs.get("content-type", "")})
            _append_jsonl(anchor_ledger, {
                **anc,
                "run_id": run_id,
                "task_id": task_id,
                "term": term,
                "claim_id": claim_id,
                "relation_guess": rr.relation,
                "relation_confidence": rr.confidence,
                "relation_rationale": rr.rationale,
            })
            link_anchor_to_claim(
                run_id=run_id,
                claim_id=claim_id,
                anchor=anc,
                relation=rr.relation or relation_default,
                evidence_graph_ledger=evidence_graph_ledger,
            )
            created.append({
                "anchor_id": anc.get("anchor_id"),
                "url": anc.get("url"),
                "domain": anc.get("domain"),
                "title": anc.get("title"),
                "relation": rr.relation,
                "confidence": rr.confidence,
            })
        except Exception as e:
            errors.append({"url": u, "error": str(e)})

    return {
        "status": "OK",
        "provider": provider,
        "meta": meta,
        "created_anchors": created,
        "errors": errors,
        "notes": "Anchors emitted + edges linked. Downstream metrics recompute required.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-78: resolve routed online sourcing into anchors + evidence edges")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--execute-report", default="")  # acquisition_execute_*.json from WO-77
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--evidence-ledger", default="out/ledger/evidence_graph.jsonl")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--max-tasks", type=int, default=10)
    ap.add_argument("--max-fetch", type=int, default=8)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    # Load latest acquisition_execute if not provided
    exec_path = args.execute_report
    if not exec_path:
        import glob
        paths = sorted(glob.glob("out/reports/acquisition_execute_*.json"))
        exec_path = paths[-1] if paths else ""
    if not exec_path:
        raise SystemExit("No acquisition_execute report found. Run `python -m abx.acquisition_execute` first.")

    obj = _read_json(exec_path)
    executed = obj.get("executed") if isinstance(obj.get("executed"), list) else []
    executed = executed[: int(args.max_tasks)]

    results = []
    task_anchor_map: Dict[str, List[str]] = {}
    for it in executed:
        if not isinstance(it, dict):
            continue
        task = it.get("task") if isinstance(it.get("task"), dict) else {}
        routing = it.get("routing") if isinstance(it.get("routing"), dict) else {}
        if not task or not routing:
            continue

        task_id = str(task.get("task_id") or "")
        mode = str(task.get("mode") or "")
        provider = str(routing.get("provider") or "none")

        task_event(
            ledger=args.task_ledger,
            run_id=args.run_id,
            task_id=task_id,
            status="STARTED",
            mode=f"resolver:{provider}",
            claim_id=str(task.get("claim_id") or ""),
            term=str(task.get("term") or ""),
            task_kind=str(task.get("task_kind") or ""),
            detail=f"WO-78 resolving routing provider={provider}",
        )

        r = execute_task_routing(
            run_id=args.run_id,
            task=task,
            routing=routing,
            anchor_ledger=args.anchor_ledger,
            evidence_graph_ledger=args.evidence_ledger,
            relation_default="REFRAMES",
            max_fetch=int(args.max_fetch),
        )
        results.append({"task_id": task_id, "provider": provider, "result": r})

        # Collect anchor_ids for attribution (WO-81)
        created_anchors = r.get("created_anchors") if isinstance(r.get("created_anchors"), list) else []
        ids = []
        for ca in created_anchors:
            if isinstance(ca, dict) and ca.get("anchor_id"):
                ids.append(str(ca.get("anchor_id")))
        if ids:
            task_anchor_map[task_id] = ids

        task_event(
            ledger=args.task_ledger,
            run_id=args.run_id,
            task_id=task_id,
            status="COMPLETED",
            mode=f"resolver:{provider}",
            claim_id=str(task.get("claim_id") or ""),
            term=str(task.get("term") or ""),
            task_kind=str(task.get("task_kind") or ""),
            detail=f"WO-78 completed provider={provider} status={r.get('status')}",
            artifacts={"created_anchors": r.get("created_anchors"), "errors": r.get("errors")},
        )

    out_obj = {
        "version": "online_resolver.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "execute_report": exec_path,
        "n_items": len(results),
        "results": results,
        "task_anchor_map": task_anchor_map,
        "notes": "WO-78 resolves routed online tasks into anchors + evidence edges. Requires downstream metric recompute.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"online_resolver_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[ONLINE_RESOLVER] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
