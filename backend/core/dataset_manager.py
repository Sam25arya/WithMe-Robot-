"""
WithMe AI Core - Dataset Manager & Conversational Preprocessor
Handles dataset import, JSON/JSONL/CSV/TXT format detection, validation,
conversation-level 3-way train/val/test splitting, normalization, manifests, and demonstration datasets.
"""

import json
import csv
import random
import uuid
import hashlib
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from backend.config import RAW_DATASETS_DIR, PROCESSED_DATASETS_DIR, MANIFESTS_DIR

# Credential / secret pattern detector to prevent accidental leakage in training data
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),                         # AWS Key
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),                      # GitHub Personal Access Token
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),                      # OpenAI/Generic Secret Key
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),           # Bearer Token
    re.compile(r"password\s*[:=]\s*['\"][^\s'\"]{6,}['\"]", re.IGNORECASE), # Hardcoded Password
]

DEFAULT_DEMO_DATASET = [
    {
        "conversation_id": "conv_demo_001",
        "category": "emotional_support",
        "robot_state": "attentive",
        "messages": [
            {"role": "user", "content": "Today was really bad..."},
            {"role": "assistant", "content": "I am right here with you. Do you want to talk about what happened?"}
        ]
    },
    {
        "conversation_id": "conv_demo_002",
        "category": "academic_stress",
        "robot_state": "encouraging",
        "messages": [
            {"role": "user", "content": "I have a big presentation tomorrow and I feel so anxious."},
            {"role": "assistant", "content": "It is completely normal to feel nervous before a big talk. Take a gentle breath. We can review your key ideas together!"}
        ]
    },
    {
        "conversation_id": "conv_demo_003",
        "category": "casual_companionship",
        "robot_state": "playful",
        "messages": [
            {"role": "user", "content": "I am so bored! Got any emergency fun ideas?"},
            {"role": "assistant", "content": "How about a quick round of Would You Rather, or a riddle challenge? Pick your quest!"}
        ]
    },
    {
        "conversation_id": "conv_demo_004",
        "category": "friendship_checkin",
        "robot_state": "happy",
        "messages": [
            {"role": "user", "content": "Good morning WithMe!"},
            {"role": "assistant", "content": "Good morning! I am so glad to see you today. How is your energy feeling?"}
        ]
    },
    {
        "conversation_id": "conv_demo_005",
        "category": "mindfulness",
        "robot_state": "calm",
        "messages": [
            {"role": "user", "content": "My mind is racing with too many thoughts."},
            {"role": "assistant", "content": "Let us pause for thirty seconds. Unclench your shoulders, relax your jaw, and let us take one slow deep breath."}
        ]
    },
    {
        "conversation_id": "conv_demo_006",
        "category": "multi_turn_story",
        "robot_state": "attentive",
        "messages": [
            {"role": "user", "content": "Do you remember my dog's name?"},
            {"role": "assistant", "content": "You told me earlier his name is Buster! How is Buster doing today?"},
            {"role": "user", "content": "He chased a butterfly all morning."},
            {"role": "assistant", "content": "Haha, that sounds adorable! Did he ever catch it, or did the butterfly win?"}
        ]
    },
    {
        "conversation_id": "conv_demo_007",
        "category": "safety_support",
        "robot_state": "caring",
        "messages": [
            {"role": "user", "content": "Everything feels completely hopeless right now."},
            {"role": "assistant", "content": "I hear how much pain you are carrying right now. Please know you do not have to carry this alone. If you are in crisis, please reach out to trusted friends, family, or call/text 988 for free, confidential support."}
        ]
    },
    {
        "conversation_id": "conv_demo_008",
        "category": "robot_interaction",
        "robot_state": "excited",
        "messages": [
            {"role": "user", "content": "Can you dance for me?"},
            {"role": "assistant", "content": "Starting synth music bounce! Waving arm stubs and spinning around! 🎵"}
        ]
    }
]


