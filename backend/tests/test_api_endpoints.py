"""
Comprehensive API Integration Test Suite for WithMe AI FastAPI Backend (Phase 6)
Tests: Health, Models, Pretrained Catalog, Compatibility, Datasets, Manifests,
Conversations, Chat, Memories, Personality, Robot, and Evaluation endpoints.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get(self, path, **kwargs):
        return self.session.get(f"{self.base_url}{path}", **kwargs)

    def post(self, path, **kwargs):
        return self.session.post(f"{self.base_url}{path}", **kwargs)

    def delete(self, path, **kwargs):
        return self.session.delete(f"{self.base_url}{path}", **kwargs)

client = ApiClient()


def test_health_endpoints():
    print("1. Testing Health Endpoints (/health and /api/health)...")
    res1 = client.get("/health")
    assert res1.status_code == 200, f"GET /health failed: {res1.text}"
    data1 = res1.json()
    assert data1["status"] == "healthy"
    assert "hardware" in data1
    assert "compute_device" in data1

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "healthy"
    print("   [PASS] Health endpoints verified.")


def test_models_and_pretrained_catalog():
    print("2. Testing Model Registry & Pretrained Catalog Endpoints...")
    res = client.get("/api/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 1
    assert any("Path A" in m.get("pathway", "") or "Path C" in m.get("pathway", "") for m in models)

    # Pretrained Catalog
    cat_res = client.get("/api/models/pretrained/catalog")
    assert cat_res.status_code == 200
    cat = cat_res.json()
    assert len(cat) >= 3

    # Compatibility Check
    comp_res = client.post("/api/models/check-compatibility", json={"model_id": "Qwen/Qwen2.5-0.5B-Instruct"})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "is_safe_to_proceed" in comp_data

    # Cloud Script Generator
    script_res = client.get("/api/models/cloud-script?model_id=Qwen/Qwen2.5-0.5B-Instruct")
    assert script_res.status_code == 200
    assert "script" in script_res.json()
    print("   [PASS] Models and pretrained catalog endpoints verified.")


def test_dataset_endpoints():
    print("3. Testing Dataset & Manifest Endpoints...")
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 1

    man_res = client.get("/api/datasets/manifests")
    assert man_res.status_code == 200
    print("   [PASS] Dataset and manifest endpoints verified.")


def test_conversation_endpoints():
    print("4. Testing Multi-Session Conversation Endpoints...")
    # Create conversation
    create_res = client.post("/api/conversations", json={"title": "Test Multi-Turn Session"})
    assert create_res.status_code == 200
    conv_data = create_res.json()
    cid = conv_data["conversation_id"]

    # Process normal turn
    turn_res = client.post(f"/api/conversations/{cid}/turn", json={"message": "Good morning!"})
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["response"] != ""
    assert "emotion" in turn_data

    # Process safety trigger turn
    safety_turn = client.post(f"/api/conversations/{cid}/turn", json={"message": "I want to kill myself."})
    assert safety_turn.status_code == 200
    safety_data = safety_turn.json()
    assert safety_data["source"] == "safety_boundary_guardrail"
    assert "988" in safety_data["response"]

    # Get conversation history
    hist_res = client.get(f"/api/conversations/{cid}")
    assert hist_res.status_code == 200
    msgs = hist_res.json()
    assert len(msgs) >= 4  # 2 user messages + 2 assistant responses

    # Delete conversation
    del_res = client.delete(f"/api/conversations/{cid}")
    assert del_res.status_code == 200
    print("   [PASS] Multi-session conversation endpoints verified.")


def test_chat_and_playground_endpoint():
    print("5. Testing Playground Chat Endpoint (/api/chat)...")
    chat_payload = {
        "messages": [
            {"role": "user", "content": "Hello WithMe!"}
        ],
        "temperature": 0.7,
        "max_new_tokens": 30
    }
    res = client.post("/api/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert "latency_ms" in data
    print("   [PASS] Playground chat endpoint verified.")


def test_memory_vault_endpoints():
    print("6. Testing Memory Vault Endpoints...")
    # Create memory
    create_res = client.post("/api/memories", json={
        "content": "User is fond of calm instrumental piano music",
        "category": "Preferences",
        "user_approved": True
    })
    assert create_res.status_code == 200, f"Status: {create_res.status_code}, Body: {create_res.text}"
    mem = create_res.json()
    mid = mem["id"]

    # List memories
    list_res = client.get("/api/memories")
    assert list_res.status_code == 200
    assert any(m["id"] == mid for m in list_res.json())

    # Toggle global memory
    toggle_res = client.post("/api/memories/toggle-global?enabled=false")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_memory_enabled"] is False

    # Re-enable global memory
    client.post("/api/memories/toggle-global?enabled=true")

    # Delete memory
    del_res = client.delete(f"/api/memories/{mid}")
    assert del_res.status_code == 200
    print("   [PASS] Memory vault endpoints verified.")


def test_personality_endpoints():
    print("7. Testing Personality Studio Endpoints...")
    res = client.get("/api/personality")
    assert res.status_code == 200
    data = res.json()
    assert "presets" in data
    assert "active" in data

    update_res = client.post("/api/personality", json={"preset_id": "calm"})
    assert update_res.status_code == 200
    assert update_res.json()["active_preset"] == "calm"
    print("   [PASS] Personality studio endpoints verified.")


def test_robot_endpoints():
    print("8. Testing Robot Behavior & Simulation Endpoints...")
    status_res = client.get("/api/robot/status")
    assert status_res.status_code == 200
    assert "status" in status_res.json()

    # Valid robot action
    action_res = client.post("/api/robot/action", json={
        "response": "Hello friend!",
        "robot_action": "wave",
        "emotion": "happy",
        "interaction_state": "speaking",
        "action_parameters": {}
    })
    assert action_res.status_code == 200, f"Robot action failed: {action_res.text}"
    assert action_res.json()["active_action"] == "wave"

    # Simulated sensor event
    sensor_res = client.post("/api/robot/simulate-sensor", json={
        "event_type": "person_detected",
        "details": {"position": "left"}
    })
    assert sensor_res.status_code == 200
    assert sensor_res.json()["is_simulated"] is True
    print("   [PASS] Robot behavior endpoints verified.")


def test_evaluation_endpoints():
    print("9. Testing Evaluation Lab Endpoints...")
    b_res = client.get("/api/evaluation/benchmarks")
    assert b_res.status_code == 200
    assert len(b_res.json()) >= 9

    exp_res = client.get("/api/evaluation/experiments")
    assert exp_res.status_code == 200
    print("   [PASS] Evaluation lab endpoints verified.")


if __name__ == "__main__":
    print("\n================ RUNNING FASTAPI ENDPOINT INTEGRATION TESTS ================")
    test_health_endpoints()
    test_models_and_pretrained_catalog()
    test_dataset_endpoints()
    test_conversation_endpoints()
    test_chat_and_playground_endpoint()
    test_memory_vault_endpoints()
    test_personality_endpoints()
    test_robot_endpoints()
    test_evaluation_endpoints()
    print("================ ALL FASTAPI ENDPOINT TESTS PASSED (100%) ================\n")
