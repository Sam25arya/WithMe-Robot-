pub mod logical_id;
pub mod node;

use crate::btree::logical_id::LogicalId;
use crate::btree::node::BTreeNode;
use crate::error::YggError;
use crate::page::header::PAYLOAD_SIZE;

/// Abstract interface for loading and storing raw B+Tree node page payloads[cite: 2].
pub trait PageStorage {
    fn read_page(&self, page_id: u32) -> Result<[u8; PAYLOAD_SIZE], YggError>;
    fn write_page(&mut self, page_id: u32, payload: &[u8; PAYLOAD_SIZE]) -> Result<(), YggError>;
    fn allocate_page(&mut self) -> Result<u32, YggError>;
}

/// On-disk B+Tree manager handling search, insert, and delete operations[cite: 2].
pub struct BPlusTree<'a, S: PageStorage> {
    storage: &'a mut S,
    pub root_page: u32,
}

impl<'a, S: PageStorage> BPlusTree<'a, S> {
    pub fn new(storage: &'a mut S, root_page: u32) -> Self {
        Self { storage, root_page }
    }

    /// Initializes a fresh B+Tree root node if none exists[cite: 2].
    pub fn init_root(&mut self) -> Result<u32, YggError> {
        let root_id = self.storage.allocate_page()?;
        let root_node = BTreeNode::new(true);
        let mut buffer = [0u8; PAYLOAD_SIZE];
        root_node.to_bytes(&mut buffer);
        self.storage.write_page(root_id, &buffer)?;
        self.root_page = root_id;
        Ok(root_id)
    }

    /// Searches for a key in the B+Tree and returns its associated `LogicalId`[cite: 2].
    pub fn search(&self, key: i32) -> Result<Option<LogicalId>, YggError> {
        let leaf_id = self.find_leaf_page(self.root_page, key)?;
        let leaf_bytes = self.storage.read_page(leaf_id)?;
        let leaf_node = BTreeNode::from_bytes(&leaf_bytes)?;

        match leaf_node.find_key(key) {
            Ok(idx) => Ok(Some(LogicalId::from_u64(leaf_node.values[idx]))),
            Err(_) => Ok(None),
        }
    }

    /// Inserts a key and logical record identifier into the tree[cite: 2].
    pub fn insert(&mut self, key: i32, value: LogicalId) -> Result<(), YggError> {
        let leaf_id = self.find_leaf_page(self.root_page, key)?;
        let leaf_bytes = self.storage.read_page(leaf_id)?;
        let mut leaf_node = BTreeNode::from_bytes(&leaf_bytes)?;

        match leaf_node.find_key(key) {
            Ok(idx) => {
                // Update existing record reference[cite: 2]
                leaf_node.values[idx] = value.as_u64();
                let mut buffer = [0u8; PAYLOAD_SIZE];
                leaf_node.to_bytes(&mut buffer);
                self.storage.write_page(leaf_id, &buffer)?;
                Ok(())
            }
            Err(idx) => {
                // Capacity check for max capacity (254 keys to leave split room)[cite: 2, 3]
                if leaf_node.num_keys >= 254 {
                    self.split_leaf_and_insert(leaf_id, &mut leaf_node, key, value)
                } else {
                    leaf_node.insert_leaf_at(idx, key, value);
                    let mut buffer = [0u8; PAYLOAD_SIZE];
                    leaf_node.to_bytes(&mut buffer);
                    self.storage.write_page(leaf_id, &buffer)
                }
            }
        }
    }

