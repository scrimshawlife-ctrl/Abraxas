from __future__ import annotations

from abx.human_factors.actionGrammar import build_action_surfaces, detect_action_grammar_drift
from abx.human_factors.summaryGrammar import build_summary_surfaces, detect_redundant_summary_surfaces
from abx.human_factors.warningGrammar import build_warning_records, detect_inconsistent_warning_vocabulary
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_warning_action_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "WarningActionAudit.v1",
        "artifactId": "warning-action-audit",
        "warnings": [x.__dict__ for x in build_warning_records()],
        "summaries": [x.__dict__ for x in build_summary_surfaces()],
        "actions": [x.__dict__ for x in build_action_surfaces()],
        "warningVocabularyConflicts": detect_inconsistent_warning_vocabulary(),
        "redundantSummaries": detect_redundant_summary_surfaces(),
        "actionGrammarDrift": detect_action_grammar_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
