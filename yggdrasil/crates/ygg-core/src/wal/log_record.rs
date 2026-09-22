#![forbid(unsafe_code)]

use crate::btree::logical_id::LogicalId;
pub const OP_INSERT_TUPLE: u8 = 0x01;
pub const OP_DELETE_TUPLE: u8 = 0x02;
pub const OP_PAGE_UPDATE: u8 = 0x03;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WalRecord<'a> {
    InsertTuple {
        lsn: u64,
        key: i32,
        tuple_id: LogicalId,
        payload: &'a [u8],
    },
    DeleteTuple {
        lsn: u64,
        key: i32,
        tuple_id: LogicalId,
    },
    PageUpdate {
        lsn: u64,
        page_id: u32,
        payload: &'a [u8],
    },
}

impl<'a> WalRecord<'a> {
    pub fn lsn(&self) -> u64 {
        match self {
            Self::InsertTuple { lsn, .. } => *lsn,
            Self::DeleteTuple { lsn, .. } => *lsn,
            Self::PageUpdate { lsn, .. } => *lsn,
        }
    }

    pub fn op_type(&self) -> u8 {
        match self {
            Self::InsertTuple { .. } => OP_INSERT_TUPLE,
            Self::DeleteTuple { .. } => OP_DELETE_TUPLE,
            Self::PageUpdate { .. } => OP_PAGE_UPDATE,
        }
    }
}