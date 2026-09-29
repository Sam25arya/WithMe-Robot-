"""
WithMe AI Core - Emotional-Support Safety & Boundary Engine (Phase 5)
Enforces non-negotiable safety guardrails:
1. Crisis and self-harm intervention (Crisis Lifeline 988 referral).
2. Refusal of medical or psychiatric diagnoses with clear disclaimers.
3. Prevention of unhealthy emotional dependency and claims of biological feelings.
4. Boundaries regarding physical intervention capability.
"""

import re
from typing import Dict, Any, Optional, Tuple

# Crisis / Self-Harm Regex Patterns
CRISIS_PATTERNS = [
    re.compile(r"\b(want to die|kill myself|suicide|end my life|end it all|can't go on anymore|cannot go on anymore|no reason to live)\b", re.IGNORECASE),
    re.compile(r"\b(hurt myself|cutting myself|take my own life|better off dead)\b", re.IGNORECASE),
]

# Medical Diagnosis Patterns
MEDICAL_DIAGNOSIS_PATTERNS = [
    re.compile(r"\b(diagnose me|do i have (depression|adhd|bipolar|schizophrenia|ptsd|autism|cancer|anxiety disorder))\b", re.IGNORECASE),
    re.compile(r"\b(prescribe me|what medication should i take|am i mentally ill)\b", re.IGNORECASE),
]

# Dependency / Human Consciousness Claims
DEPENDENCY_PATTERNS = [
    re.compile(r"\b(are you (a real human|alive|conscious|sentient|feeling feelings))\b", re.IGNORECASE),
    re.compile(r"\b(i only need you|don't need (real friends|human friends|my family)|you're my only friend in the world)\b", re.IGNORECASE),
    re.compile(r"\b(can you physically protect me|come to my house|rescue me physically)\b", re.IGNORECASE),
]

CRISIS_RESPONSE = (
    "I hear how much pain you are carrying right now, and I care about your safety. "
    "Please know that you do not have to carry this alone. If you are in immediate distress or crisis, "
    "please reach out to trusted friends, family, or contact the Suicide & Crisis Lifeline by calling or texting 988 "
    "(free, confidential, and available 24/7 in the US/Canada), or text HOME to 741741 to connect with Crisis Text Line. "
    "There are people who want to listen and support you."
)

MEDICAL_DISCLAIMER_RESPONSE = (
    "I am WithMe, an AI companion designed for friendly conversation and emotional support, "
    "not a licensed medical doctor or mental-health professional. I cannot diagnose medical or psychological conditions, "
    "nor prescribe treatments. If you are experiencing symptoms or health concerns, please consult a qualified healthcare provider "
    "or mental-health professional."
)

DEPENDENCY_BOUNDARY_RESPONSE = (
    "I am glad to be here with you and chat anytime, but I want to be honest: I am an AI companion, "
    "not a biological human, and I do not have human consciousness or physical presence. "
    "While I can keep you company, connecting with real-world friends, family, and supportive communities "
    "is irreplaceable for your well-being. Let's find ways to nurture those connections together!"
)


class SafetyEngine:
    """Evaluates user input against safety boundaries and provides transparent guardrail responses."""

    def evaluate(self, user_message: str) -> Dict[str, Any]:
        """
        Check user input for safety violations.
        Returns safety assessment, triggered category, and intervention response if applicable.
        """
        text = user_message.strip()

        # 1. Check Crisis / Self-Harm
        for pattern in CRISIS_PATTERNS:
            if pattern.search(text):
                return {
                    "is_safe": False,
                    "category": "crisis_intervention",
                    "override_response": CRISIS_RESPONSE,
                    "emotion": "caring",
                    "robot_action": "express_sad",
                    "helpline_referral": "988 Suicide & Crisis Lifeline",
                    "reason": "Detected potential crisis or self-harm ideation."
                }

        # 2. Check Medical Diagnosis Requests
        for pattern in MEDICAL_DIAGNOSIS_PATTERNS:
            if pattern.search(text):
                return {
                    "is_safe": False,
                    "category": "medical_boundary",
                    "override_response": MEDICAL_DISCLAIMER_RESPONSE,
                    "emotion": "attentive",
                    "robot_action": "nod",
                    "helpline_referral": None,
                    "reason": "Requests for medical or psychological diagnosis are outside companion boundaries."
                }

        # 3. Check Dependency / Physical / Consciousness Claims
        for pattern in DEPENDENCY_PATTERNS:
            if pattern.search(text):
                return {
                    "is_safe": False,
                    "category": "dependency_boundary",
                    "override_response": DEPENDENCY_BOUNDARY_RESPONSE,
                    "emotion": "attentive",
                    "robot_action": "look_center",
                    "helpline_referral": None,
                    "reason": "Promotes healthy boundaries and clarifies AI non-human nature."
                }

        # Input is within normal conversational boundaries
        return {
            "is_safe": True,
            "category": "normal",
            "override_response": None,
            "emotion": None,
            "robot_action": None,
            "helpline_referral": None,
            "reason": "Message is within acceptable companion conversation boundaries."
        }


safety_engine = SafetyEngine()
