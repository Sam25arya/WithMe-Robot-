#![forbid(unsafe_code)]

use core::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum YggError {
    /// Authentication tag verification failed for a page
    PageAuthenticationFailed { page_id: u32 },
    /// Buffer capacity is insufficient for frame operations
    BufferTooSmall,
    /// Failed to convert raw slice to fixed array
    SliceConversionFailed,
    /// Header parsing failed due to invalid dimensions or corrupted layout
    HeaderParseFailed,
    /// Hardware/Storage tier error
    StorageError,
}

impl fmt::Display for YggError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::PageAuthenticationFailed { page_id } => {
                write!(f, "Page authentication failed for Page ID: {page_id}")
            }
            Self::BufferTooSmall => write!(f, "Buffer capacity is insufficient for frame operations"),
            Self::SliceConversionFailed => write!(f, "Failed to convert raw slice to fixed array"),
            Self::HeaderParseFailed => write!(f, "Page header bytes corrupted or malformed"),
            Self::StorageError => write!(f, "Underlying block device I/O error"),
        }
    }
}