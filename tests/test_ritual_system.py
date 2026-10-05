"""Tests for Ritual System (N5 Canonical Action)"""

from __future__ import annotations

from abraxas.ritual import (
    RitualType,
    ModulationTarget,
    RitualParameter,
    RitualProtocol,
    RitualExecution,
    EffectTracker,
    RitualEngine,
    create_ritual_engine,
    create_default_protocols,
)


def test_ritual_parameter_validation():
    """Test ritual parameter validation."""
    param = RitualParameter(
        target=ModulationTarget.PHASE_THRESHOLDS,
        parameter_name="test_param",
        baseline_value=0.5,
        ritual_value=0.7,
        min_value=0.0,
        max_value=1.0,
        units="test",
    )
    assert param.validate() is True

    # Test out of bounds
    param_bad = RitualParameter(
        target=ModulationTarget.PHASE_THRESHOLDS,
        parameter_name="test_param",
        baseline_value=0.5,
        ritual_value=1.5,
        min_value=0.0,
        max_value=1.0,
        units="test",
    )
    assert param_bad.validate() is False


def test_ritual_protocol_creation():
    """Test ritual protocol creation and serialization."""
    protocol = RitualProtocol(
        protocol_id="TEST-001",
        name="Test Ritual",
        ritual_type=RitualType.PHASE_TRANSITION,
        description="Test protocol",
        parameters=[
            RitualParameter(
                target=ModulationTarget.PHASE_THRESHOLDS,
                parameter_name="threshold",
                baseline_value=0.5,
                ritual_value=0.6,
                min_value=0.0,
                max_value=1.0,
                units="test",
            )
        ],
        preconditions={"test": "value"},
        postconditions={"expected": "result"},
        duration_hours=24.0,
        cooldown_hours=72.0,
    )

    d = protocol.to_dict()
    assert d["protocol_id"] == "TEST-001"
    assert d["ritual_type"] == "phase_transition"
    assert len(d["parameters"]) == 1


def test_default_protocols():
    """Test default protocol creation."""
    protocols = create_default_protocols()

    expected_ids = [
        "RIT-PHASE-ADVANCE-001",
        "RIT-PHASE-STABILIZE-001",
        "RIT-RESONANCE-BOOST-001",
        "RIT-TAU-RECALIBRATE-001",
        "RIT-DOMAIN-COUPLE-001",
        "RIT-CASCADE-SUPPRESS-001",
        "RIT-SYMBOLIC-ANCHOR-001",
    ]

    assert len(protocols) == 7
    for pid in expected_ids:
        # The keys are the short names, not the protocol IDs
        # Find the protocol with this ID
        found = None
        for protocol in protocols.values():
            if protocol.protocol_id == pid:
                found = protocol
                break
        assert found is not None, f"Protocol {pid} not found"
        protocol = found
        assert len(protocol.parameters) > 0
        assert protocol.duration_hours > 0
        assert protocol.cooldown_hours > 0


def test_ritual_engine_creation():
    """Test ritual engine creation."""
    engine = create_ritual_engine()
    assert len(engine._protocols) == 7

    # Test listing
    all_protocols = engine.list_protocols()
    assert len(all_protocols) == 7

    phase_protocols = engine.list_protocols(RitualType.PHASE_TRANSITION)
    assert len(phase_protocols) == 2


def test_precondition_checking():
    """Test ritual precondition checking."""
    engine = create_ritual_engine()
    protocol = engine.get_protocol("phase_advance")
    assert protocol is not None

    # Test with matching preconditions
    state_match = {"domain_phase": "front", "tau_velocity": 0.5}
    met, failures = engine.check_preconditions(protocol, state_match)
    assert met is True
    assert len(failures) == 0

    # Test with non-matching preconditions
    state_fail = {"domain_phase": "proto", "tau_velocity": 0.1}
    met, failures = engine.check_preconditions(protocol, state_fail)
    assert met is False
    assert len(failures) > 0


def test_ritual_execution():
    """Test ritual execution."""
    engine = create_ritual_engine()

    current_state = {
        "domain_phase": "front",
        "tau_velocity": 0.5,
        "alignment_strength": 0.6,
        "domains_aligned": 3,
    }

    execution = engine.execute_ritual(
        protocol_id="phase_advance",
        operator="test_operator",
        current_state=current_state,
        timestamp_utc="2025-12-29T12:00:00Z",
    )

    assert execution.protocol_id == "RIT-PHASE-ADVANCE-001"
    assert execution.operator == "test_operator"
    assert execution.success is True
    assert execution.effect_magnitude > 0
    assert len(execution.parameters_applied) == 2


def test_effect_tracker():
    """Test effect tracking."""
    tracker = EffectTracker()

    # Create mock executions
    for i in range(3):
        exec_obj = RitualExecution(
            execution_id=f"EXEC-TEST-{i}",
            protocol_id="TEST-PROTOCOL",
            timestamp_utc=f"2025-12-2{i+1}T12:00:00Z",
            operator="test",
            parameters_applied={"param": 0.5 + i * 0.1},
            pre_state={},
            post_state={},
            provenance=None,  # type: ignore
            success=True,
            effect_magnitude=0.3 + i * 0.1,
        )
        tracker.add_execution(exec_obj)

    history = tracker.get_effect_history("TEST-PROTOCOL")
    assert len(history) == 3

    avg = tracker.compute_average_effect("TEST-PROTOCOL")
    assert 0.3 <= avg <= 0.5


def test_active_modulations():
    """Test active modulation tracking."""
    engine = create_ritual_engine()

    current_state = {
        "domain_phase": "front",
        "tau_velocity": 0.5,
    }

    # Execute ritual with current timestamp
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    engine.execute_ritual(
        protocol_id="phase_advance",
        operator="test",
        current_state=current_state,
        timestamp_utc=timestamp,
    )

    # Check active modulations
    mods = engine.get_active_modulations()
    assert "phase_thresholds" in mods
    assert "front_to_saturated_threshold" in mods["phase_thresholds"]
    assert "tau_velocity_weight" in mods
    assert "velocity_amplification" in mods["tau_velocity_weight"]


def test_ritual_execution_serialization():
    """Test ritual execution serialization."""
    engine = create_ritual_engine()

    current_state = {"domain_phase": "front", "tau_velocity": 0.5}

    execution = engine.execute_ritual(
        protocol_id="phase_advance",
        operator="test_operator",
        current_state=current_state,
        timestamp_utc="2025-12-29T12:00:00Z",
    )

    d = execution.to_dict()
    assert d["execution_id"] is not None
    assert d["protocol_id"] == "RIT-PHASE-ADVANCE-001"
    assert d["operator"] == "test_operator"
    assert d["success"] is True
    assert "parameters_applied" in d


if __name__ == "__main__":
    # Run all tests manually
    test_ritual_parameter_validation()
    print("✓ test_ritual_parameter_validation")

    test_ritual_protocol_creation()
    print("✓ test_ritual_protocol_creation")

    test_default_protocols()
    print("✓ test_default_protocols")

    test_ritual_engine_creation()
    print("✓ test_ritual_engine_creation")

    test_precondition_checking()
    print("✓ test_precondition_checking")

    test_ritual_execution()
    print("✓ test_ritual_execution")

    test_effect_tracker()
    print("✓ test_effect_tracker")

    test_active_modulations()
    print("✓ test_active_modulations")

    test_ritual_execution_serialization()
    print("✓ test_ritual_execution_serialization")

    print("\nAll tests passed!")