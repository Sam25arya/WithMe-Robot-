"""
WithMe AI Core - Pretrained Model Fine-Tuning Pipeline & LoRA Engine (Phase 4)
Maintains strict separation between:
- Path A: From-scratch experimental Transformer models
- Path B: Pretrained open-weight language models with Low-Rank Adaptation (LoRA)

Features:
1. Hardware & storage safety checker (RAM, CPU, disk, model size budget).
2. LoRALinear module implementing h = x W0^T + (alpha / r) * x A^T B^T.
3. LoRA adapter injection, checkpoint saving (adapter_model.pt, adapter_config.json).
4. Pretrained catalog registry with licenses, parameter counts, and resource requirements.
5. Cloud-GPU training export script generator for remote execution.
"""

import math
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import torch
import torch.nn as nn

from backend.config import FINETUNED_MODELS_DIR, ADAPTERS_DIR, get_hardware_info


# Curated catalog of compatible open-weight models with explicit licensing & hardware specs
PRETRAINED_MODEL_CATALOG: Dict[str, Dict[str, Any]] = {
    "Qwen/Qwen2.5-0.5B-Instruct": {
        "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "name": "Qwen 2.5 (0.5B Instruct)",
        "family": "Qwen",
        "parameters": 490_000_000,
        "license": "Apache 2.0",
        "download_size_gb": 1.0,
        "ram_required_inference_gb": 2.5,
        "ram_required_lora_train_gb": 6.0,
        "context_length": 4096,
        "recommended_device": "CPU / CUDA",
        "description": "Ultra-compact open-weight model capable of basic CPU inference on modern laptops."
    },
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {
        "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "name": "TinyLlama (1.1B Chat)",
        "family": "Llama",
        "parameters": 1_100_000_000,
        "license": "Apache 2.0",
        "download_size_gb": 2.2,
        "ram_required_inference_gb": 4.5,
        "ram_required_lora_train_gb": 10.0,
        "context_length": 2048,
        "recommended_device": "CPU / CUDA",
        "description": "Standard 1B parameter open-weight baseline for lightweight dialogue research."
    },
    "google/gemma-2-2b-it": {
        "model_id": "google/gemma-2-2b-it",
        "name": "Gemma 2 (2B Instruct)",
        "family": "Gemma",
        "parameters": 2_600_000_000,
        "license": "Gemma Terms of Use",
        "download_size_gb": 5.2,
        "ram_required_inference_gb": 8.0,
        "ram_required_lora_train_gb": 16.0,
        "context_length": 8192,
        "recommended_device": "CUDA GPU / Cloud",
        "description": "High-quality 2B model. Local training requires 16+ GB RAM or external Cloud GPU."
    }
}


def check_hardware_compatibility_for_model(model_identifier: str) -> Dict[str, Any]:
    """
    Inspect host RAM, available disk space, and compute device before permitting downloads or training.
    """
    hw = get_hardware_info()
    spec = PRETRAINED_MODEL_CATALOG.get(model_identifier, {
        "name": model_identifier,
        "parameters": 1_000_000_000,
        "download_size_gb": 3.0,
        "ram_required_inference_gb": 5.0,
        "ram_required_lora_train_gb": 12.0
    })

    ram_avail = hw.get("ram_available_gb", 4.0)
    disk_free = hw.get("disk_free_gb", 10.0)
    has_cuda = hw.get("cuda_available", False)

    has_enough_disk = disk_free >= (spec["download_size_gb"] * 2.0)  # Need space for weights + temp
    can_infer_local = ram_avail >= spec["ram_required_inference_gb"]
    can_train_local = (ram_avail >= spec["ram_required_lora_train_gb"]) or has_cuda

    recommendation = []
    if not has_enough_disk:
        recommendation.append(f"Insufficient disk space ({disk_free} GB free, need ~{spec['download_size_gb'] * 2} GB).")
    if not can_infer_local:
        recommendation.append(f"Available RAM ({ram_avail} GB) is below recommended inference threshold ({spec['ram_required_inference_gb']} GB).")
    if not can_train_local:
        recommendation.append(f"Local CPU training not recommended (needs {spec['ram_required_lora_train_gb']} GB RAM or dedicated GPU). Use the provided Cloud GPU configuration.")

    is_safe_to_proceed = has_enough_disk and can_infer_local

    return {
        "model_id": model_identifier,
        "model_name": spec.get("name", model_identifier),
        "license": spec.get("license", "Unknown"),
        "parameter_count": spec["parameters"],
        "host_hardware": {
            "ram_total_gb": hw.get("ram_total_gb"),
            "ram_available_gb": ram_avail,
            "disk_free_gb": disk_free,
            "compute_device": hw.get("compute_device")
        },
        "requirements": {
            "download_size_gb": spec["download_size_gb"],
            "inference_ram_gb": spec["ram_required_inference_gb"],
            "training_ram_gb": spec["ram_required_lora_train_gb"]
        },
        "can_infer_locally": can_infer_local,
        "can_train_locally": can_train_local,
        "is_safe_to_proceed": is_safe_to_proceed,
        "recommendation_summary": " | ".join(recommendation) if recommendation else "Hardware is compatible for local execution."
    }


