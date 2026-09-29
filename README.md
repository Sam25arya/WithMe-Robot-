# WithMe AI Core — Trainable AI Companion & Robot Prototype

> **"WithMe doesn't just answer you. It stays with you."**

WithMe is a hybrid AI-powered emotional companion platform featuring a **genuine from-scratch PyTorch training pipeline**, a modular **FastAPI backend**, an **AI Training Studio** with 11 research modules, an **expressive virtual robot avatar**, a transparent **lexical memory vault** (SQLite), and a hardware-agnostic **robot behavior controller**.

---

## 🌟 Key Highlights & Engineering Transparency

1. **Genuine PyTorch Training Pipeline**: Includes a small causal Transformer LM, custom conversational tokenizer, teacher-forced next-token prediction, AdamW optimization, cross-entropy loss tracking, and persistent `.pt` checkpoints.
2. **Transparent Machine Learning**: No fake progress bars. The UI and documentation explicitly distinguish between:
   - **From-Scratch Pretraining**: Weight matrices initialized randomly ($\mathcal{N}(0, 0.02)$); requires dataset training to learn tokens.
   - **Pretrained Models & Fine-Tuning**: Pre-existing weights adapted via LoRA or instruction tuning.
   - **Inference Steering**: Personality sliders alter prompt directives at inference time—**not** neural weights.
   - **Retrieval-Based Memory**: Memories are stored in SQLite and injected into the context window—**not** embedded into neural weights.
3. **Hardware Agnostic**: Supports local CPU or CUDA GPU execution. No reliance on proprietary cloud LLM APIs.
4. **Safety & Allowlist Protocol**: Language model outputs conform to a strict Pydantic allowlist schema. Arbitrary code execution is strictly prohibited.
5. **Simulated Hardware Layer**: Camera, distance, gestures, and person detection are transparently labeled as software simulations until physical hardware drivers are connected.

---

## 🏗️ Architecture Overview

```text
                               +------------------------------------+
                               |       WITHME USER INTERFACES       |
                               |  - AI Training Studio (11 Modules) |
                               |  - Companion Robot Interface (SVG) |
                               +------------------------------------+
                                                 |
                                         REST / WebSocket
                                                 v
+---------------------------------------------------------------------------------------------------+
|                                       FASTAPI BACKEND CORE                                        |
|                                                                                                   |
|  +---------------------+   +---------------------+   +--------------------+   +----------------+  |
|  |   TRAINING ENGINE   |   |  INFERENCE ENGINE   |   |   MEMORY SERVICE   |   | ROBOT SERVICE  |  |
|  | - PyTorch LM        |   | - Tokenizer Encode  |   | - SQLite withme.db |   | - Action Schema|  |
|  | - AdamW / Loss Step |   | - Autoregressive Gen|   | - Explicit CRUD    |   | - Allowlist    |  |
|  | - Async Thread      |   | - Hybrid Fallback   |   | - Turn History     |   | - Sim Sensors  |  |
|  +---------------------+   +---------------------+   +--------------------+   +----------------+  |
|             |                         |                         |                     |           |
|             v                         v                         v                     v           |
|  +---------------------+   +---------------------+   +--------------------+   +----------------+  |
|  |   DATASET MANAGER   |   |   MODEL REGISTRY    |   | PERSONALITY ENGINE |   | EVALUATION LAB |  |
|  | - Multi-turn JSONL  |   | - Local Checkpoints |   | - 5 Preset Profiles|   | - 5 Test Suites|  |
|  | - Conversation Split|   | - Checkpoint Loader |   | - Custom Sliders   |   | - Latency & Q  |  |
+---------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
                               +------------------------------------+
                               |     LOCAL STORAGE (withme-data/)   |
                               |  checkpoints/  datasets/  database/|
                               +------------------------------------+
```

---

## 📂 Repository Directory Layout

