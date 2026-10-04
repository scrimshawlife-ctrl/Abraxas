# Using Cypher Memory Layer with Timechain Integration

## Overview
This tutorial demonstrates how to configure and use the Cypher memory layer with optional Timechain integration for persistent, tamper-evident storage of evidence envelopes and decisions.

## Prerequisites
- Abraxas installed (`pip install -e .[dev]`)
- For Timechain integration: Timechain Python package and access to a Timechain network

## Step 1: Basic Usage Without Timechain

By default, the Cypher memory layer uses file-based storage.

```python
from abraxas.yggdrasil.memory import CypherMemoryLayer

# Initialize with default file storage
memory = CypherMemoryLayer()
memory.initialize()

# Store evidence
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep

envelope = EvidenceEnvelope(
    engine="tutorial_engine",
    engine_version="1.0",
    model_identity="tutorial_model",
    request_id="tutorial-001",
    claim="The tutorial demonstrates memory layer usage",
    candidate_outputs=[CandidateOutput(
        answer="Understood",
        confidence=0.95,
        reasoning_trace="Following the tutorial steps",
        relation_steps=[]
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.95,
    uncertainty=0.05,
    provenance={"tutorial": True}
)

record_id = memory.store_evidence(envelope)
print(f"Stored evidence with record ID: {record_id}")

# Retrieve evidence
retrieved = memory.retrieve_evidence(record_id)
print(f"Retrieved evidence: {retrieved['claim']}")

# Store a decision
from abraxas.evidence.contract import Decision
decision_id = memory.store_decision(record_id, Decision.ACCEPT)
print(f"Stored decision with ID: {decision_id}")

# Retrieve decision
retrieved_decision = memory.retrieve_decision(record_id)
print(f"Retrieved decision: {retrieved_decision}")

memory.shutdown()
```

## Step 2: Configuring Custom Storage Path

You can specify a custom storage path for the file-based storage.

```python
import os
import tempfile

# Create a temporary directory for storage
storage_dir = tempfile.mkdtemp(prefix="abraxas_memory_")
print(f"Using storage directory: {storage_dir}")

# Initialize with custom storage path
memory = CypherMemoryLayer(storage_path=storage_dir)
memory.initialize()

# Use the memory layer as usual
envelope = EvidenceEnvelope(
    engine="custom_path_engine",
    engine_version="1.0",
    model_identity="custom_path_model",
    request_id="custom-001",
    claim="Using custom storage path",
    candidate_outputs=[CandidateOutput(
        answer="Success",
        confidence=0.9,
        reasoning_trace="Stored in custom directory",
        relation_steps=[]
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.9,
    uncertainty=0.1,
    provenance={"custom_path": True}
)

record_id = memory.store_evidence(envelope)
print(f"Stored evidence in custom path: {record_id}")

# Verify files were created
print(f"Files in storage directory: {os.listdir(storage_dir)}")

memory.shutdown()
```

## Step 3: Enabling Timechain Integration

The Cypher memory layer supports optional integration with Timechain for persistent, tamper-evident storage.

### 3.1 Install Timechain Dependencies

```bash
pip install timechain-py  # Or whatever the Timechain package is called
```

### 3.2 Configure Timechain Integration

```python
from abraxas.yggdrasil.memory import CypherMemoryLayer, TimechainConfig

# Configure Timechain (replace with your actual configuration)
timechain_config = TimechainConfig(
    enabled=True,
    root="/path/to/timechain/root",  # Path to Timechain root or URL
    network="mainnet",               # or "testnet", "devnet"
    contract_address="0x1234...",    # Timechain contract address
    # private_key should be handled securely, e.g., from environment variable
    # For demonstration, we'll use a placeholder - in production use secure secret management
    private_key=os.environ.get("TIMECHAIN_PRIVATE_KEY", "0x...")  # NOT SECURE FOR PRODUCTION
)

# Initialize memory layer with Timechain configuration
memory = CypherMemoryLayer(timechain_config=timechain_config)
memory.initialize()

# Check if Timechain is enabled
status = memory.get_status()
print(f"Timechain enabled: {status.get('timechain_enabled', False)}")

# Use the memory layer - storage attempts to Timechain will be made
# with fallback to file storage if Timechain is unavailable
envelope = EvidenceEnvelope(
    engine="timechain_engine",
    engine_version="1.0",
    model_identity="timechain_model",
    request_id="timechain-001",
    claim="Storing evidence with Timechain integration",
    candidate_outputs=[CandidateOutput(
        answer="Stored",
        confidence=0.92,
        reasoning_trace="Using Timechain for persistent storage",
        relation_steps=[]
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.92,
    uncertainty=0.08,
    provenance={"timechain_integration": True}
)

record_id = memory.store_evidence(envelope)
print(f"Stored evidence with Timechain integration: {record_id}")

# The record ID may be a Timechain transaction hash or a file-based ID
# depending on storage success and configuration

memory.shutdown()
```

