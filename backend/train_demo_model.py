"""
Train an initial experimental WithMe Transformer model checkpoint on the synthetic dataset.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.dataset_manager import dataset_manager, DEFAULT_DEMO_DATASET
from backend.core.tokenizer import WithMeTokenizer
from backend.core.training import training_engine


def main():
    print("Preparing demo dataset...")
    raw_path = dataset_manager.raw_dir / "withme_synthetic_demo.jsonl"
    prep = dataset_manager.prepare_and_save_dataset(
        raw_filepath=raw_path,
        dataset_name="WithMe Synthetic Foundation Dataset",
        val_ratio=0.25,
        seed=42
    )
    print(f"Dataset prepared: {prep['train_count']} train, {prep['val_count']} val conversations.")

    # Train tokenizer
    all_texts = []
    for c in DEFAULT_DEMO_DATASET:
        for m in c.get("messages", []):
            all_texts.append(m.get("content", ""))

    tokenizer = WithMeTokenizer()
    tokenizer.train_from_corpus(all_texts, max_vocab_size=800, min_freq=1)
    print(f"Tokenizer vocabulary size: {tokenizer.vocab_size}")

    import json
    with open(prep["filepath"], "r", encoding="utf-8") as f:
        data = json.load(f)

    config = {
        "epochs": 6,
        "batch_size": 2,
        "learning_rate": 5e-4,
        "d_model": 64,
        "n_layers": 3,
        "n_heads": 2,
        "ffn_dim": 128,
        "max_seq_len": 64,
        "dropout": 0.05
    }

    print("Launching PyTorch training job...")
    job = training_engine.create_job(
        model_name="WithMe-Mini-Transformer-v1",
        config=config,
        train_conversations=data["train"],
        val_conversations=data["validation"],
        tokenizer=tokenizer
    )

    job.start()

    # Wait for completion
    while job.status == "running":
        import time
        time.sleep(0.5)

    print(f"Training finished with status: {job.status.upper()}")
    print(f"Initial Train Loss: {job.loss_history[0]['loss']} -> Final Train Loss: {job.latest_train_loss}")
    print(f"Latest Validation Loss: {job.latest_val_loss}")
    print(f"Saved Checkpoint: {job.latest_checkpoint_path}")


if __name__ == "__main__":
    main()
