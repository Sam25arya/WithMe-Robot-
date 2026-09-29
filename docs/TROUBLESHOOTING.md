# WithMe AI — Troubleshooting Guide (`TROUBLESHOOTING.md`)

This guide outlines common issues encountered when running, training, and testing WithMe AI on Windows and CPU-only environments, along with verified solutions.

---

## 1. Windows SQLite Locking (`sqlite3.OperationalError: database is locked`)

### Symptom
When accessing conversations or memory via the API or during rapid test suites on Windows, SQLite throws:
```
sqlite3.OperationalError: database is locked
```

### Cause
On Windows NTFS filesystems, open file handles held by any lingering connection block subsequent processes or threads from acquiring write locks.

### Resolution
WithMe enforces context-managed connection lifecycles in `backend/core/memory_service.py` and `backend/core/conversation_manager.py`:
```python
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        yield conn
    finally:
        conn.close()
```
Always use `with get_db() as conn:` rather than retaining persistent database connection handles across requests.

---

## 2. Port Conflicts (8000 for FastAPI or 5173 for Vite)

### Symptom
FastAPI fails to start: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`.

### Resolution
Check for lingering background Python or Node processes on Windows using PowerShell:
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```
Alternatively, launch FastAPI on an alternate port:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

---

## 3. CPU Training Performance & Thread Contention

### Symptom
CPU usage hits 100% on all cores or thermal throttling causes training iterations to slow down significantly.

### Cause
PyTorch's default behavior on multi-core Windows systems is to spawn threads equal to logical CPU cores, causing thread contention and context-switching overhead on lightweight transformer models.

### Resolution
WithMe automatically bounds CPU threads in `backend/core/training.py`:
```python
import os, torch
threads = min(4, os.cpu_count() or 1)
torch.set_num_threads(threads)
```
You can also select the `cpu_smoke_test` preset in `ModelConfig` for instant verification:
- `cpu_smoke_test`: `d_model=64`, `n_layers=2`, `n_heads=2`, `max_seq_len=64` (~100k parameters).
- `cpu_standard`: `d_model=128`, `n_layers=4`, `n_heads=4`, `max_seq_len=128` (~500k parameters).

---

## 4. Vocabulary Size Mismatch on Checkpoint Resumption

### Symptom
When resuming training from a saved checkpoint, PyTorch throws:
```
RuntimeError: Error(s) in loading state_dict for WithMeTransformerLM:
size mismatch for token_embedding.weight: copying a param with shape torch.Size([X, 64]) from checkpoint, the shape in current model is torch.Size([Y, 64]).
```

### Cause
The tokenizer was retrained or re-initialized with a different corpus, producing a different vocabulary size than the model checkpoint was configured for.

### Resolution
WithMe provides `check_tokenizer_compatibility(tokenizer, checkpoint_vocab_size)` in `backend/core/tokenizer.py`. Always ensure that the saved checkpoint's `vocab_size` stored in its metadata matches the tokenizer loaded into the training job.

---

## 5. Dropout Randomness During Checkpoint Comparison

### Symptom
In evaluation or unit tests, comparing outputs of the same checkpoint before and after reloading yields slightly different logits.

### Cause
The model remains in training mode (`model.train()`), meaning dropout masks randomly zero out activations on each forward pass.

### Resolution
Always call `model.eval()` and wrap inference in `with torch.no_grad():` before running evaluations, benchmarks, or deterministic comparison tests.

---

## 6. Dataset Format Validation Errors

### Symptom
`dataset_manager.validate_and_normalize()` rejects turns with `Invalid role` or `Missing turn content`.

### Expected Format
WithMe expects multi-turn conversational JSON matching:
```json
{
  "conversations": [
    {
      "id": "conv_001",
      "turns": [
        {"role": "user", "content": "I feel anxious today."},
        {"role": "assistant", "content": "I hear you. Take a slow breath with me."}
      ]
    }
  ]
}
```
Validation rules:
1. `turns` must alternate starting with `user`.
2. Every conversation must contain at least one `assistant` turn.
3. Length must be within 2 to 2,000 characters.
4. Content must not match credential/token patterns (API keys, passwords, bearer tokens).

---

## 7. Emergency Stop Reset in Robot Lab

### Symptom
The avatar or robot stops responding to action requests and reports `status: rejected` with `Emergency stop is active`.

### Resolution
Call the reset endpoint or reset button:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/robot/action" -Method Post -ContentType "application/json" -Body '{"action":"idle"}'
```
Or execute in Python:
```python
from backend.core.robot_adapters import simulation_adapter
simulation_adapter.reset_emergency_stop()
```
