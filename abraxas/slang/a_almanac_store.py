"""AAlmanac Store: Write-once, annotate-only ledger for symbolic evolution.

Storage format: JSONL (one entry per line)
Location: data/a_almanac/terms.jsonl

Schema per entry:
{
  "term_id": "<uuid>",
  "term": "<canonical_form>",
  "class_id": "<SA_class>",
  "created_at": "<ISO8601Z>",
  "lifecycle_state": "<state>",
  "tau_snapshot": {...},
  "annotations": [...],
  "provenance": {...}
}

Rule: Write-once, annotate-only. No destructive edits.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from abraxas.core.provenance import Provenance
from abraxas.core.temporal_tau import TauSnapshot, TauCalculator, Observation
from abraxas.slang.lifecycle import LifecycleState, LifecycleEngine, MutationEvidence


@dataclass
class Annotation:
    """Single annotation entry (append-only)."""

    timestamp: str  # ISO8601Z
    type: str  # annotation type (e.g., "tau_update", "affinity", "observation")
    data: Dict[str, Any]
    provenance: Dict[str, Any]


@dataclass
class AAlmanacEntry:
    """Complete AAlmanac entry for a single term."""

    term_id: str
    term: str
    class_id: str  # SA class or archetype
    created_at: str  # ISO8601Z
    lifecycle_state: str  # LifecycleState value
    tau_snapshot: Optional[Dict[str, Any]]  # TauSnapshot as dict
    annotations: List[Annotation]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "term_id": self.term_id,
            "term": self.term,
            "class_id": self.class_id,
            "created_at": self.created_at,
            "lifecycle_state": self.lifecycle_state,
            "tau_snapshot": self.tau_snapshot,
            "annotations": [
                {
                    "timestamp": ann.timestamp,
                    "type": ann.type,
                    "data": ann.data,
                    "provenance": ann.provenance,
                }
                for ann in self.annotations
            ],
            "provenance": self.provenance,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> AAlmanacEntry:
        """Create entry from dict."""
        annotations = [
            Annotation(
                timestamp=ann["timestamp"],
                type=ann["type"],
                data=ann["data"],
                provenance=ann["provenance"],
            )
            for ann in data.get("annotations", [])
        ]

        return AAlmanacEntry(
            term_id=data["term_id"],
            term=data["term"],
            class_id=data["class_id"],
            created_at=data["created_at"],
            lifecycle_state=data.get("lifecycle_state", "Proto"),
            tau_snapshot=data.get("tau_snapshot"),
            annotations=annotations,
            provenance=data["provenance"],
        )


class AAlmanacStore:
    """
    Write-once, annotate-only ledger for symbolic evolution tracking.

    Storage: JSONL file (one entry per line)
    Operations:
    - load_entries(): Load all entries from disk
    - create_entry_if_missing(): Write new entry (once)
    - append_annotation(): Add annotation to existing entry
    - compute_current_state(): Recompute lifecycle state from τ
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        tau_calculator: Optional[TauCalculator] = None,
        lifecycle_engine: Optional[LifecycleEngine] = None,
    ):
        """
        Initialize store.

        Args:
            storage_path: Path to JSONL storage file (default: data/a_almanac/terms.jsonl)
            tau_calculator: Optional τ calculator (created if not provided)
            lifecycle_engine: Optional lifecycle engine (created if not provided)
        """
        self.storage_path = Path(
            storage_path or "data/a_almanac/terms.jsonl"
        ).resolve()
        self.tau_calculator = tau_calculator or TauCalculator()
        self.lifecycle_engine = lifecycle_engine or LifecycleEngine()

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache (loaded on demand)
        self._cache: Optional[Dict[str, AAlmanacEntry]] = None

    def load_entries(self) -> List[AAlmanacEntry]:
        """
        Load all entries from storage.

        Returns:
            List of AAlmanacEntry objects
        """
        if not self.storage_path.exists():
            return []

        entries = []
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(AAlmanacEntry.from_dict(data))

        return entries

    def get_entry(self, term_id: str) -> Optional[AAlmanacEntry]:
        """
        Get entry by term_id.

        Args:
            term_id: Term identifier

        Returns:
            AAlmanacEntry or None if not found
        """
        self._ensure_cache()
        return self._cache.get(term_id)

    def get_entry_by_term(self, term: str) -> Optional[AAlmanacEntry]:
        """
        Get entry by term (canonical form).

        Args:
            term: Canonical term string

        Returns:
            AAlmanacEntry or None if not found
        """
        self._ensure_cache()
        for entry in self._cache.values():
            if entry.term == term:
                return entry
        return None

    def create_entry_if_missing(
        self,
        term: str,
        class_id: str,
        created_at: str,
        provenance: Provenance,
    ) -> str:
        """
        Create new entry if term doesn't exist (write-once).

        Args:
            term: Canonical term
            class_id: SA class or archetype
            created_at: ISO8601Z timestamp
            provenance: Provenance record

        Returns:
            term_id (existing or newly created)
        """
        self._ensure_cache()

        # Check if term already exists
        existing = self.get_entry_by_term(term)
        if existing:
            return existing.term_id

        # Create new entry
        term_id = str(uuid4())
        entry = AAlmanacEntry(
            term_id=term_id,
            term=term,
            class_id=class_id,
            created_at=created_at,
            lifecycle_state=LifecycleState.PROTO.value,
            tau_snapshot=None,
            annotations=[],
            provenance=provenance.__dict__,
        )

        # Append to storage
        self._append_to_storage(entry)

        # Update cache
        self._cache[term_id] = entry

        return term_id

    def append_annotation(
        self,
        term_id: str,
        annotation_type: str,
        data: Dict[str, Any],
        provenance: Provenance,
    ) -> bool:
        """
        Append annotation to existing entry.

        Args:
            term_id: Term identifier
            annotation_type: Type of annotation
            data: Annotation data
            provenance: Provenance record

        Returns:
            True if successful, False if term not found
        """
        self._ensure_cache()

        entry = self.get_entry(term_id)
        if not entry:
            return False

        # Create annotation
        annotation = Annotation(
            timestamp=Provenance.now_iso_z(),
            type=annotation_type,
            data=data,
            provenance=provenance.__dict__,
        )

        # Add to entry
        entry.annotations.append(annotation)

        # Rewrite entire file (JSONL: simple append not safe for updates)
        self._rewrite_storage()

        return True

    def compute_current_state(
        self,
        term_id: str,
        *,
        run_id: Optional[str] = None,
        current_time_utc: Optional[str] = None,
    ) -> Optional[tuple[LifecycleState, TauSnapshot]]:
        """
        Recompute lifecycle state and τ snapshot from annotations.

        Args:
            term_id: Term identifier
            run_id: Optional run identifier
            current_time_utc: Optional reference time

        Returns:
            Tuple of (LifecycleState, TauSnapshot) or None if not found
        """
        self._ensure_cache()

        entry = self.get_entry(term_id)
        if not entry:
            return None

        # Extract observations from annotations
        observations = []
        for ann in entry.annotations:
            if ann.type == "observation":
                obs = Observation(
                    ts=ann.timestamp,
                    value=ann.data.get("value", 1.0),
                    source_id=ann.data.get("source_id", "unknown"),
                )
                observations.append(obs)

        # Compute τ snapshot
        tau_snapshot = self.tau_calculator.compute_snapshot(
            observations, run_id=run_id, current_time_utc=current_time_utc
        )

        # Extract mutation evidence if present
        mutation_evidence = None
        for ann in entry.annotations:
            if ann.type == "mutation":
                mutation_evidence = MutationEvidence(
                    edit_distance=ann.data.get("edit_distance", 0),
                    token_modifier_changed=ann.data.get(
                        "token_modifier_changed", False
                    ),
                    description=ann.data.get("description", ""),
                )
                break  # Use most recent mutation

        # Compute lifecycle state
        current_state = LifecycleState(entry.lifecycle_state)
        new_state = self.lifecycle_engine.compute_state(
            current_state, tau_snapshot, mutation_evidence
        )

        # Update entry if state changed
        if new_state != current_state:
            entry.lifecycle_state = new_state.value

        # Update tau snapshot in entry
        entry.tau_snapshot = {
            "tau_half_life": tau_snapshot.tau_half_life,
            "tau_velocity": tau_snapshot.tau_velocity,
            "tau_phase_proximity": tau_snapshot.tau_phase_proximity,
            "confidence": tau_snapshot.confidence.value,
            "observation_count": tau_snapshot.observation_count,
            "observation_window_hours": tau_snapshot.observation_window_hours,
            "provenance": tau_snapshot.provenance.__dict__,
        }

        # Rewrite storage to persist updates
        self._rewrite_storage()

        return (new_state, tau_snapshot)

    def _ensure_cache(self) -> None:
        """Ensure cache is loaded."""
        if self._cache is None:
            entries = self.load_entries()
            self._cache = {entry.term_id: entry for entry in entries}

    def _append_to_storage(self, entry: AAlmanacEntry) -> None:
        """Append entry to storage file."""
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=True) + "\n")

    def _rewrite_storage(self) -> None:
        """Rewrite entire storage file from cache."""
        if self._cache is None:
            return

        with open(self.storage_path, "w", encoding="utf-8") as f:
            for entry in self._cache.values():
                f.write(json.dumps(entry.to_dict(), ensure_ascii=True) + "\n")
