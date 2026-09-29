"""
WithMe AI Core - End-to-End API and Pipeline Integration Test
Verifies all FastAPI REST endpoints, real PyTorch training loop, checkpoint loading,
autoregressive generation with latency/tokens-per-sec metrics, SQLite memory, and robot simulation.
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000/api"


def run_e2e():
    print("\n================ STARTING WITHME AI CORE E2E INTEGRATION TEST ================\n")

    # 1. Health & Hardware
    print("1. Testing Health and Compute Hardware...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health = r.json()
    print(f"   [PASS] Health Status: {health['status']} | Active Model: {health['active_model']} | Device: {health['compute_device']}")

    r_hw = requests.get(f"{BASE_URL}/hardware")
    assert r_hw.status_code == 200
    hw = r_hw.json()
    print(f"   [PASS] Compute Specs: {hw['processor']} ({hw['cpu_count_physical']} physical cores) | RAM: {hw['ram_available_gb']} GB Free / {hw['ram_total_gb']} GB Total")

    # 2. Datasets
    print("\n2. Testing Datasets...")
    r_d = requests.get(f"{BASE_URL}/datasets")
    assert r_d.status_code == 200
    datasets = r_d.json()
    print(f"   [PASS] Discovered {len(datasets)} dataset(s).")
    for d in datasets:
        print(f"          - {d['name']} ({d['type']}, {d['format']}): {d.get('conversation_count', 0)} conversations")

    # 3. Model Registry & Checkpoints
    print("\n3. Testing Model Registry & Checkpoint Catalog...")
    r_m = requests.get(f"{BASE_URL}/models")
    assert r_m.status_code == 200
    models = r_m.json()
    print(f"   [PASS] Discovered {len(models)} registered model(s).")
    for m in models:
        print(f"          - {m['name']} (ID: {m['model_id']}, Params: {m['param_count']:,}, File: {m['checkpoint_file']})")

    # Find the trained from-scratch checkpoint
    trained_model = next((m for m in models if m["development_type"] == "from_scratch"), None)
    assert trained_model is not None, "A trained from-scratch PyTorch model checkpoint must exist!"

    # 4. Load Model into Inference Engine
    print(f"\n4. Loading Trained Model '{trained_model['model_id']}' into PyTorch Inference Engine...")
    r_load = requests.post(f"{BASE_URL}/models/load", json={"model_id": trained_model["model_id"]})
    assert r_load.status_code == 200, f"Load model failed: {r_load.text}"
    load_res = r_load.json()
    print(f"   [PASS] Model loaded successfully: {load_res['model_id']} ({load_res['architecture']}, {load_res['param_count']:,} weights on {load_res['device']})")

    # Verify active model
    r_act = requests.get(f"{BASE_URL}/models/active")
    assert r_act.status_code == 200
    assert r_act.json()["active_model_id"] == trained_model["model_id"]
    print(f"   [PASS] Confirmed active model: {r_act.json()['active_model_id']}")

    # 5. Live Inference (Autoregressive Generation)
    print("\n5. Testing Live Autoregressive Inference from Saved Checkpoint...")
    prompt = "Hello WithMe, how are you today?"
    chat_payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_new_tokens": 30,
        "include_memories": True
    }
    t0 = time.time()
    r_chat = requests.post(f"{BASE_URL}/chat", json=chat_payload)
    assert r_chat.status_code == 200, f"Chat generation failed: {r_chat.text}"
    chat_res = r_chat.json()
    print(f"   [PASS] User Input: \"{prompt}\"")
    print(f"          Model Output: \"{chat_res['text']}\"")
    print(f"          Source Disclosure: {chat_res['source']} (is_genuine_trained_model: {chat_res['is_genuine_trained_model']})")
    print(f"          Latency: {chat_res['latency_ms']} ms | Tokens/sec: {chat_res['tokens_per_second']}")
    print(f"          Robot Emotion: {chat_res['emotion']} | Robot Action: {chat_res['robot_action']}")

    # 6. Memory Lab (SQLite Storage & Retrieval)
    print("\n6. Testing SQLite Memory Lab...")
    r_mem_create = requests.post(f"{BASE_URL}/memories", json={
        "content": "User is studying human-robot interaction and affective computing.",
        "category": "Academic",
        "tag": "Research",
        "user_approved": True
    })
    assert r_mem_create.status_code == 200
    new_mem = r_mem_create.json()
    print(f"   [PASS] Stored Memory: \"{new_mem['content']}\" (ID: {new_mem['id']})")

    r_mems = requests.get(f"{BASE_URL}/memories")
    assert r_mems.status_code == 200
    all_mems = r_mems.json()
    print(f"   [PASS] Total User Memories in SQLite: {len(all_mems)}")

    # Test memory context retrieval during inference
    r_mem_chat = requests.post(f"{BASE_URL}/chat", json={
        "messages": [{"role": "user", "content": "What am I studying in my research?"}],
        "include_memories": True
    })
    assert r_mem_chat.status_code == 200
    mem_chat_res = r_mem_chat.json()
    assert len(mem_chat_res["retrieved_memories"]) > 0, "Should retrieve relevant memory context!"
    print(f"   [PASS] Memory Injected in Context: \"{mem_chat_res['retrieved_memories'][0]['content']}\"")

    # 7. Evaluation Lab (Benchmark Suite)
    print("\n7. Testing Evaluation Lab Benchmark Suite...")
    r_eval = requests.post(f"{BASE_URL}/evaluation/run", json={})
    assert r_eval.status_code == 200, f"Evaluation run failed: {r_eval.text}"
    eval_res = r_eval.json()
    print(f"   [PASS] Evaluation Report Generated (ID: {eval_res['eval_id']})")
    print(f"          Model Tested: {eval_res['model_id']} | Source: {eval_res['model_source']}")
    print(f"          Test Prompts Evaluated: {eval_res['test_count']} | Avg Latency: {eval_res['average_latency_ms']} ms")
    for r in eval_res["results"][:2]:
        print(f"          * [{r['category']}] \"{r['prompt']}\" -> \"{r['actual_output']}\" ({r['latency_ms']} ms)")

    # 8. Robot Integration & Simulated Vision/Sensors
    print("\n8. Testing Robot Behavior & Sensor Simulation Layer...")
    r_sim = requests.post(f"{BASE_URL}/robot/simulate-sensor", json={
        "event_type": "person_detected",
        "details": {"position": "left", "distance_meters": 1.2}
    })
    assert r_sim.status_code == 200
    sim_data = r_sim.json()
    print(f"   [PASS] Triggered Sensor Event: person_detected (left) -> Resulting Action: {sim_data['resulting_action']}")
    print(f"          Disclosure: {sim_data['note']}")

    r_stat = requests.get(f"{BASE_URL}/robot/status")
    assert r_stat.status_code == 200
    current_robot = r_stat.json()["status"]
    assert current_robot["active_action"] == "look_left", "Robot state should have turned left toward simulated person!"
    print(f"   [PASS] Current Robot State: action={current_robot['active_action']}, emotion={current_robot['emotion']}, is_simulation={r_stat.json()['status']['is_simulation']}")

    # 9. Real Training Job Launch Test
    print("\n9. Testing Asynchronous PyTorch Training Job Launch...")
    train_job_req = {
        "model_name": "WithMe-SmokeTest-LM",
        "dataset_id": datasets[0]["id"] if datasets else "withme_synthetic_demo",
        "epochs": 2,
        "batch_size": 2,
        "learning_rate": 0.001
    }
    r_job = requests.post(f"{BASE_URL}/training/jobs", json=train_job_req)
    assert r_job.status_code == 200, f"Training job launch failed: {r_job.text}"
    job_info = r_job.json()
    job_id = job_info["job_id"]
    print(f"   [PASS] Asynchronous Training Job Launched (ID: {job_id})")

    # Poll status for a couple steps
    time.sleep(1.5)
    r_poll = requests.get(f"{BASE_URL}/training/jobs/{job_id}")
    assert r_poll.status_code == 200
    poll_data = r_poll.json()
    print(f"   [PASS] Training Job Status: {poll_data['status'].upper()} | Epoch: {poll_data['current_epoch']}/{poll_data['total_epochs']} | Step: {poll_data['current_step']}/{poll_data['total_steps']}")
    if poll_data.get("latest_train_loss"):
        print(f"          Latest Measured Loss: {poll_data['latest_train_loss']:.4f}")

    print("\n================ ALL 9 E2E INTEGRATION TESTS PASSED WITH 100% SUCCESS ================\n")


if __name__ == "__main__":
    run_e2e()