    /// Deletes a key entry from the tree[cite: 2].
    pub fn delete(&mut self, key: i32) -> Result<bool, YggError> {
        let leaf_id = self.find_leaf_page(self.root_page, key)?;
        let leaf_bytes = self.storage.read_page(leaf_id)?;
        let mut leaf_node = BTreeNode::from_bytes(&leaf_bytes)?;

        if let Ok(idx) = leaf_node.find_key(key) {
            let count = leaf_node.num_keys as usize;
            if idx < count - 1 {
                leaf_node.keys.copy_within(idx + 1..count, idx);
                leaf_node.values.copy_within(idx + 1..count, idx);
            }
            leaf_node.num_keys -= 1;

            let mut buffer = [0u8; PAYLOAD_SIZE];
            leaf_node.to_bytes(&mut buffer);
            self.storage.write_page(leaf_id, &buffer)?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    /// Traverses internal nodes down to the leaf page for a given key[cite: 2].
    fn find_leaf_page(&self, current_page: u32, key: i32) -> Result<u32, YggError> {
        let page_bytes = self.storage.read_page(current_page)?;
        let node = BTreeNode::from_bytes(&page_bytes)?;

        if node.is_leaf {
            Ok(current_page)
        } else {
            let child_idx = match node.find_key(key) {
                Ok(idx) => idx + 1,
                Err(idx) => idx,
            };
            let child_page = node.children[child_idx];
            self.find_leaf_page(child_page, key)
        }
    }

    /// Splits a full leaf node and propagates the separator key to the parent node[cite: 2].
    fn split_leaf_and_insert(
        &mut self,
        leaf_id: u32,
        leaf_node: &mut BTreeNode,
        key: i32,
        value: LogicalId,
    ) -> Result<(), YggError> {
        let new_leaf_id = self.storage.allocate_page()?;
        let mut new_leaf = BTreeNode::new(true);

        // Compute split mid-point[cite: 2]
        let mid = (leaf_node.num_keys as usize) / 2;

        // Move right half to new leaf[cite: 2]
        let right_count = leaf_node.num_keys as usize - mid;
        new_leaf.keys[..right_count].copy_from_slice(&leaf_node.keys[mid..leaf_node.num_keys as usize]);
        new_leaf.values[..right_count].copy_from_slice(&leaf_node.values[mid..leaf_node.num_keys as usize]);
        new_leaf.num_keys = right_count as u16;

        leaf_node.num_keys = mid as u16;

        // Maintain leaf linked list pointers[cite: 2, 3]
        new_leaf.next_leaf = leaf_node.next_leaf;
        leaf_node.next_leaf = new_leaf_id;
        new_leaf.parent_page = leaf_node.parent_page;

        // Target correct side for new insertion[cite: 2]
        if key >= new_leaf.keys[0] {
            let idx = new_leaf.find_key(key).unwrap_err();
            new_leaf.insert_leaf_at(idx, key, value);
        } else {
            let idx = leaf_node.find_key(key).unwrap_err();
            leaf_node.insert_leaf_at(idx, key, value);
        }

        let mut buf_left = [0u8; PAYLOAD_SIZE];
        let mut buf_right = [0u8; PAYLOAD_SIZE];
        leaf_node.to_bytes(&mut buf_left);
        new_leaf.to_bytes(&mut buf_right);

        self.storage.write_page(leaf_id, &buf_left)?;
        self.storage.write_page(new_leaf_id, &buf_right)?;

        let split_key = new_leaf.keys[0];
        self.insert_into_parent(leaf_id, split_key, new_leaf_id, leaf_node.parent_page)
    }

    /// Propagates internal splits or attaches new leaf pointers to parent nodes[cite: 2].
    fn insert_into_parent(
        &mut self,
        left_child: u32,
        key: i32,
        right_child: u32,
        parent_page: u32,
    ) -> Result<(), YggError> {
        if parent_page == 0 {
            // Create a new root node[cite: 2]
            let new_root_id = self.storage.allocate_page()?;
            let mut new_root = BTreeNode::new(false);
            new_root.keys[0] = key;
            new_root.children[0] = left_child;
            new_root.children[1] = right_child;
            new_root.num_keys = 1;

            let mut root_buf = [0u8; PAYLOAD_SIZE];
            new_root.to_bytes(&mut root_buf);
            self.storage.write_page(new_root_id, &root_buf)?;

            // Update parent pointers on child nodes[cite: 2, 3]
            self.update_parent_pointer(left_child, new_root_id)?;
            self.update_parent_pointer(right_child, new_root_id)?;

            self.root_page = new_root_id;
            Ok(())
        } else {
            let parent_bytes = self.storage.read_page(parent_page)?;
            let mut parent_node = BTreeNode::from_bytes(&parent_bytes)?;

            let insert_idx = match parent_node.find_key(key) {
                Ok(idx) => idx + 1,
                Err(idx) => idx,
            };

            if parent_node.num_keys >= 254 {
                // Internal split logic[cite: 2]
                self.split_internal_and_insert(parent_page, &mut parent_node, insert_idx, key, right_child)
            } else {
                parent_node.insert_internal_at(insert_idx, key, right_child);
                let mut buffer = [0u8; PAYLOAD_SIZE];
                parent_node.to_bytes(&mut buffer);
                self.storage.write_page(parent_page, &buffer)?;
                self.update_parent_pointer(right_child, parent_page)
            }
        }
    }

    /// Splits an internal node when full and promotes the median key upward[cite: 2].
    fn split_internal_and_insert(
        &mut self,
        parent_id: u32,
        parent_node: &mut BTreeNode,
        insert_idx: usize,
        key: i32,
        right_child: u32,
    ) -> Result<(), YggError> {
        parent_node.insert_internal_at(insert_idx, key, right_child);

        let mid = (parent_node.num_keys as usize) / 2;
        let promoted_key = parent_node.keys[mid];

        let new_internal_id = self.storage.allocate_page()?;
        let mut new_internal = BTreeNode::new(false);

        let right_keys_count = parent_node.num_keys as usize - (mid + 1);
        new_internal.keys[..right_keys_count].copy_from_slice(&parent_node.keys[mid + 1..parent_node.num_keys as usize]);
        new_internal.children[..right_keys_count + 1].copy_from_slice(&parent_node.children[mid + 1..parent_node.num_keys as usize + 1]);
        new_internal.num_keys = right_keys_count as u16;
        new_internal.parent_page = parent_node.parent_page;

        parent_node.num_keys = mid as u16;

        let mut buf_left = [0u8; PAYLOAD_SIZE];
        let mut buf_right = [0u8; PAYLOAD_SIZE];
        parent_node.to_bytes(&mut buf_left);
        new_internal.to_bytes(&mut buf_right);

        self.storage.write_page(parent_id, &buf_left)?;
        self.storage.write_page(new_internal_id, &buf_right)?;

        // Reparent moved children to new internal node[cite: 2, 3]
        for i in 0..=right_keys_count {
            self.update_parent_pointer(new_internal.children[i], new_internal_id)?;
        }

        self.insert_into_parent(parent_id, promoted_key, new_internal_id, parent_node.parent_page)
    }

    /// Helper method to update parent pointers on page headers[cite: 2, 3].
    fn update_parent_pointer(&mut self, child_id: u32, parent_id: u32) -> Result<(), YggError> {
        let child_bytes = self.storage.read_page(child_id)?;
        let mut child_node = BTreeNode::from_bytes(&child_bytes)?;
        child_node.parent_page = parent_id;
        let mut buffer = [0u8; PAYLOAD_SIZE];
        child_node.to_bytes(&mut buffer);
        self.storage.write_page(child_id, &buffer)
    }
}