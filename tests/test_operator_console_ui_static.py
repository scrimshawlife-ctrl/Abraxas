from pathlib import Path

UI_PATH = Path('webpanel/static/operator_console_patch004.html')
DOC_PATH = Path('docs/operator_console_ui_v1.md')


def test_archetype_timeline_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Archetype Trend Timeline',
        'ArchetypeTrendTimeline.v1',
        'ArchetypeTrend.v1',
        'LOCAL_BROWSER_ARCHETYPE_TIMELINE_ONLY',
        'Load Archetype Reports',
        'Build Archetype Trend Timeline',
        'Export Archetype Trend Timeline JSON',
        'input_report_count',
        'input_archetype_count',
        'timeline_point_count',
        'dominant_archetype_id',
        'dominant_archetype_family',
        'trend_summary',
        'rising_count',
        'falling_count',
        'stable_count',
        'volatile_count',
        'critical_trend_count',
        'archetype_trends',
        'timeline_points',
        'RISING',
        'FALLING',
        'STABLE',
        'VOLATILE',
        'NOT_COMPUTABLE',
        'trend_strength',
        'confidence_delta',
        'archetype timeline does not repair anomalies',
        'archetype timeline does not alter archetypes',
        'archetype timeline does not execute repairs',
        'archetype timeline is observational only',
        'repair_allowed: false',
        'FileReader',
        'JSON.parse',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_archetype_forecast_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Archetype Drift Forecast',
        'ArchetypeDriftForecast.v1',
        'ArchetypeDriftForecastItem.v1',
        'LOCAL_BROWSER_ARCHETYPE_FORECAST_ONLY',
        'Build Archetype Drift Forecast',
        'Export Archetype Drift Forecast JSON',
        'source_timeline_id',
        'input_trend_count',
        'forecast_horizon',
        'likely_next_dominant_archetype_id',
        'likely_next_dominant_family',
        'forecast_confidence',
        'forecast_status',
        'warning_surface',
        'critical_pressure_expected',
        'volatile_archetype_present',
        'rising_safety_or_integrity',
        'forecast_items',
        'forecast_pressure_score',
        'predicted_next_state',
        'recommended_operator_attention',
        'NEXT_RUN',
        'NEXT_3_RUNS',
        'NO_DATA',
        'LOW_CONFIDENCE',
        'WATCH',
        'ELEVATED',
        'CRITICAL',
        'CRITICAL_PRESSURE',
        'archetype forecast does not repair anomalies',
        'archetype forecast does not alter archetypes',
        'archetype forecast does not execute repairs',
        'archetype forecast is observational only',
        'forecast does not promote action',
        'repair_allowed: false',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_archetype_warning_digest_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Archetype Warning Digest',
        'ArchetypeWarningDigest.v1',
        'LOCAL_BROWSER_WARNING_DIGEST_ONLY',
        'Build Archetype Warning Digest',
        'Export Archetype Warning Digest JSON',
        'dominant_concern',
        'alert_level',
        'operator_attention_summary',
        'recommended_review_only',
        'warning_digest_items',
        'digest does not repair anomalies',
        'digest does not alter forecasts',
        'digest does not execute repairs',
        'digest is observational only',
        'repair_allowed: false',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_warning_history_tracker_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Warning Digest History + Escalation Tracker',
        'WarningDigestHistoryTracker.v1',
        'WarningHistoryPoint.v1',
        'ConcernTrack.v1',
        'LOCAL_BROWSER_WARNING_HISTORY_ONLY',
        'Load Warning Digests',
        'Build Warning History Tracker',
        'Export Warning History Tracker JSON',
        'input_digest_count',
        'history_point_count',
        'dominant_concern',
        'latest_alert_level',
        'escalation_status',
        'unresolved_concern_count',
        'false_alarm_pressure',
        'tracker_summary',
        'history_points',
        'concern_tracks',
        'NONE',
        'WATCH',
        'ELEVATED',
        'CRITICAL',
        'NO_DATA',
        'STABLE',
        'ESCALATING',
        'DE_ESCALATING',
        'VOLATILE',
        'PERSISTENT_CRITICAL',
        'NEW',
        'PERSISTENT',
        'RESOLVED',
        'warning history does not repair anomalies',
        'warning history does not alter digests',
        'warning history does not execute repairs',
        'warning history is observational only',
        'escalation tracker does not promote action',
        'repair_allowed: false',
        'FileReader',
        'JSON.parse',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_warning_resolution_ledger_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Warning Resolution Ledger',
        'WarningResolutionLedger.v1',
        'WarningResolutionEntry.v1',
        'WarningResolutionAnalytics.v1',
        'LOCAL_BROWSER_WARNING_RESOLUTION_ONLY',
        'Record Warning Resolution Locally',
        'Preview Warning Resolution Entry',
        'Export Warning Resolution Ledger JSON',
        'Import Warning Resolution Ledger JSON',
        'WARNING_RESOLUTION_ONLY',
        'RESOLVED',
        'IGNORED',
        'REPEATED',
        'FALSE_POSITIVE',
        'NOT_COMPUTABLE',
        'resolution_rate',
        'ignored_rate',
        'repeat_rate',
        'false_positive_rate',
        'warning_trust_score',
        'unresolved_pressure_decay',
        'resolution_bottleneck_signal',
        'HEALTHY_RESOLUTION',
        'REPEAT_PRESSURE',
        'IGNORED_PRESSURE',
        'FALSE_ALARM_PRESSURE',
        'MIXED',
        'BLOCKED DATA — UNSAFE ARTIFACT',
        'warning resolution ledger does not repair anomalies',
        'warning resolution ledger does not alter warning history',
        'warning resolution ledger does not execute repairs',
        'warning resolution ledger is observational only',
        'resolution records do not promote action',
        'repair_allowed: false',
        'FileReader',
        'JSON.parse',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_warning_trust_calibration_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'Warning Trust Calibration',
        'WarningTrustCalibration.v1',
        'WarningTrustProfile.v1',
        'LOCAL_BROWSER_WARNING_TRUST_ONLY',
        'Build Warning Trust Calibration',
        'Export Warning Trust Calibration JSON',
        'input_warning_count',
        'input_resolution_count',
        'matched_count',
        'unmatched_warning_count',
        'resolution_rate',
        'repeat_rate',
        'false_positive_rate',
        'ignored_rate',
        'warning_trust_score',
        'calibration_status',
        'family_trust_profiles',
        'archetype_trust_profiles',
        'calibration_summary',
        'HIGH_TRUST',
        'LOW_TRUST',
        'FALSE_ALARM_HEAVY',
        'REPEAT_PRESSURE',
        'IGNORED_PRESSURE',
        'CALIBRATED',
        'UNDER_SAMPLED',
        'NO_DATA',
        'MIXED',
        'suppression_allowed: false',
        'warning trust calibration does not suppress warnings',
        'warning trust calibration does not repair anomalies',
        'warning trust calibration does not alter warning history',
        'warning trust calibration does not execute repairs',
        'warning trust calibration is observational only',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_warning_intelligence_closure_batch_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'WarningReliabilityTimeline.v1',
        'WarningReliabilityMatrix.v1',
        'WarningTrustDigest.v1',
        'WarningCalibrationExportBundle.v1',
        'WarningIntelligenceClosureReport.v1',
        'Warning Reliability Timeline',
        'Build Warning Reliability Timeline',
        'Export Warning Reliability Timeline JSON',
        'Warning Family / Archetype Reliability Matrix',
        'Build Warning Reliability Matrix',
        'Export Warning Reliability Matrix JSON',
        'Warning Trust Digest',
        'Build Warning Trust Digest',
        'Export Warning Trust Digest JSON',
        'Warning Calibration Export Bundle',
        'Preview Warning Calibration Bundle',
        'Export Warning Calibration Bundle JSON',
        'Import Warning Calibration Bundle JSON',
        'Warning Intelligence Closure Report',
        'Build Warning Intelligence Closure Report',
        'Export Warning Intelligence Closure Report JSON',
        'CLOSED_OBSERVATIONAL_LOOP',
        'UNDER_INSTRUMENTED',
        'REVIEW_REQUIRED',
        'BLOCKED DATA — UNSAFE ARTIFACT',
        'warning intelligence closure does not suppress warnings',
        'warning intelligence closure does not repair anomalies',
        'warning intelligence closure does not execute repairs',
        'warning intelligence closure is observational only',
        'suppression_allowed: false',
        'Blob',
        'URL.createObjectURL',
        'FileReader',
        'JSON.parse',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_cross_domain_signal_fusion_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'CrossDomainSignalRegistry.v1',
        'CrossDomainConflictReport.v1',
        'CrossDomainAlignmentScore.v1',
        'CrossDomainMetaConfidence.v1',
        'CrossDomainFusionDigest.v1',
        'CrossDomainFusionBundle.v1',
        'WARNING_TRUST_CONFLICT',
        'ANOMALY_WARNING_CONFLICT',
        'OPERATOR_MODEL_CONFLICT',
        'INTEGRITY_STATE_CONFLICT',
        'FORECAST_RESOLUTION_CONFLICT',
        'LOW_ALIGNMENT',
        'MIXED_ALIGNMENT',
        'HIGH_ALIGNMENT',
        'CONFLICT_HEAVY',
        'BLOCKED_BY_INTEGRITY',
        'BLOCKED_BY_CONFLICT',
        'ALIGNED',
        'MIXED',
        'BLOCKED',
        'cross-domain fusion does not repair anomalies',
        'cross-domain fusion does not suppress warnings',
        'cross-domain fusion does not execute repairs',
        'cross-domain fusion does not alter source domains',
        'cross-domain fusion is observational only',
        'FileReader',
        'JSON.parse',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_fusion_meta_learning_markers_present() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    doc = DOC_PATH.read_text(encoding='utf-8')
    merged = f"{ui}\n{doc}"
    required = [
        'FusionOutcomeLedger.v1',
        'FusionOutcomeEntry.v1',
        'FusionDriftTimeline.v1',
        'FusionDriftPoint.v1',
        'FusionConflictRecurrenceMatrix.v1',
        'FusionConflictRecurrenceRow.v1',
        'MetaConfidenceCalibration.v1',
        'MetaConfidenceCalibrationProfile.v1',
        'FusionLearningDigest.v1',
        'FusionLearningExportBundle.v1',
        'FusionLearningClosureReport.v1',
        'CONFIRMED',
        'PARTIAL',
        'MISALIGNED',
        'FALSE_SIGNAL',
        'RISING',
        'FALLING',
        'STABLE',
        'VOLATILE',
        'WARNING_TRUST_CONFLICT',
        'ANOMALY_WARNING_CONFLICT',
        'OPERATOR_MODEL_CONFLICT',
        'INTEGRITY_STATE_CONFLICT',
        'FORECAST_RESOLUTION_CONFLICT',
        'CALIBRATED',
        'OVERCONFIDENT',
        'UNDERCONFIDENT',
        'LOW_SAMPLE',
        'LEARNING_STABLE',
        'LEARNING_DEGRADED',
        'CONFLICT_RECURRING',
        'CONFIDENCE_MISCALIBRATED',
        'CLOSED_OBSERVATIONAL_LOOP',
        'UNDER_INSTRUMENTED',
        'REVIEW_REQUIRED',
        'fusion learning does not repair anomalies',
        'fusion learning does not suppress warnings',
        'fusion learning does not execute repairs',
        'fusion learning does not alter source domains',
        'fusion learning is observational only',
        'fusion learning does not promote action',
        'FileReader',
        'JSON.parse',
        'Blob',
        'URL.createObjectURL',
        'toFixed(4)',
    ]
    for marker in required:
        assert marker in merged


def test_no_backend_calls_and_forbidden_controls() -> None:
    ui = UI_PATH.read_text(encoding='utf-8')
    assert 'fetch(' not in ui
    assert 'XMLHttpRequest' not in ui
    assert 'navigator.sendBeacon' not in ui
    forbidden = ['>Execute<', '>Apply<', '>Merge<', '>Mutate<', 'Run Repair', 'Auto-Apply']
    for marker in forbidden:
        assert marker not in ui
