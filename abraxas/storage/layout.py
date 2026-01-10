"""CAS layout helpers - deterministic directory structure.

Performance Drop v1.0 - Content-Addressed Storage layout.

Layout:
  data/cas/
    raw/<source_id>/<yyyy>/<mm>/<sha>.bin
    parsed/<source_id>/<yyyy>/<mm>/<sha>.json
    packets/<source_id>/<yyyy>/<mm>/<window_sha>.packet.<codec>
    dict/<source_id>/<yyyy>/<mm>.zstdict
    index/<index_db_or_json>
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Literal


CASNamespace = Literal["raw", "parsed", "packets", "dict", "index"]


def get_cas_root() -> Path:
    """Get CAS root directory.

    Returns:
        Path to data/cas directory
    """
    # Assume repo root is current working directory or infer from env
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / "data" / "cas"


def get_cas_path(
    namespace: CASNamespace,
    source_id: str,
    file_hash: str,
    *,
    year: int | None = None,
    month: int | None = None,
    ext: str = "bin",
) -> Path:
    """Compute deterministic CAS path for a given namespace and hash.

    Args:
        namespace: CAS namespace (raw, parsed, packets, dict, index)
        source_id: Source identifier
        file_hash: Content hash (hex)
        year: Optional year for temporal partitioning
        month: Optional month for temporal partitioning
        ext: File extension (default: bin)

    Returns:
        Path to CAS file
    """
    root = get_cas_root()
    base = root / namespace / source_id

    if year is not None and month is not None:
        base = base / f"{year:04d}" / f"{month:02d}"

    return base / f"{file_hash}.{ext}"


def get_dict_path(source_id: str, year: int, month: int) -> Path:
    """Get zstd dictionary path for a source/time window.

    Args:
        source_id: Source identifier
        year: Year
        month: Month

    Returns:
        Path to .zstdict file
    """
    root = get_cas_root()
    return root / "dict" / source_id / f"{year:04d}" / f"{month:02d}.zstdict"


def ensure_cas_dirs(path: Path) -> None:
    """Ensure CAS directory structure exists.

    Args:
        path: Path to file that needs parent directories
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_timestamp_components(ts_utc: str) -> tuple[int, int]:
    """Parse year and month from ISO8601 timestamp.

    Args:
        ts_utc: ISO8601 timestamp (e.g., "2026-01-03T00:00:00Z")

    Returns:
        Tuple of (year, month)
    """
    dt = datetime.fromisoformat(ts_utc.replace("Z", "+00:00"))
    return dt.year, dt.month
