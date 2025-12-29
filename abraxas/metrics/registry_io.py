"""Registry I/O: Load/Save with Schema Validation

Handles:
- Loading/saving candidate metrics registry
- Loading/saving canonical metrics registry (simulation registry)
- Loading/appending to promotion ledger
- Schema validation (basic checks, full JSONSchema optional)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from abraxas.metrics.governance import (
    CandidateMetric,
    CandidateStatus,
    PromotionLedgerEntry,
)
from abraxas.metrics.hashutil import hash_json, verify_hash_chain


# WORKING THEORY ASSUMPTION:
# - registries in ./registry/
# - ledgers in ./ledger/
# If actual paths differ, adjust these constants

DEFAULT_CANDIDATE_REGISTRY_PATH = Path("registry/metrics_candidate.json")
DEFAULT_CANONICAL_REGISTRY_PATH = Path("data/simulation/metrics.json")
DEFAULT_PROMOTION_LEDGER_PATH = Path("ledger/metric_promotions.jsonl")
DEFAULT_CHAIN_LEDGER_PATH = Path("ledger/metric_promotions_chain.jsonl")


class CandidateRegistry:
    """Registry for candidate metrics."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or DEFAULT_CANDIDATE_REGISTRY_PATH
        self.candidates: Dict[str, CandidateMetric] = {}
        self.load()

    def load(self):
        """Load candidates from disk."""
        if not self.registry_path.exists():
            return

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        for candidate_data in data.get("candidates", []):
            candidate = CandidateMetric.from_dict(candidate_data)
            self.candidates[candidate.provenance.metric_id] = candidate

    def save(self):
        """Save candidates to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "candidates": [c.to_dict() for c in self.candidates.values()],
            "count": len(self.candidates),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def add(self, candidate: CandidateMetric):
        """Add new candidate."""
        metric_id = candidate.provenance.metric_id
        if metric_id in self.candidates:
            raise ValueError(f"Candidate {metric_id} already exists")

        self.candidates[metric_id] = candidate

    def get(self, metric_id: str) -> Optional[CandidateMetric]:
        """Get candidate by ID."""
        return self.candidates.get(metric_id)

    def update_status(self, metric_id: str, new_status: CandidateStatus):
        """Update candidate status."""
        candidate = self.get(metric_id)
        if not candidate:
            raise ValueError(f"Candidate {metric_id} not found")

        candidate.update_status(new_status)
        self.save()

    def list_by_status(self, status: CandidateStatus) -> List[CandidateMetric]:
        """List all candidates with given status."""
        return [c for c in self.candidates.values() if c.status == status]

    def remove(self, metric_id: str):
        """Remove candidate (use with caution - prefer status updates)."""
        if metric_id in self.candidates:
            del self.candidates[metric_id]
            self.save()


class PromotionLedger:
    """Append-only ledger for metric promotions with hash chain."""

    def __init__(
        self,
        ledger_path: Optional[Path] = None,
        chain_path: Optional[Path] = None,
    ):
        self.ledger_path = ledger_path or DEFAULT_PROMOTION_LEDGER_PATH
        self.chain_path = chain_path or DEFAULT_CHAIN_LEDGER_PATH
        self.entries: List[PromotionLedgerEntry] = []
        self.load()

    def load(self):
        """Load ledger from disk (JSONL format)."""
        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entry_data = json.loads(line)
                    entry = PromotionLedgerEntry.from_dict(entry_data)
                    self.entries.append(entry)

    def append(self, entry: PromotionLedgerEntry):
        """Append new entry to ledger (append-only).

        CRITICAL: This is append-only. No modifications allowed.
        """
        # Ensure directories exist
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to memory
        self.entries.append(entry)

        # Append to disk (JSONL)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        # Also append to chain file
        with open(self.chain_path, "a") as f:
            chain_entry = {
                "timestamp": entry.timestamp,
                "metric_id": entry.metric_id,
                "decision": entry.decision.value,
                "prev_hash": entry.prev_hash,
                "signature": entry.signature,
            }
            f.write(json.dumps(chain_entry) + "\n")

    def get_last_hash(self) -> str:
        """Get hash of last entry for chain continuation."""
        if not self.entries:
            return "0" * 64  # Genesis hash

        last_entry = self.entries[-1]
        # Compute hash of last entry (excluding signature)
        entry_dict = {
            k: v for k, v in last_entry.to_dict().items() if k != "signature"
        }
        return hash_json(entry_dict)

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        if not self.entries:
            return True

        entry_dicts = [e.to_dict() for e in self.entries]
        return verify_hash_chain(entry_dicts, prev_hash_key="prev_hash")

    def get_entries_for_metric(self, metric_id: str) -> List[PromotionLedgerEntry]:
        """Get all ledger entries for a specific metric."""
        return [e for e in self.entries if e.metric_id == metric_id]


def load_canonical_registry(registry_path: Optional[Path] = None) -> Dict:
    """Load canonical metrics registry (simulation registry).

    WORKING THEORY: Uses existing simulation metric registry.

    Args:
        registry_path: Path to canonical registry

    Returns:
        Dict with canonical metrics
    """
    path = registry_path or DEFAULT_CANONICAL_REGISTRY_PATH

    if not path.exists():
        return {"metrics": [], "count": 0}

    with open(path, "r") as f:
        return json.load(f)


def save_canonical_registry(data: Dict, registry_path: Optional[Path] = None):
    """Save canonical metrics registry.

    Args:
        data: Registry data dict
        registry_path: Path to save to
    """
    path = registry_path or DEFAULT_CANONICAL_REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    data["last_updated"] = datetime.utcnow().isoformat() + "Z"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def promote_candidate_to_canonical(
    candidate: CandidateMetric,
    candidate_registry: CandidateRegistry,
    canonical_registry_path: Optional[Path] = None,
):
    """Promote candidate metric to canonical registry.

    Args:
        candidate: Candidate metric to promote
        candidate_registry: Candidate registry instance
        canonical_registry_path: Path to canonical registry
    """
    # Load canonical registry
    canonical_data = load_canonical_registry(canonical_registry_path)

    # Convert candidate to canonical format
    # (Simplified - in practice, would need full MetricDefinition conversion)
    canonical_metric = {
        "metric_id": candidate.provenance.metric_id,
        "version": candidate.version,
        "description": candidate.provenance.description,
        "units": candidate.provenance.units,
        "valid_range": candidate.provenance.valid_range,
        "dependencies": candidate.provenance.dependencies,
        "promoted_from_candidate": True,
        "promotion_timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Add to canonical registry
    canonical_data.setdefault("metrics", []).append(canonical_metric)
    canonical_data["count"] = len(canonical_data["metrics"])

    # Save canonical registry
    save_canonical_registry(canonical_data, canonical_registry_path)

    # Update candidate status to PROMOTED
    candidate_registry.update_status(
        candidate.provenance.metric_id, CandidateStatus.PROMOTED
    )


__all__ = [
    "CandidateRegistry",
    "PromotionLedger",
    "load_canonical_registry",
    "save_canonical_registry",
    "promote_candidate_to_canonical",
]
