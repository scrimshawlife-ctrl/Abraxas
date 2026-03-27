from __future__ import annotations

from abx.explain.explainIrCoverage import build_explain_coverage
from abx.explain.explainOwnership import explain_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def run_explain_ir_audit() -> dict[str, object]:
    coverage = [x.__dict__ for x in build_explain_coverage()]
    owners = explain_ownership()
    payload = {"coverage": coverage, "owners": owners}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "ExplainIRAudit.v1",
        "artifactId": "explain-ir-audit",
        "coverage": coverage,
        "owners": owners,
        "auditHash": digest,
    }
