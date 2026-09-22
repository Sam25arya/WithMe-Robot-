#![forbid(unsafe_code)]

use crate::btree::logical_id::LogicalId;
use crate::error::YggError;
use crate::page::header::PAYLOAD_SIZE;

pub const OFFSET_PAGE_TYPE: usize = 0;
pub const OFFSET_SLOT_COUNT: usize = 1;
pub const OFFSET_FREE_POINTER: usize = 3;
pub const OFFSET_FREE_SPACE: usize = 5;
pub const HEADER_END: usize = 7;

pub const TYPE_SLOTTED_DATA: u8 = 0x01;

pub struct SlottedPage {
    pub page_number: u32,
    pub slot_count: u16,
    pub free_space_pointer: u16,
    pub payload: [u8; PAYLOAD_SIZE],
}

impl SlottedPage {
    pub fn new(page_number: u32) -> Self {
        let mut page = Self {
            page_number,
            slot_count: 0,
            free_space_pointer: PAYLOAD_SIZE as u16,
            payload: [0u8; PAYLOAD_SIZE],
        };
        page.payload[OFFSET_PAGE_TYPE] = TYPE_SLOTTED_DATA;
        page.update_header();
        page
    }

    pub fn from_bytes(page_number: u32, bytes: &[u8; PAYLOAD_SIZE]) -> Result<Self, YggError> {
        let slot_count = u16::from_be_bytes(
            bytes[OFFSET_SLOT_COUNT..OFFSET_SLOT_COUNT + 2]
                .try_into()
                .map_err(|_| YggError::HeaderParseFailed)?,
        );
        let free_space_pointer = u16::from_be_bytes(
            bytes[OFFSET_FREE_POINTER..OFFSET_FREE_POINTER + 2]
                .try_into()
                .map_err(|_| YggError::HeaderParseFailed)?,
        );

        let mut payload = [0u8; PAYLOAD_SIZE];
        payload.copy_from_slice(bytes);

        Ok(Self {
            page_number,
            slot_count,
            free_space_pointer,
            payload,
        })
    }

    #[inline]
    fn directory_end(&self, slots: u16) -> usize {
        HEADER_END + (slots as usize * 4)
    }

    pub fn record_length(&self, slot_index: u16) -> Option<i16> {
        if slot_index >= self.slot_count {
            return None;
        }
        let entry_offset = HEADER_END + (slot_index as usize * 4);
        let len_bytes: [u8; 2] = self.payload[entry_offset + 2..entry_offset + 4]
            .try_into()
            .ok()?;
        Some(i16::from_be_bytes(len_bytes))
    }

    pub fn insert_record(&mut self, record_data: &[u8]) -> Result<LogicalId, YggError> {
        // Reuse tombstoned slots if available
        for slot_idx in 0..self.slot_count {
            if let Some(len) = self.record_length(slot_idx) {
                if len < 0 {
                    return self.insert_record_at(slot_idx, record_data);
                }
            }
        }
        self.insert_record_at(self.slot_count, record_data)
    }

    pub fn insert_record_at(&mut self, slot_index: u16, record_data: &[u8]) -> Result<LogicalId, YggError> {
        let reusing_slot = slot_index < self.slot_count;
        if reusing_slot {
            if let Some(len) = self.record_length(slot_index) {
                if len >= 0 {
                    return Err(YggError::BufferTooSmall);
                }
            }
        }

        let target_slot_count = self.slot_count.max(slot_index + 1);
        let slot_directory_end = self.directory_end(target_slot_count);
        let additional_slot_space = (target_slot_count - self.slot_count) as usize * 4;
        let required_space = record_data.len() + additional_slot_space;

        let mut available_space = self.free_space_pointer as usize - slot_directory_end;

        if available_space < required_space {
            self.compact();
            available_space = self.free_space_pointer as usize - self.directory_end(target_slot_count);
            if available_space < required_space {
                return Err(YggError::BufferTooSmall);
            }
        }

        let new_free_ptr = self.free_space_pointer as usize - record_data.len();
        self.free_space_pointer = new_free_ptr as u16;

        self.payload[new_free_ptr..new_free_ptr + record_data.len()].copy_from_slice(record_data);

        let entry_offset = HEADER_END + (slot_index as usize * 4);
        self.payload[entry_offset..entry_offset + 2].copy_from_slice(&(new_free_ptr as u16).to_be_bytes());
        self.payload[entry_offset + 2..entry_offset + 4].copy_from_slice(&(record_data.len() as i16).to_be_bytes());

        self.slot_count = target_slot_count;
        self.update_header();

        Ok(LogicalId::pack(self.page_number, slot_index as u32))
    }

