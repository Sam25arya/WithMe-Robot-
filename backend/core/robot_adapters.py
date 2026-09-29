"""
WithMe AI Core - Hardware-Agnostic Robot Adapter Layer (Phase 7)
Provides:
1. StructuredRobotAction schema with strict validation and bounds.
2. BaseRobotAdapter (Abstract hardware interface) with Emergency Stop protocol.
3. SimulationRobotAdapter (Software virtual stage adapter).
4. PhysicalHardwareAdapterPlaceholder (Ready for future ESP32/Pi/ROS drivers).
5. Voice interface contracts (STT, TTS, VAD, and interrupt capability).
6. Vision and sensor interface contracts (Simulated camera and proximity hub).
"""

import time
import abc
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field, validator

ALLOWED_TARGETS = {"face", "head", "arm", "chassis", "audio", "lights"}

ALLOWED_ACTIONS = {
    "idle", "listen", "look_left", "look_right", "look_center",
    "nod", "wave", "greet", "express_happy", "express_sad",
    "express_curiosity", "express_excited", "sleep", "emergency_stop"
}


class StructuredRobotAction(BaseModel):
    """
    Validated structured action proposal.
    Guarantees language models cannot execute arbitrary hardware or shell commands.
    """
    target: str = Field(default="face", example="face")
    action: str = Field(..., example="wave")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(default=1500, ge=50, le=10000)

    @validator("target")
    def validate_target(cls, v):
        clean = v.lower().strip()
        if clean not in ALLOWED_TARGETS:
            raise ValueError(f"Invalid target '{v}'. Permitted targets: {ALLOWED_TARGETS}")
        return clean

    @validator("action")
    def validate_action(cls, v):
        clean = v.lower().strip()
        if clean not in ALLOWED_ACTIONS:
            raise ValueError(f"Action '{v}' is not in the permitted allowlist: {ALLOWED_ACTIONS}")
        return clean


class BaseRobotAdapter(abc.ABC):
    """Abstract contract for all future robot hardware platforms."""

    @abc.abstractmethod
    def connect(self) -> bool:
        """Establish connection to robot controller."""
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Safely terminate connection."""
        raise NotImplementedError

    @abc.abstractmethod
    def execute_action(self, action: StructuredRobotAction) -> Dict[str, Any]:
        """Execute a validated structured robot action."""
        raise NotImplementedError

    @abc.abstractmethod
    def emergency_stop(self) -> Dict[str, Any]:
        """Immediately cut motor power and place robot in safe neutral position."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Query hardware sensor state, motor temperatures, and battery levels."""
        raise NotImplementedError


class SimulationRobotAdapter(BaseRobotAdapter):
    """Software-only simulation adapter driving the virtual avatar stage."""

    def __init__(self):
        self.connected = True
        self.current_action = "idle"
        self.current_target = "face"
        self.current_emotion = "happy"
        self.emergency_stopped = False
        self.event_log: List[Dict[str, Any]] = []

    def connect(self) -> bool:
        self.connected = True
        self.emergency_stopped = False
        return True

    def disconnect(self) -> None:
        self.connected = False

    def execute_action(self, action: StructuredRobotAction) -> Dict[str, Any]:
        if self.emergency_stopped:
            return {
                "status": "rejected",
                "reason": "Emergency stop is active. Reset required before executing actions.",
                "action": action.action
            }

        self.current_action = action.action
        self.current_target = action.target

        # Map actions to virtual expressions
        if "happy" in action.action:
            self.current_emotion = "happy"
        elif "sad" in action.action:
            self.current_emotion = "sad"
        elif "sleep" in action.action:
            self.current_emotion = "sleepy"

        entry = {
            "timestamp": time.time(),
            "target": action.target,
            "action": action.action,
            "duration_ms": action.duration_ms,
            "is_simulated": True
        }
        self.event_log.append(entry)
        return {
            "status": "executed",
            "adapter": "SimulationRobotAdapter",
            "current_action": self.current_action,
            "target": self.current_target,
            "duration_ms": action.duration_ms,
            "is_hardware_simulated": True
        }

    def emergency_stop(self) -> Dict[str, Any]:
        self.emergency_stopped = True
        self.current_action = "emergency_stop"
        self.current_emotion = "calm"
        entry = {
            "timestamp": time.time(),
            "event": "EMERGENCY_STOP_ACTIVATED",
            "reason": "Immediate safety stop triggered."
        }
        self.event_log.append(entry)
        return {
            "status": "emergency_stopped",
            "adapter": "SimulationRobotAdapter",
            "action": "emergency_stop",
            "message": "All virtual actuators stopped. System placed in safe hold."
        }

    def reset_emergency_stop(self) -> Dict[str, Any]:
        self.emergency_stopped = False
        self.current_action = "idle"
        return {"status": "normal", "message": "Emergency stop cleared."}

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "adapter": "SimulationRobotAdapter",
            "connected": self.connected,
            "emergency_stopped": self.emergency_stopped,
            "current_action": self.current_action,
            "current_target": self.current_target,
            "current_emotion": self.current_emotion,
            "battery_level_percent": 100,
            "is_physical_hardware": False
        }


