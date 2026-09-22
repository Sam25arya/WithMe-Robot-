#![forbid(unsafe_code)]

use crate::error::YggError;

pub const KEY_LEN: usize = 16;
pub const NONCE_LEN: usize = 16;
pub const TAG_LEN: usize = 16;

fn transform_state(st: &mut [u64; 5], rounds: usize) {
    let start_round = 12 - rounds;
    for r in start_round..12 {
        st[2] ^= (((0x0F - r as u64) << 4) | (r as u64)) as u64;

        st[0] ^= st[4];
        st[4] ^= st[3];
        st[2] ^= st[1];

        let v0 = !st[0] & st[1];
        let v1 = !st[1] & st[2];
        let v2 = !st[2] & st[3];
        let v3 = !st[3] & st[4];
        let v4 = !st[4] & st[0];

        st[0] ^= v1;
        st[1] ^= v2;
        st[2] ^= v3;
        st[3] ^= v4;
        st[4] ^= v0;

        st[1] ^= st[0];
        st[0] ^= st[4];
        st[3] ^= st[2];
        st[2] = !st[2];

        st[0] ^= st[0].rotate_right(19) ^ st[0].rotate_right(28);
        st[1] ^= st[1].rotate_right(61) ^ st[1].rotate_right(39);
        st[2] ^= st[2].rotate_right(1) ^ st[2].rotate_right(6);
        st[3] ^= st[3].rotate_right(10) ^ st[3].rotate_right(17);
        st[4] ^= st[4].rotate_right(7) ^ st[4].rotate_right(41);
    }
}

pub fn encrypt_in_place(
    key: &[u8; KEY_LEN],
    nonce: &[u8; NONCE_LEN],
    assoc_data: &[u8],
    buf: &mut [u8],
    payload_len: usize,
) -> Result<usize, YggError> {
    if buf.len() < payload_len + TAG_LEN {
        return Err(YggError::BufferTooSmall);
    }

    let k0 = match key[0..8].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let k1 = match key[8..16].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let n0 = match nonce[0..8].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let n1 = match nonce[8..16].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };

    let mut st = [0x8040_0c06_0000_0000u64, k0, k1, n0, n1];

    transform_state(&mut st, 12);
    st[3] ^= k0;
    st[4] ^= k1;

    if !assoc_data.is_empty() {
        let mut chunks = assoc_data.chunks_exact(8);
        for chunk in chunks.by_ref() {
            let block = match chunk.try_into() {
                Ok(bytes) => u64::from_be_bytes(bytes),
                Err(_) => return Err(YggError::SliceConversionFailed),
            };
            st[0] ^= block;
            transform_state(&mut st, 6);
        }

        let rem = chunks.remainder();
        let mut pad_block = 0u64;
        for (i, &b) in rem.iter().enumerate() {
            pad_block |= (b as u64) << (56 - i * 8);
        }
        pad_block |= 0x80u64 << (56 - rem.len() * 8);
        st[0] ^= pad_block;
        transform_state(&mut st, 6);
    }
    st[4] ^= 1;

    let (payload_buf, tag_buf) = buf[..payload_len + TAG_LEN].split_at_mut(payload_len);
    let mut chunks = payload_buf.chunks_exact_mut(8);

    for chunk in chunks.by_ref() {
        let p_block = match chunk.try_into() {
            Ok(bytes) => u64::from_be_bytes(bytes),
            Err(_) => return Err(YggError::SliceConversionFailed),
        };
        st[0] ^= p_block;
        chunk.copy_from_slice(&st[0].to_be_bytes());
        transform_state(&mut st, 6);
    }

    let rem = chunks.into_remainder();
    let rem_len = rem.len();
    if rem_len > 0 {
        let mut tail_block = 0u64;
        for (i, &b) in rem.iter().enumerate() {
            tail_block |= (b as u64) << (56 - i * 8);
        }
        tail_block |= 0x80u64 << (56 - rem_len * 8);
        st[0] ^= tail_block;

        for (i, byte) in rem.iter_mut().enumerate() {
            *byte = (st[0] >> (56 - i * 8)) as u8;
        }
    }

    st[1] ^= k0;
    st[2] ^= k1;
    transform_state(&mut st, 12);
    st[3] ^= k0;
    st[4] ^= k1;

    tag_buf[0..8].copy_from_slice(&st[3].to_be_bytes());
    tag_buf[8..16].copy_from_slice(&st[4].to_be_bytes());

    Ok(payload_len + TAG_LEN)
}

