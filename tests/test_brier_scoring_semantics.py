import json
from pathlib import Path
import subprocess


from abraxas.semantic.contracts import attach_canonical_hash


def test_brier_scoring_computes():
    Path('out/scoring').mkdir(parents=True, exist_ok=True)
    payload = attach_canonical_hash({'schema_version':'ForecastOutcomeSet.v1','forecasts':[{'id':'f1','probability':0.8,'label':'YES'},{'id':'f2','probability':0.2,'label':'NO'}],'outcomes':[{'forecast_id':'f1','resolved_value':1},{'forecast_id':'f2','resolved_value':0}]})
    Path('out/scoring/forecast_outcome_set.latest.json').write_text(json.dumps(payload))
    subprocess.run(['python', 'scripts/run_brier_scoring.py'], check=True)
    out = json.loads(Path('out/scoring/brier_scoring.latest.json').read_text())
    assert out['schema_version'] == 'BrierScoringRun.v1'
    assert out['scored_count'] == 2
    assert abs(out['mean_brier'] - 0.04) < 1e-12


def test_brier_scoring_not_computable_without_data():
    payload = attach_canonical_hash({'schema_version':'ForecastOutcomeSet.v1','forecasts':[],'outcomes':[]})
    Path('out/scoring/forecast_outcome_set.latest.json').write_text(json.dumps(payload))
    subprocess.run(['python', 'scripts/run_brier_scoring.py'], check=True)
    out = json.loads(Path('out/scoring/brier_scoring.latest.json').read_text())
    assert out['status'] == 'NOT_COMPUTABLE'