### 3.3 Handling Timechain Failures Gracefully

The memory layer is designed to handle Timechain failures gracefully by falling back to file storage.

```python
from abraxas.yggdrasil.memory import CypherMemoryLayer, TimechainConfig
import logging

# Enable logging to see fallback messages
logging.basicConfig(level=logging.INFO)

# Configure with intentionally invalid Timechain settings to trigger fallback
timechain_config = TimechainConfig(
    enabled=True,
    root="/invalid/path/that/does/not/exist",
    network="mainnet",
    contract_address="0xinvalid",
    private_key="0xinvalid"
)

# Initialize - this will log warnings about Timechain setup failure
# but will succeed with file storage fallback
memory = CypherMemoryLayer(timechain_config=timechain_config)
memory.initialize()

status = memory.get_status()
print(f"Timechain enabled: {status.get('timechain_enabled', False)}")
print(f"Storage path: {status.get('storage_path', 'unknown')}")

# The memory layer will work normally using file storage
envelope = EvidenceEnvelope(
    engine="fallback_engine",
    engine_version="1.0",
    model_identity="fallback_model",
    request_id="fallback-001",
    claim="Fallback to file storage due to Timechain issues",
    candidate_outputs=[CandidateOutput(
        answer="Fallback works",
        confidence=0.88,
        reasoning_trace="Timechain failed, fell back to file storage",
        relation_steps=[]
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.88,
    uncertainty=0.12,
    provenance={"fallback_test": True}
)

record_id = memory.store_evidence(envelope)
print(f"Stored evidence via fallback: {record_id}")

# Verify we can retrieve it
retrieved = memory.retrieve_evidence(record_id)
print(f"Retrieved evidence: {retrieved['claim']}")

memory.shutdown()
```

## Step 4: Best Practices

### 4.1 Security Considerations
- Never hardcode Timechain private keys in source code
- Use environment variables or secure secret management systems
- Restrict file storage permissions when storing sensitive evidence
- Consider encrypting file storage for highly sensitive deployments

### 4.2 Performance Considerations
- Timechain integration adds latency due to blockchain transactions
- For high-throughput scenarios, consider batching Timechain submissions
- Monitor Timechain transaction costs and confirmation times
- File storage fallback ensures system continues operating during Timechain outages

### 4.3 Configuration Recommendations
- For development/testing: Use file storage only (Timechain disabled)
- For staging: Test Timechain integration with testnet
- For production: Enable Timechain with proper monitoring and alerting
- Always monitor storage layer status and set up alerts for failures

## Step 5: Monitoring and Maintenance

### 5.1 Checking Memory Layer Status
```python
from abraxas.yggdrasil.memory import CypherMemoryLayer

memory = CypherMemoryLayer()
memory.initialize()
status = memory.get_status()
print("Memory Layer Status:")
for key, value in status.items():
    print(f"  {key}: {value}")
memory.shutdown()
```

### 5.2 Checking Timechain Connection
If you have direct access to Timechain, you can verify the connection independently:
```bash
# Example Timechain CLI check (adjust for your Timechain implementation)
timechain-cli status --network mainnet
```

### 5.3 Backup and Recovery
Refer to the operational runbook for detailed backup and recovery procedures.
The memory layer storage path can be backed up like any other directory.
If using Timechain, the evidence is already persisted on the Timechain network.

## Conclusion
The Cypher memory layer in Abraxas provides flexible storage options with optional Timechain integration for enhanced persistence and tamper-evidence. By following this tutorial, you can configure the memory layer to suit your deployment needs, from simple file-based storage to robust Timechain-backed persistence.

For more information, see:
- API Reference: `docs/api.md` (CypherMemoryLayer section)
- Architecture Decision Records: `docs/adr/` (for storage-related decisions)
- Operational Guide: `docs/runbooks/operational_procedures.md` (Memory Layer Maintenance)