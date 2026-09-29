"""
WithMe AI Core - Real Asynchronous PyTorch Training Engine
Executes genuine Causal LM teacher-forced training, tracks real loss curves,
computes validation loss, handles AdamW optimization, learning rate scheduling,
early stopping, checkpoint resumption, and safe CPU resource bounds.
"""

import time
import math
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import torch
from torch.utils.data import Dataset, DataLoader

from backend.config import CHECKPOINTS_DIR, EXPERIMENTAL_MODELS_DIR
from backend.core.model import WithMeTransformerLM
from backend.core.tokenizer import BaseWithMeTokenizer, PAD_TOKEN_ID, EOS_TOKEN_ID


class ConversationDataset(Dataset):
    """PyTorch Dataset for conversational token sequences."""

    def __init__(self, conversations: List[Dict[str, Any]], tokenizer: BaseWithMeTokenizer, max_seq_len: int = 128):
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.examples = []

        for conv in conversations:
            messages = conv.get("messages", [])
            formatted_text = tokenizer.format_conversation(messages)
            token_ids = tokenizer.encode(formatted_text, add_special_tokens=True)

            if len(token_ids) < 3:
                continue

            if len(token_ids) > max_seq_len:
                token_ids = token_ids[:max_seq_len]

            self.examples.append(token_ids)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ids = self.examples[idx]
        seq_len = len(ids)

        padded = ids + [PAD_TOKEN_ID] * (self.max_seq_len - seq_len)
        input_ids = torch.tensor(padded[:-1], dtype=torch.long)
        target_ids = torch.tensor(padded[1:], dtype=torch.long)
        target_ids[target_ids == PAD_TOKEN_ID] = PAD_TOKEN_ID

        return {
            "input_ids": input_ids,
            "target_ids": target_ids,
            "seq_len": seq_len
        }


class LinearWarmupCosineScheduler:
    """Linear warmup followed by cosine annealing learning rate scheduler."""

    def __init__(self, optimizer: torch.optim.Optimizer, warmup_steps: int, total_steps: int, base_lr: float, min_lr: float = 1e-6):
        self.optimizer = optimizer
        self.warmup_steps = max(1, warmup_steps)
        self.total_steps = max(self.warmup_steps + 1, total_steps)
        self.base_lr = base_lr
        self.min_lr = min_lr

    def step(self, current_step: int) -> float:
        if current_step < self.warmup_steps:
            # Linear warmup
            lr = self.base_lr * (current_step + 1) / self.warmup_steps
        else:
            # Cosine decay
            progress = (current_step - self.warmup_steps) / max(1, (self.total_steps - self.warmup_steps))
            progress = min(1.0, max(0.0, progress))
            lr = self.min_lr + 0.5 * (self.base_lr - self.min_lr) * (1.0 + math.cos(math.pi * progress))

        for param_group in self.optimizer.param_groups:
            param_group["lr"] = lr
        return lr


