#!/usr/bin/env python3
"""ABX-Runes Sigil Generator CLI.

Deterministic SVG sigil generation for ABX-Runes.
Generates sigils, computes hashes, and maintains manifest.

Usage:
    python scripts/gen_abx_sigils.py --all --write-manifest
    python scripts/gen_abx_sigils.py --id ϟ₄
    python scripts/gen_abx_sigils.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path to import abraxas modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from abraxas.runes.models import RuneDefinition, SigilManifest, SigilManifestEntry
from abraxas.runes.sigil_generator import generate_sigil

GENERATOR_VERSION = "1.0.0"
REPO_ROOT = Path(__file__).parent.parent
DEFINITIONS_DIR = REPO_ROOT / "abraxas" / "runes" / "definitions"
SIGILS_DIR = REPO_ROOT / "abraxas" / "runes" / "sigils"
MANIFEST_PATH = SIGILS_DIR / "manifest.json"


def load_rune_definition(definition_path: Path) -> RuneDefinition:
    """Load a rune definition from JSON file."""
    with open(definition_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RuneDefinition(**data)


def load_all_rune_definitions() -> list[RuneDefinition]:
    """Load all rune definitions from definitions directory."""
    definitions = []
    for json_file in sorted(DEFINITIONS_DIR.glob("rune_*.json")):
        definitions.append(load_rune_definition(json_file))
    return definitions


def compute_svg_hash(svg_content: str) -> str:
    """Compute SHA-256 hash of SVG content."""
    return hashlib.sha256(svg_content.encode("utf-8")).hexdigest()


def get_sigil_filename(rune: RuneDefinition) -> str:
    """Get deterministic filename for sigil."""
    # Clean ID for filename (remove special chars)
    id_clean = rune.id.replace("ϟ", "rune").replace("₁", "1").replace("₂", "2").replace("₃", "3").replace("₄", "4").replace("₅", "5").replace("₆", "6")
    return f"{id_clean}_{rune.short_name}.svg"


def generate_and_save_sigil(rune: RuneDefinition, output_dir: Path) -> tuple[Path, str]:
    """Generate sigil and save to file.

    Returns:
        Tuple of (file_path, sha256_hash)
    """
    print(f"Generating sigil for {rune.id} {rune.short_name}...")

    # Generate SVG
    seed_material = rune.get_seed_material()
    svg_content = generate_sigil(rune.id, seed_material)

    # Compute hash
    svg_hash = compute_svg_hash(svg_content)

    # Save to file
    filename = get_sigil_filename(rune)
    file_path = output_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"  Saved: {file_path.relative_to(REPO_ROOT)}")
    print(f"  Hash:  {svg_hash[:16]}...")

    return file_path, svg_hash


def create_manifest_entry(rune: RuneDefinition, file_path: Path, svg_hash: str) -> SigilManifestEntry:
    """Create manifest entry for a sigil."""
    return SigilManifestEntry(
        id=rune.id,
        short_name=rune.short_name,
        svg_path=str(file_path.relative_to(REPO_ROOT)),
        sha256=svg_hash,
        seed_material=rune.get_seed_material(),
        width=512,
        height=512,
    )


def generate_all_sigils(write_manifest: bool = True) -> SigilManifest:
    """Generate all sigils and optionally write manifest.

    Args:
        write_manifest: Whether to write manifest to disk

    Returns:
        SigilManifest object
    """
    print(f"\n{'='*60}")
    print("ABX-Runes Sigil Generator")
    print(f"Generator Version: {GENERATOR_VERSION}")
    print(f"{'='*60}\n")

    # Ensure output directory exists
    SIGILS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all rune definitions
    runes = load_all_rune_definitions()
    print(f"Loaded {len(runes)} rune definitions\n")

    # Generate sigils
    manifest_entries = []
    for rune in runes:
        file_path, svg_hash = generate_and_save_sigil(rune, SIGILS_DIR)
        entry = create_manifest_entry(rune, file_path, svg_hash)
        manifest_entries.append(entry)

    # Create manifest
    manifest = SigilManifest(
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        generator_version=GENERATOR_VERSION,
        entries=manifest_entries,
    )

    # Write manifest if requested
    if write_manifest:
        print(f"\nWriting manifest to {MANIFEST_PATH.relative_to(REPO_ROOT)}...")
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)
            f.write("\n")  # Add trailing newline
        print("Manifest written successfully!")

    print(f"\n{'='*60}")
    print(f"Generated {len(manifest_entries)} sigils")
    print(f"{'='*60}\n")

    return manifest


def generate_single_sigil(rune_id: str) -> None:
    """Generate sigil for a single rune by ID."""
    print(f"\n{'='*60}")
    print(f"Generating sigil for {rune_id}")
    print(f"{'='*60}\n")

    # Find rune definition
    runes = load_all_rune_definitions()
    rune = next((r for r in runes if r.id == rune_id), None)

    if rune is None:
        print(f"ERROR: No rune definition found for ID: {rune_id}")
        sys.exit(1)

    # Ensure output directory exists
    SIGILS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate sigil
    file_path, svg_hash = generate_and_save_sigil(rune, SIGILS_DIR)

    print(f"\n{'='*60}")
    print("Done!")
    print(f"{'='*60}\n")


def check_manifest() -> bool:
    """Check that manifest hashes match generated files.

    Returns:
        True if all hashes match, False otherwise
    """
    print(f"\n{'='*60}")
    print("Checking manifest integrity")
    print(f"{'='*60}\n")

    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH.relative_to(REPO_ROOT)}")
        return False

    # Load manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest = SigilManifest(**manifest_data)

    print(f"Manifest version: {manifest.generator_version}")
    print(f"Generated at: {manifest.generated_at_utc}")
    print(f"Entries: {len(manifest.entries)}\n")

    all_valid = True
    for entry in manifest.entries:
        file_path = REPO_ROOT / entry.svg_path
        print(f"Checking {entry.id} {entry.short_name}...")

        if not file_path.exists():
            print(f"  ERROR: File not found: {entry.svg_path}")
            all_valid = False
            continue

        # Read file and compute hash
        with open(file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        actual_hash = compute_svg_hash(svg_content)

        if actual_hash == entry.sha256:
            print(f"  ✓ Hash matches: {actual_hash[:16]}...")
        else:
            print(f"  ✗ Hash mismatch!")
            print(f"    Expected: {entry.sha256}")
            print(f"    Actual:   {actual_hash}")
            all_valid = False

    print(f"\n{'='*60}")
    if all_valid:
        print("✓ All manifest entries valid!")
    else:
        print("✗ Manifest validation failed!")
    print(f"{'='*60}\n")

    return all_valid


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ABX-Runes Sigil Generator")
    parser.add_argument("--all", action="store_true", help="Generate all sigils")
    parser.add_argument("--id", type=str, help="Generate sigil for specific rune ID (e.g., ϟ₄)")
    parser.add_argument("--check", action="store_true", help="Check manifest integrity")
    parser.add_argument("--write-manifest", action="store_true", help="Write manifest file (use with --all)")

    args = parser.parse_args()

    if args.check:
        success = check_manifest()
        sys.exit(0 if success else 1)
    elif args.all:
        generate_all_sigils(write_manifest=args.write_manifest)
    elif args.id:
        generate_single_sigil(args.id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
