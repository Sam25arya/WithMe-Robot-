"""
WithMe AI Core - Model Registry (Phase 4)
Manages local model checkpoints, pretrained models, LoRA adapters, metadata configurations,
and active model state, maintaining transparent separation between Path A and Path B models.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import CHECKPOINTS_DIR, EXPERIMENTAL_MODELS_DIR, FINETUNED_MODELS_DIR, ADAPTERS_DIR
from backend.core.finetuning import PRETRAINED_MODEL_CATALOG


class ModelRegistry:
    """Discovers, catalogs, and manages WithMe model versions across Path A and Path B."""

    def __init__(self):
        self.checkpoints_dir = CHECKPOINTS_DIR
        self.adapters_dir = ADAPTERS_DIR
        self.active_model_id: Optional[str] = None
        self.active_model_metadata: Optional[Dict[str, Any]] = None

    def scan_models(self) -> List[Dict[str, Any]]:
        """Scan checkpoints and adapter storage directories for registered models."""
        models = []

        # PATH A: From-Scratch Experimental Checkpoints
        for job_dir in sorted(self.checkpoints_dir.glob("job_*")):
            if not job_dir.is_dir():
                continue
            config_file = job_dir / "model_config.json"
            pt_files = sorted(job_dir.glob("*.pt"))
            if not pt_files:
                continue

            latest_pt = pt_files[-1]
            meta = {}
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            model_id = job_dir.name
            size_mb = round(latest_pt.stat().st_size / (1024 * 1024), 2)
            models.append({
                "model_id": model_id,
                "name": meta.get("model_name", f"WithMe Transformer ({model_id})"),
                "pathway": "Path A (From-Scratch Experimental)",
                "development_type": "from_scratch",
                "architecture": meta.get("architecture", "WithMeTransformerLM"),
                "param_count": meta.get("param_count", 0),
                "checkpoint_path": str(latest_pt),
                "checkpoint_file": latest_pt.name,
                "config_path": str(config_file) if config_file.exists() else None,
                "size_mb": size_mb,
                "created_at": latest_pt.stat().st_mtime,
                "train_loss": meta.get("latest_train_loss"),
                "val_loss": meta.get("latest_val_loss"),
                "license": "Internal Research / Apache 2.0",
                "is_active": (self.active_model_id == model_id)
            })

        # PATH B: LoRA Adapters for Pretrained Models
        for adapter_dir in sorted(self.adapters_dir.glob("*")):
            if not adapter_dir.is_dir():
                continue
            config_file = adapter_dir / "adapter_config.json"
            weights_file = adapter_dir / "adapter_model.pt"
            if not weights_file.exists() or not config_file.exists():
                continue

            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                adapter_id = adapter_dir.name
                size_mb = round(weights_file.stat().st_size / (1024 * 1024), 2)
                models.append({
                    "model_id": adapter_id,
                    "name": f"LoRA Adapter ({cfg.get('base_model', 'Pretrained')})",
                    "pathway": "Path B (Pretrained Model Fine-Tuning)",
                    "development_type": "finetuned_adapter",
                    "architecture": f"LoRA (Rank {cfg.get('rank', 4)}, Alpha {cfg.get('alpha', 8)})",
                    "base_model": cfg.get("base_model"),
                    "param_count": cfg.get("num_adapter_tensors", 0),
                    "checkpoint_path": str(weights_file),
                    "checkpoint_file": weights_file.name,
                    "config_path": str(config_file),
                    "size_mb": size_mb,
                    "created_at": weights_file.stat().st_mtime,
                    "license": "Inherits base model license",
                    "is_active": (self.active_model_id == adapter_id)
                })
            except Exception:
                pass

        # Built-in Hybrid Smart Fallback (Deterministic Rule-Based Conversational Engine)
        models.append({
            "model_id": "withme_hybrid_smart_engine",
            "name": "WithMe Local Hybrid Rule & Heuristic Engine",
            "pathway": "Path C (Hybrid Companion Heuristics)",
            "development_type": "hybrid_local_smart",
            "architecture": "Rule-Based Intent & Knowledge Retrieval",
            "param_count": 0,
            "checkpoint_path": "builtin://hybrid_engine",
            "checkpoint_file": "hybrid_smart_engine.py",
            "config_path": None,
            "size_mb": 0.1,
            "created_at": time.time(),
            "train_loss": None,
            "val_loss": None,
            "license": "Internal WithMe Core",
            "is_active": (self.active_model_id == "withme_hybrid_smart_engine") or (self.active_model_id is None and len(models) == 0)
        })

        return models

    def list_pretrained_catalog(self) -> List[Dict[str, Any]]:
        """Return list of authorized open-weight models available for fine-tuning."""
        return list(PRETRAINED_MODEL_CATALOG.values())

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        for m in self.scan_models():
            if m["model_id"] == model_id:
                return m
        return None

    def set_active_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        model = self.get_model(model_id)
        if model:
            self.active_model_id = model_id
            self.active_model_metadata = model
            return model
        return None


model_registry = ModelRegistry()
