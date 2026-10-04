# Architecture Decision Record: Real-time Streaming Capabilities

## Status
Accepted

## Context
Abraxas needed to support real-time evidence processing for high-throughput scenarios where low-latency responses are required. The existing batch-oriented architecture was sufficient for many use cases but couldn't handle streaming evidence efficiently.

## Decision
We implemented a ProducerOrchestrator pattern with a thread-safe queue and worker pool for real-time evidence streaming, rather than using reactive streams or message queues.

## Consequences

### Positive
- Simple to understand and debug
- No external dependencies required
- Backpressure handling through queue size limits
- Configurable worker count for different workloads
- Graceful shutdown capabilities
- Thread-safe implementation
- Minimal latency overhead

### Negative
- Limited to single-node deployment (no distribution)
- Manual scaling required (no auto-scaling)
- Potential for queue backup under sustained high load
- More complex than pure synchronous processing

## Implementation Details

### Components
1. **Stream Queue**: Thread-safe queue for holding incoming evidence
2. **Worker Pool**: Configurable number of worker threads that process evidence from the queue
3. **Stream Manager**: Coordinates submission, processing, and result retrieval
4. **Result Storage**: Temporary storage for completed stream results with timeout-based cleanup

### Key Features
- **Backpressure Handling**: Queue size limits prevent memory exhaustion
- **Timeout-Based Retrieval**: Clients can specify timeouts for result retrieval
- **Worker Isolation**: Failures in one worker don't affect others
- **Graceful Shutdown**: Workers finish current jobs before terminating
- **Result Expiration**: Automatic cleanup of old results to prevent memory leaks

### Configuration
- `num_workers`: Number of worker threads (default: 3)
- `queue_maxsize`: Maximum queue size (default: 1000)
- `result_timeout`: Default timeout for result retrieval (default: 30.0 seconds)
- `worker_timeout`: Timeout for worker operations (default: 5.0 seconds)

### Interface
- `start_streaming_processor(num_workers: int = 3)`: Start the streaming processor
- `stop_streaming_processor()`: Stop the streaming processor
- `submit_evidence_stream(evidence_id: str, claim: str, context: Dict[str, Any] = None)` -> str: Submit evidence for streaming processing
- `get_stream_result(stream_id: str, timeout: Optional[float] = None)` -> Optional[Dict[str, Any]]: Retrieve stream processing result

## Alternatives Considered

### Reactive Streams (RxPY, Asyncio)
- **Pros**: Natural fit for streaming, built-in backpressure, composable
- **Cons**: Increased complexity, steeper learning curve, potential for callback hell, harder to debug

### Message Queues (Redis, RabbitMQ, Apache Kafka)
- **Pros**: Distributed, scalable, persistent, mature ecosystem
- **Cons**: External dependencies, operational overhead, increased latency, complexity overkill for current scale

### Thread Pool Executor (concurrent.futures)
- **Pros**: Simple, built-in, good for fire-and-forget
- **Cons**: No built-in queue for backpressure, harder to manage result retrieval, limited control over worker lifecycle

### Custom Actor Model
- **Pros**: Excellent concurrency model, location transparency
- **Cons**: Significant implementation overhead, steep learning curve, over-engineering

## Related Decisions
- ADR-001: Evidence Container Standardization (defines EvidenceEnvelope)
- ADR-002: Verifier Interface Standardization
- ADR-003: Governance Gate Framework

## References
- Java ConcurrentLinkedQueue inspiration for thread-safe queue design
- Python threading documentation for worker implementation
- "Patterns for Concurrent and Networked Objects" by Douglas Schmidt

## Acceptance Criteria
- [x] Streaming processor can be started and stopped gracefully
- [x] Evidence can be submitted for streaming processing
- [x] Results can be retrieved with configurable timeouts
- [x] System handles backpressure appropriately
- [x] Worker failures don't crash the system
- [x] Memory usage remains bounded under load
- [x] Latency measurements show improvement over batch processing for streaming scenarios
- [x] Integration tests pass for streaming scenarios
- [x] Chaos engineering tests verify resilience

## Implementation Location
- Primary: `abraxas/governance/production.py` (ProductionOrchestrator class)
- Tests: `tests/integration/test_edge_cases.py` (streaming scenarios)
- Chaos Tests: `tests/chaos/test_resilience.py` (resilience verification)

## Notes
The implementation prioritizes operational simplicity and reliability over maximum performance or distributed capabilities. This aligns with Abraxas' design philosophy of providing robust, understandable systems that can be operated effectively by small teams.

Future enhancements could include:
- Metrics collection for monitoring streaming performance
- Dynamic worker scaling based on queue depth
- Persistent result storage for longer-term stream processing
- Integration with external message queues for distributed scenarios