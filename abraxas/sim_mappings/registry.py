"""SML Registry: Paper reference registry for known simulation sources.

Provides:
- load_paper_refs: Load paper references from JSON
- get_paper_ref: Retrieve specific paper by ID
- Storage in data/sim_sources/papers.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from abraxas.sim_mappings.types import PaperRef


DEFAULT_REGISTRY_PATH = "data/sim_sources/papers.json"


def load_paper_refs(registry_path: Optional[str] = None) -> List[PaperRef]:
    """
    Load paper references from JSON registry.

    Args:
        registry_path: Path to registry file (default: data/sim_sources/papers.json)

    Returns:
        List of PaperRef objects
    """
    path = Path(registry_path or DEFAULT_REGISTRY_PATH)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [PaperRef.from_dict(paper_data) for paper_data in data.get("papers", [])]


def get_paper_ref(paper_id: str, registry_path: Optional[str] = None) -> Optional[PaperRef]:
    """
    Retrieve specific paper reference by ID.

    Args:
        paper_id: Paper identifier
        registry_path: Path to registry file

    Returns:
        PaperRef or None if not found
    """
    papers = load_paper_refs(registry_path)
    for paper in papers:
        if paper.paper_id == paper_id:
            return paper
    return None


def save_paper_refs(papers: List[PaperRef], registry_path: Optional[str] = None) -> None:
    """
    Save paper references to JSON registry.

    Args:
        papers: List of PaperRef objects
        registry_path: Path to registry file
    """
    path = Path(registry_path or DEFAULT_REGISTRY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "papers": [paper.to_dict() for paper in papers],
        "count": len(papers),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
