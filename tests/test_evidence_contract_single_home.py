"""Tests verifying the EvidenceEnvelope contract has a single canonical home.

Plan: single-home-the-evidence-contract, Phase 1.

The envelope was formerly defined twice -- once in the package `__init__` and once in
`abraxas/evidence/contract.py` -- and the copies differed by exactly one field, `schema_version`.
The first attempt to resolve that divergence DELETED the field. That was wrong, and this file records
why, because the reason is not visible in the field list:

    `EvidenceSchemaMigrator.migrate()` READS `schema_version` to decide whether migration is needed
    (`current_version = envelope.get("schema_version", "v1")`, abraxas/evidence/__init__.py). The
    early return fires only when the version MATCHES the target, and the migration is what records the
    new version. Deleting the field therefore forced the deletion of the write, which silently made
    migration non-idempotent: a migrated envelope keeps reading as "v1", so `migrate()` re-runs its
    defaults on every call and the early return can never fire. No test covered that. The suite stayed
    green, so nothing warned anyone.

The divergence is therefore resolved by PROMOTING the field to the canonical envelope, not by removing
it: it describes the artifact's FORMAT, which belongs on the artifact, while remaining excluded from
content and identity hashes -- the same identity-versus-metadata rule this repository applies to
`timestamp`, the rune hash, and the lexicon content fingerprint.
"""

from dataclasses import fields

import pytest

from abraxas.evidence import EvidenceEnvelope, EvidenceSchemaMigrator
from abraxas.evidence.contract import EvidenceEnvelope as ContractEnvelope

#: The canonical field count. Asserted rather than derived, so a silent re-divergence fails here.
EXPECTED_FIELD_COUNT = 22


def test_evidence_envelope_single_home_identity():
    """The package-level EvidenceEnvelope IS the contract copy -- not a duplicate."""
    assert EvidenceEnvelope is ContractEnvelope, (
        "EvidenceEnvelope must be a single canonical type. "
        "The package __init__ must re-export the contract copy, not redefine it."
    )


def test_canonical_envelope_field_count():
    """The canonical envelope has exactly 22 fields, and `schema_version` is one of them."""
    field_names = [f.name for f in fields(EvidenceEnvelope)]
    assert len(field_names) == EXPECTED_FIELD_COUNT, (
        f"Expected {EXPECTED_FIELD_COUNT} fields, got {len(field_names)}: {field_names}. "
        "If you are here because you removed a field: check whether anything READS it before "
        "deleting it -- see this module's docstring."
    )
    assert "schema_version" in field_names, (
        "schema_version must be present: EvidenceSchemaMigrator reads it to decide whether to "
        "migrate, and writes it so that a second migration is a no-op."
    )


def test_the_package_export_cannot_diverge_from_the_contract():
    """A re-introduced divergent copy is the defect this plan exists to remove. Asserting the field
    lists catches a divergence even if the identity check were somehow satisfied by a shared name."""
    package_fields = [f.name for f in fields(EvidenceEnvelope)]
    contract_fields = [f.name for f in fields(ContractEnvelope)]
    assert package_fields == contract_fields, (
        "the package export and the contract type disagree on their fields -- that is the original "
        "defect, which cost an isinstance check against a real engine's output"
    )


def test_schema_version_is_serialized():
    """The field is on the artifact, so `to_dict()` must carry it -- otherwise a round trip loses the
    format marker and the migration cannot detect its own work."""
    payload = EvidenceEnvelope(engine="noesis").to_dict()
    assert payload.get("schema_version") == "v2"


def test_migration_is_idempotent():
    """Migrating twice must equal migrating once.

    This is the guard for the regression described in the module docstring. When the version stamp was
    removed, the second call re-ran the defaults and this property broke while every other test passed.
    """
    v1 = {
        "evidence_id": "e-1",
        "engine": "noesis",
        "claim": "does A imply B?",
        "evidence_type": "relational_reasoning",
        "confidence": 0.4,
    }
    once = EvidenceSchemaMigrator.migrate(dict(v1), target_version="v2")
    twice = EvidenceSchemaMigrator.migrate(dict(once), target_version="v2")

    assert once.get("schema_version") == "v2", (
        "a migrated envelope must record the version it was migrated to, or the migration cannot "
        "detect that it has already run"
    )
    assert once == twice, (
        "migration is not idempotent: the second call changed the envelope. The likely cause is a "
        "missing version stamp, which makes the early return unreachable."
    )


def test_migration_is_a_no_op_for_an_already_current_envelope():
    """The early return that the version stamp exists to enable."""
    current = {"evidence_id": "e-2", "engine": "noesis", "claim": "c",
               "evidence_type": "relational_reasoning", "confidence": 0.5, "schema_version": "v2"}
    snapshot = dict(current)
    out = EvidenceSchemaMigrator.migrate(current, target_version="v2")
    assert out is current, "an already-current envelope must be returned unchanged, not rebuilt"
    assert current == snapshot


# --- Generalized object-identity guard over every contract type the package exports ---

# Each row: (name-for-error-message, package-module, home-module, attribute-name)
# The package module is where consumers import from (`abraxas.evidence`).
# The home module is the single canonical definition.
# Adding one line here catches a new duplicate.
_CONTRACT_TYPE_TABLE = [
    ("EvidenceEnvelope",  "abraxas.evidence",             "abraxas.evidence.contract",  "EvidenceEnvelope"),
    ("EvidenceProvider",  "abraxas.evidence",             "abraxas.evidence.provider",  "EvidenceProvider"),
    ("RelationStep",      "abraxas.evidence",             "abraxas.evidence.contract",  "RelationStep"),
    ("CandidateOutput",   "abraxas.evidence",             "abraxas.evidence.contract",  "CandidateOutput"),
    ("EvidenceType",      "abraxas.evidence",             "abraxas.evidence.contract",  "EvidenceType"),
    ("Decision",          "abraxas.evidence",             "abraxas.evidence.contract",  "Decision"),
]


def _resolve(pkg_module: str, home_module: str, attr: str):
    """Import and return (package_copy, home_copy) for a single type."""
    import importlib
    pkg = importlib.import_module(pkg_module)
    home = importlib.import_module(home_module)
    return getattr(pkg, attr), getattr(home, attr)


@pytest.mark.parametrize("name, pkg_mod, home_mod, attr", _CONTRACT_TYPE_TABLE)
def test_contract_type_has_a_single_canonical_home(name, pkg_mod, home_mod, attr):
    """Every contract type exported by the package must be the SAME OBJECT
    as its single canonical home -- not merely equal, not structurally similar.

    This guard catches a duplicate definition in the package __init__ before
    any consumer is silently given the wrong type.
    """
    pkg_copy, home_copy = _resolve(pkg_mod, home_mod, attr)
    assert pkg_copy is home_copy, (
        f"{name} must be single-homed. "
        f"The package {pkg_mod} must re-export the canonical {attr} "
        f"from {home_mod}, not redefine it. "
        f"Got {pkg_copy!r} is not {home_copy!r}."
    )