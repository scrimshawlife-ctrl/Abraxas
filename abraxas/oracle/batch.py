from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.oracle.mda_bridge import run_mda_for_oracle
from abraxas.mda.signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check
from abraxas.oracle.renderers import render_from_signal_v2
from abraxas.oracle.packet import OraclePacket, OraclePacketRun
from abraxas.overlays.abx_gt_shadow import try_run_abx_gt_shadow
from abraxas.training.integrate_v1 import oracle_attach_training_shadow
from abraxas.oracle.attach_aalmanac_shadow import attach_aalmanac_shadow


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _shadow_summary_from_signal_v2(sig: Dict[str, Any], *, cap_alert_tokens: int = 5) -> Optional[Dict[str, Any]]:
    """
    Extract a compact summary of shadow.anagram_* artifacts.
    Deterministic, bounded, safe to include in packet.
    """
    osv2 = sig.get("oracle_signal_v2") or {}
    mda = (osv2.get("mda_v1_1") or {})
    shadow = mda.get("shadow")
    if not isinstance(shadow, dict):
        return None

    cl = shadow.get("anagram_cluster_v1") or shadow.get("anagram_cluster") or None
    an = shadow.get("anagram_v1") or shadow.get("anagram") or None

    out: Dict[str, Any] = {"present": True}

    if isinstance(an, dict):
        an1 = an.get("shadow_anagram_v1") or {}
        cands = an1.get("candidates") or []
        out["anagram_v1"] = {
            "candidates_count": int(len(cands)) if isinstance(cands, list) else 0,
            "artifact_hash": str(an1.get("artifact_hash", "")),
            "has_evidence": bool((an1.get("provenance", {}) or {}).get("has_evidence", False)),
        }

    if isinstance(cl, dict):
        cl1 = cl.get("shadow_anagram_cluster_v1") or {}
        clusters = cl1.get("clusters") or []
        alerts = cl1.get("watch_alerts") or []
        tok_sample: List[str] = []
        if isinstance(alerts, list):
            for a in alerts[:cap_alert_tokens]:
                t = str(a.get("token", "")).strip()
                if t:
                    tok_sample.append(t)
        out["anagram_cluster_v1"] = {
            "clusters_count": int(len(clusters)) if isinstance(clusters, list) else 0,
            "global_count": int(cl1.get("global_count", 0) or 0),
            "watch_alerts_count": int(len(alerts)) if isinstance(alerts, list) else 0,
            "watch_alert_tokens_sample": tok_sample,
            "artifact_hash": str(cl1.get("artifact_hash", "")),
        }

    return out


def _list_payloads(payload_dir: str) -> List[str]:
    return sorted(
        os.path.join(payload_dir, p)
        for p in os.listdir(payload_dir)
        if p.endswith(".json")
    )


def _parse_domains(s: str) -> Optional[Tuple[str, ...]]:
    if not s.strip():
        return None
    return tuple(x.strip() for x in s.split(",") if x.strip())


def _make_index_md(runs: List[OraclePacketRun], *, out_dir: str) -> str:
    lines = []
    lines.append("# Oracle Batch Index")
    lines.append("")
    lines.append(f"- Output directory: `{out_dir}`")
    lines.append("")
    lines.append("| Run | Payload | Mode | Slice Hash | Shadow Alerts | Shadow Alert Tokens | Artifacts |")
    lines.append("|---:|---|---|---|---:|---|---|")
    for r in runs:
        arts = ", ".join(r.artifacts)
        ss = r.shadow_summary or {}
        alerts = ""
        toks = ""
        if isinstance(ss, dict):
            cl = ss.get("anagram_cluster_v1") or {}
            alerts = str(cl.get("watch_alerts_count", ""))
            toks = ", ".join(cl.get("watch_alert_tokens_sample") or [])
        lines.append(
            f"| `{r.run_id}` | `{os.path.basename(r.payload_path)}` | `{r.mode}` | `{r.signal_slice_hash}` | {alerts} | {toks} | {arts} |"
        )
    lines.append("")
    return "\n".join(lines)


