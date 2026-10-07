#!/usr/bin/env python
"""Test script for deterministic logging."""

import sqlite3
import sys
from abx.store.sqlite_store import connect
from abx.log import ledger, compactor, policy

def test_append_events(con, count=2000):
    """Append multiple events for testing."""
    print(f"Appending {count} events...")
    for i in range(count):
        ledger.append_event(
            con,
            kind="perf",
            module="bench",
            frame_id=f"frame_{i % 10}",
            payload={"index": i, "message": f"Event {i}"}
        )
        if (i + 1) % 500 == 0:
            print(f"  {i + 1} events appended")
    print(f"Done! Total appended: {count}")

def test_verify(con):
    """Verify hash chain."""
    print("\nVerifying hash chain...")
    result = ledger.verify_chain(con)
    print(f"  Verified: {result['verified']} events")
    print(f"  OK: {result['ok']}")
    if not result['ok']:
        print(f"  Errors: {result['errors']}")
    return result['ok']

def test_compact(con):
    """Test compaction."""
    print("\nTesting compaction...")
    stats = ledger.get_stats(con)
    print(f"  Total events: {stats['total_events']}")

    comp_range = policy.calculate_compaction_range(stats)
    if comp_range is None:
        print(f"  Not enough events to compact")
        return None

    start_id, end_id = comp_range
    print(f"  Compacting range [{start_id}, {end_id}]...")

    segment_id = compactor.compact(con, start_id, end_id, top_k=policy.DICT_TOPK)
    segment = compactor.get_segment(con, segment_id)

    print(f"  Segment ID: {segment_id}")
    print(f"  SHA256: {segment['sha256']}")
    print(f"  Codec: {segment['codec']}")
    print(f"  Raw events: {segment['raw_event_count']}")
    print(f"  Compressed size: {segment['compressed_size']} bytes")

    return segment

def test_deterministic_compaction():
    """Test that compaction is deterministic."""
    print("\n=== Testing Deterministic Compaction ===")

    # Create two separate databases
    import tempfile
    import os
    from pathlib import Path
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        db1 = Path(tmpdir) / "test1.db"
        db2 = Path(tmpdir) / "test2.db"

        con1 = sqlite3.connect(str(db1))
        con1.execute("PRAGMA journal_mode=WAL;")
        con2 = sqlite3.connect(str(db2))
        con2.execute("PRAGMA journal_mode=WAL;")

        ledger.init_ledger(con1)
        ledger.init_ledger(con2)
        compactor.init_compactor_tables(con1)
        compactor.init_compactor_tables(con2)

        # Add events to first database
        print("Creating event stream in database 1...")
        for i in range(100):
            payload = {"index": i, "data": f"test_{i}"}
            ledger.append_event(con1, kind="test", module="demo", frame_id=f"f{i%5}", payload=payload)

        # Copy exact events from db1 to db2 by reading the raw event_json
        print("Copying identical events to database 2...")
        events1 = ledger.get_events_range(con1, 1, 100)

        # Insert exact same events into db2 (copying the event_json directly)
        for event in events1:
            # Parse the event JSON to get the data
            event_data = json.loads(event.event_json)
            # Insert with same data, which will produce same event_json
            con2.execute("""
            INSERT INTO log_events(id, ts, kind, module, frame_id, event_json, hash, prev_hash)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?);
            """, (event.id, event.ts, event.kind, event.module, event.frame_id, event.event_json, event.hash, event.prev_hash))
        con2.commit()

        # Verify chains
        print("\nVerifying both chains...")
        v1 = ledger.verify_chain(con1)
        v2 = ledger.verify_chain(con2)
        assert v1['ok'] and v2['ok'], "Hash chain verification failed"
        print("  Both chains verified OK")

        # Verify events are identical
        events2 = ledger.get_events_range(con2, 1, 100)
        for e1, e2 in zip(events1, events2):
            assert e1.event_json == e2.event_json, f"Event {e1.id} differs"
            assert e1.hash == e2.hash, f"Hash {e1.id} differs"
        print("  Events are identical")

        # Compact both
        print("\nCompacting both databases...")
        seg1 = compactor.compact(con1, 1, 100)
        seg2 = compactor.compact(con2, 1, 100)

        # Get segments
        s1 = compactor.get_segment(con1, seg1)
        s2 = compactor.get_segment(con2, seg2)

        print(f"\nDatabase 1 segment SHA256: {s1['sha256']}")
        print(f"Database 2 segment SHA256: {s2['sha256']}")

        if s1['sha256'] == s2['sha256']:
            print("✓ SUCCESS: Compaction is deterministic!")
            return True
        else:
            print("✗ FAIL: Compaction produced different hashes!")
            return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "deterministic":
        success = test_deterministic_compaction()
        sys.exit(0 if success else 1)

    con = connect()
    ledger.init_ledger(con)
    compactor.init_compactor_tables(con)

    # Get current stats
    stats = ledger.get_stats(con)
    current_count = stats['total_events']
    print(f"Current events in ledger: {current_count}")

    # Add events to reach 2000
    if current_count < 2000:
        needed = 2000 - current_count
        test_append_events(con, needed)

    # Verify
    if not test_verify(con):
        sys.exit(1)

    # Compact
    segment = test_compact(con)
    if segment is None:
        print("Compaction skipped (not enough events)")

    print("\n✓ All tests passed!")

if __name__ == "__main__":
    main()
