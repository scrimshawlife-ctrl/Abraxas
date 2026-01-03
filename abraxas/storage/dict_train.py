"""Zstd dictionary training for source-specific compression.

Performance Drop v1.0 - Deterministic dictionary training.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from abraxas.storage.layout import ensure_cas_dirs, get_dict_path


def train_zstd_dict(
    source_id: str,
    year: int,
    month: int,
    sample_paths: list[Path],
    *,
    dict_size: int = 110 * 1024,  # 110KB default
    max_samples: int = 100,
) -> Path:
    """Train zstd dictionary for a source/time window.

    Args:
        source_id: Source identifier
        year: Year
        month: Month
        sample_paths: Paths to sample files for training
        dict_size: Target dictionary size in bytes (default: 110KB)
        max_samples: Maximum number of samples to use (default: 100)

    Returns:
        Path to trained .zstdict file
    """
    try:
        import zstandard as zstd
    except ImportError:
        raise RuntimeError("zstandard library required for dictionary training")

    # Deterministic sample selection: sort by path, take first N
    sorted_samples = sorted(sample_paths)[:max_samples]

    # Load sample data
    samples = []
    for sample_path in sorted_samples:
        if sample_path.exists():
            with open(sample_path, "rb") as f:
                samples.append(f.read())

    if not samples:
        raise ValueError(f"No valid samples found for {source_id}/{year}/{month}")

    # Train dictionary
    dict_data = zstd.train_dictionary(dict_size, samples)

    # Compute provenance hash
    samples_hash = hashlib.sha256(b"".join(samples)).hexdigest()

    # Save dictionary
    dict_path = get_dict_path(source_id, year, month)
    ensure_cas_dirs(dict_path)

    with open(dict_path, "wb") as f:
        f.write(dict_data.as_bytes())

    # Save provenance metadata
    meta_path = dict_path.with_suffix(".meta.json")
    meta = {
        "source_id": source_id,
        "year": year,
        "month": month,
        "dict_size": len(dict_data.as_bytes()),
        "num_samples": len(samples),
        "samples_hash": samples_hash,
        "sample_paths": [str(p) for p in sorted_samples],
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)

    return dict_path


def should_retrain_dict(
    source_id: str,
    year: int,
    month: int,
    current_samples: list[Path],
    *,
    drift_threshold: float = 0.2,
) -> bool:
    """Determine if dictionary should be retrained based on drift.

    Args:
        source_id: Source identifier
        year: Year
        month: Month
        current_samples: Current sample paths
        drift_threshold: Drift threshold for retraining (default: 0.2)

    Returns:
        True if dictionary should be retrained, False otherwise
    """
    dict_path = get_dict_path(source_id, year, month)
    meta_path = dict_path.with_suffix(".meta.json")

    if not dict_path.exists() or not meta_path.exists():
        return True

    # Load previous metadata
    with open(meta_path, "r") as f:
        prev_meta = json.load(f)

    prev_samples_hash = prev_meta.get("samples_hash")
    if not prev_samples_hash:
        return True

    # Compute current samples hash
    sorted_samples = sorted(current_samples)[: prev_meta.get("num_samples", 100)]
    current_samples_bytes = []
    for sample_path in sorted_samples:
        if sample_path.exists():
            with open(sample_path, "rb") as f:
                current_samples_bytes.append(f.read())

    current_samples_hash = hashlib.sha256(b"".join(current_samples_bytes)).hexdigest()

    # Deterministic drift metric: Hamming distance on hash prefixes
    prev_prefix = prev_samples_hash[:16]
    curr_prefix = current_samples_hash[:16]

    hamming_dist = sum(c1 != c2 for c1, c2 in zip(prev_prefix, curr_prefix))
    drift_score = hamming_dist / len(prev_prefix)

    return drift_score > drift_threshold
