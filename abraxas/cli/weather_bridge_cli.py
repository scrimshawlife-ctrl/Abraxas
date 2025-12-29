#!/usr/bin/env python3
"""Weather Bridge CLI

Convert Oracle v2 outputs to weather intel artifacts and fronts.

Usage:
    python -m abraxas.cli.weather_bridge_cli --oracle-runs data/oracle_runs.jsonl --output data/intel/
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List

from abraxas.oracle.v2.pipeline import OracleV2Output
from abraxas.oracle.weather_bridge import (
    oracle_to_weather_intel,
    oracle_to_mimetic_weather_fronts,
    write_mimetic_weather_report,
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_oracle_outputs(input_path: Path) -> List[OracleV2Output]:
    """Load Oracle v2 outputs from JSONL file.

    Args:
        input_path: Path to JSONL file with Oracle outputs

    Returns:
        List of OracleV2Output objects
    """
    logger = logging.getLogger(__name__)
    outputs = []
    line_num = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                output = OracleV2Output.from_dict(data)
                outputs.append(output)
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: Failed to parse JSON: {e}")
            except Exception as e:
                logger.error(f"Line {line_num}: Failed to deserialize Oracle output: {e}")

    logger.info(f"✓ Loaded {len(outputs)} Oracle outputs from {input_path}")
    return outputs


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Oracle v2 outputs to weather intel and fronts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Oracle runs to weather intel
  python -m abraxas.cli.weather_bridge_cli \\
      --oracle-runs data/oracle_runs.jsonl \\
      --output data/intel/

  # Generate weather report
  python -m abraxas.cli.weather_bridge_cli \\
      --oracle-runs data/oracle_runs.jsonl \\
      --mode report \\
      --output out/reports/weather_report.json

  # Generate both intel and report
  python -m abraxas.cli.weather_bridge_cli \\
      --oracle-runs data/oracle_runs.jsonl \\
      --mode both \\
      --intel-dir data/intel/ \\
      --report-path out/reports/weather_report.json
        """,
    )

    parser.add_argument(
        "--oracle-runs",
        type=Path,
        required=True,
        help="Path to JSONL file with Oracle v2 outputs",
    )

    parser.add_argument(
        "--mode",
        choices=["intel", "report", "both"],
        default="intel",
        help="What to generate: intel artifacts, weather report, or both",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for intel artifacts (when mode=intel)",
    )

    parser.add_argument(
        "--intel-dir",
        type=Path,
        default="data/intel",
        help="Output directory for intel artifacts (when mode=both)",
    )

    parser.add_argument(
        "--report-path",
        type=Path,
        default="out/reports/weather_report.json",
        help="Output path for weather report JSON (when mode=report or mode=both)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info(f"Weather Bridge CLI - Mode: {args.mode}")

    # Validate inputs
    if not args.oracle_runs.exists():
        logger.error(f"Oracle runs file not found: {args.oracle_runs}")
        return 1

    # Load Oracle outputs
    logger.info(f"Loading Oracle outputs from: {args.oracle_runs}")
    oracle_outputs = load_oracle_outputs(args.oracle_runs)

    if not oracle_outputs:
        logger.error("No Oracle outputs loaded. Exiting.")
        return 1

    logger.info(f"Processing {len(oracle_outputs)} Oracle outputs...")

    # Generate intel artifacts
    if args.mode in {"intel", "both"}:
        output_dir = args.output if args.mode == "intel" else args.intel_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating weather intel artifacts in: {output_dir}")
        written_intel = oracle_to_weather_intel(oracle_outputs, output_dir)

        logger.info(f"✓ Generated {len(written_intel)} intel artifacts:")
        for name, path in written_intel.items():
            logger.info(f"  - {name}: {path}")

    # Generate weather report
    if args.mode in {"report", "both"}:
        report_path = args.report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating weather fronts report at: {report_path}")
        fronts = oracle_to_mimetic_weather_fronts(oracle_outputs)

        logger.info(f"✓ Generated {len(fronts)} weather fronts")

        # Write report
        write_mimetic_weather_report(fronts, report_path)
        logger.info(f"✓ Weather report written to: {report_path}")

    logger.info("✓ Weather bridge CLI execution complete")
    return 0


if __name__ == "__main__":
    exit(main())
