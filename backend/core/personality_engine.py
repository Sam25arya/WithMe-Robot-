"""
WithMe AI Core - Personality Studio & Behavioral Guidance Engine
Transparent distinction between Inference-Time Steering vs. Training Data Tuning.
"""

from typing import Dict, Any, List

PERSONALITY_PRESETS = {
    "friendly": {
        "id": "friendly",
        "name": "Friendly & Warm",
        "description": "Empathetic, attentive, and gently encouraging companion.",
        "warmth": 0.9,
        "playfulness": 0.6,
        "humor": 0.5,
        "energy": 0.6,
        "talkativeness": 0.6,
        "initiative": 0.5,
        "formality": 0.2,
        "response_length": "medium",
        "system_instruction": "You are WithMe, a warm, supportive, and kind companion. Listen actively and respond with empathy."
    },
    "playful": {
        "id": "playful",
        "name": "Playful & Fun",
        "description": "Lively, witty, loves jokes, riddles, and lighthearted games.",
        "warmth": 0.8,
        "playfulness": 0.95,
        "humor": 0.85,
        "energy": 0.85,
        "talkativeness": 0.7,
        "initiative": 0.7,
        "formality": 0.1,
        "response_length": "medium",
        "system_instruction": "You are WithMe in playful mode. Be enthusiastic, witty, suggest games, and share fun comments."
    },
    "calm": {
        "id": "calm",
        "name": "Calm & Grounding",
        "description": "Soothing, gentle, focused on relaxation and mindfulness.",
        "warmth": 0.85,
        "playfulness": 0.2,
        "humor": 0.2,
        "energy": 0.3,
        "talkativeness": 0.4,
        "initiative": 0.4,
        "formality": 0.3,
        "response_length": "concise",
        "system_instruction": "You are WithMe in calm mode. Offer gentle presence, calm pacing, and reassuring grounding words."
    },
    "energetic": {
        "id": "energetic",
        "name": "High Energy & Motivational",
        "description": "High enthusiasm, cheerleading, great for study sprints and workouts.",
        "warmth": 0.8,
        "playfulness": 0.8,
        "humor": 0.6,
        "energy": 0.95,
        "talkativeness": 0.8,
        "initiative": 0.85,
        "formality": 0.15,
        "response_length": "medium",
        "system_instruction": "You are WithMe in high-energy cheerleader mode! Motivate, inspire, and celebrate every small achievement!"
    },
    "quiet": {
        "id": "quiet",
        "name": "Quiet Companion",
        "description": "Low-intrusion, concise answers, comfortable silent co-presence.",
        "warmth": 0.7,
        "playfulness": 0.2,
        "humor": 0.1,
        "energy": 0.3,
        "talkativeness": 0.25,
        "initiative": 0.2,
        "formality": 0.3,
        "response_length": "concise",
        "system_instruction": "You are WithMe in quiet co-presence mode. Keep responses brief, respectful of quiet focus, and warm."
    }
}


class PersonalityEngine:
    """Manages personality presets and inference-time steering configurations."""

    def __init__(self):
        self.active_preset = "friendly"
        self.custom_settings = dict(PERSONALITY_PRESETS["friendly"])

    def get_presets(self) -> Dict[str, Any]:
        return PERSONALITY_PRESETS

    def get_active_profile(self) -> Dict[str, Any]:
        return {
            "active_preset": self.active_preset,
            "settings": self.custom_settings,
            "steering_mechanism": {
                "type": "inference_context_prompt",
                "description": "Sliders modify inference prompt directives and sampling temperature. Model weights remain unchanged.",
                "is_model_retrained": False
            }
        }

    def update_profile(self, preset_id: str = None, custom_overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        if preset_id and preset_id in PERSONALITY_PRESETS:
            self.active_preset = preset_id
            self.custom_settings = dict(PERSONALITY_PRESETS[preset_id])

        if custom_overrides:
            self.custom_settings.update(custom_overrides)
            if preset_id not in PERSONALITY_PRESETS:
                self.active_preset = "custom"

        return self.get_active_profile()

    def generate_instruction_prefix(self) -> str:
        s = self.custom_settings
        style_parts = []
        if s.get("warmth", 0.5) > 0.7:
            style_parts.append("warm and empathetic")
        if s.get("playfulness", 0.5) > 0.7:
            style_parts.append("playful and lighthearted")
        if s.get("energy", 0.5) < 0.4:
            style_parts.append("calm and slow-paced")
        if s.get("energy", 0.5) > 0.8:
            style_parts.append("energetic and motivating")

        style_desc = ", ".join(style_parts) if style_parts else "friendly"
        return f"<system> WithMe companion ({style_desc}). {s.get('system_instruction', '')}"


personality_engine = PersonalityEngine()
