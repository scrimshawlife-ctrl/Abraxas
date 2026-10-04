# Plan for Executing Steps 1-3 of the Abraxas Further Work Plan

## Goal
Execute steps 1 (Technical Debt Resolution), 2 (Feature Extensions), and 3 (Integration & Testing) of the Abraxas further work plan to improve system quality, add features, and verify correctness.

## Current Context / Assumptions
- The Abraxas repository is located at `/Users/appliedalchemylabs/Abraxas`.
- The current branch is `main` and is clean.
- The system has a Python 3.14+ environment with dependencies installed (as per the existing setup).
- The existing codebase includes the Abraxas multi-engine evidence arbitration kernel with core components: EvidenceController, Yggdrasil Coordinator, and several evidence engines (Athanor, Hyperlex, Semion, Noesis, etc.).
- The test suite includes directories `tests/evidence`, `tests/integration`, and `tests/chaos`.
- The user has zero context for the codebase, so the plan must be explicit and assume no prior knowledge.
- The plan is written for an implementer with questionable taste, meaning steps must be obvious and unambiguous.

## Architecture / Proposed Approach
We will execute the three sections in order, following a test-driven development (TDD) cycle for each task:
1. **Technical Debt Resolution**: Address code quality issues, performance bottlenecks, and debt items without changing behavior.
2. **Feature Extensions**: Add new features as specified in the original plan, ensuring they integrate cleanly with existing architecture.
3. **Integration & Testing**: Expand test coverage to validate new and existing functionality, including edge cases and failure scenarios.

Each section will be broken down into small, verifiable tasks. We will use the existing tooling (pytest, etc.) and follow the project's conventions.

## Step-by-Step Tasks

### Section 1: Technical Debt Resolution
We resolve technical debt items identified in the original plan.

#### Task 1.1: Fix JSON Serialization Warnings in Memory Layer
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/memory.py`
- **Issue**: JSON serialization warnings when serializing complex objects (e.g., enum, nested dataclasses).
- **Solution**: Implement a custom JSON serializer that handles Abraxas-specific types.
- **Steps**:
  1. Open the file and locate the JSON serialization logic (likely in `to_json` or similar methods).
  2. Replace ad-hoc serialization with a centralized `_json_serializer` function (similar to the one in `abraxas/governance/production.py`).
  3. Ensure the serializer handles `Enum`, `datetime`, and custom classes like `EvidenceEnvelope` and `RelationStep`.
  4. Update all JSON dumping calls to use this serializer.
- **Expected Output**: No warnings when running `python3 -m pytest tests/ -Wd::DeprecationWarning` related to JSON serialization.

#### Task 1.2: Resolve Deprecation Warnings (datetime.utcnow)
- **File**: Search across the codebase for `datetime.utcnow`.
- **Issue**: `datetime.utcnow()` is deprecated in Python 3.12+.
- **Solution**: Replace with `datetime.now(timezone.utc)`.
- **Steps**:
  1. Run `grep -r "datetime.utcnow" .` to find all occurrences.
  2. For each file, replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
  3. Ensure the import `from datetime import timezone` is present.
- **Expected Output**: No deprecation warnings when running tests with `-Wd`.

#### Task 1.3: Optimize Performance-Critical Paths in Verifiers
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/verifiers/sign.py` (SignRelationVerifier)
- **Issue**: Repeated computation in verification logic.
- **Solution**: Add LRU caching to the verification method.
- **Steps**:
  1. Identify the method that performs the core verification (e.g., `verify`).
  2. Import `functools.lru_cache`.
  3. Decorate the method with `@lru_cache(maxsize=128)` (or a suitable size).
  4. Ensure the method arguments are hashable (convert mutable inputs to immutable if needed).
- **Expected Output**: Improved performance in benchmarks; no change in verification correctness.

#### Task 1.4: Enhance Error Handling and Recovery Mechanisms
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/coordinator.py`
- **Issue**: Lack of error handling during initialization and operation.
- **Solution**: Add try/catch blocks and fallback mechanisms.
- **Steps**:
  1. Locate the `__init__` method of `YggdrasilCoordinator`.
  2. Wrap external resource initialization (e.g., database connections) in try/catch.
  3. On failure, log the error and set a fallback state (e.g., disabled mode or safe default).
  4. Update health check methods to reflect the fallback state.
- **Expected Output**: Coordinator initializes even if external dependencies are unavailable; system continues in degraded mode.

#### Task 1.5: Add VIDEO_ANALYSIS Evidence Type
- **Files**:
  - `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/contract.py` (add new EvidenceType)
  - `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/adapters/video.py` (new adapter)
  - `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/verifiers/video.py` (new verifier)
- **Issue**: Missing support for video evidence.
- **Solution**: Define a new evidence type and implement adapter/verifier.
- **Steps**:
  1. In `contract.py`, add `VIDEO_ANALYSIS = "video_analysis"` to the `EvidenceType` enum.
  2. Create a new adapter file `video.py` that implements `EvidenceProvider` (stubbed for now).
  3. Create a new verifier file `video.py` that implements `Verifier` (stubbed for now).
  4. Register the new adapter and verifier in the provider registry and arbiter.
- **Expected Output**: System recognizes `VIDEO_ANALYSIS` evidence type without errors.

### Section 2: Feature Extensions
We extend features as per the original plan.

#### Task 2.1: Enhance Oracle Engine with Context-Aware Narrative Synthesis
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/adapters/oracle.py`
- **Issue**: Oracle engine produces generic narratives.
- **Solution**: Add tone selection (explanatory, descriptive, prescriptive) based on context.
- **Steps**:
  1. Review the existing `OracleAdapter.generate_narrative` method.
  2. Add a `tone` parameter (default: "explanatory").
  3. Implement logic to vary narrative structure and vocabulary based on tone.
  4. Update the adapter to accept tone from input context or configuration.
