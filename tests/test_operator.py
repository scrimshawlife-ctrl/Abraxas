# tests/test_operator.py
from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.operators.symbolic_compression import SymbolicCompressionOperator

def test_operator_emits_event_for_clear_case():
    transparency = TransparencyLexicon.build(["nick of time", "nit of time"])
    op = SymbolicCompressionOperator(transparency)
    e = op.analyze(
        original_token="nick of time",
        replacement_token="nit of time",
        context_before="we arrived in the nick of time",
        context_after="we arrived in the nit of time",
        domain="idiom",
        observed_frequency=12
    )
    assert e is not None
    assert e.event_type == "SymbolicCompressionEvent"
    assert e.provenance_sha256
