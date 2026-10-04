# Streaming Evidence Processing Tutorial

## Overview
This tutorial demonstrates how to use Abraxas' real-time streaming capabilities for processing evidence in high-throughput scenarios.

## Prerequisites
- Abraxas installed (`pip install -e .[dev]`)
- Basic understanding of Abraxas concepts (evidence envelopes, arbiters, orchestrators)

## Step 1: Import Required Components

```python
from abraxas.governance.production import ProductionOrchestrator
import time
```

## Step 2: Initialize the Orchestrator

```python
# Create and initialize the orchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()

print("Orchestrator initialized successfully")
```

## Step 3: Start the Streaming Processor

```python
# Start the background streaming processor with 4 workers
orchestrator.start_streaming_processor(num_workers=4)

print("Streaming processor started with 4 workers")
```

## Step 4: Submit Evidence for Streaming Processing

```python
# Submit multiple pieces of evidence for processing
stream_ids = []

claims = [
    "What is the capital of France?",
    "Explain the theory of relativity in simple terms",
    "Is machine learning effective for image recognition?",
    "What are the health benefits of regular exercise?",
    "How does photosynthesis work in plants?",
    "What causes the seasons on Earth?",
    "Who wrote the novel '1984'?",
    "What is the chemical formula for water?",
    "Explain the concept of supply and demand in economics",
    "What is the largest planet in our solar system?"
]

for i, claim in enumerate(claims):
    stream_id = orchestrator.submit_evidence_stream(
        evidence_id=f"evidence-{i:03d}",
        claim=claim,
        context={
            "domain": "general_knowledge",
            "priority": "medium" if i % 3 != 0 else "high",
            "timestamp": time.time()
        }
    )
    stream_ids.append(stream_id)
    print(f"Submitted evidence {i}: {stream_id}")

print(f"Submitted {len(stream_ids)} evidence items for streaming processing")
```

## Step 5: Retrieve Results

```python
# Wait for processing to complete (in a real application, you might use callbacks or websockets)
time.sleep(5)  # Adjust based on expected processing time

# Retrieve results for each stream
results = []
for i, stream_id in enumerate(stream_ids):
    result = orchestrator.get_stream_result(stream_id, timeout=10.0)
    results.append(result)
    
    if result:
        print(f"Result {i}: Decision={result.get('decision', 'UNKNOWN')}, "
              f"Governed={result.get('governed', False)}")
    else:
        print(f"Result {i}: No result available (timeout or not processed)")
```

## Step 6: Check Streaming Processor Status

```python
# Get status of the streaming processor
status = orchestrator.get_system_status()
streaming_info = status.get('streaming', {})

print("\nStreaming Processor Status:")
print(f"  Active: {streaming_info.get('active', False)}")
print(f"  Worker Count: {streaming_info.get('worker_count', 0)}")
print(f"  Queue Size: {streaming_info.get('queue_size', 0)}")
print(f"  Processed Count: {streaming_info.get('processed_count', 0)}")
print(f"  Failed Count: {streaming_info.get('failed_count', 0)}")
```

## Step 7: Stop the Streaming Processor

```python
# Stop the background streaming processor
orchestrator.stop_streaming_processor()
print("Streaming processor stopped")

# Note: In a long-running application, you would typically keep the processor running
# and stop it only when shutting down the application
```

## Advanced Usage

### Handling Stream Results Asynchronously

Instead of polling for results, you can implement a callback system:

```python
import threading
from abraxas.governance.production import ProductionOrchestrator

class StreamResultHandler:
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()
    
    def handle_result(self, stream_id: str, result: dict):
        with self.lock:
            self.results[stream_id] = result
        # Process result immediately or trigger events
        print(f"Received result for stream {stream_id}: {result.get('decision')}")

# Usage would involve modifying the orchestrator to accept result callbacks
# This is an advanced pattern that builds on the basic streaming infrastructure
```

### Configuring Streaming Parameters

You can configure the streaming processor for different workloads:

```python
# For high-throughput, low-latency processing
orchestrator.start_streaming_processor(num_workers=8)  # More workers

# For resource-constrained environments
orchestrator.start_streaming_processor(num_workers=2)  # Fewer workers

# The queue size and timeouts can be configured in the ProductionOrchestrator constructor
# or via environment variables/configuration files
```

### Error Handling in Streaming

The streaming processor handles errors gracefully:

```python
# If a worker encounters an error processing an evidence item:
# 1. The error is logged
# 2. The item is marked as failed
# 3. The worker continues to process other items
# 4. The stream result will indicate failure when retrieved

# You can check for failed streams:
status = orchestrator.get_system_status()
failed_count = status.get('streaming', {}).get('failed_count', 0)
if failed_count > 0:
    print(f"Warning: {failed_count} streams failed processing")
```

## Best Practices

1. **Start the processor early**: Initialize and start the streaming processor when your application starts
2. **Monitor queue size**: Watch the queue size to detect backpressure
3. **Handle timeouts appropriately**: Choose timeout values based on your latency requirements
4. **Clean up resources**: Stop the streaming processor when shutting down your application
5. **Use appropriate worker counts**: Match worker count to your CPU cores and workload characteristics
6. **Handle partial failures**: Design your application to handle cases where some streams fail or timeout

## Common Patterns

### Real-time Dashboard Updates
```python
# In a web application:
# 1. User submits a claim via web form
# 2. Backend submits claim to Abraxas streaming processor
# 3. Frontend polls for results or uses websockets for updates
# 4. Display result when available
```

### Batch Processing with Streaming Backend
```python
# For processing large batches:
# 1. Split batch into individual stream submissions
# 2. Process all streams in parallel via the streaming processor
# 3. Collect results as they become available
# 4. Aggregate results when all streams complete
```

### Event-Driven Architecture
```python
# In an event-driven system:
# 1. Evidence-generating events trigger stream submissions
# 2. Stream results trigger downstream processing events
# 3. Use the streaming processor as a central evidence processing hub
```

## Conclusion
Abraxas' streaming capabilities enable high-throughput, low-latency evidence processing while maintaining the system's governance guarantees. By using the streaming processor, you can handle bursty workloads, provide responsive user experiences, and scale your evidence processing independently of your submission rate.

For more information, see:
- API Reference: `docs/api.md` (ProductionOrchestrator section)
- Architecture Decision Record: `docs/adr/004-real-time-streaming.md`
- Operational Guide: `docs/runbooks/operational_procedures.md` (Streaming Processor Operations)