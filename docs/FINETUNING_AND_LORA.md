# WithMe AI Core — Pretrained Model Fine-Tuning & LoRA Specification (Phase 4)

> **Mandatory Transparency Rule**: *"Never misrepresent fine-tuning as training a foundation model from scratch. Never pretend a pretrained model has been fine-tuned if training did not occur."*

---

## 1. Two Distinct Model Pathways

WithMe AI enforces strict separation between three model paradigms:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WITHME MODEL REGISTRY                               │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ PATH A: From-Scratch Model    │ PATH B: Pretrained Model Fine-Tuning        │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ • Random weight initialization│ • Open-weight base model (e.g. Qwen, Llama) │
│ • Small Transformer (45K-2.5M)│ • Billions of pre-existing trained weights  │
│ • Local CPU training in < 60s │ • Low-Rank Adaptation (LoRA) adapter layers │
│ • Custom WithMe Tokenizer     │ • Compatible Pretrained Tokenizer           │
│ • Educational & Architectural │ • Practical Companion Intelligence          │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

The system will **never** silently switch between these pathways. The active pathway is prominently displayed in the Model Registry, Playground, and API metadata.

---

## 2. Hardware-Aware Model Selection

Before any model download or fine-tuning process is initialized, WithMe performs automated hardware and storage safety checks:

```python
from backend.core.finetuning import check_hardware_compatibility_for_model

compat = check_hardware_compatibility_for_model("Qwen/Qwen2.5-0.5B-Instruct")
print(compat["is_safe_to_proceed"])
print(compat["recommendation_summary"])
```

### Approved Pretrained Catalog:

| Model Identifier | Parameter Count | License | Weights Download | Minimum RAM (Inference) | Minimum RAM (LoRA Training) | Recommended Compute |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `Qwen/Qwen2.5-0.5B-Instruct` | 0.49B | Apache 2.0 | ~1.0 GB | 2.5 GB | 6.0 GB | Local CPU / CUDA GPU |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1.10B | Apache 2.0 | ~2.2 GB | 4.5 GB | 10.0 GB | Local CPU / CUDA GPU |
| `google/gemma-2-2b-it` | 2.60B | Gemma Terms | ~5.2 GB | 8.0 GB | 16.0 GB | Dedicated GPU / Cloud |

---

## 3. Low-Rank Adaptation (LoRA) Architecture

Rather than performing full fine-tuning on billions of base parameters, WithMe utilizes **Low-Rank Adaptation (LoRA)**:

$$h = x W_0^T + \Delta W x = x W_0^T + \frac{\alpha}{r} x A^T B^T$$

where:
- $W_0 \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$ is the frozen base model weight matrix (`requires_grad = False`).
- $A \in \mathbb{R}^{r \times d_{\text{in}}}$ is initialized with Gaussian noise $\mathcal{N}(0, \sigma^2)$.
- $B \in \mathbb{R}^{d_{\text{out}} \times r}$ is initialized to zero ($B = 0$).
- $r$ is the adaptation rank ($r \ll \min(d_{\text{in}}, d_{\text{out}})$, typically $r = 4$ or $8$).
- $\alpha$ is a constant scaling hyperparameter (typically $\alpha = 2r = 16$).

### Advantages for WithMe:
1. **Zero Base Weight Mutation**: Base foundation model weights remain immutable and shared across users.
2. **Minimal Memory Overhead**: Trainable parameter count is reduced by over $99.5\%$, enabling parameter updates without consuming gigabytes of optimizer state.
3. **Modular Adapter Swapping**: LoRA adapter weights (`adapter_model.pt` + `adapter_config.json`, ~10-25 MB) can be loaded and swapped dynamically for specific companion personalities or tasks.

---

## 4. Cloud GPU Fine-Tuning Execution

For models exceeding local CPU capabilities ($> 1\text{B}$ parameters), WithMe generates copy-paste ready scripts for external GPU environments (Google Colab T4, RunPod, Lambda Labs):

```python
from backend.core.finetuning import generate_cloud_gpu_training_script

script = generate_cloud_gpu_training_script("Qwen/Qwen2.5-0.5B-Instruct")
with open("cloud_train.py", "w") as f:
    f.write(script)
```

Trained adapter weights can then be placed into `withme-data/models/adapters/` and registered locally in the Model Registry.
