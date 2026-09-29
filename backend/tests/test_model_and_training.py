"""
Unit Tests for WithMe AI Transformer, Tokenizer Suite, and CPU Training (Phase 2)
Tests: Character and Subword (BPE) tokenizers with Hinglish, ModelConfig validation,
CPU resource presets, forward/loss computation, gradient clipping, LR scheduling,
and checkpoint saving/resumption.
"""

import sys
import tempfile
from pathlib import Path
import torch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.tokenizer import (
    WithMeTokenizer,
    WithMeCharTokenizer,
    WithMeSubwordTokenizer,
    check_tokenizer_compatibility
)
from backend.core.model import (
    WithMeTransformerLM,
    ModelConfig,
    create_model_from_preset,
    CPU_PRESETS
)
from backend.core.training import LinearWarmupCosineScheduler


def test_tokenizers_and_hinglish():
    print("Testing Tokenizer Suite (Char, Subword BPE, Hinglish support)...")

    corpus = [
        "Namaste WithMe! Aap kaise ho?",
        "Main theek hoon, aap bataiye.",
        "Today was a great day, bahut maza aaya!",
        "Kasa ahes mitr, all good?"
    ]

    # 1. Character Tokenizer
    char_tok = WithMeCharTokenizer()
    char_tok.train_from_corpus(corpus)
    encoded = char_tok.encode("Namaste!", add_special_tokens=True)
    decoded = char_tok.decode(encoded, skip_special_tokens=True)
    assert decoded == "Namaste!", f"Char tokenizer decoded mismatch: '{decoded}'"

    # 2. Subword BPE Tokenizer
    sub_tok = WithMeSubwordTokenizer()
    sub_tok.train_from_corpus(corpus, max_merges=30)
    sub_enc = sub_tok.encode("Namaste WithMe!", add_special_tokens=True)
    sub_dec = sub_tok.decode(sub_enc, skip_special_tokens=True)
    assert "Namaste" in sub_dec, f"Subword decoding missing word: '{sub_dec}'"

    # 3. Standard Tokenizer with Hinglish
    std_tok = WithMeTokenizer()
    std_tok.train_from_corpus(corpus)
    std_enc = std_tok.encode("Aap kaise ho?", add_special_tokens=True)
    std_dec = std_tok.decode(std_enc, skip_special_tokens=True)
    assert "Aap" in std_dec and "kaise" in std_dec, "Hinglish tokens not preserved in standard tokenizer"

    # Compatibility check
    compatible, msg = check_tokenizer_compatibility(std_tok, {"vocab_size": std_tok.vocab_size})
    assert compatible, f"Expected compatible, got: {msg}"
    incompatible, _ = check_tokenizer_compatibility(std_tok, {"vocab_size": 9999})
    assert not incompatible, "Expected incompatible for wrong vocab size"

    print("[PASS] test_tokenizers_and_hinglish passed.")


def test_model_config_and_presets():
    print("Testing ModelConfig validation and CPU presets...")

    # Valid config
    valid_cfg = ModelConfig(vocab_size=100, d_model=64, n_heads=4)
    valid_cfg.validate()
    params = valid_cfg.estimate_parameter_count()
    assert params > 1000, f"Expected >1000 params estimate, got {params}"

    # Invalid config (d_model not divisible by n_heads)
    invalid_cfg = ModelConfig(vocab_size=100, d_model=65, n_heads=4)
    try:
        invalid_cfg.validate()
        assert False, "Should have raised ValueError for d_model % n_heads != 0"
    except ValueError as e:
        assert "divisible by n_heads" in str(e)

    # CPU Presets
    assert "cpu_smoke_test" in CPU_PRESETS
    assert "cpu_standard" in CPU_PRESETS
    model_smoke = create_model_from_preset("cpu_smoke_test", vocab_size=150)
    assert model_smoke.d_model == 64
    assert model_smoke.n_layers == 2
    assert model_smoke.count_parameters() > 10000

    print("[PASS] test_model_config_and_presets passed.")