class TrainingJob:
    """Manages an active or historical training job."""

    def __init__(
        self,
        job_id: str,
        model_name: str,
        config: Dict[str, Any],
        train_conversations: List[Dict[str, Any]],
        val_conversations: List[Dict[str, Any]],
        tokenizer: BaseWithMeTokenizer,
        resume_from: Optional[str] = None
    ):
        self.job_id = job_id
        self.model_name = model_name
        self.config = config
        self.train_conversations = train_conversations
        self.val_conversations = val_conversations
        self.tokenizer = tokenizer
        self.resume_from = resume_from

        # Status: 'idle' | 'running' | 'paused' | 'stopped' | 'completed' | 'failed'
        self.status = "idle"
        self.current_epoch = 0
        self.total_epochs = config.get("epochs", 5)
        self.current_step = 0
        self.total_steps = 0
        self.latest_train_loss: Optional[float] = None
        self.latest_val_loss: Optional[float] = None
        self.best_val_loss: float = float("inf")
        self.learning_rate: float = config.get("learning_rate", 3e-4)

        # Early stopping configuration
        self.early_stopping_patience = config.get("early_stopping_patience", 3)
        self.patience_counter = 0

        # Metrics history
        self.loss_history: List[Dict[str, Any]] = []
        self.val_history: List[Dict[str, Any]] = []
        self.logs: List[str] = []
        self.start_time: Optional[float] = None
        self.elapsed_seconds: float = 0.0
        self.error_message: Optional[str] = None
        self.latest_checkpoint_path: Optional[str] = None
        self.best_checkpoint_path: Optional[str] = None

        # Control flags
        self._stop_requested = False
        self._thread: Optional[threading.Thread] = None

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def to_dict(self) -> Dict[str, Any]:
        elapsed = self.elapsed_seconds
        if self.status == "running" and self.start_time:
            elapsed = time.time() - self.start_time

        return {
            "job_id": self.job_id,
            "model_name": self.model_name,
            "status": self.status,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "latest_train_loss": round(self.latest_train_loss, 4) if self.latest_train_loss is not None else None,
            "latest_val_loss": round(self.latest_val_loss, 4) if self.latest_val_loss is not None else None,
            "best_val_loss": round(self.best_val_loss, 4) if self.best_val_loss != float("inf") else None,
            "learning_rate": self.learning_rate,
            "elapsed_seconds": round(elapsed, 1),
            "loss_history": self.loss_history[-100:],
            "val_history": self.val_history,
            "logs": self.logs[-50:],
            "latest_checkpoint_path": self.latest_checkpoint_path,
            "best_checkpoint_path": self.best_checkpoint_path,
            "error_message": self.error_message,
            "config": self.config
        }

    def start(self):
        if self.status == "running":
            return
        self.status = "running"
        self._stop_requested = False
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._run_training_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_requested = True
        self.log("Cancellation requested by user. Finalizing checkpoint...")

    def _run_training_loop(self):
        """Worker thread executing PyTorch training with LR scheduler and early stopping."""
        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.log(f"Initializing PyTorch model on compute device: {device}")

            # CPU thread management
            cpu_threads = self.config.get("cpu_threads")
            if cpu_threads and device.type == "cpu":
                torch.set_num_threads(max(1, int(cpu_threads)))
                self.log(f"Configured CPU execution to {cpu_threads} thread(s).")

            # Deterministic seed if configured
            seed = self.config.get("seed", 42)
            torch.manual_seed(seed)

            # Instantiate model
            model = WithMeTransformerLM(
                vocab_size=self.tokenizer.vocab_size,
                d_model=self.config.get("d_model", 128),
                n_layers=self.config.get("n_layers", 4),
                n_heads=self.config.get("n_heads", 4),
                ffn_dim=self.config.get("ffn_dim", 256),
                max_seq_len=self.config.get("max_seq_len", 128),
                dropout=self.config.get("dropout", 0.1),
                pad_token_id=PAD_TOKEN_ID
            ).to(device)

            param_count = model.count_parameters()
            self.log(f"Model initialized: {param_count:,} trainable parameters.")

            # Create Datasets & DataLoaders
            batch_size = max(1, self.config.get("batch_size", 4))
            train_dataset = ConversationDataset(
                self.train_conversations,
                self.tokenizer,
                max_seq_len=self.config.get("max_seq_len", 128)
            )
            val_dataset = ConversationDataset(
                self.val_conversations,
                self.tokenizer,
                max_seq_len=self.config.get("max_seq_len", 128)
            )

            if len(train_dataset) == 0:
                raise ValueError("Training dataset has 0 valid tokenized sequences.")

            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False) if len(val_dataset) > 0 else None

            self.total_steps = len(train_loader) * self.total_epochs
            self.log(f"Dataset prepared: {len(train_dataset)} train samples, {len(val_dataset)} val samples.")

            # Optimizer (AdamW)
            lr = float(self.config.get("learning_rate", 3e-4))
            weight_decay = float(self.config.get("weight_decay", 0.01))
            optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

            # Learning Rate Scheduler
            warmup_steps = max(1, int(self.total_steps * 0.1))
            scheduler = LinearWarmupCosineScheduler(
                optimizer=optimizer,
                warmup_steps=warmup_steps,
                total_steps=self.total_steps,
                base_lr=lr
            )

            start_epoch = 1
            # Checkpoint Resumption
            if self.resume_from:
                resume_p = Path(self.resume_from)
                if resume_p.exists():
                    self.log(f"Resuming training from checkpoint: {resume_p.name}")
                    ckpt = torch.load(resume_p, map_location=device)
                    model.load_state_dict(ckpt["model_state_dict"])
                    if "optimizer_state_dict" in ckpt:
                        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
                    start_epoch = ckpt.get("epoch", 0) + 1
                    self.current_step = ckpt.get("step", 0)
                    self.log(f"Resumed at Epoch {start_epoch}, Step {self.current_step}.")

            # Training loop across epochs
            for epoch in range(start_epoch, self.total_epochs + 1):
                if self._stop_requested:
                    break

                self.current_epoch = epoch
                model.train()
                epoch_loss_sum = 0.0
                epoch_steps = 0

                for batch in train_loader:
                    if self._stop_requested:
                        break

                    input_ids = batch["input_ids"].to(device)
                    target_ids = batch["target_ids"].to(device)

                    optimizer.zero_grad()
                    _, loss = model(input_ids, targets=target_ids)

                    loss.backward()
                    # Gradient clipping
                    grad_clip = self.config.get("grad_clip", 1.0)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)

                    # Update parameters and schedule LR
                    optimizer.step()
                    current_lr = scheduler.step(self.current_step)
                    self.learning_rate = round(current_lr, 7)

                    loss_val = loss.item()
                    epoch_loss_sum += loss_val
                    epoch_steps += 1
                    self.current_step += 1
                    self.latest_train_loss = loss_val

                    self.loss_history.append({
                        "step": self.current_step,
                        "epoch": epoch,
                        "loss": round(loss_val, 4),
                        "lr": self.learning_rate,
                        "timestamp": time.time()
                    })

                    if self.current_step % max(1, len(train_loader) // 2) == 0:
                        self.log(f"Epoch {epoch}/{self.total_epochs} | Step {self.current_step}/{self.total_steps} | Loss: {loss_val:.4f} | LR: {self.learning_rate:.2e}")

                    time.sleep(0.01)

                avg_train_loss = epoch_loss_sum / max(1, epoch_steps)

                # Validation step
                avg_val_loss = None
                if val_loader:
                    model.eval()
                    val_loss_sum = 0.0
                    val_steps = 0
                    with torch.no_grad():
                        for val_batch in val_loader:
                            v_input = val_batch["input_ids"].to(device)
                            v_target = val_batch["target_ids"].to(device)
                            _, v_loss = model(v_input, targets=v_target)
                            val_loss_sum += v_loss.item()
                            val_steps += 1
                    avg_val_loss = val_loss_sum / max(1, val_steps)
                    self.latest_val_loss = avg_val_loss
                    self.val_history.append({
                        "epoch": epoch,
                        "step": self.current_step,
                        "val_loss": round(avg_val_loss, 4)
                    })

                    # Check for new best validation loss
                    if avg_val_loss < self.best_val_loss:
                        self.best_val_loss = avg_val_loss
                        self.patience_counter = 0
                        best_ckpt = self._save_checkpoint(model, optimizer, epoch, is_best=True)
                        self.best_checkpoint_path = str(best_ckpt)
                        self.log(f"New best validation loss: {avg_val_loss:.4f}! Saved {best_ckpt.name}")
                    else:
                        self.patience_counter += 1
                        self.log(f"Val loss did not improve (patience {self.patience_counter}/{self.early_stopping_patience}).")

                    self.log(f"Epoch {epoch} complete -> Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

                    # Early stopping condition
                    if self.patience_counter >= self.early_stopping_patience:
                        self.log(f"Early stopping triggered after {epoch} epochs (no validation improvement for {self.early_stopping_patience} epochs).")
                        break
                else:
                    self.log(f"Epoch {epoch} complete -> Train Loss: {avg_train_loss:.4f}")

                # Save intermediate periodic checkpoint
                self._save_checkpoint(model, optimizer, epoch, is_final=False)

            # Final checkpoint save
            final_ckpt = self._save_checkpoint(model, optimizer, self.current_epoch, is_final=True)
            self.latest_checkpoint_path = str(final_ckpt)
            self.status = "stopped" if self._stop_requested else "completed"
            self.elapsed_seconds = time.time() - self.start_time
            self.log(f"Training job {self.status.upper()}. Final checkpoint saved at {final_ckpt.name}")

        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            self.log(f"ERROR encountered during training: {e}")

    def _save_checkpoint(
        self,
        model: WithMeTransformerLM,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        is_final: bool = False,
        is_best: bool = False
    ) -> Path:
        """Save model checkpoint, weights, optimizer state, tokenizer, and config metadata to disk."""
        ckpt_dir = CHECKPOINTS_DIR / self.job_id
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        if is_best:
            prefix = "checkpoint_best"
        elif is_final:
            prefix = "checkpoint_final"
        else:
            prefix = f"checkpoint_epoch_{epoch}"

        ckpt_file = ckpt_dir / f"{prefix}.pt"
        config_file = ckpt_dir / "model_config.json"
        tokenizer_file = ckpt_dir / "tokenizer.json"

        torch.save({
            "epoch": epoch,
            "step": self.current_step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "train_loss": self.latest_train_loss,
            "val_loss": self.latest_val_loss,
            "best_val_loss": self.best_val_loss if self.best_val_loss != float("inf") else None,
            "config": model.get_config(),
            "created_at": time.time(),
            "torch_version": torch.__version__,
            "seed": self.config.get("seed", 42)
        }, ckpt_file)

        import json
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({
                "model_id": self.job_id,
                "model_name": self.model_name,
                "development_type": "from_scratch",
                "architecture": "WithMeTransformerLM",
                "param_count": model.count_parameters(),
                "config": model.get_config(),
                "training_config": self.config,
                "latest_train_loss": self.latest_train_loss,
                "latest_val_loss": self.latest_val_loss,
                "best_val_loss": self.best_val_loss if self.best_val_loss != float("inf") else None,
                "total_epochs": epoch,
                "latest_checkpoint": str(ckpt_file),
                "torch_version": torch.__version__
            }, f, indent=2)

        self.tokenizer.save(tokenizer_file)
        self.latest_checkpoint_path = str(ckpt_file)
        return ckpt_file


class TrainingEngine:
    """Singleton coordinator of training jobs."""

    def __init__(self):
        self.jobs: Dict[str, TrainingJob] = {}

    def create_job(
        self,
        model_name: str,
        config: Dict[str, Any],
        train_conversations: List[Dict[str, Any]],
        val_conversations: List[Dict[str, Any]],
        tokenizer: BaseWithMeTokenizer,
        resume_from: Optional[str] = None
    ) -> TrainingJob:
        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:4]}"
        job = TrainingJob(
            job_id=job_id,
            model_name=model_name,
            config=config,
            train_conversations=train_conversations,
            val_conversations=val_conversations,
            tokenizer=tokenizer,
            resume_from=resume_from
        )
        self.jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [job.to_dict() for job in reversed(list(self.jobs.values()))]


training_engine = TrainingEngine()
