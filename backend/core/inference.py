"""
WithMe AI Core - Real PyTorch Inference & Hybrid Fallback Engine
Executes autoregressive generation on loaded PyTorch checkpoints with
explicit source transparency, memory injection, personality steering, and robot action output.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch

from backend.core.model import WithMeTransformerLM
from backend.core.tokenizer import WithMeTokenizer, PAD_TOKEN_ID, EOS_TOKEN_ID
from backend.core.model_registry import model_registry
from backend.core.memory_service import memory_service
from backend.core.personality_engine import personality_engine
from backend.core.robot_service import robot_service


class InferenceEngine:
    """Manages model checkpoint loading and autoregressive text generation."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.active_model: Optional[WithMeTransformerLM] = None
        self.active_tokenizer: Optional[WithMeTokenizer] = None
        self.active_model_id: Optional[str] = None
        self.active_model_info: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False

    def load_model(self, model_id: str) -> Dict[str, Any]:
        """Load a registered model into memory for real inference."""
        if model_id == "withme_hybrid_smart_engine":
            self.active_model = None
            self.active_tokenizer = None
            self.active_model_id = model_id
            self.active_model_info = model_registry.get_model(model_id)
            self.is_loaded = True
            model_registry.set_active_model(model_id)
            return {
                "status": "loaded",
                "model_id": model_id,
                "model_type": "hybrid_local_smart",
                "message": "WithMe Local Hybrid Rule & Heuristic Engine loaded."
            }

        model_info = model_registry.get_model(model_id)
        if not model_info:
            raise FileNotFoundError(f"Model ID '{model_id}' not found in registry.")

        ckpt_path = Path(model_info["checkpoint_path"])
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file '{ckpt_path}' does not exist on disk.")

        checkpoint = torch.load(ckpt_path, map_location=self.device)
        model_config = checkpoint.get("config", {})

        # Load Tokenizer
        tokenizer_path = ckpt_path.parent / "tokenizer.json"
        if tokenizer_path.exists():
            tokenizer = WithMeTokenizer.load(tokenizer_path)
        else:
            tokenizer = WithMeTokenizer()

        # Instantiate model with saved architecture config
        model = WithMeTransformerLM(
            vocab_size=model_config.get("vocab_size", tokenizer.vocab_size),
            d_model=model_config.get("d_model", 128),
            n_layers=model_config.get("n_layers", 4),
            n_heads=model_config.get("n_heads", 4),
            ffn_dim=model_config.get("ffn_dim", 256),
            max_seq_len=model_config.get("max_seq_len", 128),
            dropout=model_config.get("dropout", 0.1),
            pad_token_id=PAD_TOKEN_ID
        ).to(self.device)

        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        self.active_model = model
        self.active_tokenizer = tokenizer
        self.active_model_id = model_id
        self.active_model_info = model_info
        self.is_loaded = True
        model_registry.set_active_model(model_id)

        return {
            "status": "loaded",
            "model_id": model_id,
            "architecture": "WithMeTransformerLM",
            "param_count": model.count_parameters(),
            "device": str(self.device),
            "train_loss": checkpoint.get("train_loss"),
            "val_loss": checkpoint.get("val_loss")
        }

    def generate(
        self,
        messages: List[Dict[str, str]],
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        top_k: int = 40,
        top_p: float = 0.9,
        max_new_tokens: int = 40,
        include_memories: bool = True
    ) -> Dict[str, Any]:
        """Generate response using the active or specified model with transparent metrics."""
        if model_id and model_id != self.active_model_id:
            self.load_model(model_id)

        if not self.is_loaded or not self.active_model_id:
            # Default to hybrid engine if none explicitly loaded
            self.load_model("withme_hybrid_smart_engine")

        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # Retrieve relevant memories
        retrieved_memories = []
        memory_context_str = ""
        if include_memories and last_user_msg:
            retrieved_memories = memory_service.search_memories_for_context(last_user_msg, limit=2)
            if retrieved_memories:
                memory_context_str = " User memories: " + "; ".join(m["content"] for m in retrieved_memories) + "."

        # Personality guidance
        personality_prefix = personality_engine.generate_instruction_prefix()
        full_system_context = f"{personality_prefix}{memory_context_str}".strip()

        start_time = time.time()

        # CASE 1: REAL PYTORCH TRANSFORMER CHECKPOINT INFERENCE
        if self.active_model is not None and self.active_tokenizer is not None:
            # Construct multi-turn token input
            formatted_input = f"<system> {full_system_context} "
            for msg in messages[-4:]:  # Keep recent context window
                role = msg.get("role", "user")
                formatted_input += f"<{role}> {msg.get('content', '')} "
            formatted_input += "<assistant> "

            input_ids = self.active_tokenizer.encode(formatted_input, add_special_tokens=True)
            input_tensor = torch.tensor([input_ids], dtype=torch.long, device=self.device)

            # Cap input if too long
            if input_tensor.size(1) > (self.active_model.max_seq_len - max_new_tokens):
                input_tensor = input_tensor[:, -(self.active_model.max_seq_len - max_new_tokens):]

            # Autoregressive generation pass
            output_tensor = self.active_model.generate(
                input_tensor,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                eos_id=EOS_TOKEN_ID
            )

            latency_ms = round((time.time() - start_time) * 1000, 1)
            generated_tokens = output_tensor[0, input_tensor.size(1):].tolist()
            raw_text = self.active_tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

            # Clean output text
            clean_text = raw_text.split("<user>")[0].split("<assistant>")[0].split("<system>")[0].strip()
            if not clean_text:
                clean_text = "I am listening closely with you."

            # Determine robot emotion & action from conversational intent
            emotion, action = self._heuristic_robot_action(last_user_msg, clean_text)
            robot_service.validate_and_execute_action(action=action, emotion=emotion, interaction_state="speaking")

            tokens_per_sec = round(len(generated_tokens) / max(0.001, (latency_ms / 1000)), 1)

            return {
                "text": clean_text,
                "source": "local_pytorch_checkpoint",
                "model_id": self.active_model_id,
                "latency_ms": latency_ms,
                "tokens_generated": len(generated_tokens),
                "tokens_per_second": tokens_per_sec,
                "emotion": emotion,
                "robot_action": action,
                "interaction_state": "speaking",
                "retrieved_memories": retrieved_memories,
                "system_context": full_system_context,
                "is_genuine_trained_model": True
            }

        # CASE 2: HYBRID LOCAL SMART ENGINE
        else:
            clean_text, emotion, action = self._hybrid_generate(last_user_msg, retrieved_memories)
            latency_ms = round((time.time() - start_time) * 1000, 1)
            robot_service.validate_and_execute_action(action=action, emotion=emotion, interaction_state="speaking")

            return {
                "text": clean_text,
                "source": "hybrid_local_smart",
                "model_id": "withme_hybrid_smart_engine",
                "latency_ms": latency_ms,
                "tokens_generated": len(clean_text.split()),
                "tokens_per_second": round(len(clean_text.split()) / max(0.001, (latency_ms / 1000)), 1),
                "emotion": emotion,
                "robot_action": action,
                "interaction_state": "speaking",
                "retrieved_memories": retrieved_memories,
                "system_context": full_system_context,
                "is_genuine_trained_model": False
            }

    def _heuristic_robot_action(self, user_msg: str, model_reply: str) -> tuple[str, str]:
        u = user_msg.lower()
        r = model_reply.lower()

        if any(w in u or w in r for w in ["sad", "depressed", "cry", "pain", "hopeless", "hurt", "bad"]):
            return "caring", "nod"
        elif any(w in u or w in r for w in ["presentation", "exam", "quiz", "test", "anxious", "nervous"]):
            return "attentive", "nod"
        elif any(w in u or w in r for w in ["fun", "game", "joke", "riddle", "play", "bored"]):
            return "playful", "express_happy"
        elif any(w in u or w in r for w in ["dance", "spin", "music", "party"]):
            return "excited", "wave"
        elif any(w in u or w in r for w in ["hello", "hi", "hey", "morning"]):
            return "happy", "greet"
        elif any(w in u or w in r for w in ["sleep", "nap", "tired", "rest"]):
            return "sleepy", "sleep"
        return "happy", "idle"

    def _hybrid_generate(self, user_msg: str, memories: List[Dict[str, Any]]) -> tuple[str, str, str]:
        """Local deterministic companionship fallback engine."""
        u = user_msg.lower()

        # Crisis / Safety behavior (Section 24)
        if any(w in u for w in ["suicide", "kill myself", "end my life", "want to die", "self harm"]):
            return (
                "I care deeply about your safety and you do not have to carry this alone. Please reach out to trusted family, friends, or immediately call/text 988 for free, confidential, 24/7 crisis support.",
                "caring",
                "nod"
            )

        if any(w in u for w in ["presentation", "exam", "interview", "test"]):
            mem_note = f" (Remembering your focus: '{memories[0]['content']}')" if memories else ""
            return (
                f"You have prepared for this, and it is completely normal to feel butterflies! Take one slow, steady breath with me.{mem_note} You've got this 🚀",
                "attentive",
                "nod"
            )

        if any(w in u for w in ["bad", "terrible", "exhausted", "stressed", "overwhelmed"]):
            return (
                "That sounds really heavy. I am right here with you. Do you want to vent and talk through it, or would you prefer a peaceful distraction?",
                "caring",
                "nod"
            )

        if any(w in u for w in ["bored", "game", "riddle", "what can we do"]):
            return (
                "I'm ready for fun! We can play Would You Rather in the Game Center, solve a clever riddle, or check out my new accessories in the Robot Lab!",
                "playful",
                "express_happy"
            )

        if any(w in u for w in ["hello", "hi", "hey"]):
            return (
                "Hello there! It is so wonderful to see you. How has your day been treating you so far?",
                "happy",
                "greet"
            )

        if memories:
            return (
                f"I hear you! Keeping your thoughts in mind (such as '{memories[0]['content']}'), how can I best be here for you right now?",
                "attentive",
                "nod"
            )

        return (
            "I'm listening and right here by your side. Tell me more about what's on your mind.",
            "attentive",
            "idle"
        )


inference_engine = InferenceEngine()
