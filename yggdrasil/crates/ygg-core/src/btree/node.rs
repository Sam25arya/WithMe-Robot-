#![forbid(unsafe_code)]

use crate::btree::logical_id::LogicalId;
use crate::error::YggError;
use crate::page::header::PAYLOAD_SIZE;

pub const NODE_TYPE_LEAF: u8 = 0x01;
pub const NODE_TYPE_INTERNAL: u8 = 0x02;

pub const OFFSET_NODE_TYPE: usize = 0;
pub const OFFSET_NUM_KEYS: usize = 1;
pub const OFFSET_PARENT_PAGE: usize = 3;
pub const OFFSET_NEXT_LEAF: usize = 7;
pub const OFFSET_KEYS_START: usize = 11;

/// Represents a B+Tree node backed by a fixed byte buffer[cite: 3].
#[derive(Debug, Clone)]
pub struct BTreeNode {
    pub is_leaf: bool,
    pub num_keys: u16,
    pub parent_page: u32,
    pub next_leaf: u32, // Only valid if `is_leaf` is true[cite: 3]
    pub keys: [i32; 255],
    /// For Leaf Nodes: array of packed LogicalIds matching key indices[cite: 3].
    pub values: [u64; 255],
    /// For Internal Nodes: array of child page numbers (num_keys + 1 entries)[cite: 3].
    pub children: [u32; 256],
}

impl BTreeNode {
    /// Creates a new, empty B+Tree node[cite: 3].
    pub fn new(is_leaf: bool) -> Self {
        Self {
            is_leaf,
            num_keys: 0,
            parent_page: 0,
            next_leaf: 0,
            keys: [0; 255],
            values: [0; 255],
            children: [0; 256],
        }
    }

    /// Deserializes a node from raw page payload bytes[cite: 3].
    pub fn from_bytes(bytes: &[u8; PAYLOAD_SIZE]) -> Result<Self, YggError> {
        let node_type = bytes[OFFSET_NODE_TYPE];
        let is_leaf = match node_type {
            NODE_TYPE_LEAF => true,
            NODE_TYPE_INTERNAL => false,
            _ => return Err(YggError::HeaderParseFailed),
        };

        let num_keys = u16::from_be_bytes(
            bytes[OFFSET_NUM_KEYS..OFFSET_NUM_KEYS + 2]
                .try_into()
                .map_err(|_| YggError::HeaderParseFailed)?,
        );

        let parent_page = u32::from_be_bytes(
            bytes[OFFSET_PARENT_PAGE..OFFSET_PARENT_PAGE + 4]
                .try_into()
                .map_err(|_| YggError::HeaderParseFailed)?,
        );

        let next_leaf = u32::from_be_bytes(
            bytes[OFFSET_NEXT_LEAF..OFFSET_NEXT_LEAF + 4]
                .try_into()
                .map_err(|_| YggError::HeaderParseFailed)?,
        );

        let mut node = Self::new(is_leaf);
        node.num_keys = num_keys;
        node.parent_page = parent_page;
        node.next_leaf = next_leaf;

        let mut cursor = OFFSET_KEYS_START;

        // Deserializes sorted keys[cite: 3]
        for i in 0..num_keys as usize {
            if cursor + 4 > PAYLOAD_SIZE {
                return Err(YggError::HeaderParseFailed);
            }
            node.keys[i] = i32::from_be_bytes(bytes[cursor..cursor + 4].try_into().unwrap());
            cursor += 4;
        }

        if is_leaf {
            // Leaf node: deserialize LogicalId array[cite: 3]
            for i in 0..num_keys as usize {
                if cursor + 8 > PAYLOAD_SIZE {
                    return Err(YggError::HeaderParseFailed);
                }
                node.values[i] = u64::from_be_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
                cursor += 8;
            }
        } else {
            // Internal node: deserialize child pointers (num_keys + 1)[cite: 3]
            let child_count = (num_keys as usize) + 1;
            for i in 0..child_count {
                if cursor + 4 > PAYLOAD_SIZE {
                    return Err(YggError::HeaderParseFailed);
                }
                node.children[i] = u32::from_be_bytes(bytes[cursor..cursor + 4].try_into().unwrap());
                cursor += 4;
            }
        }

        Ok(node)
    }

    /// Serializes node state into raw page payload bytes[cite: 3].
    pub fn to_bytes(&self, bytes: &mut [u8; PAYLOAD_SIZE]) {
        bytes.fill(0);

        bytes[OFFSET_NODE_TYPE] = if self.is_leaf {
            NODE_TYPE_LEAF
        } else {
            NODE_TYPE_INTERNAL
        };

        bytes[OFFSET_NUM_KEYS..OFFSET_NUM_KEYS + 2].copy_from_slice(&self.num_keys.to_be_bytes());
        bytes[OFFSET_PARENT_PAGE..OFFSET_PARENT_PAGE + 4].copy_from_slice(&self.parent_page.to_be_bytes());
        bytes[OFFSET_NEXT_LEAF..OFFSET_NEXT_LEAF + 4].copy_from_slice(&self.next_leaf.to_be_bytes());

        let mut cursor = OFFSET_KEYS_START;

        // Serializes keys[cite: 3]
        for i in 0..self.num_keys as usize {
            bytes[cursor..cursor + 4].copy_from_slice(&self.keys[i].to_be_bytes());
            cursor += 4;
        }

        if self.is_leaf {
            // Serializes values[cite: 3]
            for i in 0..self.num_keys as usize {
                bytes[cursor..cursor + 8].copy_from_slice(&self.values[i].to_be_bytes());
                cursor += 8;
            }
        } else {
            // Serializes children[cite: 3]
            let child_count = (self.num_keys as usize) + 1;
            for i in 0..child_count {
                bytes[cursor..cursor + 4].copy_from_slice(&self.children[i].to_be_bytes());
                cursor += 4;
            }
        }
    }

    /// Performs binary search to locate key or target child pointer[cite: 3].
    pub fn find_key(&self, key: i32) -> Result<usize, usize> {
        let keys_slice = &self.keys[..self.num_keys as usize];
        keys_slice.binary_search(&key)
    }

    /// Inserts a key-value pair into a leaf node at specified index[cite: 3].
    pub fn insert_leaf_at(&mut self, index: usize, key: i32, value: LogicalId) {
        let count = self.num_keys as usize;
        if index < count {
            self.keys.copy_within(index..count, index + 1);
            self.values.copy_within(index..count, index + 1);
        }
        self.keys[index] = key;
        self.values[index] = value.as_u64();
        self.num_keys += 1;
    }

    /// Inserts a key and right-child pointer into an internal node at specified index[cite: 3].
    pub fn insert_internal_at(&mut self, index: usize, key: i32, right_child: u32) {
        let count = self.num_keys as usize;
        if index < count {
            self.keys.copy_within(index..count, index + 1);
        }
        let child_index = index + 1;
        let total_children = count + 1;
        if child_index < total_children {
            self.children.copy_within(child_index..total_children, child_index + 1);
        }
        self.keys[index] = key;
        self.children[child_index] = right_child;
        self.num_keys += 1;
    }
}