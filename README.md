# WithMe-Robot-

A Rust-based storage engine organized around encrypted pages, B+ tree indexing, and write-ahead logging.

## Project structure

The core implementation lives in `crates/ygg-core/src/`:

```text
crates/ygg-core/src/
├── lib.rs
├── error.rs             # Consolidated YggError and I/O errors
├── crypto/
│   └── ascon128.rs      # In-place AEAD encryption and decryption
├── page/
│   ├── mod.rs           # PageFrame
│   ├── header.rs        # PageHeader and page constants
│   └── slotted.rs       # Slotted-page storage and compaction
├── btree/
│   ├── mod.rs           # B+ tree operations
│   ├── node.rs          # Internal and leaf node logic
│   └── logical_id.rs    # Tuple IDs and packed 64-bit pointers
└── wal/
    ├── mod.rs           # Write-ahead log manager
    ├── log_record.rs    # Binary WAL records
    └── recovery.rs      # Log replay and crash recovery
```

## Core components

- **Error handling** — Centralized `YggError` types for page authentication and I/O failures.
- **Authenticated encryption** — ASCON-128 support for in-place page data encryption and decryption.
- **Page management** — Page headers, page frames, and slotted pages with compaction support.
- **B+ tree indexing** — Internal and leaf node structures with compact logical tuple identifiers.
- **Durability and recovery** — Binary write-ahead log records, replay, and crash recovery.

## Status

This repository is under active development. APIs and internal data structures may change as the storage engine evolves.
