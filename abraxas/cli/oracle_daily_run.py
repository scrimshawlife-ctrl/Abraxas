#!/usr/bin/env python3
"""Oracle Daily Run CLI

Execute Oracle v2 pipeline with date-stamped output for historical tracking.

This script:
1. Fetches observations from configured sources
2. Processes through Oracle v2 pipeline
3. Saves outputs to dated JSONL ledger
4. Generates weather intel artifacts
5. Updates historical metrics for stabilization gate

Usage:
    python -m abraxas.cli.oracle_daily_run --config config/oracle_daily.json
"""

import argparse
import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import List, Dict, Any, Iterable

from abraxas.lexicon.dce import DCEPack, DCERegistry, DomainCompressionEngine
from abraxas.lexicon.engine import InMemoryLexiconRegistry, LexiconEntry, LexiconPack
from abraxas.oracle.v2.pipeline import OracleV2Pipeline, OracleSignal, OracleV2Output
from abraxas.oracle.weather_bridge import oracle_to_weather_intel, write_mimetic_weather_report


def setup_logging(verbose: bool = False, log_file: Path = None):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    handlers = [logging.StreamHandler()]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9']{3,}", text.lower())
    unique = []
    seen = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique.append(token)
    return unique


def _fetch_rss_feed(url: str) -> List[Dict[str, str]]:
    with urllib.request.urlopen(url, timeout=10) as response:
        raw = response.read()
    tree = ET.fromstring(raw)
    items = []
    for item in tree.findall(".//item"):
        title = unescape((item.findtext("title") or "").strip())
        description = unescape((item.findtext("description") or "").strip())
        if not title and not description:
            continue
        items.append({"title": title, "description": description})
    return items


def _collect_observations_from_rss(
    rss_sources: Iterable[Any], logger: logging.Logger
) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    for source in rss_sources:
        if isinstance(source, str):
            source_config = {"url": source, "domain": "general"}
        else:
            source_config = dict(source)
        url = source_config.get("url")
        domain = source_config.get("domain", "general")
        subdomain = source_config.get("subdomain")
        if not url:
            continue
        try:
            items = _fetch_rss_feed(url)
        except Exception as exc:
            logger.warning("Failed to fetch RSS feed %s: %s", url, exc)
            continue
        texts = []
        tokens = []
        for item in items[:10]:
            text = " ".join([item.get("title", ""), item.get("description", "")]).strip()
            if text:
                texts.append(text)
                tokens.extend(_tokenize(text))
        if texts:
            observations.append(
                {
                    "domain": domain,
                    "subdomain": subdomain,
                    "observations": texts,
                    "tokens": tokens,
                }
            )
    return observations


def _collect_observations_from_api(
    api_sources: Iterable[Any], logger: logging.Logger
) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    for source in api_sources:
        if not isinstance(source, dict):
            continue
        url = source.get("url")
        domain = source.get("domain", "general")
        subdomain = source.get("subdomain")
        text_fields = source.get("text_fields", ["title", "summary"])
        if not url:
            continue
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("Failed to fetch API source %s: %s", url, exc)
            continue
        items = payload if isinstance(payload, list) else payload.get("items", [])
        texts = []
        tokens = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue
            parts = [str(item.get(field, "")).strip() for field in text_fields]
            text = " ".join([p for p in parts if p])
            if text:
                texts.append(text)
                tokens.extend(_tokenize(text))
        if texts:
            observations.append(
                {
                    "domain": domain,
                    "subdomain": subdomain,
                    "observations": texts,
                    "tokens": tokens,
                }
            )
    return observations