| Directory / File | Description |
| :--- | :--- |
| `backend/` | FastAPI server, PyTorch neural networks, training engine, memory service, and endpoints. |
| `backend/core/model.py` | PyTorch causal Transformer architecture (`WithMeTransformerLM`) with Positional Encoding and Self-Attention. |
| `backend/core/tokenizer.py` | Custom vocabulary builder and token encoder/decoder for conversational tokens. |
| `backend/core/training.py` | Asynchronous training worker loop with AdamW optimizer, step metrics, and validation loss. |
| `backend/core/memory_service.py`| SQLite CRUD and lexical context retrieval for user-approved memories. |
| `backend/core/robot_service.py` | Robot action validation schema, allowlist validator, and simulated sensor events. |
| `backend/tests/` | Automated unit tests and end-to-end API integration tests. |
| `src/components/training-studio/`| React components for the 11-module AI Training Studio. |
| `src/engine/aiCoreClient.js` | REST client connecting React to FastAPI endpoints. |
| `withme-data/` | Local directory for datasets, model checkpoints, evaluations, logs, and `withme.db`. |
| `TECHNICAL_ARCHITECTURE.md` | Formal ML and robotics architecture documentation. |

---

## ⚙️ Prerequisites & System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux (Ubuntu 20.04+).
- **Python**: Version 3.10, 3.11, or 3.12 (with `pip`).
- **Node.js**: Version 18.x or 20.x (with `npm`).
- **RAM**: Minimum 4 GB (8 GB+ recommended).
- **Compute**: CPU works out-of-the-box; CUDA GPU is automatically detected if available.

---

## 🚀 Quickstart & Setup Guide

### 1. Backend Setup

#### On Windows (PowerShell):
```powershell
# Navigate to the project root
cd C:\Users\shagu\.antigravity\withme-app

# (Optional) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required Python dependencies
pip install fastapi uvicorn pydantic torch requests

# Launch the FastAPI backend server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### On Linux / macOS (Bash):
```bash
# Navigate to the project root
cd withme-app

# (Optional) Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required Python dependencies
pip install fastapi uvicorn pydantic torch requests

# Launch the FastAPI backend server
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be live at: `http://127.0.0.1:8000`  
Swagger / OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup

In a separate terminal:

#### On Windows (PowerShell) / Linux / macOS:
```bash
# In withme-app directory
npm install
npm run dev
```

The React Application will be live at: `http://localhost:5173/`

Click the **AI Training Studio 🧠** tab in the navigation bar to enter the machine learning platform.

---

## 🧪 Conversational Dataset Format

Datasets are stored in JSONL format, grouping multi-turn dialogues by conversation to prevent split leakage between training and validation:

```json
{
  "conversation_id": "emo_support_001",
  "category": "emotional_support",
  "messages": [
    {"role": "user", "content": "I had a really exhausting day today."},
    {"role": "assistant", "content": "I hear you. Take a deep breath. Want to vent about it?"}
  ],
  "robot_state": "attentive"
}
```

Import or create datasets under **Studio > Dataset Studio**. The validation engine checks structure, detects duplicates, removes empty messages, and performs conversation-level train/validation splitting.

---

## 🔬 How to Train a Model from Scratch

1. **Open AI Training Studio**: Navigate to `http://localhost:5173/` and select **AI Training Studio**.
2. **Initialize Model (Model Lab)**:
   - Configure parameters (e.g., Embedding Dim: 64, Layers: 3, Heads: 2, Max Seq: 128).
   - Click **Initialize Experimental Transformer**.
   - Note: Weights are initialized randomly ($\mathcal{N}(0, 0.02)$).
3. **Launch Training (Training Center)**:
   - Select your prepared dataset (e.g., `synthetic_demo_v1`).
   - Configure epochs (e.g., `5`), batch size (`4`), learning rate (`0.001`).
   - Click **Start Training Job**.
4. **Monitor Live Training**:
   - The interactive SVG training curve tracks **Training Loss** and **Validation Loss** in real-time.
   - At the end of training, a model checkpoint (`checkpoint_final.pt`), `tokenizer.json`, and `model_config.json` are saved to disk under `withme-data/checkpoints/`.
5. **Alternatively, run headlessly via CLI**:
```powershell
python backend/train_demo_model.py
```

---

## 💬 Using the Live Playground

1. Go to **Studio > Model Registry** and click **Load Model** on your saved checkpoint.
2. Open **Studio > Live Playground**.
3. Send a message:
   - The Playground displays the active model source (`Local PyTorch Checkpoint` vs. `Hybrid Companion Fallback`).
   - Generation metrics report actual **latency (ms)** and **tokens/second**.
   - The connected virtual robot avatar transitions between `listening` $\to$ `thinking` $\to$ `speaking` $\to$ target emotion (e.g., `express_happy`).

