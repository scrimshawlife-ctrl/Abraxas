from types import SimpleNamespace

from abraxas.core.provenance import Provenance
from abraxas.narratives.workflows import build_resonance_narrative_artifacts
from abraxas.phase.coupling import DriftResonanceCoupling
from abraxas.phase.detector import PhaseAlignment
from abraxas.phase.early_warning import PhaseTransitionWarning


def _prov(seed: str) -> Provenance:
    return Provenance(
        run_id=f"RUN-{seed}",
        started_at_utc="2026-01-01T00:00:00Z",
        inputs_hash=seed * 64,
        config_hash=(seed.upper()) * 64,
    )


def _oracle_output() -> SimpleNamespace:
    return SimpleNamespace(
        compression=SimpleNamespace(
            domain="politics",
            compressed_tokens=["election", "trust"],
            domain_signals=["ideology_left"],
            transparency_score=0.62,
            affect_direction="negative",
        ),
        forecast=SimpleNamespace(
            phase_transitions=[{"domain": "politics", "to": "emergence"}],
            weather_trajectory="compression_accelerating",
            memetic_pressure=0.55,
            resonance_score=0.73,
        ),
    )


def _alignment() -> PhaseAlignment:
    return PhaseAlignment(
        alignment_id="ALIGN-1",
        timestamp_utc="2026-01-01T00:00:00Z",
        aligned_phase="seed",
        domains=("media", "politics"),
        alignment_strength=0.76,
        tokens_in_phase={"media": ["signal"], "politics": ["trust", "vote"]},
        provenance=_prov("a"),
    )


def _warning(warning_id: str = "WARN-1") -> PhaseTransitionWarning:
    return PhaseTransitionWarning(
        warning_id=warning_id,
        domain="politics",
        current_phase="seed",
        predicted_phase="emergence",
        estimated_hours=16.0,
        confidence=0.71,
        trigger_signals=("tau_velocity",),
        evidence={"observation_count": 9},
        issued_utc="2026-01-01T00:00:00Z",
        provenance=_prov("b"),
    )


def _coupling() -> DriftResonanceCoupling:
    return DriftResonanceCoupling(
        coupling_id="COUPLING-1",
        timestamp_utc="2026-01-01T00:00:00Z",
        domains=("media", "politics"),
        drift_strength=0.8,
        resonance_strength=0.75,
        coupling_strength=0.6,
        cascade_risk="HIGH",
        tokens_drifting={"media": ["narrative"], "politics": ["trust"]},
        evidence={"coupled_domain_count": 2},
        provenance=_prov("c"),
    )


def test_build_resonance_narrative_artifacts_generates_full_artifact_set(tmp_path):
    result = build_resonance_narrative_artifacts(
        oracle_output=_oracle_output(),
        alignments=[_alignment()],
        warnings=[_warning()],
        couplings=[_coupling()],
        run_id="WF-1",
        output_dir=tmp_path,
    )

    # 1 alignment + 1 warning + 1 coupling
    assert len(result.narratives) == 3

    # 3 narrative artifacts + 1 comprehensive report artifact
    assert len(result.artifacts) == 4
    assert all(a.package_hash for a in result.artifacts)
    report_artifact = [a for a in result.artifacts if a.artifact_type == "comprehensive_report"][0]
    assert report_artifact.narrative_metadata["narrative_types"] == sorted(
        report_artifact.narrative_metadata["narrative_types"]
    )

    # all artifacts exported in both formats by default
    assert len(result.exported_paths) == 4
    for _, paths in result.exported_paths.items():
        assert "json" in paths
        assert "md" in paths
        assert paths["json"].exists()
        assert paths["md"].exists()



def test_build_resonance_narrative_artifacts_without_export_keeps_paths_empty():
    result = build_resonance_narrative_artifacts(
        oracle_output=_oracle_output(),
        alignments=[_alignment()],
        warnings=[_warning()],
        couplings=[_coupling()],
        run_id="WF-2",
    )

    assert len(result.narratives) == 3
    assert len(result.artifacts) == 4
    assert result.exported_paths == {}
    assert "# Abraxas Intelligence Report" in result.report


def test_build_resonance_narrative_artifacts_uses_source_stable_artifact_ids(tmp_path):
    result = build_resonance_narrative_artifacts(
        oracle_output=_oracle_output(),
        alignments=[_alignment()],
        warnings=[_warning("WARN-A"), _warning("WARN-B")],
        couplings=[_coupling()],
        run_id="WF-3",
        output_dir=tmp_path,
    )

    assert len(result.narratives) == 4
    assert len(result.artifacts) == 5
    assert len(result.exported_paths) == 5
    assert any("WARN-A" in artifact.artifact_id for artifact in result.artifacts)
    assert any("WARN-B" in artifact.artifact_id for artifact in result.artifacts)


def test_build_resonance_narrative_artifacts_handles_duplicate_ids_and_sanitizes_filenames(tmp_path):
    result = build_resonance_narrative_artifacts(
        oracle_output=_oracle_output(),
        alignments=[_alignment()],
        warnings=[_warning("WARN/A"), _warning("WARN/A")],
        couplings=[_coupling()],
        run_id="WF-4",
        output_dir=tmp_path,
    )

    assert len(result.exported_paths) == 5
    duplicate_keys = [k for k in result.exported_paths if k.startswith("ARTIFACT-NARR-PHASE-WARN/A")]
    assert "ARTIFACT-NARR-PHASE-WARN/A" in duplicate_keys
    assert "ARTIFACT-NARR-PHASE-WARN/A__2" in duplicate_keys

    exported_json_names = [paths["json"].name for paths in result.exported_paths.values() if "json" in paths]
    assert any(name.startswith("ARTIFACT-NARR-PHASE-WARN_A-") and name.endswith(".json") for name in exported_json_names)


def test_build_resonance_narrative_artifacts_avoids_sanitized_filename_collisions(tmp_path):
    result = build_resonance_narrative_artifacts(
        oracle_output=_oracle_output(),
        alignments=[_alignment()],
        warnings=[_warning("WARN/A"), _warning("WARN?A")],
        couplings=[_coupling()],
        run_id="WF-5",
        output_dir=tmp_path,
    )

    phase_json_names = sorted(
        paths["json"].name
        for artifact_key, paths in result.exported_paths.items()
        if artifact_key.startswith("ARTIFACT-NARR-PHASE")
    )
    assert len(phase_json_names) == 2
    assert phase_json_names[0] != phase_json_names[1]
    assert all(name.startswith("ARTIFACT-NARR-PHASE-WARN_A-") for name in phase_json_names)