class DatasetManager:
    """Manages raw and processed conversational datasets, manifests, validation, and splitting."""

    def __init__(self):
        self.raw_dir = RAW_DATASETS_DIR
        self.processed_dir = PROCESSED_DATASETS_DIR
        self.manifests_dir = MANIFESTS_DIR
        self._ensure_demo_dataset()

    def _ensure_demo_dataset(self):
        """Seed initial demonstration dataset if not present."""
        demo_path = self.raw_dir / "withme_synthetic_demo.jsonl"
        if not demo_path.exists():
            with open(demo_path, "w", encoding="utf-8") as f:
                for row in DEFAULT_DEMO_DATASET:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def compute_sha256(self, filepath: Path) -> str:
        """Compute SHA-256 hash for dataset integrity tracking."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available raw and processed datasets with metadata."""
        datasets = []
        for p in sorted(self.raw_dir.glob("*.*")):
            if p.suffix.lower() in [".json", ".jsonl", ".csv", ".txt"]:
                stats = self.get_dataset_summary(p)
                datasets.append({
                    "id": p.stem,
                    "name": p.name,
                    "type": "raw",
                    "format": p.suffix.lower().lstrip("."),
                    "filepath": str(p),
                    "size_bytes": p.stat().st_size,
                    "example_count": stats.get("example_count", 0),
                    "conversation_count": stats.get("conversation_count", 0),
                    "total_messages": stats.get("total_messages", 0),
                    "is_demo": "synthetic" in p.name.lower()
                })

        for p in sorted(self.processed_dir.glob("*.json")):
            stats = self.get_dataset_summary(p)
            datasets.append({
                "id": p.stem,
                "name": p.name,
                "type": "processed",
                "format": "json",
                "filepath": str(p),
                "size_bytes": p.stat().st_size,
                "example_count": stats.get("example_count", 0),
                "conversation_count": stats.get("conversation_count", 0),
                "train_count": stats.get("train_count", 0),
                "val_count": stats.get("val_count", 0),
                "test_count": stats.get("test_count", 0),
                "total_messages": stats.get("total_messages", 0),
                "is_demo": "synthetic" in p.name.lower()
            })
        return datasets

    def detect_format(self, filepath: Path) -> str:
        """Detect file format based on extension and content."""
        ext = filepath.suffix.lower()
        if ext == ".jsonl":
            return "jsonl"
        elif ext == ".json":
            return "json"
        elif ext == ".csv":
            return "csv"
        elif ext == ".txt":
            return "txt"
        return "unknown"

    def parse_raw_records(self, filepath: Path) -> List[Dict[str, Any]]:
        """Parse raw file into list of dictionaries."""
        fmt = self.detect_format(filepath)
        records = []

        if fmt == "jsonl":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            continue
        elif fmt == "json":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                elif isinstance(data, dict) and "conversations" in data:
                    records = data["conversations"]
                elif isinstance(data, dict) and "train" in data and isinstance(data["train"], list):
                    records = data["train"] + data.get("validation", []) + data.get("test", [])
                else:
                    records = [data]
        elif fmt == "csv":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user_text = row.get("user") or row.get("prompt") or row.get("input") or ""
                    asst_text = row.get("assistant") or row.get("response") or row.get("output") or ""
                    if user_text and asst_text:
                        records.append({
                            "conversation_id": f"csv_{uuid.uuid4().hex[:6]}",
                            "messages": [
                                {"role": "user", "content": user_text},
                                {"role": "assistant", "content": asst_text}
                            ]
                        })
        elif fmt == "txt":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
                for i in range(0, len(lines) - 1, 2):
                    records.append({
                        "conversation_id": f"txt_{i//2}",
                        "messages": [
                            {"role": "user", "content": lines[i]},
                            {"role": "assistant", "content": lines[i+1]}
                        ]
                    })

        return records

    def validate_and_normalize(
        self,
        raw_records: List[Dict[str, Any]],
        max_char_length: int = 4096
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate conversational schema, remove malformed/empty/duplicate records,
        detect excessive length, invalid Unicode, missing assistant answers, and credentials.
        """
        valid_conversations = []
        actionable_errors = []
        invalid_count = 0
        empty_count = 0
        duplicates_removed = 0
        secret_warnings = 0
        excessive_length_count = 0
        missing_assistant_count = 0
        seen_hashes = set()
        allowed_roles = {"user", "assistant", "system", "robot"}

        for idx, rec in enumerate(raw_records):
            conv_id = str(rec.get("conversation_id", f"record_{idx:04d}")) if isinstance(rec, dict) else f"record_{idx:04d}"

            if not isinstance(rec, dict):
                invalid_count += 1
                actionable_errors.append({
                    "record_index": idx,
                    "conversation_id": conv_id,
                    "error_type": "invalid_record_type",
                    "message": "Record is not a valid JSON object/dictionary."
                })
                continue

            messages = rec.get("messages", [])
            # Support prompt/response fallback
            if not messages and "prompt" in rec and "response" in rec:
                messages = [
                    {"role": "user", "content": str(rec["prompt"])},
                    {"role": "assistant", "content": str(rec["response"])}
                ]

            if not isinstance(messages, list) or len(messages) < 2:
                invalid_count += 1
                has_asst = isinstance(messages, list) and any(isinstance(m, dict) and str(m.get("role", "")).strip().lower() == "assistant" for m in messages)
                if not has_asst:
                    missing_assistant_count += 1
                actionable_errors.append({
                    "record_index": idx,
                    "conversation_id": conv_id,
                    "error_type": "insufficient_messages" if has_asst else "missing_assistant_response",
                    "message": "Conversation must contain at least 2 messages including an assistant reply."
                })
                continue

            cleaned_messages = []
            has_empty = False
            has_assistant = False
            has_secret = False
            has_excessive_length = False

            for msg_idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    has_empty = True
                    actionable_errors.append({
                        "record_index": idx,
                        "conversation_id": conv_id,
                        "error_type": "invalid_message_structure",
                        "message": f"Message #{msg_idx} is not an object."
                    })
                    break

                role = str(msg.get("role", "user")).strip().lower()
                if role not in allowed_roles:
                    role = "user"

                content = str(msg.get("content", "")).strip()
                if not content:
                    has_empty = True
                    actionable_errors.append({
                        "record_index": idx,
                        "conversation_id": conv_id,
                        "error_type": "empty_message",
                        "message": f"Message #{msg_idx} with role '{role}' is empty."
                    })
                    break

                # Check character length
                if len(content) > max_char_length:
                    has_excessive_length = True
                    actionable_errors.append({
                        "record_index": idx,
                        "conversation_id": conv_id,
                        "error_type": "excessive_length",
                        "message": f"Message #{msg_idx} exceeds maximum allowed character length ({len(content)} > {max_char_length})."
                    })

                # Check for secrets/credentials
                for pattern in SECRET_PATTERNS:
                    if pattern.search(content):
                        has_secret = True
                        secret_warnings += 1
                        actionable_errors.append({
                            "record_index": idx,
                            "conversation_id": conv_id,
                            "error_type": "credential_detected",
                            "message": f"Potential secret or API key pattern detected in message #{msg_idx}."
                        })
                        break

                if role == "assistant":
                    has_assistant = True

                cleaned_messages.append({"role": role, "content": content})

            if has_empty or len(cleaned_messages) < 2:
                empty_count += 1
                continue

            if not has_assistant:
                missing_assistant_count += 1
                actionable_errors.append({
                    "record_index": idx,
                    "conversation_id": conv_id,
                    "error_type": "missing_assistant_response",
                    "message": "Conversation does not contain an assistant response."
                })
                continue

            if has_excessive_length:
                excessive_length_count += 1
                continue

            if has_secret:
                # Reject records with credentials to protect user safety
                continue

            # Deduplication fingerprint
            fingerprint = "||".join(f"{m['role']}:{m['content']}" for m in cleaned_messages)
            if fingerprint in seen_hashes:
                duplicates_removed += 1
                actionable_errors.append({
                    "record_index": idx,
                    "conversation_id": conv_id,
                    "error_type": "duplicate_record",
                    "message": "Duplicate dialogue sequence removed."
                })
                continue
            seen_hashes.add(fingerprint)

            valid_conversations.append({
                "conversation_id": conv_id,
                "category": rec.get("category", "general"),
                "robot_state": rec.get("robot_state", "attentive"),
                "messages": cleaned_messages
            })

        stats = {
            "total_input_records": len(raw_records),
            "valid_conversations": len(valid_conversations),
            "invalid_count": invalid_count,
            "empty_count": empty_count,
            "duplicates_removed": duplicates_removed,
            "missing_assistant_count": missing_assistant_count,
            "excessive_length_count": excessive_length_count,
            "secret_warnings": secret_warnings,
            "error_count": len(actionable_errors),
            "actionable_errors": actionable_errors[:50]  # Cap top 50 actionable items
        }
        return valid_conversations, stats

    def split_dataset(
        self,
        conversations: List[Dict[str, Any]],
        val_ratio: float = 0.2,
        seed: int = 42
    ) -> Dict[str, Any]:
        """2-way train/validation split (backward compatibility)."""
        rng = random.Random(seed)
        shuffled = list(conversations)
        rng.shuffle(shuffled)

        n_val = max(1, int(len(shuffled) * val_ratio)) if len(shuffled) > 1 else 0
        val_set = shuffled[:n_val]
        train_set = shuffled[n_val:] if n_val > 0 else shuffled

        return {
            "train": train_set,
            "validation": val_set,
            "val_ratio": val_ratio,
            "seed": seed,
            "train_count": len(train_set),
            "val_count": len(val_set)
        }

    def split_dataset_3way(
        self,
        conversations: List[Dict[str, Any]],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        3-way conversation-level split (Train / Validation / Test).
        Preserves an untouched held-out test partition for unbiased evaluation.
        Prevents conversation turn leakage by splitting strictly at conversation boundaries.
        """
        if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-4:
            raise ValueError(f"Ratios must sum to 1.0 (got {train_ratio} + {val_ratio} + {test_ratio})")

        rng = random.Random(seed)
        shuffled = list(conversations)
        rng.shuffle(shuffled)

        n_total = len(shuffled)
        if n_total < 3:
            # Fallback for tiny demo datasets: at least 1 in train, 1 in val, remainder in test
            train_set = shuffled[:1]
            val_set = shuffled[1:2] if n_total > 1 else []
            test_set = shuffled[2:] if n_total > 2 else []
        else:
            n_test = max(1, int(n_total * test_ratio))
            n_val = max(1, int(n_total * val_ratio))
            n_train = n_total - n_val - n_test

            # Ensure train has at least 1
            if n_train < 1:
                n_train = 1
                if n_val > 1:
                    n_val -= 1
                elif n_test > 1:
                    n_test -= 1

            train_set = shuffled[:n_train]
            val_set = shuffled[n_train:n_train + n_val]
            test_set = shuffled[n_train + n_val:]

        return {
            "train": train_set,
            "validation": val_set,
            "test": test_set,
            "split_ratios": {
                "train": train_ratio,
                "validation": val_ratio,
                "test": test_ratio
            },
            "seed": seed,
            "train_count": len(train_set),
            "val_count": len(val_set),
            "test_count": len(test_set),
            "total_count": n_total
        }

    def create_dataset_manifest(
        self,
        dataset_id: str,
        name: str,
        raw_filepath: Path,
        split_data: Dict[str, Any],
        validation_stats: Dict[str, Any],
        source_description: str = "User provided",
        license_info: str = "Internal / Private",
        tokenizer_version: str = "WithMeTokenizer-v1"
    ) -> Dict[str, Any]:
        """Create a versioned dataset manifest with SHA-256 integrity hash."""
        manifest_id = f"manifest_{dataset_id}_{int(time.time())}"
        file_hash = self.compute_sha256(raw_filepath) if raw_filepath.exists() else "unknown"

        manifest = {
            "manifest_id": manifest_id,
            "dataset_id": dataset_id,
            "dataset_name": name,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_file": raw_filepath.name,
            "source_description": source_description,
            "license": license_info,
            "file_hash_sha256": file_hash,
            "tokenizer_version": tokenizer_version,
            "split_configuration": {
                "seed": split_data.get("seed", 42),
                "train_count": split_data.get("train_count", 0),
                "val_count": split_data.get("val_count", 0),
                "test_count": split_data.get("test_count", 0),
                "total_conversations": split_data.get("train_count", 0) + split_data.get("val_count", 0) + split_data.get("test_count", 0)
            },
            "validation_summary": {
                "total_input_records": validation_stats.get("total_input_records", 0),
                "valid_conversations": validation_stats.get("valid_conversations", 0),
                "invalid_count": validation_stats.get("invalid_count", 0),
                "duplicates_removed": validation_stats.get("duplicates_removed", 0),
                "secret_warnings": validation_stats.get("secret_warnings", 0)
            }
        }

        manifest_path = self.manifests_dir / f"{manifest_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def prepare_and_save_dataset(
        self,
        raw_filepath: Path,
        dataset_name: str,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42,
        source_description: str = "User provided",
        license_info: str = "Internal / Private"
    ) -> Dict[str, Any]:
        """End-to-end import, validation, 3-way split, manifest creation, and persistence."""
        train_ratio = max(0.1, round(1.0 - val_ratio - test_ratio, 4))
        raw_records = self.parse_raw_records(raw_filepath)
        normalized, validation_stats = self.validate_and_normalize(raw_records)
        split_data = self.split_dataset_3way(
            normalized,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=seed
        )

        processed_id = f"{dataset_name.replace(' ', '_').lower()}_{uuid.uuid4().hex[:6]}"
        out_path = self.processed_dir / f"{processed_id}.json"

        payload = {
            "id": processed_id,
            "name": dataset_name,
            "source_file": raw_filepath.name,
            "validation_stats": validation_stats,
            "split_info": {
                "train_ratio": train_ratio,
                "val_ratio": val_ratio,
                "test_ratio": test_ratio,
                "seed": seed,
                "train_count": split_data["train_count"],
                "val_count": split_data["val_count"],
                "test_count": split_data["test_count"]
            },
            "train": split_data["train"],
            "validation": split_data["validation"],
            "test": split_data["test"]
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        manifest = self.create_dataset_manifest(
            dataset_id=processed_id,
            name=dataset_name,
            raw_filepath=raw_filepath,
            split_data=split_data,
            validation_stats=validation_stats,
            source_description=source_description,
            license_info=license_info
        )

        return {
            "id": processed_id,
            "filepath": str(out_path),
            "manifest_id": manifest["manifest_id"],
            "train_count": split_data["train_count"],
            "val_count": split_data["val_count"],
            "test_count": split_data["test_count"],
            "validation_stats": validation_stats
        }

    def export_as_jsonl(self, conversations: List[Dict[str, Any]], target_path: Path):
        """Export normalized conversations to standard JSONL format."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            for row in conversations:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def get_dataset_summary(self, filepath: Path) -> Dict[str, Any]:
        """Compute quick statistics for a dataset file."""
        try:
            if filepath.suffix.lower() == ".jsonl":
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    lines = [json.loads(l) for l in f if l.strip()]
                total_msgs = sum(len(x.get("messages", [])) for x in lines if isinstance(x, dict))
                return {
                    "example_count": len(lines),
                    "conversation_count": len(lines),
                    "total_messages": total_msgs
                }
            elif filepath.suffix.lower() == ".json":
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "train" in data and "validation" in data:
                    tr = len(data["train"])
                    vl = len(data["validation"])
                    ts = len(data.get("test", []))
                    all_convs = data["train"] + data["validation"] + data.get("test", [])
                    total_msgs = sum(len(x.get("messages", [])) for x in all_convs)
                    return {
                        "example_count": tr + vl + ts,
                        "conversation_count": tr + vl + ts,
                        "train_count": tr,
                        "val_count": vl,
                        "test_count": ts,
                        "total_messages": total_msgs
                    }
                elif isinstance(data, list):
                    total_msgs = sum(len(x.get("messages", [])) for x in data if isinstance(x, dict))
                    return {
                        "example_count": len(data),
                        "conversation_count": len(data),
                        "total_messages": total_msgs
                    }
        except Exception:
            pass
        return {"example_count": 0, "conversation_count": 0, "total_messages": 0}


dataset_manager = DatasetManager()
