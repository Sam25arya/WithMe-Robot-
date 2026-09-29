# WithMe AI Core — REST API Reference (Phase 6)

> **Swagger / OpenAPI Documentation**: When the backend server is running, interactive API docs are accessible at [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs).

---

## 1. System & Health

### `GET /health` | `GET /api/health`
Returns system status, active compute device (CPU/CUDA), hardware specifications (CPU physical/logical cores, total/available RAM, free disk space), active model ID, and memory status.

**Sample Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "active_model_id": "job_1790611170_6716",
  "is_model_loaded": true,
  "compute_device": "CPU",
  "hardware": {
    "platform": "Windows",
    "cpu_count_physical": 12,
    "ram_total_gb": 15.63,
    "ram_available_gb": 2.45,
    "disk_free_gb": 48.2
  },
  "is_memory_enabled": true
}
```

---

## 2. Models & Model Registry

### `GET /api/models`
Returns all registered models across:
- **Path A**: From-scratch experimental Transformer checkpoints.
- **Path B**: Pretrained open-weight LoRA adapters.
- **Path C**: Built-in hybrid companion heuristics.

### `GET /api/models/pretrained/catalog`
Returns curated open-weight foundation models (`Qwen 0.5B`, `TinyLlama 1.1B`, `Gemma 2B`) with license information, parameter counts, and minimum RAM thresholds.

### `POST /api/models/check-compatibility`
**Request Body:**
```json
{"model_id": "Qwen/Qwen2.5-0.5B-Instruct"}
```
Inspects host RAM, disk space, and GPU availability, returning whether local CPU inference and training are safe.

### `GET /api/models/cloud-script?model_id={id}`
Returns copy-paste ready Python script for training on Google Colab or RunPod GPUs.

### `POST /api/models/load`
**Request Body:**
```json
{"model_id": "job_1790611170_6716"}
```
Loads weights into the PyTorch inference engine for active generation.

---

## 3. Dataset Studio & Manifests

### `GET /api/datasets`
Lists all raw (`.jsonl`, `.json`, `.csv`, `.txt`) and processed conversational datasets.

### `GET /api/datasets/manifests`
Lists all registered dataset manifests with SHA-256 integrity hashes, creation timestamps, and split statistics.

### `POST /api/datasets/upload`
Uploads a new conversational dataset and returns validation diagnostics.

### `POST /api/datasets/{dataset_id}/split`
**Parameters:** `val_ratio=0.1`, `test_ratio=0.1`, `seed=42`.
Executes conversation-level 3-way split and generates an immutable manifest.

---

## 4. Training Engine

### `POST /api/training/jobs`
**Request Body:**
```json
{
  "model_name": "WithMe-Transformer-v2",
  "dataset_id": "foundation_demo_dataset",
  "epochs": 5,
  "batch_size": 4,
  "learning_rate": 0.0003,
  "d_model": 128,
  "n_layers": 4,
  "n_heads": 4,
  "ffn_dim": 256,
  "max_seq_len": 128,
  "cpu_threads": 4,
  "resume_from": null
}
```
Spawns non-blocking background PyTorch training worker with AdamW and LR scheduling.

### `GET /api/training/jobs`
Lists all active, completed, and historical training runs.

### `GET /api/training/jobs/{job_id}`
Returns real-time progress: step, epoch, elapsed time, current training loss, validation loss, learning rate, and loss curve telemetry.

### `POST /api/training/jobs/{job_id}/stop`
Requests graceful cancellation and saves intermediate checkpoint safely.

---

## 5. Multi-Session Conversations & Playground Chat

### `GET /api/conversations`
Lists all conversation sessions with titles, timestamps, and message counts.

### `POST /api/conversations`
Creates a new conversation session (`{"title": "Morning Checkin"}`).

### `GET /api/conversations/{conversation_id}`
Retrieves dialogue history for a session.

### `DELETE /api/conversations/{conversation_id}`
Deletes a conversation session and all its messages.

### `POST /api/conversations/{conversation_id}/turn`
**Request Body:**
```json
{
  "message": "I had a stressful presentation today.",
  "model_id": null
}
```
Processes turn through safety guardrails, retrieves relevant user memories, applies sliding context window, injects personality steering, generates model response, and records turn in SQLite.

### `POST /api/chat`
Playground endpoint for direct message generation with configurable temperature, top-$k$, top-$p$, and max tokens.

---

## 6. Memory Vault

### `GET /api/memories`
Lists user-approved memories stored in SQLite (`withme-data/database/withme.db`).

### `POST /api/memories`
Creates explicit user-approved memory with optional expiration timestamp.

### `DELETE /api/memories/{memory_id}`
Deletes individual memory record.

### `DELETE /api/memories`
Clears all stored memories (right to erasure).

### `POST /api/memories/toggle-global?enabled=true`
Global killswitch enabling or disabling persistent memory retrieval.

---

## 7. Personality Studio

### `GET /api/personality`
Returns 5 personality presets (`friendly`, `playful`, `calm`, `energetic`, `quiet`) and active profile sliders.

### `POST /api/personality`
Updates active preset and slider overrides (disclosing that neural weights remain unchanged).

---

## 8. Robot Behavior & Simulation

### `GET /api/robot/status`
Returns current avatar animation state, emotion, active action, and simulated event logs.

### `POST /api/robot/action`
Validates proposed action against allowlist (`idle`, `listen`, `look_left`, `look_right`, `nod`, `wave`, `greet`, `express_happy`, `express_sad`, `express_curiosity`, `express_excited`, `sleep`). Rejects unauthorized actions.

### `POST /api/robot/simulate-sensor`
Simulates sensory events (`person_detected`, `petting_gesture`, `sleep_timer`) and triggers corresponding avatar animations.

---

## 9. Evaluation Lab

### `GET /api/evaluation/benchmarks`
Returns the 9-category benchmark test suite.

### `POST /api/evaluation/run`
Executes test suite, calculates latency and repetition rates, and saves evaluation report.

### `GET /api/evaluation/experiments`
Lists all tracked training runs with configurations and loss curves.

### `POST /api/evaluation/experiments/compare`
Produces side-by-side comparison of two experiment runs.
