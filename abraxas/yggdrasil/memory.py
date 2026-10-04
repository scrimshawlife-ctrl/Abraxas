"""
Yggdrasil Memory Layer — Cypher Persistent Memory for Evidence

This module implements a persistent memory layer for storing evidence envelopes
and decisions, backed by Cypher (Timechain) or a simple store for now.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import enum

logger = logging.getLogger(__name__)


def _json_serializer(obj):
    """JSON serializer for enums and other non-serializable objects."""
    if isinstance(obj, enum.Enum):
        return obj.value
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


@dataclass
class MemoryRecord:
    """A record stored in persistent memory."""
    record_id: str
    record_type: str  # 'envelope' or 'decision'
    content: Dict[str, Any]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class CypherMemoryLayer:
    """Persistent memory layer for evidence and decisions."""

    def __init__(self, storage_path: Optional[str] = None):
        self._initialized = False
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".abraxas", "memory"
        )
        self._store: Dict[str, MemoryRecord] = {}
        logger.info("Yggdrasil Memory Layer initialized")
    
    def initialize(self) -> None:
        """Initialize the memory layer, load from storage if exists."""
        if self._initialized:
            return
        os.makedirs(self.storage_path, exist_ok=True)
        self._load_from_storage()
        self._initialized = True
        logger.debug(f"Yggdrasil Memory Layer initialized at {self.storage_path}")
    
    def _load_from_storage(self) -> None:
        """Load memory records from storage."""
        index_file = os.path.join(self.storage_path, "index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                for record_id, record_data in data.items():
                    self._store[record_id] = MemoryRecord(**record_data)
                logger.info(f"Loaded {len(self._store)} records from storage")
            except Exception as e:
                logger.error(f"Failed to load memory storage: {e}")
                self._store = {}
        else:
            logger.info("No existing memory storage found, starting fresh")
    
    def _save_to_storage(self) -> None:
        """Save memory records to storage."""
        index_file = os.path.join(self.storage_path, "index.json")
        try:
            data = {
                record_id: record.__dict__
                for record_id, record in self._store.items()
            }
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2, default=_json_serializer)
            logger.debug(f"Saved {len(self._store)} records to storage")
        except Exception as e:
            logger.error(f"Failed to save memory storage: {e}")
    
    def store_evidence(self, envelope: Any) -> str:
        """Store an evidence envelope in persistent memory.
        
        Returns:
            The record ID of the stored envelope.
        """
        if not self._initialized:
            self.initialize()
        
        record_id = f"env-{getattr(envelope, 'evidence_id', 'unknown')}"
        # Convert envelope to dict, handling enums properly
        if hasattr(envelope, 'to_dict'):
            content = envelope.to_dict()
            # Ensure evidence_type is serialized as string value
            if 'evidence_type' in content and hasattr(content['evidence_type'], 'value'):
                content['evidence_type'] = content['evidence_type'].value
            # Also handle Decision enum in verification_metadata if present
            if 'verification_metadata' in content and isinstance(content['verification_metadata'], dict):
                if 'decision' in content['verification_metadata'] and hasattr(content['verification_metadata']['decision'], 'value'):
                    content['verification_metadata']['decision'] = content['verification_metadata']['decision'].value
        else:
            content = {}
        record = MemoryRecord(
            record_id=record_id,
            record_type="envelope",
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"source": "yggdrasil_memory"}
        )
        self._store[record_id] = record
        self._save_to_storage()
        logger.debug(f"Stored evidence envelope: {record_id}")
        return record_id
    
    def store_decision(self, evidence_id: str, decision: Any) -> str:
        """Store a decision in persistent memory.
        
        Args:
            evidence_id: The ID of the evidence this decision is for.
            decision: The decision object (or its value).
            
        Returns:
            The record ID of the stored decision.
        """
        if not self._initialized:
            self.initialize()
        
        record_id = f"dec-{evidence_id}"
        # Convert decision to string if it's an enum, otherwise use as-is
        decision_value = decision.value if hasattr(decision, 'value') else str(decision)
        # Handle details if it's a dict that might contain enums
        details = getattr(decision, '__dict__', {})
        if isinstance(details, dict):
            # Make a copy to avoid modifying the original
            details = details.copy()
            # Convert any enum values to their string representations
            for key, value in details.items():
                if hasattr(value, 'value'):
                    details[key] = value.value
        
        record = MemoryRecord(
            record_id=record_id,
            record_type="decision",
            content={
                "evidence_id": evidence_id,
                "decision": decision_value,
                "details": details
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"source": "yggdrasil_memory"}
        )
        self._store[record_id] = record
        self._save_to_storage()
        logger.debug(f"Stored decision for evidence {evidence_id}: {record_id}")
        return record_id
    
    def retrieve_evidence(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an evidence envelope by record ID."""
        if not self._initialized:
            self.initialize()
        record = self._store.get(record_id)
        return record.content if record else None
    
    def retrieve_decision(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a decision by evidence ID."""
        if not self._initialized:
            self.initialize()
        record_id = f"dec-{evidence_id}"
        record = self._store.get(record_id)
        return record.content if record else None
    
    def list_records(self, record_type: Optional[str] = None) -> List[str]:
        """List all record IDs, optionally filtered by type."""
        if not self._initialized:
            self.initialize()
        if record_type is None:
            return list(self._store.keys())
        return [
            record_id for record_id, record in self._store.items()
            if record.record_type == record_type
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the memory layer."""
        if not self._initialized:
            self.initialize()
        envelope_count = len([r for r in self._store.values() if r.record_type == "envelope"])
        decision_count = len([r for r in self._store.values() if r.record_type == "decision"])
        return {
            "initialized": self._initialized,
            "storage_path": self.storage_path,
            "total_records": len(self._store),
            "envelope_count": envelope_count,
            "decision_count": decision_count
        }
    
    def shutdown(self) -> None:
        """Shutdown the memory layer."""
        logger.info("Shutting down Yggdrasil Memory Layer")
        self._save_to_storage()
        self._store.clear()
        self._initialized = False