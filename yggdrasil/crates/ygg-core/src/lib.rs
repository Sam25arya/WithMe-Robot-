#![forbid(unsafe_code)]
#![no_std]

#[cfg(feature = "std")]
extern crate std;

extern crate alloc;

pub mod btree;
pub mod crypto;
pub mod error;
pub mod page;
pub mod wal;

// Re-exports for convenient top-level crate usage
pub use btree::logical_id::LogicalId;
pub use btree::node::BTreeNode;
pub use btree::{BPlusTree, PageStorage};
pub use crypto::ascon128;
pub use error::YggError;
pub use page::header::{PageHeader, PAGE_SIZE, PAYLOAD_SIZE};
pub use page::slotted::SlottedPage;
pub use page::PageFrame;
pub use wal::log_record::WalRecord;
pub use wal::recovery::{RecoveryEngine, RecoveryStorage};
pub use wal::{WalManager, WalStorage};