class LoRALinear(nn.Module):
    """
    Low-Rank Adaptation (LoRA) Linear layer.
    Freezes original base layer W0 and trains low-rank decomposition matrices B and A:
    output = original_linear(x) + (scaling * x @ A^T @ B^T)
    """

    def __init__(
        self,
        base_layer: nn.Linear,
        rank: int = 4,
        alpha: float = 8.0,
        dropout: float = 0.05
    ):
        super().__init__()
        self.base_layer = base_layer
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank if rank > 0 else 1.0

        # Freeze the base layer weights
        self.base_layer.weight.requires_grad = False
        if self.base_layer.bias is not None:
            self.base_layer.bias.requires_grad = False

        in_features = base_layer.in_features
        out_features = base_layer.out_features

        # LoRA trainable low-rank matrices
        self.lora_A = nn.Parameter(torch.zeros(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))
        self.dropout = nn.Dropout(p=dropout) if dropout > 0.0 else nn.Identity()

        # Initialize: A with Gaussian, B with Zeros so initial delta W is exactly 0
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Base frozen forward pass
        base_out = self.base_layer(x)
        # Low-rank adapter forward pass
        # x shape: [B, T, in_features]
        # x @ A^T -> [B, T, rank]
        # [B, T, rank] @ B^T -> [B, T, out_features]
        lora_out = (self.dropout(x) @ self.lora_A.t()) @ self.lora_B.t()
        return base_out + (lora_out * self.scaling)


def apply_lora_to_model(
    model: nn.Module,
    rank: int = 4,
    alpha: float = 8.0,
    target_module_names: List[str] = ["q_proj", "v_proj"]
) -> Tuple[nn.Module, int]:
    """
    Traverse model modules, replace target linear layers with LoRALinear,
    and return modified model with count of newly trainable LoRA parameters.
    """
    trainable_lora_params = 0

    for name, module in list(model.named_modules()):
        for target in target_module_names:
            if hasattr(module, target):
                sub_layer = getattr(module, target)
                if isinstance(sub_layer, nn.Linear):
                    lora_wrapper = LoRALinear(sub_layer, rank=rank, alpha=alpha)
                    setattr(module, target, lora_wrapper)
                    trainable_lora_params += lora_wrapper.lora_A.numel() + lora_wrapper.lora_B.numel()

    return model, trainable_lora_params


def save_lora_adapter(
    model: nn.Module,
    adapter_dir: Path,
    base_model_name: str,
    rank: int = 4,
    alpha: float = 8.0
) -> Dict[str, Any]:
    """Save only the trained LoRA adapter weights and metadata configuration."""
    adapter_dir.mkdir(parents=True, exist_ok=True)
    lora_state = {}

    for name, param in model.named_parameters():
        if "lora_A" in name or "lora_B" in name:
            lora_state[name] = param.data.cpu()

    adapter_weights_file = adapter_dir / "adapter_model.pt"
    adapter_config_file = adapter_dir / "adapter_config.json"

    torch.save(lora_state, adapter_weights_file)

    config_data = {
        "adapter_type": "LoRA",
        "base_model": base_model_name,
        "rank": rank,
        "alpha": alpha,
        "num_adapter_tensors": len(lora_state),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "weights_file": adapter_weights_file.name
    }

    with open(adapter_config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    return config_data


def generate_cloud_gpu_training_script(
    model_identifier: str = "Qwen/Qwen2.5-0.5B-Instruct",
    dataset_name: str = "withme_conversational_v1"
) -> str:
    """
    Generate an executable Python script for Google Colab, RunPod, or Lambda Labs
    for users wishing to train larger models on free/cloud GPUs.
    """
    return f"""# WithMe AI — Cloud GPU Fine-Tuning Script
# Designed for Google Colab (T4 / A100) or RunPod
# Model: {model_identifier} | Dataset: {dataset_name}

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

MODEL_ID = "{model_identifier}"
OUTPUT_DIR = "./withme_lora_adapter"

print("Checking GPU device...")
assert torch.cuda.is_available(), "CUDA GPU required for cloud training script."
print(f"Active GPU: {{torch.cuda.get_device_name(0)}}")

# 1. Load Tokenizer & Model
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto"
)

# 2. Configure LoRA (PEFT)
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

print("Model is ready for instruction fine-tuning!")
# Next: Load WithMe JSONL dataset and launch HuggingFace SFTTrainer / Trainer.
"""
