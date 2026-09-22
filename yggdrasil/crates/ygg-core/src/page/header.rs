#![forbid(unsafe_code)]

use crate::error::YggError;

pub const PAGE_SIZE: usize = 4096;
pub const NONCE_SIZE: usize = 16;
pub const TAG_SIZE: usize = 16;
pub const CRYPTO_OVERHEAD: usize = NONCE_SIZE + TAG_SIZE;
pub const PAYLOAD_SIZE: usize = PAGE_SIZE - CRYPTO_OVERHEAD;

pub const OFFSET_NONCE: usize = 0;
pub const OFFSET_CIPHERTEXT: usize = NONCE_SIZE;
pub const OFFSET_TAG: usize = PAGE_SIZE - TAG_SIZE;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(C)]
pub struct PageHeader {
    pub page_id: u32,
    pub lsn: u64,
    pub slot_count: u16,
    pub free_ptr: u16,
}

impl PageHeader {
    pub const SIZE: usize = 16;

    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut buf = [0u8; Self::SIZE];
        buf[0..4].copy_from_slice(&self.page_id.to_be_bytes());
        buf[4..12].copy_from_slice(&self.lsn.to_be_bytes());
        buf[12..14].copy_from_slice(&self.slot_count.to_be_bytes());
        buf[14..16].copy_from_slice(&self.free_ptr.to_be_bytes());
        buf
    }

    pub fn from_bytes(buf: &[u8; Self::SIZE]) -> Result<Self, YggError> {
        let page_id = match buf[0..4].try_into() {
            Ok(bytes) => u32::from_be_bytes(bytes),
            Err(_) => return Err(YggError::HeaderParseFailed),
        };
        let lsn = match buf[4..12].try_into() {
            Ok(bytes) => u64::from_be_bytes(bytes),
            Err(_) => return Err(YggError::HeaderParseFailed),
        };
        let slot_count = match buf[12..14].try_into() {
            Ok(bytes) => u16::from_be_bytes(bytes),
            Err(_) => return Err(YggError::HeaderParseFailed),
        };
        let free_ptr = match buf[14..16].try_into() {
            Ok(bytes) => u16::from_be_bytes(bytes),
            Err(_) => return Err(YggError::HeaderParseFailed),
        };

        Ok(Self {
            page_id,
            lsn,
            slot_count,
            free_ptr,
        })
    }
}