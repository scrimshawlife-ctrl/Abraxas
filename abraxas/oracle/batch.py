from __future__ import annotations

import argparse
import os
import json
from typing import Any, Dict, List, Optional, Tuple

from abraxas.oracle.mda_bridge import run_mda_for_oracle
from abraxas.mda.signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check
from abraxas.oracle.renderers import render_from_signal_v2
from abraxas.oracle.packet import OraclePacket, OraclePacketRun, write_packet


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _list_payloads(payload_dir: str) -> List[str]:
    # Deterministic: sorted lexicographically, only .json
    items: List[str] = []
    for fn in os.listdir(payload_dir):
        if fn.lower().endswith(".json"):
            items.append(os.path.join(payload_dir, fn))
    return sorted(items)


def _parse_domains(s: str) -> Optional[Tuple[str, ...]]:
    if not s or s.strip() == "*":
        return None
    return tuple(x.strip() for x in s.split(",") if x.strip())


def _parse_subdomains(s: str) -> Optional[Tuple[str, ...]]:
    if not s or s.strip() == "*":
        return None
    return tuple(x.strip() for x in s.split(",") if x.strip())


def _make_index_md(runs: List[OraclePacketRun], *, out_dir: str) -> str:
    lines: List[str] = []
    lines.append("# Oracle Batch Index")
    lines.append("")
    lines.append(f"- Output directory: `{out_dir}`")
    lines.append("")
    lines.append("| Run | Payload | Mode | Slice Hash | Artifacts |")
    lines.append("|---:|---|---|---|---|")
    for r in runs:
        arts = ", ".join(r.artifacts)
        lines.append(
            f"| `{r.run_id}` | `{os.path.basename(r.payload_path)}` | `{r.mode}` | `{r.signal_slice_hash}` | {arts} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="abraxas.oracle.batch")
    p.add_argument("--payload-dir", required=True, help="Directory of JSON payloads (bundle or vectors-only)")
    p.add_argument("--out", default=os.path.join(".sandbox", "oracle_batch"))
    p.add_argument("--mode", default="analyst", choices=["oracle", "ritual", "analyst"])
    p.add_argument("--version", default="2.2.0")
    p.add_argument("--env", default="sandbox", choices=["sandbox", "dev", "prod"])
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--run-at", default="2026-01-01T00:00:00Z")
    p.add_argument("--domains", default="*", help="Comma list of domains or '*'")
    p.add_argument("--subdomains", default="*", help="Comma list of domain:subdomain or '*'")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    args = p.parse_args()

    payloads = _list_payloads(args.payload_dir)
    if not payloads:
        raise SystemExit(f"No .json payloads found in: {args.payload_dir}")

    domains = _parse_domains(args.domains)
    subdomains = _parse_subdomains(args.subdomains)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    packet_runs: List[OraclePacketRun] = []

    for idx, payload_path in enumerate(payloads, start=1):
        run_id = f"run_{idx:02d}"
        run_dir = os.path.join(out_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        payload = _load_json(payload_path)

        mda_out = run_mda_for_oracle(
            env=args.env,
            run_at_iso=args.run_at,
            seed=args.seed,
            abraxas_version=args.version,
            domains=domains,
            subdomains=subdomains,
            payload=payload,
        )

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

        slice_hash = sig["oracle_signal_v2"]["meta"]["slice_hash"]
        packet_runs.append(
            OraclePacketRun(
                run_id=run_id,
                payload_path=payload_path,
                mode=args.mode,
                domains=tuple(domains) if domains else tuple(),
                subdomains=tuple(subdomains) if subdomains else tuple(),
                signal_slice_hash=slice_hash,
                artifacts=tuple(artifacts),
            )
        )

    packet = OraclePacket(
        version=args.version,
        env=args.env,
        run_at=args.run_at,
        seed=args.seed,
        runs=tuple(packet_runs),
    )
    write_packet(packet, os.path.join(out_dir, "oracle_packet.json"))
    _write_text(os.path.join(out_dir, "index.md"), _make_index_md(packet_runs, out_dir=out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

