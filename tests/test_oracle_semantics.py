import json
from pathlib import Path
import subprocess


from abraxas.semantic.contracts import attach_canonical_hash


def test_oracle_semantics_not_computable_without_input():
    p = Path('out/oracle/oracle_input.latest.json')
    if p.exists():
        p.unlink()
    subprocess.run(['python', 'scripts/run_oracle_core.py'], check=True)
    out = json.loads(Path('out/oracle/oracle_signal_packet.latest.json').read_text())
    assert out['status'] == 'NOT_COMPUTABLE'
    assert out['reason'] == 'MISSING_INPUT'


def test_oracle_semantics_computable_with_input():
    Path('out/oracle').mkdir(parents=True, exist_ok=True)
    payload = attach_canonical_hash({'schema_version':'OracleInput.v1','sources':[{'id':'s1'}],'signals':[{'lane':'SHADOW','source_id':'s1','k':'v'}],'metadata':{'timestamp':'2026-05-03T00:00:00Z','source_family':'local'}})
    Path('out/oracle/oracle_input.latest.json').write_text(json.dumps(payload))
    subprocess.run(['python', 'scripts/run_oracle_core.py'], check=True)
    out = json.loads(Path('out/oracle/oracle_signal_packet.latest.json').read_text())
    assert out['status'] == 'COMPUTABLE'
    assert out['lane'] == 'SHADOW'
    assert out['source_count'] == 1
