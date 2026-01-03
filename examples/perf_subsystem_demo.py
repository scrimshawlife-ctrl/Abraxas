#!/usr/bin/env python3
"""Performance Subsystem Drop v1.0 - Demo Script.

Demonstrates:
1. Content-Addressed Storage (CAS)
2. Dynamic compression with codec selection
3. Packet serialization (CBOR/JSON)
4. Stream deduplication
5. Acquisition runes (BULK/CACHE_ONLY/SURGICAL)
6. Performance ledger metrics
"""

from __future__ import annotations

import json
from pathlib import Path

# Import storage subsystem
from abraxas.storage import (
    stable_hash_bytes,
    stable_hash_json,
    cas_put_bytes,
    cas_put_json,
    choose_codec,
    compress_bytes,
    decompress_bytes,
    encode_packet,
    decode_packet,
    shingle_hashes,
    near_dup_score,
    dedup_items,
)

# Import performance ledger
from abraxas.perf import PerfEvent, write_perf_event, summarize_perf

# Import acquisition runes
from abraxas.runes.operators.acquisition_layer import (
    apply_acquire_bulk,
    apply_acquire_cache_only,
    apply_acquire_surgical,
)


def demo_cas():
    """Demo Content-Addressed Storage."""
    print("=" * 60)
    print("1. Content-Addressed Storage (CAS) Demo")
    print("=" * 60)

    # Hash some data
    data = b"Hello, Abraxas Performance Drop v1.0!"
    data_hash = stable_hash_bytes(data)
    print(f"Data hash: {data_hash}")

    # Hash JSON object
    obj = {"source": "demo", "value": 42}
    obj_hash = stable_hash_json(obj)
    print(f"Object hash: {obj_hash}")

    print()


def demo_compression():
    """Demo dynamic compression router."""
    print("=" * 60)
    print("2. Dynamic Compression Router Demo")
    print("=" * 60)

    # Test with repetitive data
    repetitive_data = b"repeat this text " * 100
    choice = choose_codec(repetitive_data)
    print(f"Codec choice for repetitive data: {choice.codec} (reason: {choice.reason})")

    compressed = compress_bytes(repetitive_data, choice)
    ratio = len(repetitive_data) / len(compressed) if compressed else 1.0
    print(f"Compression ratio: {ratio:.2f}x ({len(repetitive_data)} -> {len(compressed)} bytes)")

    # Round-trip test
    decompressed = decompress_bytes(compressed, choice.codec)
    assert decompressed == repetitive_data
    print("Round-trip verification: PASS")

    print()


def demo_packet_codec():
    """Demo packet serialization."""
    print("=" * 60)
    print("3. Packet Serialization (CBOR/JSON) Demo")
    print("=" * 60)

    packet = {
        "source_id": "DEMO_SOURCE",
        "timestamp": "2026-01-03T00:00:00Z",
        "data": [1, 2, 3, 4, 5],
    }

    # JSON encoding
    json_encoded = encode_packet(packet, fmt="json")
    print(f"JSON encoded size: {len(json_encoded)} bytes")

    # Decode and verify
    json_decoded = decode_packet(json_encoded, fmt="json")
    assert json_decoded == packet
    print("JSON round-trip: PASS")

    print()


def demo_dedup():
    """Demo stream deduplication."""
    print("=" * 60)
    print("4. Stream Deduplication Demo")
    print("=" * 60)

    texts = [
        "The quick brown fox jumps over the lazy dog",
        "The quick brown fox jumps over the lazy dog",  # Duplicate
        "The lazy dog sleeps under the tree",
        "A completely different text about cats",
    ]

    items = [{"id": i, "text": t} for i, t in enumerate(texts)]

    kept, dropped = dedup_items(items, lambda x: x["text"], threshold=0.9)

    print(f"Original items: {len(items)}")
    print(f"Kept items: {len(kept)}")
    print(f"Dropped items: {len(dropped)}")
    print(f"Dropped refs: {dropped}")

    print()