def fetch_observations(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch observations from configured sources.

    Args:
        config: Configuration dict with source definitions

    Returns:
        List of observation dicts with domain, tokens, and text
    """
    logger = logging.getLogger(__name__)

    logger.info("Fetching observations from configured sources...")

    sources = config.get("sources", {})
    rss_sources = sources.get("rss_feeds", [])
    api_sources = sources.get("apis", [])

    observations: List[Dict[str, Any]] = []
    if rss_sources:
        observations.extend(_collect_observations_from_rss(rss_sources, logger))
    if api_sources:
        observations.extend(_collect_observations_from_api(api_sources, logger))

    if not observations and config.get("allow_sample_observations"):
        observations = config.get("sample_observations", [])
        logger.warning("Using sample observations (allow_sample_observations=true).")

    logger.info(f"✓ Fetched {len(observations)} observations")

    return observations


def load_dce_engine(config: Dict[str, Any]) -> DomainCompressionEngine | None:
    dce_config = config.get("dce", {})
    packs = dce_config.get("packs", [])
    if not packs:
        return None
    base_registry = InMemoryLexiconRegistry()
    dce_registry = DCERegistry(base_registry)

    for pack in packs:
        domain = pack.get("domain")
        version = pack.get("version", "v0.1")
        entries_raw = pack.get("entries", [])
        if not domain or not entries_raw:
            continue
        entries = tuple(
            LexiconEntry(
                token=str(entry.get("token")),
                weight=float(entry.get("weight", 0.5)),
                meta=entry.get("meta", {}) or {},
            )
            for entry in entries_raw
            if entry.get("token")
        )
        lex_pack = LexiconPack(
            domain=domain,
            version=version,
            entries=entries,
            created_at_utc=LexiconPack.now_iso_z(),
        )
        dce_pack = DCEPack.from_lexicon_pack(lex_pack)
        dce_registry.register(dce_pack)

    return DomainCompressionEngine(dce_registry)


def create_oracle_signals(observations: List[Dict[str, Any]]) -> List[OracleSignal]:
    """Convert observations to Oracle signals.

    Args:
        observations: List of observation dicts

    Returns:
        List of OracleSignal objects
    """
    logger = logging.getLogger(__name__)
    signals = []
    timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for idx, obs in enumerate(observations):
        signal = OracleSignal(
            domain=obs["domain"],
            subdomain=obs.get("subdomain"),
            observations=obs["observations"],
            tokens=obs["tokens"],
            timestamp_utc=timestamp_utc,
            source_id=f"daily_{obs['domain']}_{idx:03d}",
        )
        signals.append(signal)

    logger.info(f"✓ Created {len(signals)} Oracle signals")
    return signals


def save_oracle_outputs(outputs: List[OracleV2Output], output_path: Path):
    """Save Oracle outputs to JSONL ledger.

    Args:
        outputs: List of Oracle v2 outputs
        output_path: Path to JSONL file
    """
    logger = logging.getLogger(__name__)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "a", encoding="utf-8") as f:
        for output in outputs:
            output_dict = asdict(output)
            f.write(json.dumps(output_dict, ensure_ascii=False) + "\n")

    logger.info(f"✓ Saved {len(outputs)} outputs to {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Execute daily Oracle v2 pipeline run with historical tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python -m abraxas.cli.oracle_daily_run \\
      --config config/oracle_daily.json

  # Run with custom output directory
  python -m abraxas.cli.oracle_daily_run \\
      --config config/oracle_daily.json \\
      --output-dir data/oracle_history/

  # Run with verbose logging
  python -m abraxas.cli.oracle_daily_run \\
      --config config/oracle_daily.json \\
      --verbose \\
      --log-file logs/oracle_daily.log
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to Oracle daily run configuration JSON",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default="out/ledger",
        help="Output directory for historical Oracle runs",
    )

    parser.add_argument(
        "--intel-dir",
        type=Path,
        default="data/intel",
        help="Output directory for weather intel artifacts",
    )

    parser.add_argument(
        "--report-dir",
        type=Path,
        default="out/reports",
        help="Output directory for weather reports",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        help="Optional log file path",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose, args.log_file)
    logger = logging.getLogger(__name__)

    # Get today's date for output files
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_id = f"DAILY-{today}"

    logger.info("=" * 80)
    logger.info(f"Oracle Daily Run - {today}")
    logger.info("=" * 80)

    # Load configuration
    logger.info(f"Loading configuration from: {args.config}")
    config = load_config(args.config)
    logger.info(f"✓ Configuration loaded")

    # Fetch observations
    observations = fetch_observations(config)

    if not observations:
        logger.warning("No observations fetched. Exiting.")
        return 1

    # Create Oracle signals
    signals = create_oracle_signals(observations)

    # Initialize Oracle pipeline
    logger.info("Initializing Oracle v2 pipeline...")
    dce_engine = load_dce_engine(config)
    pipeline = OracleV2Pipeline(dce_engine=dce_engine)
    logger.info("✓ Oracle v2 pipeline initialized")

    # Process signals
    logger.info(f"Processing {len(signals)} signals...")
    outputs = []
    for idx, signal in enumerate(signals, 1):
        signal_run_id = f"{run_id}-{idx:03d}"
        logger.info(f"  [{idx}/{len(signals)}] Processing {signal.domain}...")
        output = pipeline.process(signal, run_id=signal_run_id)
        outputs.append(output)
        logger.info(f"  ✓ {signal_run_id}: {len(output.compression.compressed_tokens)} tokens")

    logger.info(f"✓ Processed {len(outputs)} signals")

    # Save outputs to historical ledger
    output_path = args.output_dir / f"oracle_runs_{today}.jsonl"
    save_oracle_outputs(outputs, output_path)

    # Generate weather intel
    logger.info("Generating weather intel artifacts...")
    intel_written = oracle_to_weather_intel(outputs, args.intel_dir)
    logger.info(f"✓ Generated {len(intel_written)} intel artifacts")

    # Generate weather report
    report_path = args.report_dir / f"weather_report_{today}.json"
    write_mimetic_weather_report(outputs, report_path)
    logger.info(f"✓ Weather report written to {report_path}")

    logger.info("=" * 80)
    logger.info(f"Oracle Daily Run Complete - {run_id}")
    logger.info("=" * 80)
    logger.info(f"Outputs saved to: {output_path}")
    logger.info(f"Intel artifacts: {args.intel_dir}")
    logger.info(f"Weather report: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