class PhysicalHardwareAdapterPlaceholder(BaseRobotAdapter):
    """
    Placeholder contract for physical hardware drivers (ESP32 / Raspberry Pi / ROS).
    Provides transparent disclosures that no physical motors are currently attached.
    """

    def connect(self) -> bool:
        return False

    def disconnect(self) -> None:
        pass

    def execute_action(self, action: StructuredRobotAction) -> Dict[str, Any]:
        return {
            "status": "unsupported",
            "reason": "No physical companion robot hardware attached. Use SimulationRobotAdapter."
        }

    def emergency_stop(self) -> Dict[str, Any]:
        return {
            "status": "acknowledged",
            "message": "Hardware stop signal ready for physical driver integration."
        }

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "adapter": "PhysicalHardwareAdapterPlaceholder",
            "connected": False,
            "hardware_type": "Unspecified / Hardware-Agnostic",
            "is_physical_hardware": True
        }


# ==================== VOICE INTERFACE CONTRACTS ====================

class BaseSTTEngine(abc.ABC):
    """Contract for speech-to-text input engines."""

    @abc.abstractmethod
    def start_listening(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def stop_listening(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def is_listening(self) -> bool:
        raise NotImplementedError


class BaseTTSEngine(abc.ABC):
    """Contract for text-to-speech voice output engines."""

    @abc.abstractmethod
    def speak(self, text: str, voice_profile: str = "friendly") -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        """Interrupt and silence speech immediately upon user interruption."""
        raise NotImplementedError


class WebSpeechAdapter(BaseTTSEngine):
    """Adapter for browser-native Web Speech API synthesis."""

    def speak(self, text: str, voice_profile: str = "friendly") -> bool:
        # Handled client-side via JavaScript SpeechSynthesis in browser
        return True

    def stop(self) -> None:
        pass


# ==================== VISION & SENSOR CONTRACTS ====================

class SimulatedSensorHub:
    """
    Simulates sensory telemetry for person detection, touch gestures, and distance.
    Enforces clear disclosures that readings are software simulations.
    """

    def __init__(self):
        self.sensor_state = {
            "person_detected": False,
            "person_position": "center",
            "estimated_distance_cm": 150,
            "touch_detected": False,
            "ambient_light": "normal"
        }

    def trigger_event(self, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        if event_type == "person_detected":
            self.sensor_state["person_detected"] = True
            self.sensor_state["person_position"] = details.get("position", "left")
            self.sensor_state["estimated_distance_cm"] = details.get("distance_cm", 120)
        elif event_type == "petting_gesture":
            self.sensor_state["touch_detected"] = True
        elif event_type == "user_departed":
            self.sensor_state["person_detected"] = False

        return {
            "event_type": event_type,
            "sensor_state": dict(self.sensor_state),
            "disclosure": "[SIMULATED SENSOR EVENT] Software simulation for robotics testing without physical sensors."
        }


simulation_adapter = SimulationRobotAdapter()
sensor_hub = SimulatedSensorHub()
