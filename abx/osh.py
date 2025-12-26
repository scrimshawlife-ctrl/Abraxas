from __future__ import annotations

import argparse

from abraxas.osh.executor import compile_jobs_from_dap, run_osh_jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Abraxas OSH v0.1 (Decodo executor)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dap", required=True, help="Path to dap_<run_id>.json")
    parser.add_argument("--out-dir", default="out")
    parser.add_argument(
        "--vector-map",
        default="data/vector_maps/source_vector_map_v0_1.yaml",
        help="Vector map YAML/JSON for node_id -> allowlist_source_ids",
    )
    parser.add_argument(
        "--allowlist-spec",
        default=None,
        help="Allowlist spec YAML/JSON with sources (preferred)",
    )
    parser.add_argument(
        "--allowlist-map",
        default=None,
        help="Fallback JSON mapping: allowlist_source_id -> url",
    )
    args = parser.parse_args()

    if not args.allowlist_spec and not args.allowlist_map:
        parser.error("Either --allowlist-spec or --allowlist-map is required.")

    jobs = compile_jobs_from_dap(
        dap_json_path=args.dap,
        run_id=args.run_id,
        allowlist_spec_path=args.allowlist_spec,
        allowlist_map_fallback_path=args.allowlist_map,
        vector_map_path=args.vector_map,
    )
    print(f"[OSH] compiled jobs: {len(jobs)}")
    if not jobs:
        return 0

    artifacts, packets = run_osh_jobs(jobs, out_dir=args.out_dir)
    print(f"[OSH] artifacts: {len(artifacts)} packets: {len(packets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
