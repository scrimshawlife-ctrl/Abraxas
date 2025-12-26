"""
Evolution Store

Manages persistence for evolution candidates, sandbox results, and promotions.

STORAGE STRUCTURE:
- data/evolution/candidates/          Individual candidate JSONs
- data/evolution/implementation_tickets/   Implementation tickets for metrics/operators
- out/evolution_ledgers/candidates.jsonl    Hash-chained candidate log
- out/evolution_ledgers/sandbox.jsonl       Hash-chained sandbox results
- out/evolution_ledgers/promotions.jsonl    Hash-chained promotion log
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from abraxas.evolution.schema import (
    MetricCandidate,
    SandboxResult,
    PromotionEntry,
    StabilizationWindow,
    ImplementationTicket,
    CandidateFilter,
    CandidateKind,
    SourceDomain
)
from abraxas.core.provenance import hash_canonical_json


class EvolutionStore:
    """Persistent storage for evolution artifacts."""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            # Default to project root
            base_path = Path(__file__).parent.parent.parent

        self.base_path = base_path
        self.data_dir = base_path / "data" / "evolution"
        self.ledger_dir = base_path / "out" / "evolution_ledgers"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "candidates").mkdir(exist_ok=True)
        (self.data_dir / "implementation_tickets").mkdir(exist_ok=True)
        (self.data_dir / "stabilization_windows").mkdir(exist_ok=True)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

    # Candidate storage

    def save_candidate(self, candidate: MetricCandidate) -> Path:
        """
        Save candidate to disk.

        Returns:
            Path to saved file
        """
        file_path = self.data_dir / "candidates" / f"{candidate.candidate_id}.json"

        with open(file_path, 'w') as f:
            json.dump(candidate.model_dump(), f, indent=2)

        return file_path

    def load_candidate(self, candidate_id: str) -> Optional[MetricCandidate]:
        """Load candidate from disk."""
        file_path = self.data_dir / "candidates" / f"{candidate_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        return MetricCandidate(**data)

    def list_candidates(self, filter_criteria: Optional[CandidateFilter] = None) -> List[MetricCandidate]:
        """
        List all candidates, optionally filtered.

        Args:
            filter_criteria: Optional filter to apply

        Returns:
            List of matching candidates
        """
        candidates_dir = self.data_dir / "candidates"
        all_candidates = []

        for file_path in candidates_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                candidate = MetricCandidate(**data)
                all_candidates.append(candidate)

        # Apply filters
        if filter_criteria:
            all_candidates = self._apply_filters(all_candidates, filter_criteria)

        return all_candidates

    def _apply_filters(
        self,
        candidates: List[MetricCandidate],
        criteria: CandidateFilter
    ) -> List[MetricCandidate]:
        """Apply filter criteria to candidate list."""
        filtered = candidates

        if criteria.kind:
            filtered = [c for c in filtered if c.kind == criteria.kind]

        if criteria.source_domain:
            filtered = [c for c in filtered if c.source_domain == criteria.source_domain]

        if criteria.enabled_only:
            filtered = [c for c in filtered if c.enabled]

        if criteria.min_priority is not None:
            filtered = [c for c in filtered if c.priority >= criteria.min_priority]

        if criteria.max_priority is not None:
            filtered = [c for c in filtered if c.priority <= criteria.max_priority]

        if criteria.proposed_after:
            filtered = [c for c in filtered if c.proposed_at >= criteria.proposed_after]

        if criteria.proposed_before:
            filtered = [c for c in filtered if c.proposed_at <= criteria.proposed_before]

        if criteria.target_horizon:
            filtered = [c for c in filtered if criteria.target_horizon in c.target_horizons]

        return filtered

    # Stabilization window storage

    def save_stabilization_window(self, window: StabilizationWindow) -> Path:
        """Save stabilization window to disk."""
        file_path = self.data_dir / "stabilization_windows" / f"{window.candidate_id}.json"

        with open(file_path, 'w') as f:
            json.dump(window.model_dump(), f, indent=2)

        return file_path

    def load_stabilization_window(self, candidate_id: str) -> Optional[StabilizationWindow]:
        """Load stabilization window from disk."""
        file_path = self.data_dir / "stabilization_windows" / f"{candidate_id}.json"

        if not file_path.exists():
            # Return new window if doesn't exist
            return StabilizationWindow(candidate_id=candidate_id)

        with open(file_path, 'r') as f:
            data = json.load(f)

        return StabilizationWindow(**data)

    # Implementation ticket storage

    def save_ticket(self, ticket: ImplementationTicket) -> Path:
        """Save implementation ticket to disk."""
        file_path = self.data_dir / "implementation_tickets" / f"{ticket.ticket_id}.json"

        with open(file_path, 'w') as f:
            json.dump(ticket.model_dump(), f, indent=2)

        # Update ticket_file_path in the object
        ticket.ticket_file_path = str(file_path)

        return file_path

    def load_ticket(self, ticket_id: str) -> Optional[ImplementationTicket]:
        """Load implementation ticket from disk."""
        file_path = self.data_dir / "implementation_tickets" / f"{ticket_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        return ImplementationTicket(**data)

    def list_tickets(self, status: Optional[str] = None) -> List[ImplementationTicket]:
        """List all implementation tickets, optionally filtered by status."""
        tickets_dir = self.data_dir / "implementation_tickets"
        all_tickets = []

        for file_path in tickets_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                ticket = ImplementationTicket(**data)

                if status is None or ticket.status == status:
                    all_tickets.append(ticket)

        return all_tickets

    # Ledger management

    def _get_last_ledger_hash(self, ledger_path: Path) -> str:
        """Get the hash of the last entry in a ledger."""
        if not ledger_path.exists():
            return "genesis"

        # Read last line
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            if not lines:
                return "genesis"

            last_entry = json.loads(lines[-1])
            return last_entry.get("step_hash", "genesis")

    def append_candidate_ledger(self, candidate: MetricCandidate) -> str:
        """
        Append candidate to hash-chained ledger.

        Returns:
            Step hash of appended entry
        """
        ledger_path = self.ledger_dir / "candidates.jsonl"
        prev_hash = self._get_last_ledger_hash(ledger_path)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_id": candidate.candidate_id,
            "kind": candidate.kind.value,
            "source_domain": candidate.source_domain.value,
            "name": candidate.name,
            "description": candidate.description,
            "rationale": candidate.rationale,
            "priority": candidate.priority,
            "proposed_by": candidate.proposed_by,
            "prev_hash": prev_hash
        }

        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        with open(ledger_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return step_hash

    def append_sandbox_ledger(self, sandbox_result: SandboxResult) -> str:
        """
        Append sandbox result to hash-chained ledger.

        Returns:
            Step hash of appended entry
        """
        ledger_path = self.ledger_dir / "sandbox.jsonl"
        prev_hash = self._get_last_ledger_hash(ledger_path)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sandbox_id": sandbox_result.sandbox_id,
            "candidate_id": sandbox_result.candidate_id,
            "run_id": sandbox_result.run_id,
            "passed": sandbox_result.passed,
            "score_delta": sandbox_result.score_delta,
            "cases_tested": sandbox_result.cases_tested,
            "prev_hash": prev_hash
        }

        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Update the sandbox_result object with hashes
        sandbox_result.prev_hash = prev_hash
        sandbox_result.step_hash = step_hash

        with open(ledger_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return step_hash

    def append_promotion_ledger(self, promotion: PromotionEntry) -> str:
        """
        Append promotion to hash-chained ledger.

        Returns:
            Step hash of appended entry
        """
        ledger_path = self.ledger_dir / "promotions.jsonl"
        prev_hash = self._get_last_ledger_hash(ledger_path)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "promotion_id": promotion.promotion_id,
            "candidate_id": promotion.candidate_id,
            "kind": promotion.kind.value,
            "name": promotion.name,
            "action_type": promotion.action_type,
            "action_details": promotion.action_details,
            "promoted_by": promotion.promoted_by,
            "prev_hash": prev_hash
        }

        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Update the promotion object with hashes
        promotion.prev_hash = prev_hash
        promotion.step_hash = step_hash

        with open(ledger_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return step_hash

    # Ledger reading

    def read_candidate_ledger(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Read entries from candidate ledger."""
        ledger_path = self.ledger_dir / "candidates.jsonl"

        if not ledger_path.exists():
            return []

        with open(ledger_path, 'r') as f:
            lines = f.readlines()

        entries = [json.loads(line) for line in lines]

        # Apply offset and limit
        if offset > 0:
            entries = entries[offset:]
        if limit is not None:
            entries = entries[:limit]

        return entries

    def read_sandbox_ledger(
        self,
        candidate_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read entries from sandbox ledger, optionally filtered by candidate_id."""
        ledger_path = self.ledger_dir / "sandbox.jsonl"

        if not ledger_path.exists():
            return []

        with open(ledger_path, 'r') as f:
            lines = f.readlines()

        entries = [json.loads(line) for line in lines]

        # Filter by candidate_id if provided
        if candidate_id is not None:
            entries = [e for e in entries if e.get("candidate_id") == candidate_id]

        # Apply limit
        if limit is not None:
            entries = entries[-limit:]  # Get last N entries

        return entries

    def read_promotion_ledger(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Read entries from promotion ledger."""
        ledger_path = self.ledger_dir / "promotions.jsonl"

        if not ledger_path.exists():
            return []

        with open(ledger_path, 'r') as f:
            lines = f.readlines()

        entries = [json.loads(line) for line in lines]

        # Apply offset and limit
        if offset > 0:
            entries = entries[offset:]
        if limit is not None:
            entries = entries[:limit]

        return entries

    # Ledger integrity verification

    def verify_ledger_chain(self, ledger_name: str) -> tuple[bool, List[str]]:
        """
        Verify hash chain integrity for a ledger.

        Args:
            ledger_name: Name of ledger ("candidates", "sandbox", "promotions")

        Returns:
            (is_valid, error_messages)
        """
        ledger_path = self.ledger_dir / f"{ledger_name}.jsonl"

        if not ledger_path.exists():
            return True, []  # Empty ledger is valid

        errors = []
        expected_prev_hash = "genesis"

        with open(ledger_path, 'r') as f:
            for i, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)

                    # Check prev_hash matches
                    actual_prev_hash = entry.get("prev_hash")
                    if actual_prev_hash != expected_prev_hash:
                        errors.append(
                            f"Line {i}: prev_hash mismatch. "
                            f"Expected '{expected_prev_hash}', got '{actual_prev_hash}'"
                        )

                    # Verify step_hash
                    step_hash = entry.get("step_hash")
                    entry_copy = dict(entry)
                    del entry_copy["step_hash"]
                    computed_hash = hash_canonical_json(entry_copy)

                    if computed_hash != step_hash:
                        errors.append(
                            f"Line {i}: step_hash mismatch. "
                            f"Expected '{step_hash}', computed '{computed_hash}'"
                        )

                    # Update expected for next iteration
                    expected_prev_hash = step_hash

                except json.JSONDecodeError as e:
                    errors.append(f"Line {i}: JSON decode error: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors


# Example usage
if __name__ == "__main__":
    from abraxas.evolution.schema import MetricCandidate, CandidateKind, SourceDomain

    store = EvolutionStore()

    # Create example candidate
    candidate = MetricCandidate(
        candidate_id="cand_test_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.AALMANAC,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test_script",
        name="test_param",
        description="Test parameter tweak",
        rationale="Testing the store",
        param_path="test.param.path",
        current_value=1.0,
        proposed_value=1.5,
        priority=5
    )

    # Save candidate
    file_path = store.save_candidate(candidate)
    print(f"✓ Saved candidate to {file_path}")

    # Append to ledger
    step_hash = store.append_candidate_ledger(candidate)
    print(f"✓ Appended to ledger, step_hash: {step_hash[:16]}...")

    # Load candidate
    loaded = store.load_candidate("cand_test_001")
    print(f"✓ Loaded candidate: {loaded.name}")

    # Verify ledger
    is_valid, errors = store.verify_ledger_chain("candidates")
    if is_valid:
        print("✓ Ledger chain verified")
    else:
        print("✗ Ledger chain invalid:")
        for err in errors:
            print(f"  - {err}")
