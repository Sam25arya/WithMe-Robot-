"""
Unit tests for WithMe AI Core - Phase 7: Robot Interaction Layer & Adapters
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pydantic import ValidationError
from backend.core.robot_adapters import (
    StructuredRobotAction,
    SimulationRobotAdapter,
    PhysicalHardwareAdapterPlaceholder,
    SimulatedSensorHub,
    WebSpeechAdapter,
    ALLOWED_ACTIONS,
    ALLOWED_TARGETS
)


def test_structured_robot_action_validation():
    """Verify that only allowed targets and actions pass validation."""
    print("Testing StructuredRobotAction schema validation...")
    valid_action = StructuredRobotAction(
        target="face",
        action="wave",
        duration_ms=1200
    )
    assert valid_action.target == "face"
    assert valid_action.action == "wave"
    assert valid_action.duration_ms == 1200

    # Invalid action not in allowlist
    invalid_action_caught = False
    try:
        StructuredRobotAction(target="face", action="rm_rf_slash", duration_ms=1000)
    except ValidationError:
        invalid_action_caught = True
    assert invalid_action_caught, "Unrecognized action should fail validation"

    # Invalid target
    invalid_target_caught = False
    try:
        StructuredRobotAction(target="nuclear_reactor", action="idle", duration_ms=1000)
    except ValidationError:
        invalid_target_caught = True
    assert invalid_target_caught, "Unrecognized target should fail validation"

    # Invalid duration (< 50 or > 10000)
    invalid_duration_caught = False
    try:
        StructuredRobotAction(target="head", action="nod", duration_ms=20)
    except ValidationError:
        invalid_duration_caught = True
    assert invalid_duration_caught, "Duration < 50ms should fail validation"

    print("[PASS] StructuredRobotAction validation test passed.")


def test_simulation_robot_adapter_execution():
    """Verify SimulationRobotAdapter executes actions and records event log."""
    print("Testing SimulationRobotAdapter execution...")
    adapter = SimulationRobotAdapter()
    assert adapter.connect() is True

    action = StructuredRobotAction(
        target="face",
        action="express_happy",
        duration_ms=1000
    )
    result = adapter.execute_action(action)
    assert result["status"] == "executed"
    assert result["current_action"] == "express_happy"
    assert result["is_hardware_simulated"] is True
    assert adapter.current_emotion == "happy"

    telemetry = adapter.get_telemetry()
    assert telemetry["is_physical_hardware"] is False
    assert telemetry["current_action"] == "express_happy"
    print("[PASS] SimulationRobotAdapter execution test passed.")


def test_simulation_robot_adapter_emergency_stop():
    """Verify emergency stop protocol halts execution and requires reset."""
    print("Testing SimulationRobotAdapter emergency stop protocol...")
    adapter = SimulationRobotAdapter()
    
    stop_res = adapter.emergency_stop()
    assert stop_res["status"] == "emergency_stopped"
    assert adapter.emergency_stopped is True

    # Any subsequent action proposal must be rejected while emergency stop is active
    action = StructuredRobotAction(target="arm", action="wave", duration_ms=1000)
    rejected_res = adapter.execute_action(action)
    assert rejected_res["status"] == "rejected"
    assert "Emergency stop is active" in rejected_res["reason"]

    # Reset allows resumption
    reset_res = adapter.reset_emergency_stop()
    assert reset_res["status"] == "normal"
    assert adapter.emergency_stopped is False

    resumed_res = adapter.execute_action(action)
    assert resumed_res["status"] == "executed"
    print("[PASS] Emergency stop test passed.")


def test_physical_hardware_adapter_placeholder():
    """Verify physical adapter returns transparent disclosure that no hardware is attached."""
    print("Testing PhysicalHardwareAdapterPlaceholder disclosure...")
    adapter = PhysicalHardwareAdapterPlaceholder()
    assert adapter.connect() is False
    
    action = StructuredRobotAction(target="head", action="nod", duration_ms=1000)
    res = adapter.execute_action(action)
    assert res["status"] == "unsupported"
    assert "No physical companion robot hardware attached" in res["reason"]

    telemetry = adapter.get_telemetry()
    assert telemetry["connected"] is False
    assert telemetry["is_physical_hardware"] is True
    print("[PASS] PhysicalHardwareAdapterPlaceholder disclosure test passed.")


def test_simulated_sensor_hub():
    """Verify SimulatedSensorHub emits clear simulation disclosures."""
    print("Testing SimulatedSensorHub disclosures...")
    hub = SimulatedSensorHub()
    event_res = hub.trigger_event("person_detected", {"position": "right", "distance_cm": 80})
    
    assert event_res["event_type"] == "person_detected"
    assert event_res["sensor_state"]["person_detected"] is True
    assert event_res["sensor_state"]["person_position"] == "right"
    assert "[SIMULATED SENSOR EVENT]" in event_res["disclosure"]
    print("[PASS] SimulatedSensorHub test passed.")


def test_voice_adapter_contracts():
    """Verify WebSpeechAdapter can speak and stop without errors."""
    print("Testing voice adapter contracts...")
    voice = WebSpeechAdapter()
    assert voice.speak("Hello there", voice_profile="friendly") is True
    voice.stop()
    print("[PASS] Voice adapter contracts test passed.")


if __name__ == "__main__":
    test_structured_robot_action_validation()
    test_simulation_robot_adapter_execution()
    test_simulation_robot_adapter_emergency_stop()
    test_physical_hardware_adapter_placeholder()
    test_simulated_sensor_hub()
    test_voice_adapter_contracts()
    print("\nALL ROBOT INTEGRATION TESTS PASSED SUCCESSFULLY (6/6)!")
