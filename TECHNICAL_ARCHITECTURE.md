# WithMe AI Core — Technical Architecture & Machine Learning Foundations

> **Philosophy**: *"WithMe doesn't just answer you. It stays with you."*

This document provides a formal engineering specification of WithMe's proprietary AI system, training mechanics, conversational memory, hardware simulation layer, and the technical distinctions between machine learning paradigms.

---

## 1. System Architecture Overview

```text
+-------------------------------------------------------------------------------+
|                       WITHME USER INTERFACES                                 |
|   +------------------------------------+  +--------------------------------+  |
|   |   WithMe AI Training Studio        |  |  WithMe Robot Companion View   |  |
|   |   (11 R&D ML Engineering Modules)  |  |  (Interactive Avatar & Stage)  |  |
|   +------------------------------------+  +--------------------------------+  |
+-------------------------------------------------------------------------------+
                                    |
                            HTTP / REST / WS
                                    v
+-------------------------------------------------------------------------------+
|                          FASTAPI BACKEND CORE                                 |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                           ROUTING LAYER                               |   |
|   |   /models  |  /datasets  |  /training  |  /chat  |  /robot  |  /memory  |   |
|   +-----------------------------------------------------------------------+   |
|                                    |                                          |
|         +--------------------------+--------------------------+               |
|         v                          v                          v               |
|   +-------------------+      +-------------------+      +-----------------+   |
|   |  TRAINING ENGINE  |      | INFERENCE ENGINE  |      | MEMORY SERVICE  |   |
|   |  - PyTorch Causal |      | - Autoregressive  |      | - SQLite DB     |   |
|   |  - Teacher-Forced |      | - Latency & Tokens|      | - Explicit CRUD |   |
|   |  - AdamW Optimizer|      | - Hybrid Fallback |      | - Context Search|   |
|   |  - Checkpoints    |      | - Robot Intent    |      +-----------------+   |
|   +-------------------+      +-------------------+              |             |
|         |                          |                            |             |
|         v                          v                            v             |
|   +-------------------+      +-------------------+      +-----------------+   |
|   | DATASET MANAGER   |      | ROBOT SERVICE     |      | PERSONALITY     |   |
|   | - JSONL / CSV / TX|      | - Action Allowlist|      | - 5 Presets     |   |
|   | - Turn Leak Split |      | - Sensor Sim Layer|      | - Custom Sliders|   |
|   | - Normalizer      |      | - Hardware Status |      | - Context Prompt|   |
|   +-------------------+      +-------------------+      +-----------------+   |
+-------------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                         STORAGE DIRECTORY STRUCTURE                           |
|   withme-data/                                                                |
|     ├── datasets/ (raw / processed)                                           |
|     ├── models/ (experimental / pretrained / finetuned / adapters)            |
|     ├── checkpoints/ (PyTorch .pt weights, tokenizer.json, model_config.json) |
|     ├── evaluations/ (benchmark reports)                                     |
|     ├── database/ (withme.db SQLite storage)                                  |
|     └── logs/ (training and telemetry logs)                                   |
+-------------------------------------------------------------------------------+
```

---

## 2. Essential Machine Learning Concepts Explained

### A. Pretraining from Random Initialization (From-Scratch)
- **Mechanism**: The neural network's weight matrices ($W_q, W_k, W_v, W_o, W_1, W_2$) are initialized randomly (using normal distribution with mean 0.0 and standard deviation 0.02). At step 0, the model has zero knowledge of language, producing random token probabilities.
- **Training Objective**: Standard Causal Language Modeling (CLM) using teacher forcing. For a sequence of tokens $x_1, x_2, \dots, x_T$, the model computes logits for each position to predict $x_{t+1}$ given $x_1, \dots, x_t$.
- **Loss Function**: Shifted Cross-Entropy Loss:
  $$\mathcal{L} = -\frac{1}{T-1} \sum_{t=1}^{T-1} \log P(x_{t+1} \mid x_1, \dots, x_t; \theta)$$
- **Backpropagation & Update**: Gradients $\nabla_\theta \mathcal{L}$ are calculated through automatic differentiation and parameters are updated via AdamW:
  $$\theta_{t+1} = \theta_t - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} - \eta \cdot \lambda \theta_t$$
- **Hardware Profile**: For our small experimental model (122,688 parameters, embedding dimension 64, 3 layers, 2 heads), CPU training requires $< 200\text{ MB}$ RAM and executes in seconds.

### B. Pretrained Models vs. Fine-Tuning
- **Pretrained Models**: A model trained on billions of tokens (e.g. Llama, Mistral, Gemma). The weights already capture grammar, world facts, and language patterns.
- **Full Fine-Tuning**: Continuing gradient updates on all layers of a pretrained model using domain-specific conversational pairs.
- **LoRA (Low-Rank Adaptation)**: Rather than updating full weight matrix $W \in \mathbb{R}^{d \times k}$, LoRA decomposes the weight update into two low-rank matrices $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$ where $r \ll \min(d, k)$:
  $$W' = W + \Delta W = W + \frac{\alpha}{r} (B \cdot A)$$
  The base model weights $W$ remain frozen, reducing memory overhead and allowing modular adapter swapping.

### C. Inference vs. Weight Updates
- **Inference**: Computing the forward pass through frozen weights with `torch.no_grad()`. No gradients are stored; no parameters are altered.
- **Weight Updates**: Gradients are computed via backpropagation and subtracted via an optimizer. Weight updates only happen during active training runs.

### D. Prompt Engineering & In-Context Learning
- Modifying the prompt text (e.g. system instructions, warmth guidelines) changes the input tokens passed into the model during inference.
- **Crucial Transparency Distinction**: Sliding a personality slider (e.g. Warmth = 0.9) in WithMe's Personality Studio modifies the runtime system directive and temperature. **It does NOT retrain or alter the model's neural weights.**

### E. Retrieval-Based Memory vs. Neural Memory
- In WithMe, user memories are stored in an explicit **SQLite database** (`withme.db`).
- During inference, relevant memories are retrieved via lexical matching and prepended to the context window.
- The model does not "remember" the user through synaptic weight modification; it reads the retrieved memory from the available prompt context.

---

## 3. Robot Action Allowlist & Safety Schema

The language model never executes raw hardware instructions. Instead, outputs must adhere to a strict allowlist schema:

```json
{
  "response": "Hello friend! Great to see you today.",
  "emotion": "happy",
  "robot_action": "greet",
  "action_parameters": {},
  "interaction_state": "speaking"
}
```

### Permitted Actions:
- `idle`: Neutral resting state
- `listen`: Tilt head forward and glow visor
- `look_left`: Turn gaze toward left field
- `look_right`: Turn gaze toward right field
- `look_center`: Re-center gaze
- `nod`: Double nod gesture
- `wave`: Raise arm stub and wave
- `greet`: Wave arm stub and chime happy double boop
- `express_happy`: Curved happy eyes with gentle bounce
- `express_sad`: Calming blue pulse with drooped eyes
- `express_curiosity`: Head tilt with question mark flicker
- `express_excited`: Star eyes with sparkle particle FX
- `sleep`: Dim visor and display Zzz particles

---

## 4. Hardware Simulation Layer Disclosures

All physical robot telemetry, camera tracking, microphone array sensing, distance sensors, and person detection are **simulated in software** unless explicit hardware drivers are attached. The UI clearly labels all sensor triggers as `[SIMULATED SENSOR EVENT]`.
