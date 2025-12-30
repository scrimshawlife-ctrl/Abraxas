"""Integration tests for lifecycle state consistency across systems.

Tests the full integration:
- DCE → Oracle v2 → Weather Bridge → Weather System
"""

import pytest
from pathlib import Path

from abraxas.slang.lifecycle import LifecycleState
from abraxas.slang.validation import LifecycleStateValidator, normalize_lifecycle_state
from abraxas.lexicon.dce import (
    DCEEntry,
    DCEPack,
    DCERegistry,
    DomainCompressionEngine,
    LifecycleState as DCELifecycleState,
)
from abraxas.oracle.v2.pipeline import (
    OracleV2Pipeline,
    OracleSignal,
)
from abraxas.oracle.weather_bridge import (
    oracle_to_weather_intel,
    oracle_to_mimetic_weather_fronts,
)


class TestLifecycleStateValidation:
    """Test lifecycle state validation utilities."""

    def test_valid_states(self):
        """Test validation of canonical lifecycle states."""
        assert LifecycleStateValidator.is_valid_state("Proto")
        assert LifecycleStateValidator.is_valid_state("Front")
        assert LifecycleStateValidator.is_valid_state("Saturated")
        assert LifecycleStateValidator.is_valid_state("Dormant")
        assert LifecycleStateValidator.is_valid_state("Archived")

    def test_invalid_states(self):
        """Test rejection of invalid lifecycle states."""
        assert not LifecycleStateValidator.is_valid_state("proto")  # lowercase
        assert not LifecycleStateValidator.is_valid_state("invalid")
        assert not LifecycleStateValidator.is_valid_state("")

    def test_normalize_lowercase(self):
        """Test normalization from lowercase to PascalCase."""
        assert normalize_lifecycle_state("proto") == "Proto"
        assert normalize_lifecycle_state("front") == "Front"
        assert normalize_lifecycle_state("saturated") == "Saturated"
        assert normalize_lifecycle_state("dormant") == "Dormant"
        assert normalize_lifecycle_state("archived") == "Archived"

    def test_normalize_already_canonical(self):
        """Test normalization of already-canonical states."""
        assert normalize_lifecycle_state("Proto") == "Proto"
        assert normalize_lifecycle_state("Front") == "Front"

    def test_validate_state_dict(self):
        """Test validation of state dictionaries."""
        valid_dict = {"token1": "Proto", "token2": "Front"}
        is_valid, errors = LifecycleStateValidator.validate_state_dict(valid_dict, raise_on_error=False)
        assert is_valid
        assert len(errors) == 0

    def test_validate_state_dict_invalid(self):
        """Test validation catches invalid states."""
        invalid_dict = {"token1": "Proto", "token2": "invalid"}
        is_valid, errors = LifecycleStateValidator.validate_state_dict(invalid_dict, raise_on_error=False)
        assert not is_valid
        assert len(errors) == 1

    def test_migrate_state_dict(self):
        """Test migration from lowercase to canonical."""
        old_dict = {"token1": "proto", "token2": "front", "token3": "saturated"}
        migrated = LifecycleStateValidator.migrate_state_dict(old_dict)

        assert migrated["token1"] == "Proto"
        assert migrated["token2"] == "Front"
        assert migrated["token3"] == "Saturated"


