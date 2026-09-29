# WithMe AI Core — Conversational Data Pipeline (Phase 1 Specification)

> **Core Requirement**: *"The dataset pipeline must be independent of the frontend and usable through both a command-line interface and the web-based Dataset Studio."*

---

## 1. Supported Conversational Formats

WithMe AI supports four primary file formats for training data ingestion, with **JSONL** serving as the canonical internal representation:

### A. Canonical JSONL (`.jsonl`)
Each line represents an independent conversational interaction:
```json
{"conversation_id": "emo_001", "category": "emotional_support", "messages": [{"role": "user", "content": "I had a rough day."}, {"role": "assistant", "content": "I hear you. Want to talk about it?"}]}
```

### B. Multi-Turn JSON (`.json`)
Structured array of conversations with optional metadata:
```json
[
  {
    "conversation_id": "study_001",
    "category": "academic",
    "messages": [
      {"role": "user", "content": "I have an exam tomorrow."},
      {"role": "assistant", "content": "Which subject?"},
      {"role": "user", "content": "Data structures and algorithms."},
      {"role": "assistant", "content": "Let's review trees and graphs step-by-step!"}
    ]
  }
]
```

### C. Prompt/Response CSV (`.csv`)
Columns: `user,assistant` or `prompt,response` or `input,output`.

### D. Alternating Plain Text (`.txt`)
Even-numbered lines represent user input; odd-numbered lines represent assistant responses.

---

## 2. Validation & Security Engine

The validator enforces structural and ethical constraints before permitting any record to enter training:

1. **Schema Integrity**: Validates JSON syntax, presence of `messages` array, and valid roles (`user`, `assistant`, `system`, `robot`).
2. **Assistant Presence**: Rejects conversations lacking assistant replies.
3. **Empty Message Detection**: Rejects records containing whitespace-only messages.
4. **Sequence Length Guard**: Flags messages exceeding 4,096 characters to prevent out-of-memory errors on CPU.
5. **Deduplication**: Computes sequence fingerprints (`role:content||...`) to eliminate duplicate dialogues.
6. **Credential & Secret Protection**: Actively checks for potential API keys, AWS tokens, GitHub PATs, and passwords via regex patterns:
   - `AKIA[0-9A-Z]{16}`
   - `ghp_[a-zA-Z0-9]{36}`
   - `sk-[a-zA-Z0-9]{20,}`
   - `bearer\s+[a-zA-Z0-9_\-\.]{20,}`
   Any matching record is rejected to ensure sensitive personal keys never enter model weights.

---

## 3. Conversation-Level 3-Way Splitting (Train / Val / Test)

To prevent direct **data leakage**, turns from the same conversation are **never** separated across partitions:

- **Train Partition (Default 80%)**: Used for model weight updates via backpropagation.
- **Validation Partition (Default 10%)**: Used during training to monitor validation loss, detect overfitting, and trigger early stopping.
- **Held-Out Test Partition (Default 10%)**: Strictly preserved and untouched during training. Used exclusively by the Evaluation Lab for unbiased benchmark reporting.

Deterministic random seeds (e.g. `--seed 42`) guarantee that dataset splits are 100% reproducible across different runs.

---

## 4. Versioned Dataset Manifests & SHA-256 Hashes

Every prepared dataset produces an immutable manifest stored in `withme-data/manifests/`:
```json
{
  "manifest_id": "manifest_foundation_demo_dataset_1790612924",
  "dataset_id": "foundation_demo_dataset_f688f9",
  "dataset_name": "Foundation Demo Dataset",
  "created_at": "2026-09-28T16:28:44Z",
  "file_hash_sha256": "47a9d0c2e39b9...64chars",
  "tokenizer_version": "WithMeTokenizer-v1",
  "split_configuration": {
    "seed": 42,
    "train_count": 6,
    "val_count": 1,
    "test_count": 1,
    "total_conversations": 8
  },
  "validation_summary": {
    "total_input_records": 8,
    "valid_conversations": 8,
    "invalid_count": 0,
    "duplicates_removed": 0,
    "secret_warnings": 0
  }
}
```

---

## 5. Command-Line Interface (CLI) Usage

The standalone CLI is located at [`backend/dataset_cli.py`](file:///c:/Users/shagu/.antigravity/withme-app/backend/dataset_cli.py):

### Validate a raw dataset:
```powershell
python backend/dataset_cli.py validate --file withme-data/datasets/raw/withme_synthetic_demo.jsonl
```

### Perform a reproducible 3-way split:
```powershell
python backend/dataset_cli.py split --file withme-data/datasets/raw/withme_synthetic_demo.jsonl --train 0.8 --val 0.1 --test 0.1 --seed 42
```

### Generate a processed dataset and registered manifest:
```powershell
python backend/dataset_cli.py manifest --file withme-data/datasets/raw/withme_synthetic_demo.jsonl --name "Foundation Demo Dataset" --val 0.1 --test 0.1 --seed 42
```

---

## 6. Privacy & Consent Policy

1. **No Silent Ingestion**: WithMe will never automatically ingest private user chats into the training pool. Datasets must be explicitly imported by the user.
2. **Right to Erasure**: Deleting a dataset removes both the raw file, processed JSON, and associated manifest from disk.
