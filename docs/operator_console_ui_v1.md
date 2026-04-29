# PATCH-004 Operator Console UI v1

## Archetype Trend Timeline
- schema: `ArchetypeTrendTimeline.v1`
- trend row schema: `ArchetypeTrend.v1`
- mode: `LOCAL_BROWSER_ARCHETYPE_TIMELINE_ONLY`
- controls:
  - `Load Archetype Reports`
  - `Build Archetype Trend Timeline`
  - `Export Archetype Trend Timeline JSON`

## Input sources
- `CausalChainArchetypeReport.v1`
- `ConsoleStateExportBundle.v1` containing archetype report data

## Trend outputs
- `input_report_count`
- `input_archetype_count`
- `timeline_point_count`
- `dominant_archetype_id`
- `dominant_archetype_family`
- `trend_summary`
- `rising_count`
- `falling_count`
- `stable_count`
- `volatile_count`
- `critical_trend_count`
- `archetype_trends`
- `timeline_points`
- `trend_strength`
- `confidence_delta`

## Status labels
- `RISING`
- `FALLING`
- `STABLE`
- `VOLATILE`
- `NOT_COMPUTABLE`

## Boundaries
- `repair_allowed: false`
- archetype timeline does not repair anomalies
- archetype timeline does not alter archetypes
- archetype timeline does not execute repairs
- archetype timeline is observational only
- `execution_allowed: false`
- `runtime_mutation_allowed: false`
- `auto_apply_allowed: false`

## Determinism and local-only behavior
- report sorting: `created_at asc`, `report_id asc`
- point sorting: `created_at asc`, `archetype_id asc`, `point_id asc`
- trend sorting: `RISING, VOLATILE, STABLE, FALLING, NOT_COMPUTABLE`, then counts/id
- confidence and ratio rendering use `toFixed(4)`
- local APIs only: `FileReader`, `JSON.parse`, `Blob`, `URL.createObjectURL`
- no backend `fetch`, `XMLHttpRequest`, `navigator.sendBeacon`
- no execute/apply/merge/mutate controls

## Archetype Drift Forecast
- schema: `ArchetypeDriftForecast.v1`
- item schema: `ArchetypeDriftForecastItem.v1`
- mode: `LOCAL_BROWSER_ARCHETYPE_FORECAST_ONLY`
- controls:
  - `Build Archetype Drift Forecast`
  - `Export Archetype Drift Forecast JSON`

## Forecast outputs
- `source_timeline_id`
- `input_trend_count`
- `forecast_horizon`
- `likely_next_dominant_archetype_id`
- `likely_next_dominant_family`
- `forecast_confidence`
- `forecast_status`
- `warning_surface`
- `critical_pressure_expected`
- `volatile_archetype_present`
- `rising_safety_or_integrity`
- `forecast_items`
- `forecast_pressure_score`
- `predicted_next_state`
- `recommended_operator_attention`

## Forecast status labels
- `NEXT_RUN`
- `NEXT_3_RUNS`
- `NO_DATA`
- `LOW_CONFIDENCE`
- `WATCH`
- `ELEVATED`
- `CRITICAL`
- `CRITICAL_PRESSURE`

## Forecast boundaries
- `repair_allowed: false`
- archetype forecast does not repair anomalies
- archetype forecast does not alter archetypes
- archetype forecast does not execute repairs
- archetype forecast is observational only
- forecast does not promote action
- `execution_allowed: false`
- `runtime_mutation_allowed: false`
- `auto_apply_allowed: false`

## Archetype Warning Digest
- schema: `ArchetypeWarningDigest.v1`
- mode: `LOCAL_BROWSER_WARNING_DIGEST_ONLY`
- controls:
  - `Build Archetype Warning Digest`
  - `Export Archetype Warning Digest JSON`
- outputs:
  - `dominant_concern`
  - `alert_level`
  - `operator_attention_summary`
  - `recommended_review_only`
  - `warning_digest_items`
