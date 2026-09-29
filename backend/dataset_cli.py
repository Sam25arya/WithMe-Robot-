"""
WithMe AI Core - Dataset Pipeline CLI Tool
Supports validating conversational datasets, splitting into train/val/test with deterministic seeds,
and generating versioned integrity manifests.
Usage:
    python backend/dataset_cli.py validate --file withme-data/datasets/raw/withme_synthetic_demo.jsonl
    python backend/dataset_cli.py split --file withme-data/datasets/raw/withme_synthetic_demo.jsonl --train 0.8 --val 0.1 --test 0.1 --seed 42
    python backend/dataset_cli.py manifest --file withme-data/datasets/raw/withme_synthetic_demo.jsonl --name "Demo Foundation"
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.dataset_manager import dataset_manager


def cmd_validate(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    print(f"\n================ VALIDATING DATASET: {filepath.name} ================")
    raw_records = dataset_manager.parse_raw_records(filepath)
    print(f"Total raw parsed records: {len(raw_records)}")

    valid_convs, stats = dataset_manager.validate_and_normalize(raw_records, max_char_length=args.max_len)

    print("\n--- Validation Statistics ---")
    print(f"Valid Conversations:      {stats['valid_conversations']}")
    print(f"Invalid Records:          {stats['invalid_count']}")
    print(f"Empty Message Sets:       {stats['empty_count']}")
    print(f"Duplicate Sequences:      {stats['duplicates_removed']}")
    print(f"Missing Assistant Reply:  {stats['missing_assistant_count']}")
    print(f"Excessive Length (> {args.max_len}): {stats['excessive_length_count']}")
    print(f"Secret / Credential Hits: {stats['secret_warnings']}")

    if stats["actionable_errors"]:
        print("\n--- Actionable Issues (first 10) ---")
        for err in stats["actionable_errors"][:10]:
            print(f"  * Record #{err['record_index']} ({err['conversation_id']}): [{err['error_type']}] {err['message']}")

    if stats["valid_conversations"] > 0:
        print(f"\n[PASS] Dataset is valid with {stats['valid_conversations']} clean conversational dialogues.")
    else:
        print("\n[FAIL] No valid conversations found.")
        sys.exit(1)


def cmd_split(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    print(f"\n================ 3-WAY SPLITTING DATASET: {filepath.name} ================")
    raw_records = dataset_manager.parse_raw_records(filepath)
    valid_convs, stats = dataset_manager.validate_and_normalize(raw_records)

    split_res = dataset_manager.split_dataset_3way(
        valid_convs,
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test,
        seed=args.seed
    )

    print(f"Total Conversations:   {split_res['total_count']}")
    print(f"Train Partition:       {split_res['train_count']} ({args.train * 100:.1f}%)")
    print(f"Validation Partition:  {split_res['val_count']} ({args.val * 100:.1f}%)")
    print(f"Held-out Test:         {split_res['test_count']} ({args.test * 100:.1f}%)")
    print(f"Deterministic Seed:    {args.seed}")
    print("[PASS] Conversation-level 3-way split successfully generated without turn-leakage.")

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(split_res, f, indent=2, ensure_ascii=False)
        print(f"Saved split metadata to: {out_p}")


def cmd_manifest(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    res = dataset_manager.prepare_and_save_dataset(
        raw_filepath=filepath,
        dataset_name=args.name,
        val_ratio=args.val,
        test_ratio=args.test,
        seed=args.seed,
        source_description=args.source,
        license_info=args.license
    )

    print(f"\n================ DATASET MANIFEST CREATED ================")
    print(f"Dataset ID:         {res['id']}")
    print(f"Manifest ID:        {res['manifest_id']}")
    print(f"Train / Val / Test: {res['train_count']} / {res['val_count']} / {res['test_count']}")
    print(f"Processed File:     {res['filepath']}")
    print("[PASS] Manifest registered.")


def main():
    parser = argparse.ArgumentParser(description="WithMe AI Conversational Dataset Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Validate
    val_p = subparsers.add_parser("validate", help="Validate a conversational dataset")
    val_p.add_argument("--file", required=True, help="Path to raw dataset (jsonl, json, csv, txt)")
    val_p.add_argument("--max-len", type=int, default=4096, help="Maximum character length per message")
    val_p.set_defaults(func=cmd_validate)

    # Split
    split_p = subparsers.add_parser("split", help="Perform conversation-level 3-way split")
    split_p.add_argument("--file", required=True, help="Path to dataset file")
    split_p.add_argument("--train", type=float, default=0.8, help="Train ratio (default 0.8)")
    split_p.add_argument("--val", type=float, default=0.1, help="Validation ratio (default 0.1)")
    split_p.add_argument("--test", type=float, default=0.1, help="Held-out test ratio (default 0.1)")
    split_p.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    split_p.add_argument("--output", help="Optional output JSON path")
    split_p.set_defaults(func=cmd_split)

    # Manifest
    man_p = subparsers.add_parser("manifest", help="Prepare dataset, generate manifest and SHA-256 hash")
    man_p.add_argument("--file", required=True, help="Path to raw dataset file")
    man_p.add_argument("--name", default="WithMe Custom Dataset", help="Dataset name")
    man_p.add_argument("--val", type=float, default=0.1, help="Validation ratio")
    man_p.add_argument("--test", type=float, default=0.1, help="Test ratio")
    man_p.add_argument("--seed", type=int, default=42, help="Seed")
    man_p.add_argument("--source", default="Manual import", help="Data source description")
    man_p.add_argument("--license", default="Internal Research", help="Dataset license")
    man_p.set_defaults(func=cmd_manifest)

    parsed = parser.parse_args()
    parsed.func(parsed)


if __name__ == "__main__":
    main()