---

## 🧠 Memory Vault & Context Retention

1. Navigate to **Studio > Memory Lab**.
2. Add a user-approved memory (e.g., *"User prefers calm music when studying"*).
3. In subsequent conversations, the backend retrieves relevant memories via lexical matching and injects them into the prompt context window.
4. **Transparency**: The model does not alter its neural weights when storing memories. Memory is retrieved and placed into the inference prompt.

---

## 🤖 Virtual Robot Simulator & Sensor Triggers

1. Navigate to **Studio > Robot Integration**.
2. Trigger simulated hardware events:
   - **Simulate Person Detected (Left / Right)** $\to$ Robot selects `look_left` or `look_right`.
   - **Simulate Petting Gesture** $\to$ Robot selects `express_happy` with chimes.
   - **Simulate Inactivity Timeout** $\to$ Robot selects `sleep` mode.
3. Every action is validated against the strict allowlist schema before dispatching to the virtual robot.

---

## 📚 Comprehensive Documentation Suite

WithMe includes an in-depth documentation suite located in [`docs/`](file:///c:/Users/shagu/.antigravity/withme-app/docs):

1. [`PROJECT_STATUS.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/PROJECT_STATUS.md) — Complete codebase audit and 7-phase verification status.
2. [`DATA_PIPELINE.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/DATA_PIPELINE.md) — Multi-format ingestion, 3-way split, credential filtering, CLI usage.
3. [`MODEL_ARCHITECTURE.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/MODEL_ARCHITECTURE.md) — Mathematical formulation of Causal Transformer, attention, and LoRA.
4. [`TRAINING_GUIDE.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/TRAINING_GUIDE.md) — Windows CPU presets, warmup schedules, clipping, and resumption.
5. [`EVALUATION_GUIDE.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/EVALUATION_GUIDE.md) — 9-category benchmark test suites, perplexity, and experiment comparison.
6. [`FINETUNING_AND_LORA.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/FINETUNING_AND_LORA.md) — Open-weight model catalog and low-rank parameter adaptation.
7. [`MEMORY_AND_PRIVACY.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/MEMORY_AND_PRIVACY.md) — SQLite memory vault, right to erasure, and safety boundary engines.
8. [`API_REFERENCE.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/API_REFERENCE.md) — 25+ REST endpoints with request/response schemas.
9. [`ROBOT_INTEGRATION.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/ROBOT_INTEGRATION.md) — Action allowlist, emergency stop protocol, voice/vision contracts.
10. [`TROUBLESHOOTING.md`](file:///c:/Users/shagu/.antigravity/withme-app/docs/TROUBLESHOOTING.md) — Windows SQLite locks, CPU performance, port conflicts, and common fixes.

---

## 🛠️ Automated Test Suites (100% Passing)

Run the full automated test suite (all phases) locally on CPU:

```powershell
# Phase 1: Conversational Data Pipeline
python backend/tests/test_dataset_pipeline.py

# Phase 2: Tokenizer, Transformer Model & Training
python backend/tests/test_model_and_training.py

# Phase 3: Evaluation Engine & Experiment Tracking
python backend/tests/test_evaluation.py

# Phase 4: Pretrained Catalog & LoRA Engine
python backend/tests/test_finetuning_pipeline.py

# Phase 5: Memory Vault, Privacy & Safety Engine
python backend/tests/test_memory_and_privacy.py

# Phase 6: FastAPI Endpoints Integration
python backend/tests/test_api_endpoints.py

# Phase 7: Robot Interaction Layer & Emergency Stop
python backend/tests/test_robot_integration.py

# Baseline Core Smoke Tests (Backward Compatibility)
python backend/tests/test_all.py
```

---

## 🛡️ Privacy & Crisis Safety Disclosures

- **Not a Medical Device**: WithMe is an emotional wellness and entertainment prototype, not a certified therapist or crisis intervention tool.
- **Safety Protocol**: Crisis-related keywords trigger supportive safety redirects with local helpline resources.
- **Local Data Sovereignty**: All conversations, datasets, and memories remain strictly on the local machine (`withme-data/`). No private user dialogue is sent to third-party commercial LLMs or automatically ingested into training data without explicit user consent.

---

## 📜 License & Acknowledgements

Created as part of the WithMe AI Companion Research Initiative. Designed with a transparent, local-first ML architecture.

