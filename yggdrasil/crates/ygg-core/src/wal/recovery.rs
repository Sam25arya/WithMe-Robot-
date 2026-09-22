#![forbid(unsafe_code)]

use crate::btree::logical_id::LogicalId;
use crate::error::YggError;
use crate::page::header::PAYLOAD_SIZE;
use crate::page::slotted::SlottedPage;
use crate::wal::log_record::WalRecord;

/// Represents an abstract storage trait for reading/writing raw page payloads
/// during crash recovery.
pub trait RecoveryStorage {
    fn read_page_payload(&self, page_id: u32) -> Result<[u8; PAYLOAD_SIZE], YggError>;
    fn write_page_payload(&mut self, page_id: u32, payload: &[u8; PAYLOAD_SIZE]) -> Result<(), YggError>;
}

/// Recovery engine that replays committed and uncommitted operations 
/// sequentially over raw page storage[cite: 5].
pub struct RecoveryEngine<'a, S: RecoveryStorage> {
    storage: &'a mut S,
    last_replayed_lsn: u64,
}

impl<'a, S: RecoveryStorage> RecoveryEngine<'a, S> {
    pub fn new(storage: &'a mut S) -> Self {
        Self {
            storage,
            last_replayed_lsn: 0,
        }
    }

    /// Returns the LSN of the last successfully replayed transaction log entry[cite: 5].
    pub fn last_replayed_lsn(&self) -> u64 {
        self.last_replayed_lsn
    }

    /// Replays a batch of parsed WAL records sequentially in log order[cite: 5].
    pub fn replay_log_records<'b>(&mut self, records: &[WalRecord<'b>]) -> Result<usize, YggError> {
        let mut replayed_count = 0;

        for record in records {
            // Guarantee monotonic log sequence execution[cite: 5]
            if record.lsn() <= self.last_replayed_lsn && self.last_replayed_lsn != 0 {
                continue;
            }

            match record {
                WalRecord::InsertTuple { tuple_id, payload, .. } => {
                    self.apply_insert_tuple(*tuple_id, payload)?;
                }
                WalRecord::DeleteTuple { tuple_id, .. } => {
                    self.apply_delete_tuple(*tuple_id)?;
                }
                WalRecord::PageUpdate { page_id, payload, .. } => {
                    self.apply_page_update(*page_id, payload)?;
                }
            }

            self.last_replayed_lsn = record.lsn();
            replayed_count += 1;
        }

        Ok(replayed_count)
    }

    /// Re-applies a tuple insertion onto the target slotted page[cite: 5, 8].
    fn apply_insert_tuple(&mut self, tuple_id: LogicalId, record_data: &[u8]) -> Result<(), YggError> {
        let page_id = tuple_id.page_number();
        let slot_idx = tuple_id.slot_index() as u16;

        let raw_payload = self.storage.read_page_payload(page_id)?;
        let mut slotted_page = SlottedPage::from_bytes(page_id, &raw_payload)?;

        // Re-insert tuple directly at its assigned physical slot[cite: 8]
        slotted_page.insert_record_at(slot_idx, record_data)?;

        self.storage.write_page_payload(page_id, &slotted_page.payload)?;
        Ok(())
    }

    /// Re-applies a tuple deletion (tombstone) onto the target slotted page[cite: 5, 8].
    fn apply_delete_tuple(&mut self, tuple_id: LogicalId) -> Result<(), YggError> {
        let page_id = tuple_id.page_number();
        let slot_idx = tuple_id.slot_index() as u16;

        let raw_payload = self.storage.read_page_payload(page_id)?;
        let mut slotted_page = SlottedPage::from_bytes(page_id, &raw_payload)?;

        slotted_page.delete_record(slot_idx);

        self.storage.write_page_payload(page_id, &slotted_page.payload)?;
        Ok(())
    }

    /// Overwrites page state directly with a logged full page image[cite: 5].
    fn apply_page_update(&mut self, page_id: u32, payload: &[u8]) -> Result<(), YggError> {
        if payload.len() != PAYLOAD_SIZE {
            return Err(YggError::BufferTooSmall);
        }

        let mut fixed_payload = [0u8; PAYLOAD_SIZE];
        fixed_payload.copy_from_slice(payload);

        self.storage.write_page_payload(page_id, &fixed_payload)?;
        Ok(())
    }
}