class TestDCEOracleIntegration:
    """Test DCE and Oracle v2 lifecycle state consistency."""

    def test_dce_uses_canonical_lifecycle_state(self):
        """Verify DCE imports LifecycleState from slang.lifecycle."""
        # DCE should now use the canonical LifecycleState
        assert DCELifecycleState is LifecycleState

    def test_dce_lifecycle_states_match_slang(self):
        """Verify DCE lifecycle state values match slang values."""
        assert LifecycleState.PROTO.value == "Proto"
        assert LifecycleState.FRONT.value == "Front"
        assert LifecycleState.SATURATED.value == "Saturated"
        assert LifecycleState.DORMANT.value == "Dormant"
        assert LifecycleState.ARCHIVED.value == "Archived"

    def test_oracle_processes_dce_states(self):
        """Test Oracle v2 can process DCE lifecycle states."""
        # Create test signal
        signal = OracleSignal(
            domain="politics",
            subdomain="test",
            observations=["test observation"],
            tokens=["equality", "justice"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        # Create Oracle pipeline
        pipeline = OracleV2Pipeline()

        # Process signal
        output = pipeline.process(signal, run_id="TEST-001")

        # Verify compression phase has lifecycle states
        assert hasattr(output.compression, "lifecycle_states")
        assert isinstance(output.compression.lifecycle_states, dict)

        # Verify all states are valid
        for token, state in output.compression.lifecycle_states.items():
            assert LifecycleStateValidator.is_valid_state(state), \
                f"Token '{token}' has invalid state '{state}'"

    def test_oracle_forecast_phase_transitions(self):
        """Test Oracle v2 forecast produces valid lifecycle transitions."""
        signal = OracleSignal(
            domain="politics",
            subdomain="test",
            observations=["test"],
            tokens=["equality"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        pipeline = OracleV2Pipeline()
        output = pipeline.process(signal, run_id="TEST-002")

        # Verify phase transitions use canonical states
        for token, next_state in output.forecast.phase_transitions.items():
            assert LifecycleStateValidator.is_valid_state(next_state), \
                f"Transition for '{token}' to invalid state '{next_state}'"


class TestWeatherBridgeIntegration:
    """Test Oracle v2 → Weather Bridge integration."""

    def test_oracle_to_weather_intel(self, tmp_path):
        """Test conversion of Oracle outputs to weather intel."""
        # Create test Oracle output
        signal = OracleSignal(
            domain="politics",
            subdomain="test",
            observations=["test"],
            tokens=["equality"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        pipeline = OracleV2Pipeline()
        oracle_output = pipeline.process(signal, run_id="TEST-003")

        # Convert to weather intel
        output_dir = tmp_path / "intel"
        written = oracle_to_weather_intel([oracle_output], output_dir)

        # Verify files were created
        assert "symbolic_pressure" in written
        assert "trust_index" in written
        assert "semantic_drift" in written

        assert written["symbolic_pressure"].exists()
        assert written["trust_index"].exists()
        assert written["semantic_drift"].exists()

    def test_oracle_to_weather_fronts(self):
        """Test conversion of Oracle outputs to weather fronts."""
        signal = OracleSignal(
            domain="politics",
            subdomain="test",
            observations=["test"],
            tokens=["equality"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        pipeline = OracleV2Pipeline()
        oracle_output = pipeline.process(signal, run_id="TEST-004")

        # Convert to weather fronts
        fronts = oracle_to_mimetic_weather_fronts([oracle_output])

        # Verify fronts were generated
        assert isinstance(fronts, list)

        # Verify front structure
        for front in fronts:
            assert "front" in front
            assert "domain" in front
            assert "terms" in front
            assert "signal" in front

            # Verify front type is valid
            assert front["front"] in {"NEWBORN", "MIGRATION", "AMPLIFY", "DRIFT", "POLLUTION"}

    def test_weather_bridge_validates_states(self):
        """Test weather bridge validates lifecycle states."""
        # Create Oracle output with lifecycle states
        signal = OracleSignal(
            domain="politics",
            subdomain="test",
            observations=["test"],
            tokens=["equality", "justice"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        pipeline = OracleV2Pipeline()
        oracle_output = pipeline.process(signal, run_id="TEST-005")

        # Weather bridge should handle valid states without errors
        fronts = oracle_to_mimetic_weather_fronts([oracle_output])

        # If there are phase transitions, they should all be valid states
        for token, state in oracle_output.forecast.phase_transitions.items():
            assert LifecycleStateValidator.is_valid_state(state)


class TestEndToEndIntegration:
    """Test full end-to-end integration from DCE through Weather."""

    def test_full_stack_integration(self, tmp_path):
        """Test complete flow: DCE → Oracle → Weather Bridge → Intel."""
        # This would be a full integration test with real DCE
        # For now, we test with Oracle's fallback mode

        # Create signal
        signal = OracleSignal(
            domain="politics",
            subdomain="rhetoric",
            observations=[
                "The establishment ignores the people",
                "We need equality and justice",
            ],
            tokens=["establishment", "people", "equality", "justice"],
            timestamp_utc="2025-12-29T12:00:00Z",
        )

        # Process through Oracle v2
        pipeline = OracleV2Pipeline()
        oracle_output = pipeline.process(signal, run_id="TEST-FULL-001")

        # Verify lifecycle states are canonical
        for token, state in oracle_output.compression.lifecycle_states.items():
            assert LifecycleStateValidator.is_valid_state(state)

        # Convert to weather intel
        intel_dir = tmp_path / "intel"
        written_intel = oracle_to_weather_intel([oracle_output], intel_dir)

        # Verify intel files exist
        assert len(written_intel) == 3
        assert all(path.exists() for path in written_intel.values())

        # Convert to weather fronts
        fronts = oracle_to_mimetic_weather_fronts([oracle_output])

        # Verify fronts generated
        assert len(fronts) > 0

        # Verify all front types are valid
        valid_front_types = {"NEWBORN", "MIGRATION", "AMPLIFY", "DRIFT", "POLLUTION"}
        for front in fronts:
            assert front["front"] in valid_front_types
            assert front["domain"] == "politics"
            assert len(front["terms"]) > 0
