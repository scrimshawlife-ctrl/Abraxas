"""
Benchmarking suites for performance regression detection in Abraxas.
"""
import sys
import os
# Add the project root to sys.path so we can import abraxas modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import statistics
from typing import List, Dict, Any
from abraxas.governance.production import ProductionOrchestrator
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep, Decision
from abraxas.evidence.provider import EvidenceProvider
from abraxas.yggdrasil.memory import CypherMemoryLayer
from abraxas.evidence.adapters.oracle import create_oracle_adapter
from abraxas.evidence.adapters.cypher import create_cypher_adapter