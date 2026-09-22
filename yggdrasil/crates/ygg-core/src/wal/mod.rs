pub mod log_record;
pub mod recovery;

use alloc::vec::Vec;

use crate::btree::logical_id::LogicalId;
use crate::error::YggError;
use crate::wal::log_record::{
    WalRecord, OP_DELETE_TUPLE, OP_INSERT_TUPLE, OP_PAGE_UPDATE,
};

/// Trait abstraction for writing and reading raw log sequence frames over a WAL stream/file[cite: 5].
pub trait WalStorage {
    fn append_frame(&mut self, frame: &[u8]) -> Result<(), YggError>;
    fn read_all_frames(&self) -> Result<Vec<u8>, YggError>;
}

/// WAL Manager handling log frame serialization, sequence numbers (LSN), and commit logs[cite: 5].
pub struct WalManager<'a, S: WalStorage> {
    storage: &'a mut S,
    current_lsn: u64,
}

impl<'a, S: WalStorage> WalManager<'a, S> {
    pub fn new(storage: &'a mut S) -> Self {
        Self {
            storage,
            current_lsn: 0,
        }
    }

    /// Gets the last generated LSN[cite: 5].
    pub fn current_lsn(&self) -> u64 {
        self.current_lsn
    }

    /// Sets the current starting LSN (e.g. after scanning active log)[cite: 5].
    pub fn set_lsn(&mut self, lsn: u64) {
        self.current_lsn = lsn;
    }

    /// Increments and returns the next monotonic LSN[cite: 5].
    fn next_lsn(&mut self) -> u64 {
        self.current_lsn += 1;
        self.current_lsn
    }

    /// Appends a tuple insertion record to the WAL[cite: 5].
    /// Frame Format: [1B OpType] [8B LSN] [4B Key] [8B TupleID] [2B PayloadLen] [N-Bytes Payload]
    pub fn log_insert_tuple(
        &mut self,
        key: i32,
        tuple_id: LogicalId,
        payload: &[u8],
    ) -> Result<u64, YggError> {
        let lsn = self.next_lsn();
        let payload_len = payload.len() as u16;
        let frame_size = 1 + 8 + 4 + 8 + 2 + payload.len();

        let mut frame = Vec::with_capacity(frame_size);
        frame.push(OP_INSERT_TUPLE);
        frame.extend_from_slice(&lsn.to_be_bytes());
        frame.extend_from_slice(&key.to_be_bytes());
        frame.extend_from_slice(&tuple_id.as_u64().to_be_bytes());
        frame.extend_from_slice(&payload_len.to_be_bytes());
        frame.extend_from_slice(payload);

        self.storage.append_frame(&frame)?;
        Ok(lsn)
    }

    /// Appends a tuple deletion record to the WAL[cite: 5].
    /// Frame Format: [1B OpType] [8B LSN] [4B Key] [8B TupleID]
    pub fn log_delete_tuple(&mut self, key: i32, tuple_id: LogicalId) -> Result<u64, YggError> {
        let lsn = self.next_lsn();
        let mut frame = [0u8; 1 + 8 + 4 + 8];

        frame[0] = OP_DELETE_TUPLE;
        frame[1..9].copy_from_slice(&lsn.to_be_bytes());
        frame[9..13].copy_from_slice(&key.to_be_bytes());
        frame[13..21].copy_from_slice(&tuple_id.as_u64().to_be_bytes());

        self.storage.append_frame(&frame)?;
        Ok(lsn)
    }

    /// Appends a full or partial page image update to the WAL[cite: 5].
    /// Frame Format: [1B OpType] [8B LSN] [4B PageID] [2B PayloadLen] [N-Bytes Payload]
    pub fn log_page_update(&mut self, page_id: u32, payload: &[u8]) -> Result<u64, YggError> {
        let lsn = self.next_lsn();
        let payload_len = payload.len() as u16;
        let frame_size = 1 + 8 + 4 + 2 + payload.len();

        let mut frame = Vec::with_capacity(frame_size);
        frame.push(OP_PAGE_UPDATE);
        frame.extend_from_slice(&lsn.to_be_bytes());
        frame.extend_from_slice(&page_id.to_be_bytes());
        frame.extend_from_slice(&payload_len.to_be_bytes());
        frame.extend_from_slice(payload);

        self.storage.append_frame(&frame)?;
        Ok(lsn)
    }

    /// Deserializes a raw log byte buffer into zero-copy / referenced `WalRecord` sequence[cite: 5].
    pub fn parse_log_bytes<'b>(bytes: &'b [u8]) -> Result<Vec<WalRecord<'b>>, YggError> {
        let mut records = Vec::new();
        let mut cursor = 0;

        while cursor < bytes.len() {
            let op_type = bytes[cursor];
            cursor += 1;

            match op_type {
                OP_INSERT_TUPLE => {
                    if cursor + 8 + 4 + 8 + 2 > bytes.len() {
                        return Err(YggError::HeaderParseFailed);
                    }
                    let lsn = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                    cursor += 8;

                    let key = i32::from_be_bytes(bytes[cursor..cursor + 4].try_into().unwrap());
                    cursor += 4;

                    let raw_tid = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                    let tuple_id = LogicalId::from_u64(raw_tid);
                    cursor += 8;

                    let payload_len = u16::from_be_bytes(bytes[cursor..cursor + 2].try_into().unwrap()) as usize;
                    cursor += 2;

                    if cursor + payload_len > bytes.len() {
                        return Err(YggError::HeaderParseFailed);
                    }
                    let payload = &bytes[cursor..cursor + payload_len];
                    cursor += payload_len;

                    records.push(WalRecord::InsertTuple {
                        lsn,
                        key,
                        tuple_id,
                        payload,
                    });
                }
                OP_DELETE_TUPLE => {
                    if cursor + 8 + 4 + 8 > bytes.len() {
                        return Err(YggError::HeaderParseFailed);
                    }
                    let lsn = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                    cursor += 8;

                    let key = i32::from_be_bytes(bytes[cursor..cursor + 4].try_into().unwrap());
                    cursor += 4;

                    let raw_tid = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                    let tuple_id = LogicalId::from_u64(raw_tid);
                    cursor += 8;

                    records.push(WalRecord::DeleteTuple { lsn, key, tuple_id });
                }
                OP_PAGE_UPDATE => {
                    if cursor + 8 + 4 + 2 > bytes.len() {
                        return Err(YggError::HeaderParseFailed);
                    }
                    let lsn = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                    cursor += 8;

                    let page_id = u32::from_be_bytes(bytes[cursor..cursor + 4].try_into().unwrap());
                    cursor += 4;

                    let payload_len = u16::from_be_bytes(bytes[cursor..cursor + 2].try_into().unwrap()) as usize;
                    cursor += 2;

                    if cursor + payload_len > bytes.len() {
                        return Err(YggError::HeaderParseFailed);
                    }
                    let payload = &bytes[cursor..cursor + payload_len];
                    cursor += payload_len;

                    records.push(WalRecord::PageUpdate {
                        lsn,
                        page_id,
                        payload,
                    });
                }
                _ => return Err(YggError::HeaderParseFailed),
            }
        }

        Ok(records)
    }
}