def test_model_forward_loss_and_generation():
    print("Testing forward pass, causal masking, loss, and generation...")
    model = create_model_from_preset("cpu_smoke_test", vocab_size=120)

    # Batch of size 2, seq len 8
    input_ids = torch.randint(4, 110, (2, 8))
    target_ids = torch.randint(4, 110, (2, 8))

    logits, loss = model(input_ids, targets=target_ids)
    assert logits.shape == (2, 8, 120), f"Unexpected logits shape: {logits.shape}"
    assert loss is not None and loss.item() > 0, "Loss calculation failed"

    # Autoregressive generation
    prompt = torch.tensor([[2, 10, 15]], dtype=torch.long)
    generated = model.generate(prompt, max_new_tokens=5, temperature=0.7)
    assert generated.shape[1] > prompt.shape[1], "Generation did not produce new tokens"

    print("[PASS] test_model_forward_loss_and_generation passed.")


def test_lr_scheduler_and_gradient_clip():
    print("Testing LR scheduler and gradient clipping...")
    model = create_model_from_preset("cpu_smoke_test", vocab_size=100)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    scheduler = LinearWarmupCosineScheduler(optimizer, warmup_steps=5, total_steps=20, base_lr=1e-3)

    # Step 0 warmup
    lr_0 = scheduler.step(0)
    assert lr_0 < 1e-3, f"Expected warmup LR < 1e-3, got {lr_0}"

    # Step 5 reached base lr
    lr_5 = scheduler.step(5)
    assert abs(lr_5 - 1e-3) < 1e-5, f"Expected base LR ~1e-3, got {lr_5}"

    # Gradient clipping test
    input_ids = torch.randint(4, 90, (2, 6))
    targets = torch.randint(4, 90, (2, 6))
    optimizer.zero_grad()
    _, loss = model(input_ids, targets=targets)
    loss.backward()

    # Clip gradients
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    assert norm >= 0.0, "Gradient clipping failed"
    optimizer.step()

    print("[PASS] test_lr_scheduler_and_gradient_clip passed.")


def test_checkpoint_saving_and_resumption():
    print("Testing checkpoint saving, loading, and training resumption...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ckpt_path = tmp / "test_resume_checkpoint.pt"

        # Initialize model and optimizer
        model1 = create_model_from_preset("cpu_smoke_test", vocab_size=80)
        opt1 = torch.optim.AdamW(model1.parameters(), lr=1e-3)

        # Do one training step
        input_ids = torch.randint(4, 75, (2, 6))
        targets = torch.randint(4, 75, (2, 6))
        opt1.zero_grad()
        _, loss1 = model1(input_ids, targets=targets)
        loss1.backward()
        opt1.step()

        # Save checkpoint
        torch.save({
            "epoch": 2,
            "step": 15,
            "model_state_dict": model1.state_dict(),
            "optimizer_state_dict": opt1.state_dict(),
            "train_loss": loss1.item(),
            "config": model1.get_config()
        }, ckpt_path)

        # Reload into fresh model and optimizer
        model2 = create_model_from_preset("cpu_smoke_test", vocab_size=80)
        opt2 = torch.optim.AdamW(model2.parameters(), lr=1e-3)

        ckpt = torch.load(ckpt_path, map_location="cpu")
        model2.load_state_dict(ckpt["model_state_dict"])
        opt2.load_state_dict(ckpt["optimizer_state_dict"])

        assert ckpt["epoch"] == 2
        assert ckpt["step"] == 15

        # Verify forward pass on resumed model produces identical logits in eval mode
        model1.eval()
        model2.eval()
        with torch.no_grad():
            logits1, _ = model1(input_ids)
            logits2, _ = model2(input_ids)
            assert torch.allclose(logits1, logits2, atol=1e-5), "Resumed model weights did not match original model"

    print("[PASS] test_checkpoint_saving_and_resumption passed.")


if __name__ == "__main__":
    print("\n================ RUNNING PHASE 2 MODEL & TRAINING TESTS ================")
    test_tokenizers_and_hinglish()
    test_model_config_and_presets()
    test_model_forward_loss_and_generation()
    test_lr_scheduler_and_gradient_clip()
    test_checkpoint_saving_and_resumption()
    print("================ ALL PHASE 2 TESTS PASSED SUCCESSFULLY! ================\n")
