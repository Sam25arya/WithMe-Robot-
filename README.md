# WithMe-Robot-

crates/ygg-core/src/
├── lib.rs
├── error.rs             <-- Consolidated YggError(PageAuthenticationException, I/O errors)
├── crypto/
│   └── ascon128.rs      <-- In-place AEAD encryption/decryption
├── page/
│   ├── mod.rs           <-- PageFrame (Page.java)
│   ├── header.rs        <-- PageHeader & constants
│   └── slotted.rs       <-- SlottedPage implementation & compaction (SlottedPage.java)
├── btree/
│   ├── mod.rs           <-- BPlusTree operations (BPlusTree.java)
│   ├── node.rs          <-- Internal & Leaf node logic (BTreeNode.java, LeafNode, InternalNode)
│   └── logical_id.rs    <-- TupleID / Packed 64-bit pointers (TupleID.java)
└── wal/
    ├── mod.rs           <-- Write-Ahead Log manager (WalManager.java)
    ├── log_record.rs    <-- Binary WAL frames (OP_INSERT_TUPLE, OP_DELETE_TUPLE, OP_PAGE_UPDATE)
    └── recovery.rs      <-- Log replayer and crash recovery engine