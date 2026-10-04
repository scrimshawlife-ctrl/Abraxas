"""Yggdrasil Memory Layer — Cypher Persistent Memory for Evidence

This module implements a persistent memory layer for storing evidence envelopes
and decisions, backed by CypherTempre Timechain or file storage.
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

# Import CypherTempre Timechain
try:
    from abraxas.yggdrasil.timechain import CypherTempreTimechain, TimechainConfig, get_timechain
    TIMECHAIN_AVAILABLE = True
except ImportError:
    TIMECHAIN_AVAILABLE = False
    logger.debug("CypherTempre Timechain not available, using file storage only")

    # Fallback TimechainConfig for type hints when import fails
    class TimechainConfig:
        enabled: bool = False
        chain_name: str = "abraxas_memory"
        namespace: str = "evidence"
        write_timeout: float = 30.0
        read_timeout: float = 30.0


def _json_serializer(obj):
    """JSON serializer for enums and other non-serializable objects."""
    if isinstance(obj, enum.Enum):
        return obj.value
    elif isinstance(obj, type) and issubclass(obj, enum.Enum):
        # Handle enum classes (e.g., if somehow passed the class instead of instance)
        return obj.__name__
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

    def __init__(self, storage_path: Optional[str] = None, timechain_config: Optional[TimechainConfig] = None):
        self._initialized = False
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".abraxas", "memory"
        )
        self._store: Dict[str, MemoryRecord] = {}
        self.timechain_config = timechain_config or TimechainConfig()
        self._timechain_client = None
        logger.info("Yggdrasil Memory Layer initialized")

    def initialize(self) -> None:
        """Initialize the memory layer, load from storage if exists."""
        if self._initialized:
            return

        try:
            # Initialize Timechain if configured
            if self.timechain_config.enabled:
                self._initialize_timechain()

            os.makedirs(self.storage_path, exist_ok=True)
            self._load_from_storage()
            self._initialized = True
            logger.debug(f"Yggdrasil Memory Layer initialized at {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to initialize memory layer: {e}")
            raise

    def _initialize_timechain(self) -> bool:
        """Initialize Timechain client if enabled and available."""
        if not self.timechain_config.enabled or not TIMECHAIN_AVAILABLE:
            return False

        try:
            # Use CypherTempre Timechain
            self._timechain_client = get_timechain()
            self._timechain_client.initialize()
            logger.info("CypherTempre Timechain client initialized")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize CypherTempre Timechain client: {e}")
            self._timechain_client = None
            return False

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

    def _save_to_timechain(self, record_id: str, content: Dict[str, Any]) -> bool:
        """Save record to Timechain if available and enabled."""
        if not self._timechain_client or not self.timechain_config.enabled:
            return False

        try:
            # Prepare data for Timechain storage
            timechain_data = {
                "record_id": record_id,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"source": "yggdrasil_memory_timechain"}
            }

            # Write to Timechain with timeout
            self._timechain_client.store(
                data=timechain_data,
                metadata={"source": "yggdrasil_memory_timechain"}
            )
            logger.debug(f"Saved record {record_id} to Timechain")
            return True
        except Exception as e:
            logger.warning(f"Failed to save to Timechain: {e}")
            return False

    def _load_from_timechain(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Load record from Timechain if available and enabled."""
        if not self._timechain_client or not self.timechain_config.enabled:
            return None

        try:
            # Read from Timechain with timeout
            result = self._timechain_client.retrieve({"block_hash": record_id})

            if result and isinstance(result, dict) and "content" in result:
                logger.debug(f"Loaded record {record_id} from Timechain")
                return result["content"]
            return None
        except Exception as e:
            logger.warning(f"Failed to load from Timechain: {e}")
            return None

    def store_evidence(self, envelope: Any) -> str:
        """Store an evidence envelope in persistent memory.

        Returns:
            The record ID of the stored envelope.
        """
        if not self._initialized:
            self.initialize()

        record_id = f"env-{getattr(envelope, 'evidence_id', 'unknown')}"
        # Convert envelope to dict, handling enums and nested objects properly
        if hasattr(envelope, 'to_dict'):
            content = envelope.to_dict()
            # Ensure evidence_type is serialized as string value
            if 'evidence_type' in content and hasattr(content['evidence_type'], 'value'):
                content['evidence_type'] = content['evidence_type'].value
            # Also handle Decision enum in verification_metadata if present
            if 'verification_metadata' in content and isinstance(content['verification_metadata'], dict):
                if 'decision' in content['verification_metadata'] and hasattr(content['verification_metadata']['decision'], 'value'):
                    content['verification_metadata']['decision'] = content['verification_metadata']['decision'].value
            # Handle nested RelationStep objects in candidate_outputs and reasoning_steps
            if 'candidate_outputs' in content and isinstance(content['candidate_outputs'], list):
                for i, candidate in enumerate(content['candidate_outputs']):
                    if isinstance(candidate, dict) and 'relation_steps' in candidate and isinstance(candidate['relation_steps'], list):
                        for j, step in enumerate(candidate['relation_steps']):
                            if isinstance(step, dict):
                                # Ensure any enums in step metadata are handled
                                if 'metadata' in step and isinstance(step['metadata'], dict):
                                    for key, value in step['metadata'].items():
                                        if hasattr(value, 'value'):
                                            step['metadata'][key] = value.value
                            # Handle RelationStep objects that weren't converted to dict by to_dict()
                            elif hasattr(step, '__dict__'):
                                # Convert RelationStep object to dict
                                step_dict = {
                                    'relation': step.relation,
                                    'subject': step.subject,
                                    'object': step.object,
                                    'result': step.result,
                                    'confidence': step.confidence,
                                    'metadata': step.metadata.copy() if hasattr(step.metadata, 'copy') else step.metadata
                                }
                                # Handle any enums in metadata
                                if 'metadata' in step_dict and isinstance(step_dict['metadata'], dict):
                                    for key, value in step_dict['metadata'].items():
                                        if hasattr(value, 'value'):
                                            step_dict['metadata'][key] = value.value
                                candidate['relation_steps'][j] = step_dict
            if 'reasoning_steps' in content and isinstance(content['reasoning_steps'], list):
                for i, step in enumerate(content['reasoning_steps']):
                    if isinstance(step, dict):
                        # Ensure any enums in step metadata are handled
                        if 'metadata' in step and isinstance(step['metadata'], dict):
                            for key, value in step['metadata'].items():
                                if hasattr(value, 'value'):
                                    step['metadata'][key] = value.value
                    # Handle RelationStep objects that weren't converted to dict by to_dict()
                    elif hasattr(step, '__dict__'):
                        # Convert RelationStep object to dict
                        step_dict = {
                            'relation': step.relation,
                            'subject': step.subject,
                            'object': step.object,
                            'result': step.result,
                            'confidence': step.confidence,
                            'metadata': step.metadata.copy() if hasattr(step.metadata, 'copy') else step.metadata
                        }
                        # Handle any enums in metadata
                        if 'metadata' in step_dict and isinstance(step_dict['metadata'], dict):
                            for key, value in step_dict['metadata'].items():
                                if hasattr(value, 'value'):
                                    step_dict['metadata'][key] = value.value
                        content['reasoning_steps'][i] = step_dict
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

        # Try to store in Timechain asynchronously (don't fail if Timechain fails)
        if self.timechain_config.enabled:
            try:
                self._save_to_timechain(record_id, content)
            except Exception as e:
                logger.debug(f"Timechain storage failed (non-critical): {e}")

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

        # Try to store in Timechain asynchronously (don't fail if Timechain fails)
        if self.timechain_config.enabled:
            try:
                self._save_to_timechain(record_id, record.content)
            except Exception as e:
                logger.debug(f"Timechain storage failed (non-critical): {e}")

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