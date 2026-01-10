"""CLI helpers for SourceAtlas."""

from __future__ import annotations

import json
from typing import List

from abraxas.sources.atlas import list_sources


def list_sources_cmd() -> int:
    sources = [spec.canonical_payload() for spec in list_sources()]
    print(json.dumps(sources, indent=2, sort_keys=True))
    return 0
