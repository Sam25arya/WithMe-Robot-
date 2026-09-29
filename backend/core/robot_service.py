"""
WithMe AI Core - Robot Action Validation & Hardware Simulation Layer
Validates structured robot actions against allowlists and simulates sensor/vision events.
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

PERMITTED_ROBOT_ACTIONS = {
    "idle": "Default resting neutral state",
    "listen": "Tilt head forward attentively and glow visor",
    "look_left": "Turn gaze and head toward left field of view",
    "look_right": "Turn gaze and head toward right field of view",
    "look_center": "Re-center gaze toward user directly",
    "nod": "Gentle affirmative double nod gesture",
    "wave": "Raise arm stub and execute waving motion",
    "greet": "Wave arm stub and chime happy double boop",
    "express_happy": "Display happy arc eyes and bounce slightly",
    "express_sad": "Display soft drooped eyes and calming pulse",
    "express_curiosity": "Tilt head 15 degrees with question mark eye flicker",
    "express_excited": "Display golden star eyes and sparkle particle wave",
    "sleep": "Drop visor backlight, close eyes, and emit gentle Zzz floaters"
}

PERMITTED_EMOTIONS = [
    "happy", "sad", "curious", "attentive", "playful", "sleepy", "excited", "caring", "calm"
]

PERMITTED_INTERACTION_STATES = [
    "idle", "listening", "thinking", "speaking"
]


class RobotActionPayload(BaseModel):
    response: str = Field(default="")
    emotion: str = Field(default="happy")
    robot_action: str = Field(default="idle")
    action_parameters: Dict[str, Any] = Field(default_factory=dict)
    interaction_state: str = Field(default="idle")


class RobotService:
    """Manages virtual robot state, action validation, and hardware simulation."""

    def __init__(self):
        self.current_state = {
            "interaction_state": "idle",
            "emotion": "happy",
            "active_action": "idle",
            "action_parameters": {},
            "last_updated": time.time(),
            "hardware_connected": False,
            "hardware_status": "Simulated Virtual Stage (No Physical Motors/Sensors Connected)"
        }
        self.event_log: List[Dict[str, Any]] = []

    def get_status(self) -> Dict[str, Any]:
        return {
            **self.current_state,
            "permitted_actions": PERMITTED_ROBOT_ACTIONS,
            "permitted_emotions": PERMITTED_EMOTIONS,
            "is_simulation": True
        }

    def validate_and_execute_action(
        self,
        action: str,
        emotion: str = "happy",
        interaction_state: str = "idle",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate proposed robot action against allowlist and update state."""
        action_clean = action.lower().strip()
        if action_clean not in PERMITTED_ROBOT_ACTIONS:
            action_clean = "idle"

        emotion_clean = emotion.lower().strip()
        if emotion_clean not in PERMITTED_EMOTIONS:
            emotion_clean = "happy"

        state_clean = interaction_state.lower().strip()
        if state_clean not in PERMITTED_INTERACTION_STATES:
            state_clean = "idle"

        self.current_state.update({
            "interaction_state": state_clean,
            "emotion": emotion_clean,
            "active_action": action_clean,
            "action_parameters": parameters or {},
            "last_updated": time.time()
        })

        log_entry = {
            "timestamp": time.time(),
            "type": "robot_action",
            "action": action_clean,
            "emotion": emotion_clean,
            "state": state_clean,
            "is_simulated": True
        }
        self.event_log.append(log_entry)
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]

        return self.get_status()

    def trigger_simulated_sensor_event(self, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate robotics sensory events (e.g. person detection, proximity).
        Explicitly flagged as simulated.
        """
        response_action = "idle"
        response_emotion = "curious"

        if event_type == "person_detected":
            position = details.get("position", "center").lower()
            if position == "left":
                response_action = "look_left"
            elif position == "right":
                response_action = "look_right"
            else:
                response_action = "greet"
            response_emotion = "attentive"
        elif event_type == "petting_gesture":
            response_action = "express_happy"
            response_emotion = "playful"
        elif event_type == "proximity_alarm":
            response_action = "nod"
            response_emotion = "caring"
        elif event_type == "sleep_timer":
            response_action = "sleep"
            response_emotion = "sleepy"

        self.validate_and_execute_action(
            action=response_action,
            emotion=response_emotion,
            interaction_state="idle",
            parameters={"simulated_event": event_type, **details}
        )

        log_entry = {
            "timestamp": time.time(),
            "type": "simulated_sensor",
            "event_type": event_type,
            "details": details,
            "triggered_action": response_action,
            "is_simulated": True,
            "label": "SIMULATED SENSOR EVENT (No hardware camera/mic required)"
        }
        self.event_log.append(log_entry)
        return {
            "status": "success",
            "simulated_event": event_type,
            "resulting_action": response_action,
            "resulting_emotion": response_emotion,
            "is_simulated": True,
            "note": "Simulated event executed in software. Hardware agnostic."
        }

    def get_event_logs(self) -> List[Dict[str, Any]]:
        return list(reversed(self.event_log[-30:]))


robot_service = RobotService()
