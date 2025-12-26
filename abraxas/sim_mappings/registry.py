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


def list_papers(registry_path: Optional[str] = None) -> List[Dict[str, str]]:
    """
    List all papers in the registry with summary information.

    Args:
        registry_path: Path to registry file

    Returns:
        List of dicts with paper_id, title, and year

    Examples:
        >>> papers = list_papers()
        >>> len(papers) > 0
        True
        >>> "paper_id" in papers[0]
        True
    """
    paper_refs = load_paper_refs(registry_path)
    return [
        {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "year": str(paper.year) if paper.year else "N/A",
            "notes": paper.notes or "",
        }
        for paper in paper_refs
    ]


def find_by_keyword(
    keyword: str,
    registry_path: Optional[str] = None,
    case_sensitive: bool = False
) -> List[PaperRef]:
    """
    Find papers by keyword search in title, paper_id, or notes.

    Args:
        keyword: Search term
        registry_path: Path to registry file
        case_sensitive: Whether to perform case-sensitive search (default: False)

    Returns:
        List of matching PaperRef objects

    Examples:
        >>> results = find_by_keyword("SIR")
        >>> len(results) > 0
        True

        >>> results = find_by_keyword("opinion dynamics")
        >>> all("opinion" in r.title.lower() for r in results)
        True
    """
    papers = load_paper_refs(registry_path)
    matches = []

    # Normalize keyword for comparison
    search_term = keyword if case_sensitive else keyword.lower()

    for paper in papers:
        # Build searchable text
        searchable_fields = [
            paper.paper_id,
            paper.title,
            paper.notes or "",
        ]

        # Normalize if case-insensitive
        if not case_sensitive:
            searchable_fields = [field.lower() for field in searchable_fields]

        # Check if keyword appears in any field
        if any(search_term in field for field in searchable_fields):
            matches.append(paper)

    return matches
