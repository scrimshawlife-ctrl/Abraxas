from aal_core.aalmanac.canonicalize import canonicalize, classify_term_from_raw
from aal_core.aalmanac.tokenizer import tokenize


def test_tokenizer_splits_compounds():
    assert tokenize("NeonGenie") == ["neon", "genie"]
    assert tokenize("shadow-bloom") == ["shadow", "bloom"]
    assert tokenize("field_state") == ["field", "state"]


def test_canonicalize_and_classify():
    assert canonicalize(tokenize("Don't")) == "don't"
    result = classify_term_from_raw("ShadowBloom", declared_class="single")
    assert result.term_class == "compound"
    assert result.note == "forced_compound_from_multitoken"
