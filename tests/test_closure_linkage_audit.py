# tests/test_closure_linkage_audit.py
from pathlib import Path


def test_linkage_fields_populated_or_marked_unresolved():
    # Verify that build_correlation_pointer_block always provides linkage fields
    # or explicit unresolved state (per P0 DoD). Uses the updated block.
    from scripts.correlation_pointer_block import build_correlation_pointer_block
    # Test with existing-ish path (may trigger unresolved if not present)
    b = build_correlation_pointer_block(root=Path('.'), paths=[Path('out/ledger/some.jsonl')])
    assert 'correlation_pointers' in b
    assert 'correlation_pointer_state' in b
    assert 'correlation' in b
    assert 'ledgerIds' in b['correlation']
    assert b['correlation_pointer_state'] in ('present', 'empty', 'unresolved')
    # Also test with no paths -> empty
    b2 = build_correlation_pointer_block(root=Path('.'), paths=[])
    assert b2['correlation_pointer_state'] in ('empty', 'unresolved')
    print('Linkage audit passed: fields present or unresolved marked')