def demo_acquisition_runes():
    """Demo acquisition runes."""
    print("=" * 60)
    print("5. Acquisition Runes Demo")
    print("=" * 60)

    run_ctx = {"run_id": "DEMO_RUN_001"}

    # Demo ACQUIRE_BULK
    print("ABX-ACQUIRE_BULK (bulk acquisition):")
    bulk_result = apply_acquire_bulk(
        source_id="DEMO_SOURCE",
        window_utc="2026-01-03T00:00:00Z",
        params={"format": "json"},
        run_ctx=run_ctx,
    )
    print(f"  Cache hit: {bulk_result['cache_hit']}")
    print(f"  Raw path: {bulk_result['raw_path']}")

    # Demo ACQUIRE_CACHE_ONLY
    print("\nABX-ACQUIRE_CACHE_ONLY (offline replay):")
    cache_result = apply_acquire_cache_only(
        cache_keys=["key1", "key2"],
        run_ctx=run_ctx,
    )
    print(f"  Cache hits: {cache_result['cache_hits']}")
    print(f"  Failures: {len(cache_result['failures'])}")

    # Demo ACQUIRE_SURGICAL
    print("\nABX-ACQUIRE_SURGICAL (Decodo gate with cap):")
    surgical_result = apply_acquire_surgical(
        target="https://example.com/blocked-resource",
        reason_code="MANIFEST_DISCOVERY",
        hard_cap_requests=2,
        run_ctx=run_ctx,
    )
    print(f"  Requests used: {surgical_result['requests_used']}")
    print(f"  Requests capped: {surgical_result['requests_capped']}")
    print(f"  Reason: {surgical_result['provenance']['reason_code']}")

    print()


def demo_perf_ledger():
    """Demo performance ledger."""
    print("=" * 60)
    print("6. Performance Ledger Demo")
    print("=" * 60)

    # Write a perf event
    event = PerfEvent(
        run_id="DEMO_RUN_001",
        op_name="compress",
        source_id="DEMO_SOURCE",
        bytes_in=10000,
        bytes_out=2500,
        duration_ms=15.5,
        cache_hit=False,
        codec_used="zstd",
        compression_ratio=4.0,
    )
    write_perf_event(event)
    print(f"Wrote perf event: {event.op_name} (ratio: {event.compression_ratio}x)")

    # Summarize performance
    summary = summarize_perf(window_hours=24)
    print(f"\nPerformance summary (24h window):")
    print(f"  Event count: {summary['event_count']}")
    print(f"  Total bytes in: {summary['total_bytes_in']}")
    print(f"  Total bytes out: {summary['total_bytes_out']}")
    print(f"  Cache hit rate: {summary['cache_hit_rate']:.2%}")
    print(f"  Avg compression ratio: {summary['avg_compression_ratio']:.2f}x")
    print(f"  Decodo calls: {summary['decodo_call_count']}")
    print(f"  Bytes saved: {summary.get('bytes_saved', 0)}")

    print()


def main():
    """Run all demos."""
    print()
    print("T" + "=" * 58 + "W")
    print("Q  ABRAXAS PERFORMANCE SUBSYSTEM DROP v1.0 - DEMO        Q")
    print("Z" + "=" * 58 + "]")
    print()

    try:
        demo_cas()
        demo_compression()
        demo_packet_codec()
        demo_dedup()
        demo_acquisition_runes()
        demo_perf_ledger()

        print("=" * 60)
        print(" All demos completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - CAS provides deterministic, hash-addressed storage")
        print("  - Compression router selects optimal codec dynamically")
        print("  - Packet codec supports CBOR/MsgPack/JSON with compression")
        print("  - Dedup uses shingling for near-duplicate detection")
        print("  - Acquisition runes enforce budget + cache-first policy")
        print("  - Performance ledger tracks rent metrics with provenance")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