- **Expected Output**: Oracle produces different narratives for the same input when tone is changed.

#### Task 2.2: Improve Cypher Memory Layer with Timechain Integration
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/adapters/cypher.py`
- **Issue**: Cypher memory layer lacks persistent, verifiable storage.
- **Solution**: Integrate Timechain for immutable memory storage with fallback to file storage.
- **Steps**:
  1. Check if Timechain is available (via environment or optional dependency).
  2. If available, use Timechain to store memory entries; otherwise, use existing file storage.
  3. Add a method to verify memory integrity via Timechain proofs.
  4. Update the memory layer abstraction to support both backends.
- **Expected Output**: Cypher engine can store and retrieve memories with optional Timechain verification.

#### Task 2.3: Add Real-Time Streaming Capabilities for Evidence Processing
- **File**: `/Users/appliedalchemylabs/Abraxas/abraxas/governance/production.py` (ProductionOrchestrator)
- **Issue**: Evidence processing is batch-oriented.
- **Solution**: Add a streaming interface with a queue and worker threads.
- **Steps**:
  1. Add a `submit_evidence_stream` method to `ProductionOrchestrator` that accepts an async iterator or queue.
  2. Implement a background thread pool that processes items from the stream.
  3. Add methods to start/stop the streaming processor and retrieve results.
  4. Ensure thread safety and proper resource cleanup.
- **Expected Output**: System can process evidence in real-time as it arrives.

### Section 3: Integration & Testing
We expand testing to cover new features and edge cases.

#### Task 3.1: Expand Integration Tests for Edge Cases
- **File**: `/Users/appliedalchemylabs/Abraxas/tests/integration/test_edge_cases.py` (create if not exists)
- **Issue**: Insufficient coverage of edge cases.
- **Solution**: Add tests for malformed envelopes, streaming failures, and governance edge cases.
- **Steps**:
  1. Create the test file if it doesn't exist.
  2. Write a test for `test_production_arbiter_with_malformed_envelope` (similar to existing).
  3. Write a test for `test_six_gate_governor_edge_cases` (varying gate weights).
  4. Write a test for `test_orchestrator_streaming_basic` (simple stream processing).
  5. Write a test for `test_memory_layer_timechain_config` (with and without Timechain).
- **Expected Output**: All new tests pass.

#### Task 3.2: Add Chaos Engineering Tests for System Resilience
- **File**: `/Users/appliedalchemylabs/Abraxas/tests/chaos/test_resilience.py` (create if not exists)
- **Issue**: Lack of resilience testing.
- **Solution**: Simulate failures and verify system behavior.
- **Steps**:
  1. Create the test file if it doesn't exist.
  2. Write a test for `test_memory_layer_resilience_to_storage_failures` (simulate disk full).
  3. Write a test for `test_orchestrator_resilience_to_engine_failures` (simulate engine crashes).
  4. Write a test for `test_memory_layer_concurrent_access_resilience` (simulate high concurrency).
  5. Write a test for `test_arbiter_resilience_to_verifier_failures` (simulate verifier timeouts).
- **Expected Output**: System degrades gracefully; no data loss; recovery possible.

#### Task 3.3: Create Benchmarking Suite for Performance Regression Detection
- **File**: `/Users/appliedalchemylabs/Abraxas/benchmarks/benchmark_suite.py`
- **Issue**: No performance benchmarking.
- **Solution**: Create a suite that benchmarks critical paths and alerts on regression.
- **Steps**:
  1. Create the benchmark suite file.
  2. Benchmark evidence creation, serialization, orchestrator pipeline, memory operations, and adapter performance.
  3. Use `timeit` or similar to measure execution time.
  4. Output results in a format that can be compared over time (e.g., JSON).
- **Expected Output**: Benchmark suite runs without errors and produces measurable metrics.

## Tests / Validation
For each code task, we follow the TDD cycle:
1. Write a failing test that captures the desired behavior or fix.
2. Run the test to confirm it fails.
3. Implement the minimal change to make the test pass.
4. Run the test to confirm it passes.
5. Commit the change.

However, since we are in PLAN MODE, we do not execute these steps. The plan includes the exact verification commands for each task.

## Risks, Tradeoffs, and Open Questions
- **Risk**: Changing JSON serialization could break external consumers if not backward-compatible.
  - **Mitigation**: Ensure the new serializer produces the same output format for existing data; add versioning if needed.
- **Tradeoff**: Adding LRU caching to verifiers trades memory for speed.
  - **Mitigation**: Tune cache size based on benchmarks; monitor memory usage.
- **Open Question**: How to handle Timechain integration when the external service is unavailable? Should we fail fast or fallback?
  - **Proposed Approach**: Fallback to file storage with a warning; make it configurable.
- **Risk**: Streaming interface could introduce complexity and potential bugs in concurrent code.
  - **Mitigation**: Use well-tested concurrency patterns (e.g., `queue.Queue`, `ThreadPoolExecutor`); write extensive unit tests for the streaming logic.

## Conclusion
This plan provides a clear, step-by-step roadmap to execute steps 1-3 of the Abraxas further work plan. Each task is bite-sized, verifiable, and follows TDD principles. An implementer with zero context should be able to follow this plan to improve the system's technical debt, add features, and enhance test coverage.

After saving this plan, the next step would be to execute it (e.g., via subagent-driven development), but that is outside the scope of this PLAN MODE turn.