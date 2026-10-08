"""CypherTempre Timechain Integration for Abraxas Yggdrasil Memory Layer.

Implements immutable Timechain-backed storage with file fallback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TimechainBlock:
    """A single block in the Timechain."""
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    merkle_root: str
    nonce: int
    difficulty: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimechainBlock':
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            data_hash=data["data_hash"],
            previous_hash=data["previous_hash"],
            merkle_root=data["merkle_root"],
            nonce=data["nonce"],
            difficulty=data["difficulty"],
        )
    
    def compute_hash(self) -> str:
        """Compute the block hash."""
        content = f"{self.index}|{self.timestamp}|{self.data_hash}|{self.previous_hash}|{self.merkle_root}|{self.nonce}|{self.difficulty}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class TimechainConfig:
    """Configuration for Timechain connection."""
    enabled: bool = True
    endpoint: str = "http://localhost:8332"  # Default Timechain endpoint
    api_key: Optional[str] = None
    difficulty: int = 4
    fallback_to_file: bool = True
    file_storage_path: str = ".abraxas/timechain"
    timeout: float = 10.0
    max_retries: int = 3


class TimechainState(str, Enum):
    """Why Timechain is or isn't in use.

    These three states were previously collapsed into a single boolean, which meant an
    operator could not tell "we never configured this" from "we configured it and it is
    down". Those need different responses: the first is the expected steady state for a
    file-backed deployment; the second is an outage.

    NOT_CONFIGURED  config.enabled is False -- fallback is intended, nothing is wrong
    UNREACHABLE     enabled, but no service answered -- fallback is masking a failure
    AVAILABLE       enabled and the endpoint answered
    """
    NOT_CONFIGURED = "not_configured"
    UNREACHABLE = "unreachable"
    AVAILABLE = "available"


class CypherTempreTimechain:
    """Timechain client for immutable record storage.
    
    Provides Timechain-backed storage with automatic fallback to file storage.
    """
    
    def __init__(self, config: Optional[TimechainConfig] = None):
        self.config = config or TimechainConfig()
        self._lock = threading.RLock()
        self._blocks: List[TimechainBlock] = []
        self._initialized = False
        self._last_hash = "0" * 64  # Genesis hash
        self._index = 0
        
        # Initialize file fallback
        if self.config.fallback_to_file:
            self._init_file_storage()
    
    def _init_file_storage(self) -> None:
        """Initialize file-based storage fallback."""
        self._file_path = Path(self.config.file_storage_path)
        self._file_path.mkdir(parents=True, exist_ok=True)
        self._blocks_file = self._file_path / "blocks.json"
        self._index_file = self._file_path / "index.json"
        
        # Load existing blocks if any
        if self._blocks_file.exists():
            self._load_blocks_from_file()
    
    def _load_blocks_from_file(self) -> None:
        """Load blocks from file storage."""
        try:
            with open(self._blocks_file, 'r') as f:
                data = json.load(f)
                self._blocks = [TimechainBlock.from_dict(b) for b in data.get("blocks", [])]
                self._index = data.get("index", 0)
                self._last_hash = data.get("last_hash", "0" * 64)
                logger.info(f"Loaded {len(self._blocks)} blocks from file storage")
        except Exception as e:
            logger.warning(f"Failed to load blocks from file: {e}")
            self._blocks = []
            self._index = 0
            self._last_hash = "0" * 64
    
    def _save_blocks_to_file(self) -> None:
        """Save blocks to file storage."""
        if not self.config.fallback_to_file:
            return
        
        try:
            data = {
                "index": self._index,
                "last_hash": self._last_hash,
                "blocks": [b.to_dict() for b in self._blocks],
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(self._blocks_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save blocks to file: {e}")
    
    def initialize(self) -> bool:
        """Initialize Timechain connection.
        
        Returns:
            True if Timechain is available, False if using file fallback.
        """
        with self._lock:
            if self._initialized:
                return True
            
            timechain_available = False
            
            if self.config.enabled:
                state = self.connection_state()
                timechain_available = state is TimechainState.AVAILABLE
                if state is TimechainState.UNREACHABLE:
                    # Distinct from "not configured": this is an outage, not a design
                    # choice. WARNING, not INFO, and it names the endpoint so an operator
                    # can tell which service is missing.
                    logger.warning(
                        "Timechain is ENABLED but unreachable at %s -- falling back to file "
                        "storage. This is an outage, not the expected steady state.",
                        self.config.endpoint,
                    )
            else:
                state = TimechainState.NOT_CONFIGURED

            if not timechain_available and self.config.fallback_to_file:
                if state is TimechainState.NOT_CONFIGURED:
                    logger.info("Timechain not configured; using file storage (expected)")
                self._initialized = True
                return False
            
            if timechain_available:
                logger.info("Timechain connection established")
                self._initialized = True
                return True
            
            logger.warning("Timechain unavailable and file fallback disabled")
            return False
    
    def _probe_endpoint(self) -> bool:
        """Make one connection attempt against the configured endpoint.

        This is the actual RPC check. Kept separate from connection_state() so the state
        logic is testable without a network, and so the probe is a single, observable
        side-effecting unit.

        Returns True only if something answered. Any failure -- refused, timeout, DNS,
        TLS, malformed URL -- is False, because from here they are the same fact: no
        usable service. The distinction that matters operationally is reachable vs not.
        """
        import urllib.request

        url = self.config.endpoint.rstrip("/") + "/health"
        req = urllib.request.Request(url, method="GET")
        if self.config.api_key:
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                return 200 <= getattr(resp, "status", 200) < 300
        except Exception:
            return False

    def _check_timechain_connection(self) -> bool:
        """Whether a Timechain service is usable right now.

        Retained for callers that want a plain boolean. Prefer connection_state(), which
        distinguishes 'not configured' from 'configured and down'.
        """
        return self.connection_state() is TimechainState.AVAILABLE

    def connection_state(self) -> TimechainState:
        """Why Timechain is or isn't in use. Probes at most once per call.

        Replaces the previous `return False` placeholder, which reported the same answer
        whether the service was absent, down, or never configured -- making the status
        surface unable to distinguish an expected steady state from an outage.
        """
        if not self.config.enabled:
            return TimechainState.NOT_CONFIGURED
        if self._probe_endpoint():
            return TimechainState.AVAILABLE
        return TimechainState.UNREACHABLE
    
    def store(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """Store data in Timechain (or file fallback).
        
        Args:
            data: The data to store
            metadata: Optional metadata
            
        Returns:
            Tuple of (block_hash, storage_id)
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            
            # Prepare data
            payload = {
                "data": data,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            payload_json = json.dumps(payload, sort_keys=True)
            data_hash = hashlib.sha256(payload_json.encode()).hexdigest()
            
            # Create block
            block = TimechainBlock(
                index=self._index,
                timestamp=datetime.now(timezone.utc).isoformat(),
                data_hash=data_hash,
                previous_hash=self._last_hash,
                merkle_root=data_hash,  # Simplified for single payload
                nonce=0,
                difficulty=self.config.difficulty,
            )
            
            # Mine block (simplified PoW)
            block = self._mine_block(block)
            
            # Add to chain
            self._blocks.append(block)
            self._last_hash = block.compute_hash()
            self._index += 1
            
            # Save to file fallback
            self._save_blocks_to_file()
            
            storage_id = f"tc-{block.index}-{self._last_hash[:16]}"
            logger.debug(f"Stored data in Timechain block {block.index}: {storage_id}")
            
            return self._last_hash, storage_id
    
    def _mine_block(self, block: TimechainBlock) -> TimechainBlock:
        """Mine a block (simplified PoW)."""
        target = "0" * self.config.difficulty
        while True:
            block_hash = block.compute_hash()
            if block_hash.startswith(target):
                return block
            block.nonce += 1
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from Timechain by query.
        
        Args:
            query: Query parameters (e.g., {"block_hash": "...", "index": 5})
            
        Returns:
            Matching data or None
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            
            # Search by block hash
            if "block_hash" in query:
                target_hash = query["block_hash"]
                for block in self._blocks:
                    if block.compute_hash() == target_hash:
                        # In production, would fetch actual data from Timechain
                        # For now, return block metadata
                        return {
                            "block": block.to_dict(),
                            "data_hash": block.data_hash,
                        }
            
            # Search by index
            if "index" in query:
                idx = query["index"]
                if 0 <= idx < len(self._blocks):
                    block = self._blocks[idx]
                    return {
                        "block": block.to_dict(),
                        "data_hash": block.data_hash,
                    }
            
            # Search by data hash
            if "data_hash" in query:
                target_hash = query["data_hash"]
                for block in self._blocks:
                    if block.data_hash == target_hash:
                        return {
                            "block": block.to_dict(),
                            "data_hash": block.data_hash,
                        }
            
            return None
    
    def verify_chain(self) -> Tuple[bool, List[str]]:
        """Verify the integrity of the Timechain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        with self._lock:
            errors = []
            
            if len(self._blocks) <= 1:
                return True, []
            
            for i in range(1, len(self._blocks)):
                current = self._blocks[i]
                previous = self._blocks[i - 1]
                
                # Check index continuity
                if current.index != previous.index + 1:
                    errors.append(f"Index gap at block {i}: {previous.index} -> {current.index}")
                
                # Check hash linkage
                if current.previous_hash != previous.compute_hash():
                    errors.append(f"Hash mismatch at block {i}: expected {previous.compute_hash()}, got {current.previous_hash}")
                
                # Check PoW
                block_hash = current.compute_hash()
                target = "0" * self.config.difficulty
                if not block_hash.startswith(target):
                    errors.append(f"Invalid PoW at block {i}: {block_hash} doesn't meet difficulty {self.config.difficulty}")
            
            return len(errors) == 0, errors
    
    def get_status(self) -> Dict[str, Any]:
        """Get Timechain status."""
        with self._lock:
            is_valid, errors = self.verify_chain()
            
            # Probe ONCE. The previous implementation called the check twice per status
            # call -- two network round trips for one answer, with no guarantee the two
            # agreed. State is computed once and reported from that single result.
            state = self.connection_state()

            return {
                "initialized": self._initialized,
                "timechain_state": state.value,
                "timechain_available": state is TimechainState.AVAILABLE,
                "fallback_mode": state is not TimechainState.AVAILABLE,
                "total_blocks": len(self._blocks),
                "last_block_hash": self._last_hash,
                "last_block_index": self._index - 1 if self._index > 0 else -1,
                "chain_valid": is_valid,
                "errors": errors,
                "config": {
                    "enabled": self.config.enabled,
                    "difficulty": self.config.difficulty,
                    "fallback_to_file": self.config.fallback_to_file,
                    "file_storage_path": self.config.file_storage_path,
                }
            }
    
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Get the latest block."""
        with self._lock:
            if not self._blocks:
                return None
            return self._blocks[-1].to_dict()
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get block by index."""
        with self._lock:
            if 0 <= index < len(self._blocks):
                return self._blocks[index].to_dict()
            return None


# Global singleton instance
_timechain_instance: Optional[CypherTempreTimechain] = None


def get_timechain(config: Optional[TimechainConfig] = None) -> CypherTempreTimechain:
    """Get or create the global Timechain instance."""
    global _timechain_instance
    if _timechain_instance is None:
        _timechain_instance = CypherTempreTimechain(config)
    return _timechain_instance


def initialize_timechain(config: Optional[TimechainConfig] = None) -> bool:
    """Initialize the global Timechain instance."""
    global _timechain_instance
    _timechain_instance = CypherTempreTimechain(config)
    return _timechain_instance.initialize()


if __name__ == "__main__":
    # Test the Timechain
    logging.basicConfig(level=logging.INFO)
    
    config = TimechainConfig(
        enabled=True,
        fallback_to_file=True,
        file_storage_path=".abraxas/test_timechain",
        difficulty=2,  # Low for testing
    )
    
    tc = CypherTempreTimechain(config)
    success = tc.initialize()
    print(f"Timechain initialized: {success}")
    
    # Store some test data
    for i in range(3):
        block_hash, storage_id = tc.store(
            {"test": f"data-{i}", "value": i * 100},
            {"source": "test", "iteration": i}
        )
        print(f"Stored: {storage_id} (hash: {block_hash[:16]}...)")
    
    # Verify chain
    valid, errors = tc.verify_chain()
    print(f"Chain valid: {valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Get status
    status = tc.get_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Retrieve by index
    result = tc.retrieve({"index": 1})
    print(f"Retrieved index 1: {json.dumps(result, indent=2)}")
    
    print("\nTimechain test complete!")