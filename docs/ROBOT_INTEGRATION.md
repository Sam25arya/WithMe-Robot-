# WithMe AI — Robot Interaction Layer Architecture (`ROBOT_INTEGRATION.md`)

## 1. Architectural Philosophy: Decoupling Brain from Actuation

WithMe is designed as an emotional companion AI that can operate both as a virtual desktop/web companion and as an embodied physical robot.

To guarantee safety, reliability, and portability, the conversational AI "brain" (transformer language model, LoRA adapter, or hybrid smart engine) is strictly decoupled from physical motor control. The language model **never** directly accesses hardware peripherals, GPIO pins, serial ports, or system shells. Instead, it emits structured action proposals that must pass through an allowlist validator before reaching the hardware adapter.

```mermaid
graph TD
    User([User Speech / Message]) --> Brain[Conversational Brain / Policy]
    Brain --> LLMProposal[Proposed Action & Emotional Tone]
    LLMProposal --> Validator[StructuredRobotAction Schema Validator]
    Validator -- "Invalid Action" --> Rejection[Drop / Fallback to Neutral]
    Validator -- "Valid Action" --> SafetyGate{Emergency Stop Active?}
    SafetyGate -- "Yes (Locked)" --> RejectStop[Block Motor Execution]
    SafetyGate -- "No (Clear)" --> AdapterRouter[Robot Adapter Router]
    AdapterRouter --> SimAdapter[SimulationRobotAdapter (Virtual Stage Avatar)]
    AdapterRouter --> PhysAdapter[PhysicalHardwareAdapterPlaceholder (ESP32/ROS)]
```

---

## 2. Action Allowlist & Schema Validation

All actuator proposals must conform to the `StructuredRobotAction` Pydantic model (`backend/core/robot_adapters.py`):

```python
class StructuredRobotAction(BaseModel):
    target: str = Field(default="face", example="face")
    action: str = Field(..., example="wave")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(default=1500, ge=50, le=10000)
```

### Permitted Targets
- `face` (screen eye expressions, blink, smile, brow movements)
- `head` (pan/tilt servos for nodding, head tilting, turning)
- `arm` (gesture servos for waving, raising hand)
- `chassis` (wheel or base motors for orientation)
- `audio` (synthesized vocal cues, chime sounds)
- `lights` (LED ring, ear lights, mood glow)

### Permitted Actions Allowlist
`{"idle", "listen", "look_left", "look_right", "look_center", "nod", "wave", "greet", "express_happy", "express_sad", "express_curiosity", "express_excited", "sleep", "emergency_stop"}`

Any attempt by a generated token or prompt injection to issue shell commands (e.g. `rm`, `exec`), open sockets, or exceed safety boundaries (e.g. durations $> 10000\text{ ms}$) triggers an immediate validation error and is safely dropped.

---

## 3. Emergency Stop Protocol

Safety is paramount in embodied robotics. WithMe implements a persistent software emergency stop protocol:

1. **Triggering**: An emergency stop can be triggered via `/api/robot/action` with action `emergency_stop` or directly calling `adapter.emergency_stop()`.
2. **Behavior**:
   - Actuators immediately cease current motion.
   - Virtual/physical state transitions to `emergency_stopped = True`.
   - The emotion state changes to neutral/calm.
   - An audit event `EMERGENCY_STOP_ACTIVATED` is logged with timestamp.
3. **Lockout**: While `emergency_stopped` is active, **all** proposed actions are immediately rejected with status `rejected`.
4. **Resumption**: Operation can only be restored by an explicit operator call to `adapter.reset_emergency_stop()`.

---

## 4. Voice Interface Contracts

WithMe abstracts voice interactions into modular interfaces (`backend/core/robot_adapters.py`):

- **Speech-to-Text (`BaseSTTEngine`)**: Contract defining `start_listening()`, `stop_listening() -> str`, and `is_listening()`. Supports browser-native Web Speech Recognition API or local Whisper models.
- **Text-to-Speech (`BaseTTSEngine`)**: Contract defining `speak(text, voice_profile)` and `stop()`.
- **Interrupt Handling**: Crucial for conversational naturalness. When the user begins speaking while the companion is vocalizing, the `stop()` method is invoked immediately to cut audio playback and allow natural turn-taking.
- **WebSpeechAdapter**: Native implementation routing synthesized speech through the browser's `window.speechSynthesis` engine with expressive pitch and rate modulation.

---

## 5. Vision and Sensor Simulation Contracts

Until physical stereo cameras, Time-of-Flight (ToF) sensors, or capacitive touch arrays are connected, all sensor feeds run through the `SimulatedSensorHub`:

- **Person Detection**: Reports simulated bounding coordinates (`left`, `center`, `right`) and distance in centimeters.
- **Touch & Petting Gestures**: Simulates capacitive touch responses on head and cheek sensors.
- **Strict Disclosures**: Every sensor payload returned to the frontend or API explicitly includes:
  `[SIMULATED SENSOR EVENT] Software simulation for robotics testing without physical sensors.`

---

## 6. Hardware Transition Guide (ESP32 / Raspberry Pi / ROS)

To connect WithMe to physical robot hardware:

1. Subclass `BaseRobotAdapter` in a new file (e.g. `backend/core/esp32_adapter.py` or `backend/core/ros_adapter.py`).
2. Implement the 5 required methods:
   - `connect()`: Open serial port (e.g. `pyserial` on `COM3` or `/dev/ttyUSB0`) or connect to ROS topic / Micro-ROS agent.
   - `disconnect()`: Safely close serial connections and park servos.
   - `execute_action(action)`: Map `StructuredRobotAction` into hardware servo PWM pulses, stepper pulses, or ROS twist messages.
   - `emergency_stop()`: Send high-priority brake byte (e.g. `0xFF 0x00`) to cut motor driver H-bridge enable lines.
   - `get_telemetry()`: Read battery ADC voltage, motor current sensors, and IMU data.
3. In `backend/core/robot_service.py`, switch `current_adapter = PhysicalESP32Adapter()` when hardware is detected.
