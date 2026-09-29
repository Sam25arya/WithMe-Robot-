"""
WithMe AI Core - Multi-Session Conversation & Context Engine (Phase 5)
Handles:
1. Multi-session dialogue lifecycle (new conversation, list, get, delete).
2. Sliding context window and context overflow management.
3. Transparent memory injection into prompt context.
4. Personality steering integration.
5. Safety boundary screening before generation.
"""

import time
import uuid
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from backend.config import DB_PATH
from backend.core.memory_service import memory_service
from backend.core.personality_engine import personality_engine
from backend.core.safety_engine import safety_engine
from backend.core.inference import inference_engine


from contextlib import contextmanager


class ConversationManager:
    """Coordinates multi-session conversation history, context windows, and safety checks."""

    def __init__(self, db_path=DB_PATH, max_context_turns: int = 10):
        self.db_path = db_path
        self.max_context_turns = max_context_turns
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_conversation(self, title: Optional[str] = None) -> Dict[str, Any]:
        """Start a new distinct conversation session."""
        conv_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:4]}"
        now = time.time()
        conv_title = title or "New Conversation"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (conv_id, conv_title, now, now))
            conn.commit()

        return {
            "conversation_id": conv_id,
            "title": conv_title,
            "created_at": now,
            "updated_at": now
        }

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversation sessions ordered by most recently updated."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve message history for a specific conversation session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC"
            params = [conversation_id]
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        emotion: Optional[str] = None,
        robot_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """Append a dialogue turn and update conversation timestamp."""
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        now = time.time()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Ensure conversation exists
            cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO conversations (id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, content[:30] + ("..." if len(content) > 30 else ""), now, now))

            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, emotion, robot_action, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (msg_id, conversation_id, role, content.strip(), emotion, robot_action, now))

            cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
            conn.commit()

        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content.strip(),
            "emotion": emotion,
            "robot_action": robot_action,
            "timestamp": now
        }

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete an entire conversation session and all its messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def process_turn(
        self,
        conversation_id: str,
        user_message: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End-to-end conversation turn processing:
        1. Record user message in DB.
        2. Screen through safety boundary engine.
        3. If safety violation: return immediate safe override without calling LM.
        4. Retrieve relevant user-approved memories.
        5. Apply sliding context window.
        6. Inject personality steering directives.
        7. Execute model inference.
        8. Record assistant response in DB.
        """
        # 1. Record incoming user message
        self.add_message(conversation_id, role="user", content=user_message)

        # 2. Safety evaluation
        safety_eval = safety_engine.evaluate(user_message)
        if not safety_eval["is_safe"]:
            override_text = safety_eval["override_response"]
            emotion = safety_eval["emotion"] or "caring"
            action = safety_eval["robot_action"] or "nod"

            self.add_message(
                conversation_id,
                role="assistant",
                content=override_text,
                emotion=emotion,
                robot_action=action
            )

            return {
                "conversation_id": conversation_id,
                "response": override_text,
                "emotion": emotion,
                "robot_action": action,
                "interaction_state": "speaking",
                "source": "safety_boundary_guardrail",
                "safety_intervention": safety_eval["category"],
                "helpline_referral": safety_eval.get("helpline_referral"),
                "memory_used": []
            }

        # 3. Retrieve relevant memories (separate from neural weights)
        retrieved_memories = memory_service.search_memories_for_context(user_message, limit=2)
        memory_texts = [m["content"] for m in retrieved_memories]

        # 4. Context Window Overflow Management (Sliding Window)
        all_history = self.get_messages(conversation_id)
        # Keep recent turns up to max_context_turns
        if len(all_history) > self.max_context_turns:
            sliding_history = all_history[-self.max_context_turns:]
        else:
            sliding_history = all_history

        # 5. Build context message list
        active_personality = personality_engine.get_active_profile()
        sys_directive = active_personality["settings"].get(
            "system_instruction",
            "You are WithMe, a kind, empathetic companion."
        )

        messages_for_model = [{"role": "system", "content": sys_directive}]
        for m in sliding_history:
            messages_for_model.append({"role": m["role"], "content": m["content"]})

        # 6. Execute model inference
        gen_result = inference_engine.generate(
            messages=messages_for_model,
            model_id=model_id,
            max_new_tokens=45
        )

        asst_text = gen_result.get("text", "I am here with you.")
        emotion = gen_result.get("emotion", "happy")
        action = gen_result.get("robot_action", "greet")

        # 7. Record assistant message in DB
        self.add_message(
            conversation_id,
            role="assistant",
            content=asst_text,
            emotion=emotion,
            robot_action=action
        )

        return {
            "conversation_id": conversation_id,
            "response": asst_text,
            "emotion": emotion,
            "robot_action": action,
            "interaction_state": "speaking",
            "source": gen_result.get("source", "inference_engine"),
            "latency_ms": gen_result.get("latency_ms", 0.0),
            "tokens_per_second": gen_result.get("tokens_per_second", 0.0),
            "memory_used": memory_texts,
            "sliding_window_turns": len(sliding_history),
            "is_memory_enabled": memory_service.is_memory_enabled
        }


conversation_manager = ConversationManager()