    pub fn get_record(&self, slot_index: u16) -> Option<&[u8]> {
        if slot_index >= self.slot_count {
            return None;
        }

        let entry_offset = HEADER_END + (slot_index as usize * 4);
        let offset_bytes: [u8; 2] = self.payload[entry_offset..entry_offset + 2].try_into().ok()?;
        let offset = u16::from_be_bytes(offset_bytes) as usize;

        let record_len = self.record_length(slot_index)?;
        if record_len < 0 {
            return None; // Deleted slot
        }
        let len = record_len as usize;

        if offset < self.directory_end(self.slot_count) || offset + len > PAYLOAD_SIZE {
            return None;
        }

        Some(&self.payload[offset..offset + len])
    }

    pub fn delete_record(&mut self, slot_index: u16) -> bool {
        if slot_index >= self.slot_count {
            return false;
        }
        if let Some(len) = self.record_length(slot_index) {
            if len < 0 {
                return false;
            }
        } else {
            return false;
        }

        let entry_offset = HEADER_END + (slot_index as usize * 4);
        // Write tombstone (-1i16)
        self.payload[entry_offset + 2..entry_offset + 4].copy_from_slice(&(-1i16).to_be_bytes());
        self.update_header();
        true
    }

    pub fn compact(&mut self) {
        let mut temp_heap = [0u8; PAYLOAD_SIZE];
        let mut new_free_ptr = PAYLOAD_SIZE;

        for i in 0..self.slot_count {
            let entry_offset = HEADER_END + (i as usize * 4);
            let old_offset = u16::from_be_bytes(
                self.payload[entry_offset..entry_offset + 2]
                    .try_into()
                    .unwrap_or([0, 0]),
            ) as usize;
            let record_len = i16::from_be_bytes(
                self.payload[entry_offset + 2..entry_offset + 4]
                    .try_into()
                    .unwrap_or([0, 0]),
            );

            if record_len >= 0 {
                let len = record_len as usize;
                new_free_ptr -= len;
                temp_heap[new_free_ptr..new_free_ptr + len]
                    .copy_from_slice(&self.payload[old_offset..old_offset + len]);

                self.payload[entry_offset..entry_offset + 2]
                    .copy_from_slice(&(new_free_ptr as u16).to_be_bytes());
            }
        }

        self.payload[new_free_ptr..PAYLOAD_SIZE].copy_from_slice(&temp_heap[new_free_ptr..PAYLOAD_SIZE]);
        self.free_space_pointer = new_free_ptr as u16;
        self.update_header();
    }

    fn update_header(&mut self) {
        self.payload[OFFSET_PAGE_TYPE] = TYPE_SLOTTED_DATA;
        self.payload[OFFSET_SLOT_COUNT..OFFSET_SLOT_COUNT + 2].copy_from_slice(&self.slot_count.to_be_bytes());
        self.payload[OFFSET_FREE_POINTER..OFFSET_FREE_POINTER + 2].copy_from_slice(&self.free_space_pointer.to_be_bytes());

        let free_space = self.free_space_pointer.saturating_sub(self.directory_end(self.slot_count) as u16);
        self.payload[OFFSET_FREE_SPACE..OFFSET_FREE_SPACE + 2].copy_from_slice(&free_space.to_be_bytes());
    }
}