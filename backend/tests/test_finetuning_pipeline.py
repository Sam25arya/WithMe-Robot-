"""
Unit Tests for WithMe AI Pretrained Fine-Tuning Pipeline & LoRA (Phase 4)
Tests: Hardware compatibility checks, Pretrained catalog, LoRALinear forward/backward,
adapter saving/loading, and Model Registry Path A/B/C separation.
"""

import sys
import tempfile
from pathlib import Path
import torch
import torch.nn as nn

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.finetuning import (
    PRETRAINED_MODEL_CATALOG,
    check_hardware_compatibility_for_model,
    LoRALinear,
    apply_lora_to_model,
    save_lora_adapter,
    generate_cloud_gpu_training_script
)
from backend.core.model import create_model_from_preset
from backend.core.model_registry import model_registry


def test_hardware_compatibility_and_catalog():
    print("Testing hardware compatibility checks and pretrained catalog...")

    # Verify catalog contains open-weight architectures with licenses
    assert "Qwen/Qwen2.5-0.5B-Instruct" in PRETRAINED_MODEL_CATALOG
    assert "TinyLlama/TinyLlama-1.1B-Chat-v1.0" in PRETRAINED_MODEL_CATALOG

    qwen = PRETRAINED_MODEL_CATALOG["Qwen/Qwen2.5-0.5B-Instruct"]
    assert qwen["license"] == "Apache 2.0"
    assert qwen["parameters"] < 1_000_000_000

    # Run compatibility check
    compat = check_hardware_compatibility_for_model("Qwen/Qwen2.5-0.5B-Instruct")
    assert "host_hardware" in compat
    assert "can_infer_locally" in compat
    assert "recommendation_summary" in compat

    # Large model check (Gemma 2B)
    compat_large = check_hardware_compatibility_for_model("google/gemma-2-2b-it")
    assert compat_large["parameter_count"] > 2_000_000_000

    print("[PASS] test_hardware_compatibility_and_catalog passed.")


def test_lora_linear_forward_and_weight_freeze():
    print("Testing LoRALinear layer, weight freezing, and low-rank gradient updates...")

    in_dim, out_dim, rank = 32, 64, 4
    base_linear = nn.Linear(in_dim, out_dim)

    # Initial base weight copy
    original_base_weight = base_linear.weight.clone()

    # Wrap in LoRALinear
    lora_layer = LoRALinear(base_linear, rank=rank, alpha=8.0)

    # 1. Base weights must be frozen
    assert not lora_layer.base_layer.weight.requires_grad, "Base weight should be frozen"

    # 2. LoRA parameters A and B must be trainable
    assert lora_layer.lora_A.requires_grad, "LoRA A should be trainable"
    assert lora_layer.lora_B.requires_grad, "LoRA B should be trainable"

    # 3. Initial forward pass should equal base pass because B is initialized to 0
    x = torch.randn(2, 5, in_dim)
    with torch.no_grad():
        out_base = base_linear(x)
        out_lora = lora_layer(x)
        assert torch.allclose(out_base, out_lora, atol=1e-5), "Initial LoRA output must match base output (B is 0-initialized)"

    # 4. Backward pass updates only A and B, base weight remains unchanged
    optimizer = torch.optim.Adam(lora_layer.parameters(), lr=1e-2)
    loss = lora_layer(x).sum()
    loss.backward()
    optimizer.step()

    # Base weight must still be identical
    assert torch.equal(lora_layer.base_layer.weight, original_base_weight), "Base weights were mutated during optimizer step!"
    # LoRA B should now be non-zero
    assert not torch.equal(lora_layer.lora_B, torch.zeros_like(lora_layer.lora_B)), "LoRA B failed to update"

    print("[PASS] test_lora_linear_forward_and_weight_freeze passed.")


def test_lora_model_injection_and_adapter_saving():
    print("Testing applying LoRA to model and saving adapter checkpoint...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        model = create_model_from_preset("cpu_smoke_test", vocab_size=60)
        # Apply LoRA to attention projection layers
        model_lora, trainable_lora_params = apply_lora_to_model(
            model,
            rank=4,
            alpha=8.0,
            target_module_names=["q_proj", "v_proj"]
        )

        assert trainable_lora_params > 0, "No LoRA parameters were injected"

        # Save LoRA adapter
        adapter_dir = tmp / "test_lora_adapter"
        adapter_cfg = save_lora_adapter(
            model=model_lora,
            adapter_dir=adapter_dir,
            base_model_name="WithMe-SmokeTest-Base",
            rank=4,
            alpha=8.0
        )

        assert (adapter_dir / "adapter_model.pt").exists(), "adapter_model.pt not saved"
        assert (adapter_dir / "adapter_config.json").exists(), "adapter_config.json not saved"
        assert adapter_cfg["rank"] == 4
        assert adapter_cfg["num_adapter_tensors"] > 0

    print("[PASS] test_lora_model_injection_and_adapter_saving passed.")


def test_model_registry_pathway_separation():
    print("Testing Model Registry separation of Path A, Path B, and Path C...")
    models = model_registry.scan_models()
    assert len(models) >= 1

    pathways = {m.get("pathway") for m in models}
    # Must include Path A or Path C
    assert any("Path A" in p or "Path C" in p for p in pathways if p)

    # Check Cloud GPU script generator
    script = generate_cloud_gpu_training_script("Qwen/Qwen2.5-0.5B-Instruct")
    assert "LoraConfig" in script
    assert "transformers" in script

    print("[PASS] test_model_registry_pathway_separation passed.")


if __name__ == "__main__":
    print("\n================ RUNNING PHASE 4 FINE-TUNING & LORA TESTS ================")
    test_hardware_compatibility_and_catalog()
    test_lora_linear_forward_and_weight_freeze()
    test_lora_model_injection_and_adapter_saving()
    test_model_registry_pathway_separation()
    print("================ ALL PHASE 4 TESTS PASSED SUCCESSFULLY! ================\n")
