"""Smoke tests for Abraxas Overlay module."""

import pytest
from abraxas.overlay import OverlayAdapter, PhaseManager, OverlaySchema
from abraxas.overlay.phases import Phase
from abraxas.overlay.run import OverlayRunner


def test_overlay_adapter_creation():
    """Test that OverlayAdapter can be instantiated."""
    adapter = OverlayAdapter()
    assert adapter is not None
    assert isinstance(adapter.adapters, dict)


def test_overlay_adapter_register():
    """Test adapter registration."""
    adapter = OverlayAdapter()
    adapter.register("test", lambda x: x * 2)
    assert "test" in adapter.adapters


def test_overlay_adapter_adapt():
    """Test adapter execution."""
    adapter = OverlayAdapter()
    adapter.register("double", lambda x: x * 2)
    result = adapter.adapt("double", 5)
    assert result == 10


def test_phase_manager_creation():
    """Test that PhaseManager can be instantiated."""
    manager = PhaseManager()
    assert manager is not None
    assert manager.current_phase is None
    assert len(manager.phase_history) == 0


def test_phase_manager_transition():
    """Test phase transitions."""
    manager = PhaseManager()
    manager.transition(Phase.INIT)
    assert manager.current_phase == Phase.INIT
    manager.transition(Phase.PROCESS)
    assert manager.current_phase == Phase.PROCESS
    assert Phase.INIT in manager.phase_history


def test_phase_manager_handler():
    """Test phase handler registration and execution."""
    manager = PhaseManager()
    manager.register_handler(Phase.INIT, lambda x: x + 1)
    result = manager.execute(Phase.INIT, 5)
    assert result == 6


def test_overlay_schema_creation():
    """Test that OverlaySchema can be instantiated."""
    schema = OverlaySchema(name="test_schema")
    assert schema is not None
    assert schema.name == "test_schema"
    assert schema.version == "1.0.0"


def test_overlay_schema_add_field():
    """Test adding fields to schema."""
    schema = OverlaySchema(name="test_schema")
    schema.add_field("name", str, required=True)
    assert "name" in schema.fields
    assert schema.fields["name"]["type"] == str
    assert schema.fields["name"]["required"] is True


def test_overlay_schema_validation():
    """Test schema validation."""
    schema = OverlaySchema(name="test_schema")
    schema.add_field("name", str, required=True)
    schema.add_field("age", int, required=False)

    # Valid data
    assert schema.validate({"name": "test", "age": 25}) is True
    assert schema.validate({"name": "test"}) is True

    # Invalid data (missing required field)
    assert schema.validate({"age": 25}) is False


def test_overlay_runner_creation():
    """Test that OverlayRunner can be instantiated."""
    runner = OverlayRunner()
    assert runner is not None
    assert runner.adapter is not None
    assert runner.phase_manager is not None


def test_overlay_runner_with_schema():
    """Test OverlayRunner with schema validation."""
    schema = OverlaySchema(name="test_schema")
    schema.add_field("data", str, required=True)
    runner = OverlayRunner(schema=schema)
    assert runner.schema == schema


def test_overlay_runner_run():
    """Test running a complete overlay operation."""
    runner = OverlayRunner()
    data = {"test": "value"}
    result = runner.run(data)
    assert result is not None
    assert "test" in result


def test_overlay_runner_run_with_validation():
    """Test running overlay with schema validation."""
    schema = OverlaySchema(name="test_schema")
    schema.add_field("required_field", str, required=True)
    runner = OverlayRunner(schema=schema)

    # Valid data
    result = runner.run({"required_field": "value"})
    assert result["required_field"] == "value"

    # Invalid data should raise error
    with pytest.raises(ValueError, match="Data validation failed"):
        runner.run({"other_field": "value"})