pub fn decrypt_in_place(
    key: &[u8; KEY_LEN],
    nonce: &[u8; NONCE_LEN],
    assoc_data: &[u8],
    buf: &mut [u8],
    page_id: u32,
) -> Result<usize, YggError> {
    if buf.len() < TAG_LEN {
        return Err(YggError::BufferTooSmall);
    }

    let raw_len = buf.len() - TAG_LEN;
    let k0 = match key[0..8].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let k1 = match key[8..16].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let n0 = match nonce[0..8].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let n1 = match nonce[8..16].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };

    let mut st = [0x8040_0c06_0000_0000u64, k0, k1, n0, n1];

    transform_state(&mut st, 12);
    st[3] ^= k0;
    st[4] ^= k1;

    if !assoc_data.is_empty() {
        let mut chunks = assoc_data.chunks_exact(8);
        for chunk in chunks.by_ref() {
            let block = match chunk.try_into() {
                Ok(bytes) => u64::from_be_bytes(bytes),
                Err(_) => return Err(YggError::SliceConversionFailed),
            };
            st[0] ^= block;
            transform_state(&mut st, 6);
        }

        let rem = chunks.remainder();
        let mut pad_block = 0u64;
        for (i, &b) in rem.iter().enumerate() {
            pad_block |= (b as u64) << (56 - i * 8);
        }
        pad_block |= 0x80u64 << (56 - rem.len() * 8);
        st[0] ^= pad_block;
        transform_state(&mut st, 6);
    }
    st[4] ^= 1;

    let (ct_buf, input_tag_buf) = buf.split_at_mut(raw_len);
    let mut chunks = ct_buf.chunks_exact_mut(8);

    for chunk in chunks.by_ref() {
        let c_block = match chunk.try_into() {
            Ok(bytes) => u64::from_be_bytes(bytes),
            Err(_) => return Err(YggError::SliceConversionFailed),
        };
        let p_block = st[0] ^ c_block;
        chunk.copy_from_slice(&p_block.to_be_bytes());
        st[0] = c_block;
        transform_state(&mut st, 6);
    }

    let rem = chunks.into_remainder();
    let rem_len = rem.len();
    if rem_len > 0 {
        let mut tail_chunk = 0u64;
        for (i, &b) in rem.iter().enumerate() {
            tail_chunk |= (b as u64) << (56 - i * 8);
        }

        for (i, byte) in rem.iter_mut().enumerate() {
            let plain = (*byte) ^ ((st[0] >> (56 - i * 8)) as u8);
            *byte = plain;
        }

        let mask = !0u64 << (56 - rem_len * 8);
        st[0] = (st[0] & !mask) | tail_chunk;
        st[0] ^= 0x80u64 << (56 - rem_len * 8);
    } else {
        st[0] ^= 0x80u64 << 56;
    }

    st[1] ^= k0;
    st[2] ^= k1;
    transform_state(&mut st, 12);
    st[3] ^= k0;
    st[4] ^= k1;

    let expected_tag1 = st[3];
    let expected_tag2 = st[4];

    let input_tag1 = match input_tag_buf[0..8].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };
    let input_tag2 = match input_tag_buf[8..16].try_into() {
        Ok(bytes) => u64::from_be_bytes(bytes),
        Err(_) => return Err(YggError::SliceConversionFailed),
    };

    if ((expected_tag1 ^ input_tag1) | (expected_tag2 ^ input_tag2)) != 0 {
        return Err(YggError::PageAuthenticationFailed { page_id });
    }

    Ok(raw_len)
}