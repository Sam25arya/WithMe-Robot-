# WithMe AI Core — Training & Checkpoint Guide (Phase 2)

> **Key Distinction**: *"Training loss is a mathematical measure of next-token prediction error on the training corpus. It does NOT guarantee human-level conversation or emotional intelligence."*

---

## 1. Teacher-Forced Causal Training Mechanics

WithMe uses teacher-forced next-token prediction:
1. An input sequence of length $T$ (e.g. `[<user>, How, are, you, ?, <assistant>, I, am]`) is fed to the Transformer.
2. The target sequence is shifted forward by 1 token: `[How, are, you, ?, <assistant>, I, am, <eos>]`.
3. The model computes logits for each token position simultaneously in parallel.
4. Loss is calculated using Cross-Entropy Loss:
   $$\mathcal{L} = -\frac{1}{T-1} \sum_{t=1}^{T-1} \log P(x_{t+1} \mid x_1, \dots, x_t)$$
   Padding tokens (`<pad>`) are masked with `ignore_index = 0`.
5. Backpropagation computes gradients $\nabla_\theta \mathcal{L}$ across all Transformer layers.
6. Gradients are clipped to `max_norm = 1.0` via `torch.nn.utils.clip_grad_norm_` to prevent exploding gradients.
7. Optimizer updates model parameters using AdamW:
   $$\theta_{t+1} = \theta_t - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} - \eta \lambda \theta_t$$

---

## 2. Learning Rate Scheduling

WithMe implements `LinearWarmupCosineScheduler`:
- **Warmup Phase (First 10% of total steps)**: Learning rate scales linearly from $0 \to \eta_{\text{base}}$. This prevents unstable early weight shock when weights are freshly initialized.
- **Cosine Decay Phase (Remaining 90% of steps)**: Learning rate decays smoothly following a half-cosine curve down to `min_lr = 1e-6`.

```text
Learning Rate
     ▲
base ┼          /‾‾\
     │         /    \
     │        /      \
     │       /        \
     │      /          \___
     │     /               \___
min  ┼────/────────────────────\────► Step
     0   Warmup             Total
```

---

## 3. Early Stopping & Best Checkpoint Tracking

To avoid overfitting to small training sets:
- At the end of each epoch, the model evaluates on the held-out validation set without gradients (`torch.no_grad()`).
- If validation loss reaches a new minimum, a dedicated `checkpoint_best.pt` is saved.
- If validation loss fails to improve for `patience` consecutive epochs (default: 3 epochs), training terminates early.

---

## 4. Checkpoint Anatomy & Format

Every checkpoint is saved to `withme-data/checkpoints/job_<timestamp>/`:

| File | Purpose |
| :--- | :--- |
| `checkpoint_final.pt` | PyTorch binary state dictionary containing model weights, optimizer state, epoch, step, loss, seed, and PyTorch version. |
| `checkpoint_best.pt` | Saved state dictionary at the exact epoch with minimum measured validation loss. |
| `model_config.json` | JSON metadata recording architecture parameters, training hyperparameters, and parameter count. |
| `tokenizer.json` | Tokenizer vocabulary and special token mappings required to load and run inference on this checkpoint. |

---

## 5. Resuming Training from a Checkpoint

To resume training without losing optimizer momentum or learning rate progress:

```python
from backend.core.training import training_engine
from backend.core.tokenizer import WithMeTokenizer

tokenizer = WithMeTokenizer.load("withme-data/checkpoints/job_xxx/tokenizer.json")

job = training_engine.create_job(
    model_name="Resumed Model",
    config={"epochs": 10, "learning_rate": 1e-4, "cpu_threads": 4},
    train_conversations=train_data,
    val_conversations=val_data,
    tokenizer=tokenizer,
    resume_from="withme-data/checkpoints/job_xxx/checkpoint_final.pt"
)
job.start()
```

---

## 6. CPU Resource Bounds on Windows Laptops

To prevent training from locking the user's computer:
- Set `cpu_threads` in config (e.g. `torch.set_num_threads(4)`).
- Yield GIL between batches via micro-sleep (`time.sleep(0.01)`) to maintain responsive UI polling.
- Always use small sequence lengths (`max_seq_len <= 128`) on CPU.
