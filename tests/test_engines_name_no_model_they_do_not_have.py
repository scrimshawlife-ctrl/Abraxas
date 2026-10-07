"""An engine must report the inference path that actually ran -- never a model it does not have.

The refactor this guards: engines used to hand-write their `model_identity` and their default inference. Oracle
shipped `"oracle-model-v1"` and a `_default_oracle_inference` that built a `coherence_score` from word counts
(`+= 0.1  # Sweet spot for coherence`) and published it as the envelope's **confidence**. Athanor shipped
`"lora-out-transfer-001-t1/checkpoint-48"` -- a checkpoint that is not loaded, is not in the repository, and
whose training is not reproducible from here.

Both are the same defect: a provenance field naming a model that produced nothing. It is worse than an empty
field, because it reads as evidence of *which model* read the claim. Downstream, that is what makes a fabricated
number look like a measurement.

The rule now: wherever an engine needs a model, it goes through `abraxas.evidence.adapters.model_agnostic`, and
it reports that adapter's identity -- `model-agnostic/<model>` when an endpoint is configured, and
`model-agnostic/offline-deterministic` when none is. A custom model may be injected, and then its own identity
is reported. What may not happen is an engine inventing a name.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ABRAXAS = Path(__file__).resolve().parents[1]

# Engine modules that produce evidence. `contract.py` is included because it carried a model identity in a
# default provenance value -- the same defect in a place nobody would think to look for a model.
ENGINE_MODULES = [
    "abraxas/evidence/adapters/oracle.py",
    "abraxas/evidence/adapters/cypher.py",
    "abraxas/evidence/adapters/model_agnostic.py",
    "abraxas/evidence/provider.py",
    "abraxas/evidence/contract.py",
]

# Shapes that name a specific checkpoint or model artifact. A model-agnostic adapter names a PATH
# (`model-agnostic/...`) or an endpoint model id, never a training run's output directory.
FAKE_MODEL_PATTERNS = [
    (re.compile(r"""["'][^"']*\blora-out-[^"']*["']"""), "a training run's output directory (lora-out-...)"),
    (re.compile(r"""["'][^"']*/checkpoint-\d+[^"']*["']"""), "a checkpoint path"),
    (re.compile(r"""["'][\w.-]+-model-v\d+["']"""), "a hand-written model version string"),
]

# Identity strings that ARE legitimate: the adapter's own vocabulary.
ALLOWED_IDENTITY_PATTERNS = [
    re.compile(r"^model-agnostic/"),
    re.compile(r"^custom/"),
    re.compile(r"^unspecified$"),
    re.compile(r"^test[/-]"),
    # A test double that calls itself a mock claims nothing false. `MockEvidenceProvider` in provider.py
    # reports `mock-model-v1`, which is exactly what it is -- the defect this guard hunts is a name that
    # reads as a real model, and "mock" cannot be mistaken for one.
    re.compile(r"^mock"),
]


def _docstring_lines(tree: "ast.Module") -> set[int]:
    """Line numbers occupied by docstrings, which are prose and may legitimately quote the old defects.

    Without this the scan flags its own explanation: `identity_of` documents the bug by naming it, and a guard
    that forbids naming a defect forbids documenting it.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            if node.end_lineno:
                lines.update(range(node.lineno, node.end_lineno + 1))
    return lines


def _scan(text: str) -> list[tuple[int, str, str]]:
    """Return (line_number, matched_text, why) for every disallowed literal in executable code.

    Accepts fragments as well as whole files: the counterfactual test feeds it single lines, which do not
    parse as modules, and a scan that raises on a snippet cannot be tested on one.
    """
    try:
        prose = _docstring_lines(ast.parse(text))
    except SyntaxError:
        prose = set()
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # Comments and docstrings describe the history; only code counts.
        if stripped.startswith("#") or lineno in prose:
            continue
        for pattern, why in FAKE_MODEL_PATTERNS:
            for match in pattern.finditer(line):
                candidate = match.group(0).strip("\"'")
                if any(a.match(candidate) for a in ALLOWED_IDENTITY_PATTERNS):
                    continue
                findings.append((lineno, match.group(0), why))
    return findings


def test_no_engine_module_names_a_model_it_does_not_have() -> None:
    """No engine module may contain a literal naming a checkpoint or a bespoke model version."""
    problems = []
    for rel in ENGINE_MODULES:
        path = ABRAXAS / rel
        assert path.exists(), f"{rel} is missing; this guard's file list is stale"
        for lineno, text, why in _scan(path.read_text()):
            problems.append(f"{rel}:{lineno}: {text} ({why})")

    assert not problems, (
        "an engine names a model identity it does not have:\n  "
        + "\n  ".join(problems)
        + "\n\nUse abraxas.evidence.adapters.model_agnostic.identity_of(inference), which reports the path "
        "that actually ran. A provenance field naming an imaginary model reads as evidence of which model "
        "produced the reading."
    )


def test_the_scan_actually_catches_a_fake_identity() -> None:
    """Counterfactual: the guard must fail on the exact strings this refactor removed.

    A guard nobody has seen fail is not known to be a guard. These are the literals from the two defects this
    module documents, plus a near-miss that must NOT be flagged.
    """
    should_flag = [
        '        return "oracle-model-v1"',
        '            return "lora-out-transfer-001-t1/checkpoint-48"',
        'provenance=provenance or {"source": "lora-out-transfer-001-t1/checkpoint-48"}',
        '        ident = "merged-nemotron-ath/checkpoint-500"',
    ]
    for line in should_flag:
        assert _scan(line), f"the scan missed a fake identity: {line}"

    should_not_flag = [
        '    return "model-agnostic/offline-deterministic"',
        '        return identity_of(inference_engine)',
        '    OFFLINE_IDENTITY = "model-agnostic/offline-deterministic"',
        '    ident = getattr(inference, "model_identity", None)',
    ]
    for line in should_not_flag:
        assert not _scan(line), f"the scan flagged a legitimate line: {line}"


@pytest.mark.parametrize("engine", ["oracle", "athanor"])
def test_an_unconfigured_engine_reports_the_offline_path(engine: str, monkeypatch) -> None:
    """With no endpoint configured, an inference-backed engine says which path ran and claims no model."""
    from abraxas.evidence.adapters.model_agnostic import OFFLINE_IDENTITY, is_configured

    monkeypatch.delenv("ABX_INFERENCE_BASE_URL", raising=False)
    monkeypatch.delenv("ABX_INFERENCE_MODEL", raising=False)
    assert not is_configured(), "this test covers the offline path; an endpoint is configured"

    if engine == "oracle":
        from abraxas.evidence.adapters.oracle import create_oracle_adapter

        provider = create_oracle_adapter()
    else:
        from abraxas.evidence.provider import create_athanor_adapter

        provider = create_athanor_adapter()

    envelope = provider.produce_evidence(
        request_id=f"guard-{engine}", claim="A claim to read.", context={"domain": "test"}
    )

    assert provider.get_model_identity() == OFFLINE_IDENTITY, (
        f"{engine} reports {provider.get_model_identity()!r}; the configured path is the offline one"
    )
    assert envelope.provenance.get("inference") == "offline-deterministic", envelope.provenance


def test_an_injected_model_is_reported_as_itself_or_not_at_all() -> None:
    """An injected custom model keeps its identity; an anonymous callable is not given one."""
    from abraxas.evidence.adapters.model_agnostic import identity_of

    def custom(claim, context):
        return {}

    assert identity_of(custom) == "custom/unlabelled"

    setattr(custom, "model_identity", "my-org/my-model")
    assert identity_of(custom) == "my-org/my-model"
