"""
Unit Tests for WithMe AI Conversational Dataset Pipeline (Phase 1)
Tests: format parsing, schema validation, secret detection, deduplication,
conversation-level 3-way splitting, and manifest generation.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.dataset_manager import dataset_manager


def test_format_parsing():
    print("Testing format parsing (JSONL, JSON, CSV, TXT)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # JSONL
        jsonl_path = tmp / "test.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]}) + "\n")
        recs = dataset_manager.parse_raw_records(jsonl_path)
        assert len(recs) == 1, "Failed to parse JSONL"

        # CSV
        csv_path = tmp / "test.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("user,assistant\nHow are you?,I am doing well!\n")
        recs = dataset_manager.parse_raw_records(csv_path)
        assert len(recs) == 1, "Failed to parse CSV"
        assert recs[0]["messages"][0]["content"] == "How are you?"

        # TXT
        txt_path = tmp / "test.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Hello\nHi there friend\n")
        recs = dataset_manager.parse_raw_records(txt_path)
        assert len(recs) == 1, "Failed to parse TXT"

    print("[PASS] test_format_parsing passed.")


def test_validation_and_secret_detection():
    print("Testing validation, edge cases, and credential detection...")
    raw_data = [
        # Valid
        {"conversation_id": "c1", "messages": [{"role": "user", "content": "Valid question"}, {"role": "assistant", "content": "Valid answer"}]},
        # Empty message
        {"conversation_id": "c2", "messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": "Reply"}]},
        # Missing assistant reply
        {"conversation_id": "c3", "messages": [{"role": "user", "content": "Only user message"}]},
        # Secret credential detection
        {"conversation_id": "c4", "messages": [{"role": "user", "content": "My AWS key is AKIA1234567890ABCDEF"}, {"role": "assistant", "content": "I should not remember keys"}]},
        # Duplicate of c1
        {"conversation_id": "c5", "messages": [{"role": "user", "content": "Valid question"}, {"role": "assistant", "content": "Valid answer"}]},
    ]

    valid, stats = dataset_manager.validate_and_normalize(raw_data)
    assert len(valid) == 1, f"Expected exactly 1 valid conversation, got {len(valid)}"
    assert stats["empty_count"] >= 1, "Failed to detect empty message"
    assert stats["missing_assistant_count"] >= 1, "Failed to detect missing assistant"
    assert stats["secret_warnings"] >= 1, "Failed to detect secret credential"
    assert stats["duplicates_removed"] >= 1, "Failed to remove duplicate sequence"
    print("[PASS] test_validation_and_secret_detection passed.")


def test_3way_conversation_split():
    print("Testing 3-way conversation-level splitting without turn leakage...")
    # Generate 10 distinct synthetic multi-turn conversations
    convs = [
        {
            "conversation_id": f"conv_{i:03d}",
            "messages": [
                {"role": "user", "content": f"Question {i} turn 1"},
                {"role": "assistant", "content": f"Answer {i} turn 1"},
                {"role": "user", "content": f"Question {i} turn 2"},
                {"role": "assistant", "content": f"Answer {i} turn 2"}
            ]
        }
        for i in range(10)
    ]

    # Split 80/10/10 with seed 42
    split1 = dataset_manager.split_dataset_3way(convs, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    assert split1["train_count"] == 8, f"Expected 8 train, got {split1['train_count']}"
    assert split1["val_count"] == 1, f"Expected 1 val, got {split1['val_count']}"
    assert split1["test_count"] == 1, f"Expected 1 test, got {split1['test_count']}"

    # Verify turn integrity (all messages of conv stay within their partition)
    train_ids = {c["conversation_id"] for c in split1["train"]}
    val_ids = {c["conversation_id"] for c in split1["validation"]}
    test_ids = {c["conversation_id"] for c in split1["test"]}

    assert train_ids.isdisjoint(val_ids), "Turn leakage between train and validation!"
    assert train_ids.isdisjoint(test_ids), "Turn leakage between train and test!"
    assert val_ids.isdisjoint(test_ids), "Turn leakage between validation and test!"

    # Verify deterministic reproducibility with same seed
    split2 = dataset_manager.split_dataset_3way(convs, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    assert [c["conversation_id"] for c in split1["train"]] == [c["conversation_id"] for c in split2["train"]], "Split not deterministic with same seed!"

    print("[PASS] test_3way_conversation_split passed.")


def test_manifest_generation():
    print("Testing dataset manifest creation and SHA-256 hash tracking...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        raw_file = tmp / "sample_manifest_data.jsonl"
        with open(raw_file, "w", encoding="utf-8") as f:
            for i in range(5):
                f.write(json.dumps({"messages": [{"role": "user", "content": f"Prompt {i}"}, {"role": "assistant", "content": f"Response {i}"}]}) + "\n")

        res = dataset_manager.prepare_and_save_dataset(
            raw_filepath=raw_file,
            dataset_name="Manifest Test Set",
            val_ratio=0.2,
            test_ratio=0.2,
            seed=42,
            source_description="Automated unit test",
            license_info="MIT / Test"
        )

        assert res["manifest_id"].startswith("manifest_"), "Invalid manifest ID"
        manifest_file = dataset_manager.manifests_dir / f"{res['manifest_id']}.json"
        assert manifest_file.exists(), "Manifest file not found on disk"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        assert manifest_data["file_hash_sha256"] != "unknown", "SHA-256 hash missing"
        assert len(manifest_data["file_hash_sha256"]) == 64, "Invalid SHA-256 hash length"
        assert manifest_data["split_configuration"]["seed"] == 42
        assert manifest_data["source_description"] == "Automated unit test"

    print("[PASS] test_manifest_generation passed.")


if __name__ == "__main__":
    print("\n================ RUNNING DATASET PIPELINE TESTS ================")
    test_format_parsing()
    test_validation_and_secret_detection()
    test_3way_conversation_split()
    test_manifest_generation()
    print("================ ALL DATASET PIPELINE TESTS PASSED ================\n")
