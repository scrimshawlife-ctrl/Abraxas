"""Simulation Mapping CLI: Map academic model parameters to Abraxas knobs.

Command:
    abx sim-map --family DIFFUSION_SIR --params beta=0.3 gamma=0.1 --paper_id PMC12281847

Outputs JSON MappingResult to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    PaperRef,
    map_paper_model,
)
from abraxas.sim_mappings.registry import get_paper_ref
from abraxas.sod.sim_adapter import convert_knobs_to_sod_priors, explain_sod_priors


def parse_params(param_strings: List[str]) -> List[ModelParam]:
    """
    Parse parameter strings in format 'name=value' or 'name:symbol=value'.

    Examples:
        - 'beta=0.3' → ModelParam(name='beta', value=0.3)
        - 'beta:β=0.3' → ModelParam(name='beta', symbol='β', value=0.3)
    """
    params = []
    for param_str in param_strings:
        # Split on '='
        if "=" not in param_str:
            print(f"Warning: Skipping invalid param '{param_str}' (no '=' found)", file=sys.stderr)
            continue

        name_part, value_str = param_str.split("=", 1)

        # Check for symbol separator ':'
        if ":" in name_part:
            name, symbol = name_part.split(":", 1)
        else:
            name = name_part
            symbol = None

        # Parse value
        try:
            value = float(value_str)
        except ValueError:
            print(f"Warning: Skipping param '{param_str}' (invalid numeric value)", file=sys.stderr)
            continue

        params.append(ModelParam(name=name, symbol=symbol, value=value))

    return params


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Map academic simulation model parameters to Abraxas knobs (MRI/IRI/τ)"
    )

    parser.add_argument(
        "--family",
        type=str,
        required=True,
        choices=[f.value for f in ModelFamily],
        help="Model family",
    )

    parser.add_argument(
        "--params",
        type=str,
        nargs="+",
        required=True,
        help="Parameters in format 'name=value' or 'name:symbol=value'",
    )

    parser.add_argument(
        "--paper_id",
        type=str,
        help="Paper ID (will look up in registry if available)",
    )

    parser.add_argument(
        "--paper_title",
        type=str,
        help="Paper title (used if paper_id not in registry)",
    )

    parser.add_argument(
        "--paper_url",
        type=str,
        help="Paper URL (used if paper_id not in registry)",
    )

    parser.add_argument(
        "--paper_year",
        type=int,
        help="Paper year (used if paper_id not in registry)",
    )

    parser.add_argument(
        "--save",
        type=str,
        help="Save mapping result to file (JSON)",
    )

    parser.add_argument(
        "--sod",
        action="store_true",
        help="Also output SOD priors",
    )

    args = parser.parse_args()

    # Parse model family
    family = ModelFamily(args.family)

    # Parse parameters
    params = parse_params(args.params)

    if not params:
        print("Error: No valid parameters provided", file=sys.stderr)
        sys.exit(1)

    # Get or create paper reference
    paper = None
    if args.paper_id:
        # Try to load from registry
        paper = get_paper_ref(args.paper_id)

        if not paper:
            # Create new paper ref
            paper = PaperRef(
                paper_id=args.paper_id,
                title=args.paper_title or f"Paper {args.paper_id}",
                url=args.paper_url or f"https://example.com/{args.paper_id}",
                year=args.paper_year,
            )
    else:
        # No paper ID provided, use generic
        paper = PaperRef(
            paper_id="UNKNOWN",
            title=args.paper_title or "Unknown Paper",
            url=args.paper_url or "https://example.com/unknown",
            year=args.paper_year,
        )

    # Map to knobs
    result = map_paper_model(paper, family, params)

    # Convert to dict
    result_dict = result.to_dict()

    # Output JSON to stdout
    print(json.dumps(result_dict, indent=2, ensure_ascii=True))

    # Optionally output SOD priors
    if args.sod:
        print("\n--- SOD Priors ---\n", file=sys.stderr)
        sod_priors = convert_knobs_to_sod_priors(result.mapped.to_dict())
        print(explain_sod_priors(sod_priors), file=sys.stderr)

    # Save if requested
    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=True)

        print(f"\nSaved to: {save_path}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
