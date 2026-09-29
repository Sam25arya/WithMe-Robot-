"""
WithMe AI Core - Comprehensive Automated Test Suite
Verifies Tokenizer, Dataset splitting, Model init, Forward pass, Loss calculation,
Optimizer step, Checkpoint save/load, Inference, Memory CRUD, and Robot actions.
"""

import sys
from pathlib import Path
# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import time
import torch
from backend.core.tokenizer import WithMeTokenizer, PAD_TOKEN_ID, EOS_TOKEN_ID
from backend.core.model import WithMeTransformerLM
from backend.core.dataset_manager import dataset_manager, DEFAULT_DEMO_DATASET
from backend.core.memory_service import memory_service
from backend.core.robot_service import robot_service
from backend.core.training import ConversationDataset, TrainingJob
from backend.core.inference import inference_engine
from backend.config import CHECKPOINTS_DIR


def test_tokenizer():
    print("Testing WithMeTokenizer...")
    tok = WithMeTokenizer()
    sample_texts = [
        "Today was really bad...",
        "I have a big presentation tomorrow!",
        "Let us play a game."
    ]
    tok.train_from_corpus(sample_texts, max_vocab_size=100)
    assert tok.vocab_size > 8, "Vocabulary size should exceed special token count."

    encoded = tok.encode("Today was really bad...", add_special_tokens=True)
    assert len(encoded) > 2, "Encoded sequence must include tokens and boundaries."
    decoded = tok.decode(encoded, skip_special_tokens=True)
    assert "Today" in decoded or "bad" in decoded, "Decoded text should reflect original words."
    print("[PASS] Tokenizer test passed.")


def test_dataset_pipeline():
    print("Testing Dataset validation and split...")
    valid_convs, stats = dataset_manager.validate_and_normalize(DEFAULT_DEMO_DATASET)
    assert len(valid_convs) > 0, "Demo conversations should be valid."
    assert stats["valid_conversations"] == len(valid_convs)

    split = dataset_manager.split_dataset(valid_convs, val_ratio=0.25, seed=42)
    assert split["train_count"] > 0, "Train split must contain conversations."
    assert split["val_count"] > 0, "Val split must contain conversations."
    print("[PASS] Dataset pipeline test passed.")


def test_model_forward_and_loss():
    print("Testing Model initialization, forward pass, and loss calculation...")
    tok = WithMeTokenizer()
    tok.train_from_corpus(["Hello world", "WithMe is here"], max_vocab_size=50)

    model = WithMeTransformerLM(
        vocab_size=tok.vocab_size,
        d_model=64,
        n_layers=2,
        n_heads=2,
        ffn_dim=128,
        max_seq_len=32,
        dropout=0.0
    )
    assert model.count_parameters() > 1000, "Model should have trainable parameters."

    # Dummy batch
    batch_size = 2
    seq_len = 10
    input_ids = torch.randint(1, tok.vocab_size, (batch_size, seq_len))
    target_ids = torch.randint(1, tok.vocab_size, (batch_size, seq_len))

    logits, loss = model(input_ids, targets=target_ids)
    assert logits.shape == (batch_size, seq_len, tok.vocab_size), "Logits shape mismatch."
    assert loss is not None and loss.item() > 0.0, "Loss must be a positive float."
    print(f"[PASS] Model forward and loss passed (initial loss: {loss.item():.4f}).")


def test_training_step_updates_weights():
    print("Testing that training step actually updates model weights...")
    tok = WithMeTokenizer()
    tok.train_from_corpus(["A friendly companion helps out."], max_vocab_size=50)

    model = WithMeTransformerLM(vocab_size=tok.vocab_size, d_model=32, n_layers=2, n_heads=2, ffn_dim=64, max_seq_len=16)
    initial_weight = model.tok_emb.weight.clone()

    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    input_ids = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
    target_ids = torch.tensor([[2, 3, 4, 3]], dtype=torch.long)

    model.train()
    optimizer.zero_grad()
    _, loss = model(input_ids, targets=target_ids)
    loss.backward()
    optimizer.step()

    assert not torch.equal(model.tok_emb.weight, initial_weight), "Weights must change after optimizer step!"
    print(f"[PASS] Weight update verified (loss: {loss.item():.4f}).")


def test_checkpoint_save_and_load():
    print("Testing Checkpoint saving and loading...")
    tok = WithMeTokenizer()
    tok.train_from_corpus(["Save and load test"], max_vocab_size=40)

    model = WithMeTransformerLM(vocab_size=tok.vocab_size, d_model=32, n_layers=2, n_heads=2, ffn_dim=64, max_seq_len=16)
    test_ckpt_dir = CHECKPOINTS_DIR / "test_smoke_job"
    test_ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = test_ckpt_dir / "checkpoint_final.pt"

    torch.save({
        "epoch": 1,
        "step": 5,
        "model_state_dict": model.state_dict(),
        "train_loss": 2.45,
        "val_loss": 2.50,
        "config": model.get_config()
    }, ckpt_path)
    tok.save(test_ckpt_dir / "tokenizer.json")

    assert ckpt_path.exists(), "Checkpoint file must exist on disk."

    # Load back
    loaded_data = torch.load(ckpt_path, map_location="cpu")
    model_loaded = WithMeTransformerLM(**{k: v for k, v in loaded_data["config"].items() if k != "param_count"})
    model_loaded.load_state_dict(loaded_data["model_state_dict"])
    model_loaded.eval()

    test_input = torch.tensor([[1, 2]], dtype=torch.long)
    output = model_loaded.generate(test_input, max_new_tokens=5, temperature=0.7)
    assert output.size(1) > 2, "Generated sequence must produce new tokens."
    print("[PASS] Checkpoint saving, loading, and generation passed.")


def test_memory_service():
    print("Testing SQLite Memory Service...")
    mem = memory_service.add_memory("User has a pet cat named Luna", "Personal", "Pets", user_approved=True)
    assert mem["id"].startswith("mem_")

    retrieved = memory_service.search_memories_for_context("cat pet", limit=1)
    assert len(retrieved) > 0, "Should retrieve relevant memory."
    assert "Luna" in retrieved[0]["content"]

    deleted = memory_service.delete_memory(mem["id"])
    assert deleted is True, "Memory should be deleted successfully."
    print("[PASS] Memory service test passed.")


def test_robot_service_actions():
    print("Testing Robot Service actions and validation...")
    status = robot_service.validate_and_execute_action("wave", "happy", "speaking")
    assert status["active_action"] == "wave"
    assert status["emotion"] == "happy"
    assert status["interaction_state"] == "speaking"

    # Invalid action rejection
    invalid_status = robot_service.validate_and_execute_action("arbitrary_hacker_code_exec", "unknown", "flying")
    assert invalid_status["active_action"] == "idle", "Unauthorized action should fall back to idle."

    # Simulated sensor event
    sim_res = robot_service.trigger_simulated_sensor_event("person_detected", {"position": "left"})
    assert sim_res["resulting_action"] == "look_left"
    assert sim_res["is_simulated"] is True
    print("[PASS] Robot service test passed.")


if __name__ == "__main__":
    print("\n================ STARTING WITHME AI CORE SMOKE TESTS ================\n")
    test_tokenizer()
    test_dataset_pipeline()
    test_model_forward_and_loss()
    test_training_step_updates_weights()
    test_checkpoint_save_and_load()
    test_memory_service()
    test_robot_service_actions()
    print("\n================ ALL SMOKE TESTS COMPLETED SUCCESSFULLY! ================\n")
