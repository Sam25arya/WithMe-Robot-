pub mod header;
pub mod slotted;

use core::sync::atomic::{AtomicBool, AtomicU16, Ordering};

use crate::crypto::ascon128;
use crate::error::YggError;
use header::{PAYLOAD_SIZE, OFFSET_CIPHERTEXT, OFFSET_NONCE, PAGE_SIZE};

pub struct PageFrame {
    pub page_id: u32,
    pub page_number: u32,
    pub lsn: u64,
    pub pin_count: AtomicU16,
    pub is_dirty: AtomicBool,
    pub data: [u8; PAGE_SIZE],
}

impl PageFrame {
    pub fn new(page_id: u32, page_number: u32) -> Self {
        Self {
            page_id,
            page_number,
            lsn: 0,
            pin_count: AtomicU16::new(0),
            is_dirty: AtomicBool::new(false),
            data: [0u8; PAGE_SIZE],
        }
    }

    #[inline]
    pub fn physical_offset(&self) -> u64 {
        (self.page_number as u64) * (PAGE_SIZE as u64)
    }

    #[inline]
    pub fn pin(&self) {
        self.pin_count.fetch_add(1, Ordering::SeqCst);
    }

    #[inline]
    pub fn unpin(&self) {
        self.pin_count.fetch_sub(1, Ordering::SeqCst);
    }

    #[inline]
    pub fn associated_data(&self) -> [u8; 4] {
        self.page_id.to_be_bytes()
    }

    pub fn encrypt_frame(
        &mut self,
        secret_key: &[u8; 16],
        nonce: &[u8; 16],
        raw_payload: &[u8; PAYLOAD_SIZE],
    ) -> Result<(), YggError> {
        self.data[OFFSET_NONCE..OFFSET_NONCE + 16].copy_from_slice(nonce);
        self.data[OFFSET_CIPHERTEXT..OFFSET_CIPHERTEXT + PAYLOAD_SIZE]
            .copy_from_slice(raw_payload);

        ascon128::encrypt_in_place(
            secret_key,
            nonce,
            &self.associated_data(),
            &mut self.data[OFFSET_CIPHERTEXT..],
            PAYLOAD_SIZE,
        )?;

        self.is_dirty.store(false, Ordering::SeqCst);
        Ok(())
    }

    pub fn decrypt_frame(&mut self, secret_key: &[u8; 16]) -> Result<&[u8], YggError> {
        let mut nonce = [0u8; 16];
        nonce.copy_from_slice(&self.data[OFFSET_NONCE..OFFSET_NONCE + 16]);

        let associated_data = self.associated_data();
        let ct_and_tag = &mut self.data[OFFSET_CIPHERTEXT..];
        let plain_len = ascon128::decrypt_in_place(
            secret_key,
            &nonce,
            &associated_data,
            ct_and_tag,
            self.page_id,
        )?;

        Ok(&self.data[OFFSET_CIPHERTEXT..OFFSET_CIPHERTEXT + plain_len])
    }
}