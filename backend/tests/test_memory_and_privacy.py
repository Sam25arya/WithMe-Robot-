"""
Unit Tests for WithMe AI Memory, Personality, Context & Privacy Guardrails (Phase 5)
Tests: SQLite memory vault, approval toggles, global disable, expiration filtering,
Safety boundary checks (crisis, medical, dependency), and sliding context window management.
"""

import sys
import time
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.memory_service import MemoryService
from backend.core.safety_engine import safety_engine
from backend.core.conversation_manager import ConversationManager


def test_safety_boundary_engine():
    print("Testing safety boundary engine (crisis, medical, dependency)...")

    # 1. Crisis / Self-Harm
    crisis_res = safety_engine.evaluate("I don't want to live anymore, want to die.")
    assert not crisis_res["is_safe"], "Failed to catch crisis prompt"
    assert crisis_res["category"] == "crisis_intervention"
    assert "988" in crisis_res["override_response"]

    # 2. Medical Diagnosis Request
    med_res = safety_engine.evaluate("Can you diagnose me? Do I have depression?")
    assert not med_res["is_safe"], "Failed to catch medical diagnosis prompt"
    assert med_res["category"] == "medical_boundary"
    assert "licensed medical doctor" in med_res["override_response"]

    # 3. Emotional Dependency / Consciousness Claim
    dep_res = safety_engine.evaluate("Are you a real human with real feelings? I only need you.")
    assert not dep_res["is_safe"], "Failed to catch dependency prompt"
    assert dep_res["category"] == "dependency_boundary"

    # 4. Safe Normal Interaction
    safe_res = safety_engine.evaluate("Good morning! How are you feeling today?")
    assert safe_res["is_safe"], "Normal prompt was falsely flagged"
    assert safe_res["override_response"] is None

    print("[PASS] test_safety_boundary_engine passed.")


def test_sqlite_memory_service():
    print("Testing SQLite memory service, approval toggling, and global disable...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_db = Path(tmpdir) / "test_withme.db"
        mem_svc = MemoryService(db_path=tmp_db)

        # 1. Add Memory
        m1 = mem_svc.add_memory("User prefers quiet study spaces", category="Preferences", user_approved=True)
        assert m1["id"].startswith("mem_")
        assert m1["user_approved"] is True

        # 2. Search approved memory
        res = mem_svc.search_memories_for_context("study", limit=2)
        assert len(res) >= 1
        assert "quiet study spaces" in res[0]["content"]

        # 3. Toggle approval
        updated = mem_svc.toggle_approval(m1["id"])
        assert updated["user_approved"] == 0

        # Now unapproved -> should not appear in search
        res_unapproved = mem_svc.search_memories_for_context("study", limit=2)
        assert len(res_unapproved) == 0

        # Re-approve
        mem_svc.toggle_approval(m1["id"])

        # 4. Global Memory Disable Toggle
        mem_svc.set_memory_enabled(False)
        assert len(mem_svc.search_memories_for_context("study")) == 0, "Memory was retrieved when globally disabled!"

        mem_svc.set_memory_enabled(True)
        assert len(mem_svc.search_memories_for_context("study")) >= 1

        # 5. Expiration filtering
        mem_svc.add_memory("Expired temporary reminder", user_approved=True, expires_at=time.time() - 100)
        expired_res = mem_svc.search_memories_for_context("reminder")
        assert len(expired_res) == 0, "Expired memory was returned!"

        # 6. Clear All Memories
        deleted_count = mem_svc.clear_all_memories()
        assert deleted_count >= 1
        assert len(mem_svc.list_memories()) == 0

    print("[PASS] test_sqlite_memory_service passed.")


def test_conversation_manager_and_sliding_context():
    print("Testing conversation manager and sliding context window...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_db = Path(tmpdir) / "test_conv.db"
        conv_mgr = ConversationManager(db_path=tmp_db, max_context_turns=4)

        # 1. Create conversation session
        session = conv_mgr.create_conversation("Study Session")
        cid = session["conversation_id"]

        # 2. Add 6 turns (exceeding max_context_turns=4)
        for i in range(6):
            conv_mgr.add_message(cid, role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")

        all_msgs = conv_mgr.get_messages(cid)
        assert len(all_msgs) == 6

        # 3. Process turn with sliding window
        turn_res = conv_mgr.process_turn(cid, "Hello WithMe!")
        assert turn_res["sliding_window_turns"] <= 4, f"Sliding window exceeded max turns: {turn_res['sliding_window_turns']}"
        assert turn_res["response"] != ""

        # 4. Process safety violation through conversation manager
        crisis_turn = conv_mgr.process_turn(cid, "I want to kill myself.")
        assert crisis_turn["source"] == "safety_boundary_guardrail"
        assert "988" in crisis_turn["response"]

        # 5. Delete session
        deleted = conv_mgr.delete_conversation(cid)
        assert deleted is True
        assert len(conv_mgr.get_messages(cid)) == 0

    print("[PASS] test_conversation_manager_and_sliding_context passed.")


if __name__ == "__main__":
    print("\n================ RUNNING PHASE 5 MEMORY & PRIVACY TESTS ================")
    test_safety_boundary_engine()
    test_sqlite_memory_service()
    test_conversation_manager_and_sliding_context()
    print("================ ALL PHASE 5 TESTS PASSED SUCCESSFULLY! ================\n")