def _ensure_slice_hash(sig: Dict[str, Any]) -> str:
    osv2 = sig.setdefault("oracle_signal_v2", {})
    meta = osv2.setdefault("meta", {})
    if isinstance(meta, dict) and meta.get("slice_hash"):
        return str(meta["slice_hash"])
    slice_hash = sha256_hex(canonical_json(osv2))
    meta["slice_hash"] = slice_hash
    return slice_hash


def _shadow_seed(seed: str) -> int:
    try:
        return int(seed)
    except (TypeError, ValueError):
        return int(sha256_hex(str(seed))[:8], 16)


def _shadow_context(payload: Dict[str, Any], *, run_at: str) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {
        "oracle_date": str(payload.get("oracle_date") or payload.get("date") or run_at.split("T")[0]),
    }
    location = payload.get("location")
    if location:
        ctx["location"] = location
    signals = payload.get("signals")
    if isinstance(signals, dict):
        ctx["signals"] = signals
    return ctx


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Run oracle batch packaging.")
    p.add_argument("--payload-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--mode", default="analyst")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--env", default="sandbox")
    p.add_argument("--seed", default="0")
    p.add_argument("--run-at", default="1970-01-01T00:00:00Z")
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--domains", default="")
    p.add_argument("--subdomains", default="")
    args = p.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    payloads = _list_payloads(args.payload_dir)
    domains = _parse_domains(args.domains)
    subdomains = _parse_domains(args.subdomains)

    packet_runs: List[OraclePacketRun] = []
    shadow_context: Optional[Dict[str, Any]] = None
    for idx, payload_path in enumerate(payloads, start=1):
        run_id = f"run_{idx:02d}"
        run_dir = os.path.join(args.out, run_id)
        os.makedirs(run_dir, exist_ok=True)

        with open(payload_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if shadow_context is None and isinstance(payload, dict):
            shadow_context = _shadow_context(payload, run_at=args.run_at)

        mda_out = run_mda_for_oracle(payload, env=args.env, run_at=args.run_at)
        sig = mda_to_oracle_signal_v2(mda_out)
        if args.signal_schema_check:
            shallow_schema_check(sig)

        artifacts: List[str] = []
        if args.emit_signal_v2:
            sp = os.path.join(run_dir, "signal_v2.json")
            with open(sp, "w", encoding="utf-8") as f:
                json.dump(sig, f, ensure_ascii=False, indent=2, sort_keys=True)
            artifacts.append("signal_v2.json")

        rendered = render_from_signal_v2(sig, mode=args.mode)
        md_path = os.path.join(run_dir, f"{args.mode}.md")
        _write_text(md_path, rendered.markdown)
        artifacts.append(f"{args.mode}.md")

        slice_hash = _ensure_slice_hash(sig)
        shadow_summary = _shadow_summary_from_signal_v2(sig)
        packet_runs.append(OraclePacketRun(
            run_id=run_id,
            payload_path=payload_path,
            mode=args.mode,
            domains=tuple(domains) if domains else tuple(),
            subdomains=tuple(subdomains) if subdomains else tuple(),
            signal_slice_hash=slice_hash,
            artifacts=tuple(artifacts),
            shadow_summary=shadow_summary,
        ))

    packet = OraclePacket(
        version=args.version,
        env=args.env,
        run_at=args.run_at,
        seed=args.seed,
        runs=tuple(packet_runs),
        shadow={"abx_gt": try_run_abx_gt_shadow(seed=_shadow_seed(args.seed), context=shadow_context or {})},
    )
    packet_obj = packet.to_json()
    packet_obj.pop("oracle_packet_hash", None)
    packet_obj = oracle_attach_training_shadow(packet_obj)
    packet_obj = attach_aalmanac_shadow(packet_obj)
    packet_obj["oracle_packet_hash"] = sha256_hex(canonical_json(packet_obj))
    with open(os.path.join(args.out, "oracle_packet.json"), "w", encoding="utf-8") as f:
        json.dump(packet_obj, f, ensure_ascii=False, indent=2, sort_keys=True)
    _write_text(os.path.join(args.out, "index.md"), _make_index_md(packet_runs, out_dir=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
