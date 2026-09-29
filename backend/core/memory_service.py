"""
WithMe AI Core - SQLite Memory Management Service (Phase 5)
Persistent, user-controlled memory vault separate from neural model weights.
Supports explicit CRUD, approval toggles, category filtering, expiration dates,
and a global memory enablement toggle.
"""

import sqlite3
import uuid
import time
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH


from contextlib import contextmanager


class MemoryService:
    """Manages explicit user-approved memory storage, retrieval, and privacy controls."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.is_memory_enabled = True
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    tag TEXT DEFAULT 'custom',
                    user_approved INTEGER DEFAULT 1,
                    source TEXT DEFAULT 'user_explicit',
                    created_at REAL NOT NULL,
                    expires_at REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion TEXT,
                    robot_action TEXT,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
            """)
            # Migration check: ensure expires_at exists in memories table
            cursor.execute("PRAGMA table_info(memories)")
            existing_cols = [col["name"] for col in cursor.fetchall()]
            if "expires_at" not in existing_cols:
                cursor.execute("ALTER TABLE memories ADD COLUMN expires_at REAL")

            conn.commit()

            # Seed initial sample memories if table is empty
            cursor.execute("SELECT COUNT(*) as cnt FROM memories")
            if cursor.fetchone()["cnt"] == 0:
                initial_memories = [
                    ("mem_001", "User mentioned having an upcoming major presentation.", "Events", "Academic", 1, "explicit", time.time(), None),
                    ("mem_002", "User loves sci-fi guessing games and Would You Rather.", "Preferences", "Hobbies", 1, "explicit", time.time(), None),
                    ("mem_003", "User prefers gentle, supportive check-ins when feeling stressed.", "Communication", "Emotional", 1, "explicit", time.time(), None)
                ]
                cursor.executemany("""
                    INSERT INTO memories (id, content, category, tag, user_approved, source, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, initial_memories)
                conn.commit()

    def set_memory_enabled(self, enabled: bool) -> bool:
        """Global toggle to enable or disable persistent memory retrieval."""
        self.is_memory_enabled = enabled
        return self.is_memory_enabled

    def list_memories(self, category: Optional[str] = None, approved_only: bool = False) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM memories WHERE 1=1"
            params = []
            if category and category.lower() != "all":
                query += " AND category = ?"
                params.append(category)
            if approved_only:
                query += " AND user_approved = 1"
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def add_memory(
        self,
        content: str,
        category: str = "general",
        tag: str = "custom",
        user_approved: bool = True,
        expires_at: Optional[float] = None
    ) -> Dict[str, Any]:
        mem_id = f"mem_{uuid.uuid4().hex[:8]}"
        created_at = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (id, content, category, tag, user_approved, source, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, 'user_input', ?, ?)
            """, (mem_id, content.strip(), category, tag, 1 if user_approved else 0, created_at, expires_at))
            conn.commit()
        return {
            "id": mem_id,
            "content": content.strip(),
            "category": category,
            "tag": tag,
            "user_approved": user_approved,
            "created_at": created_at,
            "expires_at": expires_at
        }

    def delete_memory(self, memory_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        """Delete all memories from database (user privacy right to erasure)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories")
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def toggle_approval(self, memory_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_approved FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            new_val = 0 if row["user_approved"] == 1 else 1
            cursor.execute("UPDATE memories SET user_approved = ? WHERE id = ?", (new_val, memory_id))
            conn.commit()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            return dict(cursor.fetchone())

    def search_memories_for_context(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve user-approved, non-expired memories relevant to current user conversation query.
        Returns empty list if memory is globally disabled.
        """
        if not self.is_memory_enabled:
            return []

        all_approved = self.list_memories(approved_only=True)
        now = time.time()
        # Filter out expired memories
        valid_memories = [m for m in all_approved if m.get("expires_at") is None or m["expires_at"] > now]

        if not valid_memories:
            return []

        query_words = set(query.lower().split())
        scored = []
        for mem in valid_memories:
            content_words = set(mem["content"].lower().split())
            overlap = len(query_words.intersection(content_words))
            scored.append((overlap, mem))

        # Sort by overlap descending, then recent
        scored.sort(key=lambda x: (-x[0], -x[1]["created_at"]))
        matching = [m for overlap, m in scored if overlap > 0]
        return matching[:limit]


memory_service = MemoryService()
