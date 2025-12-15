# tests/test_pipeline.py
from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.pipelines.sco_pipeline import SCOPipeline

def test_pipeline_runs():
    lex = [
        {"canonical": "aphex twin", "variants": ["aphex twins", "apex twin"]},
    ]
    records = [
        {"id": "1", "text": "I love Aphex Twins, especially the early stuff."},
        {"id": "2", "text": "Apex Twin is a legend."},
    ]
    transparency = TransparencyLexicon.build(["aphex twin", "aphex twins", "apex twin"])
    pipe = SCOPipeline(transparency)
    events = pipe.run(records, lexicon=lex, domain="music")
    assert len(events) >= 1
    assert all(e.domain == "music" for e in events)
