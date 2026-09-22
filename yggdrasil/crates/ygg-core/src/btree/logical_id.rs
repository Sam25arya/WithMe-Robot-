#![forbid(unsafe_code)]

/// Packed 64-bit identifier representing a record's physical position:
/// Upper 32 bits = Page Number
/// Lower 32 bits = Slot Index
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct LogicalId(pub u64);

impl LogicalId {
    #[inline]
    pub fn pack(page_number: u32, slot_index: u32) -> Self {
        let packed = ((page_number as u64) << 32) | (slot_index as u64);
        Self(packed)
    }

    #[inline]
    pub fn page_number(&self) -> u32 {
        (self.0 >> 32) as u32
    }

    #[inline]
    pub fn slot_index(&self) -> u32 {
        self.0 as u32
    }

    #[inline]
    pub fn as_u64(&self) -> u64 {
        self.0
    }

    #[inline]
    pub fn from_u64(raw: u64) -> Self {
        Self(raw)
    }
}