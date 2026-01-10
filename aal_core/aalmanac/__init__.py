"""AALmanac core utilities."""

from aal_core.aalmanac.canonicalize import (
    canonicalize,
    classify_term,
    classify_term_from_raw,
)
from aal_core.aalmanac.drift import compute_drift
from aal_core.aalmanac.filter import quality_gate, rejection_reason
from aal_core.aalmanac.generate import propose_candidates
from aal_core.aalmanac.mutation import detect_mutation, load_reference_dictionary
from aal_core.aalmanac.oracle_attachment import (
    build_oracle_attachment,
    build_oracle_attachment_from_storage,
    build_oracle_attachment_with_rejections,
    summarize_rejections,
)
from aal_core.aalmanac.pipeline import mint_entries_from_slang
from aal_core.aalmanac.scoring import priority_score
from aal_core.aalmanac.storage.entries import append_entry, load_entries
from aal_core.aalmanac.storage.index import build_index, write_index
from aal_core.aalmanac.tokenizer import tokenize

__all__ = [
    "append_entry",
    "build_index",
    "build_oracle_attachment",
    "build_oracle_attachment_from_storage",
    "build_oracle_attachment_with_rejections",
    "summarize_rejections",
    "canonicalize",
    "classify_term",
    "classify_term_from_raw",
    "compute_drift",
    "detect_mutation",
    "priority_score",
    "propose_candidates",
    "mint_entries_from_slang",
    "quality_gate",
    "rejection_reason",
    "tokenize",
    "write_index",
    "load_entries",
    "load_reference_dictionary",
]
