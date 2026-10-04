# Getting Started with Abraxas

## Installation

To get started with Abraxas, you'll need Python 3.8 or higher installed on your system.

### From Source

```bash
# Clone the repository
git clone https://github.com/appliedalchemylabs/abraxas.git
cd abraxas

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Using Pip

```bash
pip install abraxas-framework
```

## Quick Start Guide

Let's walk through a simple example of using Abraxas to evaluate a claim.

### Step 1: Import Required Components

```python
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
from abraxas.evidence.arbiter.arbiter import EvidenceArbiter, DefaultArbitrationPolicy
from abraxas.evidence.verifiers.relational import RelationalVerifier
from abraxas.governance.production import ProductionArbiter
```

### Step 2: Set Up the Arbiter

```python
# Create arbitration policy with custom thresholds (optional)
policy = DefaultArbitrationPolicy(
    accept_confidence=0.85,    # Accept if confidence > 0.85
    verify_confidence=0.60,    # Verify if confidence > 0.60
    recompute_confidence=0.40, # Recompute if confidence > 0.40
    max_uncertainty=0.30,      # Max allowed uncertainty
)

# Create arbiter and register verifiers
arbiter = EvidenceArbiter(policy=policy)
arbiter.register_verifier("RELATIONAL_REASONING", RelationalVerifier())
```

### Step 3: Create Evidence

```python
# Create an evidence envelope for a simple claim
envelope = EvidenceEnvelope(
    engine="example_engine",
    engine_version="1.0",
    model_identity="example_model_v1",
    request_id="req-001",
    claim="Water boils at 100°C at sea level",
    candidate_outputs=[
        CandidateOutput(
            answer="True",
            confidence=0.95,
            reasoning_trace="Based on standard atmospheric pressure and the definition of Celsius scale",
            relation_steps=[
                RelationStep(
                    relation="defines",
                    subject="Celsius scale",
                    object="boiling point of water",
                    result="100°C at standard atmospheric pressure",
                    confidence=0.98
                )
            ]
        ),
        CandidateOutput(
            answer="False",
            confidence=0.05,
            reasoning_trace="Incorrect understanding of temperature scales",
            relation_steps=[]
        )
    ],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.95,
    uncertainty=0.05,
    provenance={
        "source": "scientific_consensus",
        "reference": "International Temperature Scale of 1990"
    }
)
```

### Step 4: Arbitrate the Evidence

```python
# Run arbitration to get a decision
decision = arbiter.arbitrate(envelope)

print(f"Evidence Decision: {decision}")
print(f"Claim: {envelope.claim}")
print(f"Confidence: {envelope.confidence}")
```

### Step 5: Using the Production Arbiter (Recommended)

For production use, we recommend using the ProductionArbiter which includes governance checks:

```python
# Create production arbiter
prod_arbiter = ProductionArbiter()

# Arbitrate with governance checks
result = prod_arbiter.arbitrate(envelope, verify=True)

print(f"Decision: {result['decision']}")
print(f"Governed: {result['governed']}")
print(f"Governance Score: {result['governance_score']:.3f}")
if 'gate_results' in result:
    print("Gate Results:")
    for gate_result in result['gate_results']:
        print(f"  {gate_result['gate']}: {gate_result['passed']} (score: {gate_result['score']:.3f})")
```

## Running the Examples

Save the above code to a file called `getting_started.py` and run it:

```bash
python getting_started.py
```

You should see output similar to:

```
Evidence Decision: ACCEPT
Claim: Water boils at 100°C at sea level
Confidence: 0.95
Decision: ACCEPT
Governed: True
Governance Score: 0.92
Gate Results:
  Provenance: True (score: 0.95)
  Falsifiability: True (score: 0.88)
  Redundancy: True (score: 0.90)
  Rent: True (score: 0.85)
  Ablation: True (score: 0.92)
  Stabilization: True (score: 0.95)
```

## Next Steps

1. **Try different claims**: Modify the claim to see how the system handles various types of statements
2. **Explore different evidence types**: Try creating evidence with different EvidenceType values
3. **Add more verifiers**: Register additional verifiers like LexicalConsistencyVerifier or SignRelationVerifier
4. **Use the orchestrator**: Try the ProductionOrchestrator for multi-engine pipelines
5. **Check out the benchmarks**: Run the benchmark suite to see performance characteristics
6. **Read the API documentation**: Refer to `docs/api.md` for detailed API reference

## Troubleshooting

### Common Issues

#### Import Errors
If you see import errors like `ModuleNotFoundError: No module named 'abraxas'`, make sure you've installed the package correctly:
```bash
pip install -e .
```

#### Validation Errors
If you get validation errors when creating EvidenceEnvelope objects, check that:
- All required fields are present
- EvidenceType values are valid enum members
- Confidence and uncertainty values are between 0.0 and 1.0
- Lists contain the correct types of objects

#### Performance Issues
If you notice performance issues:
1. Check that you're using the latest version
2. Consider enabling caching in verifiers (already enabled in SignRelationVerifier)
3. Profile your specific use case to identify bottlenecks
4. Consider using the streaming capabilities for high-volume scenarios

## Where to Go Next

- **API Reference**: See `docs/api.md` for complete API documentation
- **Tutorials**: Check `docs/tutorials/` for more advanced usage patterns
- **Architecture**: See `docs/adr/` for Architecture Decision Records
- **Operational Guides**: See `docs/runbooks/` for deployment and operations guidance
- **Examples**: Look in the `examples/` directory for runnable code samples
- **Testing**: Run `python -m pytest` to run the test suite

## Getting Help

If you encounter issues or have questions:

1. Check the existing documentation
2. Search through closed GitHub issues
3. Open a new issue with details about your problem
4. For urgent issues, contact the maintainers directly

Happy reasoning with Abraxas! 🧠