- boundaries:
  - digest does not repair anomalies
  - digest does not alter forecasts
  - digest does not execute repairs
  - digest is observational only
  - `repair_allowed: false`

## Warning Digest History + Escalation Tracker
- schema: `WarningDigestHistoryTracker.v1`
- point schema: `WarningHistoryPoint.v1`
- track schema: `ConcernTrack.v1`
- mode: `LOCAL_BROWSER_WARNING_HISTORY_ONLY`
- controls:
  - `Load Warning Digests`
  - `Build Warning History Tracker`
  - `Export Warning History Tracker JSON`
- outputs:
  - `input_digest_count`
  - `history_point_count`
  - `dominant_concern`
  - `latest_alert_level`
  - `escalation_status`
  - `unresolved_concern_count`
  - `false_alarm_pressure`
  - `tracker_summary`
  - `history_points`
  - `concern_tracks`
- status labels:
  - `NONE`, `WATCH`, `ELEVATED`, `CRITICAL`
  - `NO_DATA`, `STABLE`, `ESCALATING`, `DE_ESCALATING`, `VOLATILE`, `PERSISTENT_CRITICAL`
  - `NEW`, `PERSISTENT`, `RESOLVED`
- boundaries:
  - warning history does not repair anomalies
  - warning history does not alter digests
  - warning history does not execute repairs
  - warning history is observational only
  - escalation tracker does not promote action
  - `repair_allowed: false`

## Warning Resolution Ledger
- schemas: `WarningResolutionLedger.v1`, `WarningResolutionEntry.v1`, `WarningResolutionAnalytics.v1`
- mode: `LOCAL_BROWSER_WARNING_RESOLUTION_ONLY`
- controls:
  - `Record Warning Resolution Locally`
  - `Preview Warning Resolution Entry`
  - `Export Warning Resolution Ledger JSON`
  - `Import Warning Resolution Ledger JSON`
- decision scope: `WARNING_RESOLUTION_ONLY`
- analytics:
  - `resolution_rate`
  - `ignored_rate`
  - `repeat_rate`
  - `false_positive_rate`
  - `warning_trust_score`
  - `unresolved_pressure_decay`
  - `resolution_bottleneck_signal`
  - `dominant_concern_resolution_profile`
- status labels:
  - `RESOLVED`, `IGNORED`, `REPEATED`, `FALSE_POSITIVE`, `NOT_COMPUTABLE`
  - `HEALTHY_RESOLUTION`, `REPEAT_PRESSURE`, `IGNORED_PRESSURE`, `FALSE_ALARM_PRESSURE`, `MIXED`
- boundaries:
  - warning resolution ledger does not repair anomalies
  - warning resolution ledger does not alter warning history
  - warning resolution ledger does not execute repairs
  - warning resolution ledger is observational only
  - resolution records do not promote action
  - `repair_allowed: false`

## Warning Trust Calibration
- schemas: `WarningTrustCalibration.v1`, `WarningTrustProfile.v1`
- mode: `LOCAL_BROWSER_WARNING_TRUST_ONLY`
- controls:
  - `Build Warning Trust Calibration`
  - `Export Warning Trust Calibration JSON`
- outputs:
  - `input_warning_count`, `input_resolution_count`, `matched_count`, `unmatched_warning_count`
  - `resolution_rate`, `repeat_rate`, `false_positive_rate`, `ignored_rate`, `warning_trust_score`
  - `calibration_status`, `family_trust_profiles`, `archetype_trust_profiles`, `calibration_summary`
- labels:
  - `HIGH_TRUST`, `LOW_TRUST`, `FALSE_ALARM_HEAVY`, `REPEAT_PRESSURE`, `IGNORED_PRESSURE`
  - `CALIBRATED`, `UNDER_SAMPLED`, `NO_DATA`, `MIXED`
- boundaries:
  - warning trust calibration does not suppress warnings
  - warning trust calibration does not repair anomalies
  - warning trust calibration does not alter warning history
  - warning trust calibration does not execute repairs
  - warning trust calibration is observational only
  - `suppression_allowed: false`

## PATCH-004 Warning Intelligence Closure Batch
- schemas:
  - `WarningReliabilityTimeline.v1`
  - `WarningReliabilityMatrix.v1`
  - `WarningTrustDigest.v1`
  - `WarningCalibrationExportBundle.v1`
  - `WarningIntelligenceClosureReport.v1`
- controls:
  - `Build Warning Reliability Timeline` / `Export Warning Reliability Timeline JSON`
  - `Build Warning Reliability Matrix` / `Export Warning Reliability Matrix JSON`
  - `Build Warning Trust Digest` / `Export Warning Trust Digest JSON`
  - `Preview Warning Calibration Bundle` / `Export Warning Calibration Bundle JSON` / `Import Warning Calibration Bundle JSON`
  - `Build Warning Intelligence Closure Report` / `Export Warning Intelligence Closure Report JSON`
- boundaries:
  - warning intelligence closure does not suppress warnings
  - warning intelligence closure does not repair anomalies
  - warning intelligence closure does not execute repairs
  - warning intelligence closure is observational only
  - `suppression_allowed: false`

## PATCH004 Cross-Domain Signal Fusion Batch
- schemas:
  - `CrossDomainSignalRegistry.v1`
  - `CrossDomainConflictReport.v1`
  - `CrossDomainAlignmentScore.v1`
  - `CrossDomainMetaConfidence.v1`
  - `CrossDomainFusionDigest.v1`
  - `CrossDomainFusionBundle.v1`
- conflicts:
  - `WARNING_TRUST_CONFLICT`
  - `ANOMALY_WARNING_CONFLICT`
  - `OPERATOR_MODEL_CONFLICT`
  - `INTEGRITY_STATE_CONFLICT`
  - `FORECAST_RESOLUTION_CONFLICT`
- statuses:
  - `LOW_ALIGNMENT`, `MIXED_ALIGNMENT`, `HIGH_ALIGNMENT`, `CONFLICT_HEAVY`
  - `BLOCKED_BY_INTEGRITY`, `BLOCKED_BY_CONFLICT`
  - `ALIGNED`, `MIXED`, `BLOCKED`
- boundaries:
  - cross-domain fusion does not repair anomalies
  - cross-domain fusion does not suppress warnings
  - cross-domain fusion does not execute repairs
  - cross-domain fusion does not alter source domains
  - cross-domain fusion is observational only

## PATCH004 Fusion Meta-Learning Batch
- schemas:
  - `FusionOutcomeLedger.v1`
  - `FusionOutcomeEntry.v1`
  - `FusionDriftTimeline.v1`
  - `FusionDriftPoint.v1`
  - `FusionConflictRecurrenceMatrix.v1`
  - `FusionConflictRecurrenceRow.v1`
  - `MetaConfidenceCalibration.v1`
  - `MetaConfidenceCalibrationProfile.v1`
  - `FusionLearningDigest.v1`
  - `FusionLearningExportBundle.v1`
  - `FusionLearningClosureReport.v1`
- labels:
  - `CONFIRMED`, `PARTIAL`, `MISALIGNED`, `FALSE_SIGNAL`
  - `RISING`, `FALLING`, `STABLE`, `VOLATILE`
  - `CALIBRATED`, `OVERCONFIDENT`, `UNDERCONFIDENT`, `LOW_SAMPLE`
  - `LEARNING_STABLE`, `LEARNING_DEGRADED`, `CONFLICT_RECURRING`, `CONFIDENCE_MISCALIBRATED`
  - `CLOSED_OBSERVATIONAL_LOOP`, `UNDER_INSTRUMENTED`, `REVIEW_REQUIRED`
- boundaries:
  - fusion learning does not repair anomalies
  - fusion learning does not suppress warnings
  - fusion learning does not execute repairs
  - fusion learning does not alter source domains
  - fusion learning is observational only
  - fusion learning does not promote action
