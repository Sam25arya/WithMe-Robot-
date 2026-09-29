"""
WithMe AI Core - FastAPI Main Application Server (Phase 6)
Full REST API for WithMe AI Training Studio, Model Registry, Dataset Studio,
Evaluation Lab, Memory Vault, Multi-Session Conversation Manager, and Robot Companion.
"""

import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import RAW_DATASETS_DIR, MANIFESTS_DIR, get_hardware_info
from backend.core.tokenizer import WithMeTokenizer
from backend.core.dataset_manager import dataset_manager
from backend.core.model_registry import model_registry
from backend.core.training import training_engine
from backend.core.inference import inference_engine
from backend.core.memory_service import memory_service
from backend.core.personality_engine import personality_engine
from backend.core.conversation_manager import conversation_manager
from backend.core.safety_engine import safety_engine
from backend.core.robot_service import robot_service, RobotActionPayload
from backend.core.evaluation_engine import evaluation_engine
from backend.core.finetuning import (
    PRETRAINED_MODEL_CATALOG,
    check_hardware_compatibility_for_model,
    generate_cloud_gpu_training_script
)

app = FastAPI(
    title="WithMe AI Core Platform API",
    description="Dedicated AI Training Pipeline, Model Registry, Memory Vault, Conversation Manager, and Robot Controller.",
    version="0.2.0"
)

# Enable CORS for local React/Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== REQUEST / RESPONSE SCHEMAS =====================

class ModelInitRequest(BaseModel):
    model_name: str = Field(..., example="WithMe Experimental Transformer v1")
    vocab_size: int = Field(default=1500, ge=100, le=10000)
    d_model: int = Field(default=128, ge=32, le=512)
    n_layers: int = Field(default=4, ge=1, le=12)
    n_heads: int = Field(default=4, ge=1, le=16)
    ffn_dim: int = Field(default=256, ge=64, le=1024)
    max_seq_len: int = Field(default=128, ge=32, le=512)
    dropout: float = Field(default=0.1, ge=0.0, le=0.5)


class ModelLoadRequest(BaseModel):
    model_id: str


class TrainingJobRequest(BaseModel):
    model_name: str
    dataset_id: str
    epochs: int = Field(default=5, ge=1, le=50)
    batch_size: int = Field(default=4, ge=1, le=64)
    learning_rate: float = Field(default=3e-4, ge=1e-5, le=1e-2)
    d_model: int = Field(default=128)
    n_layers: int = Field(default=4)
    n_heads: int = Field(default=4)
    ffn_dim: int = Field(default=256)
    max_seq_len: int = Field(default=128)
    dropout: float = Field(default=0.1)
    cpu_threads: Optional[int] = Field(default=None)
    resume_from: Optional[str] = Field(default=None)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None
    model_id: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)
    top_k: int = Field(default=40, ge=0, le=100)
    top_p: float = Field(default=0.9, ge=0.1, le=1.0)
    max_new_tokens: int = Field(default=45, ge=5, le=128)
    include_memories: bool = True


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None


class ConversationTurnRequest(BaseModel):
    message: str
    model_id: Optional[str] = None


class MemoryCreateRequest(BaseModel):
    content: str
    category: str = "General"
    tag: str = "Custom"
    user_approved: bool = True
    expires_in_seconds: Optional[int] = None


class SimulatedSensorRequest(BaseModel):
    event_type: str = Field(..., example="person_detected")
    details: Dict[str, Any] = Field(default_factory=dict)


class PersonalityUpdateRequest(BaseModel):
    preset_id: Optional[str] = None
    custom_overrides: Optional[Dict[str, Any]] = None


class HardwareCheckRequest(BaseModel):
    model_id: str


class ExperimentCompareRequest(BaseModel):
    experiment_id_1: str
    experiment_id_2: str


# ===================== ENDPOINTS =====================

# ---------- HEALTH & SYSTEM ----------

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def get_health_status():
    """Application health status, compute hardware, and active model state."""
    hw = get_hardware_info()
    return {
        "status": "healthy",
        "version": "0.2.0",
        "active_model_id": inference_engine.active_model_id or "withme_hybrid_smart_engine",
        "is_model_loaded": inference_engine.is_loaded,
        "compute_device": hw["compute_device"],
        "hardware": hw,
        "is_memory_enabled": memory_service.is_memory_enabled,
        "timestamp": time.time()
    }


# ---------- MODEL LAB & REGISTRY ----------

@app.get("/api/models", tags=["Models"])
def list_models():
    """List all registered models across Path A, Path B, and Path C."""
    return model_registry.scan_models()


@app.get("/api/models/pretrained/catalog", tags=["Models"])
def list_pretrained_catalog():
    """List approved open-weight foundation models available for fine-tuning."""
    return model_registry.list_pretrained_catalog()


@app.post("/api/models/check-compatibility", tags=["Models"])
def check_model_compatibility(req: HardwareCheckRequest):
    """Check hardware requirements (RAM, Disk, GPU) before downloading or fine-tuning."""
    return check_hardware_compatibility_for_model(req.model_id)


@app.get("/api/models/cloud-script", tags=["Models"])
def get_cloud_gpu_script(model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"):
    """Generate copy-paste ready script for Google Colab / RunPod GPU fine-tuning."""
    return {
        "model_id": model_id,
        "script": generate_cloud_gpu_training_script(model_id)
    }


@app.get("/api/models/{model_id}", tags=["Models"])
def get_model_details(model_id: str):
    """Get metadata for a specific model."""
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return model


@app.post("/api/models/load", tags=["Models"])
def load_model(req: ModelLoadRequest):
    """Load a specific model checkpoint or hybrid engine into active inference."""
    try:
        res = inference_engine.load_model(req.model_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- DATASET STUDIO ----------

@app.get("/api/datasets", tags=["Datasets"])
def list_datasets():
    """List all raw and processed conversational datasets."""
    return dataset_manager.list_datasets()


@app.get("/api/datasets/manifests", tags=["Datasets"])
def list_dataset_manifests():
    """List all registered dataset integrity manifests."""
    manifests = []
    for p in sorted(MANIFESTS_DIR.glob("manifest_*.json"), reverse=True):
        try:
            import json
            with open(p, "r", encoding="utf-8") as f:
                manifests.append(json.load(f))
        except Exception:
            pass
    return manifests


@app.post("/api/datasets/upload", tags=["Datasets"])
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a raw conversational dataset file."""
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jsonl", ".json", ".csv", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Must be .jsonl, .json, .csv, or .txt"
        )

    target_path = RAW_DATASETS_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw_records = dataset_manager.parse_raw_records(target_path)
    valid_convs, stats = dataset_manager.validate_and_normalize(raw_records)

    return {
        "filename": file.filename,
        "filepath": str(target_path),
        "format": ext.lstrip("."),
        "total_parsed": len(raw_records),
        "validation_stats": stats
    }


@app.post("/api/datasets/{dataset_id}/split", tags=["Datasets"])
def split_dataset_endpoint(
    dataset_id: str,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
):
    """Perform 3-way conversation-level split and generate registered manifest."""
    raw_files = list(RAW_DATASETS_DIR.glob(f"{dataset_id}.*"))
    if not raw_files:
        raise HTTPException(status_code=404, detail=f"Raw dataset '{dataset_id}' not found.")

    res = dataset_manager.prepare_and_save_dataset(
        raw_filepath=raw_files[0],
        dataset_name=dataset_id,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed
    )
    return res


# ---------- TRAINING CENTER ----------

@app.post("/api/training/jobs", tags=["Training"])
def start_training_job(req: TrainingJobRequest):
    """Launch asynchronous PyTorch training job."""
    raw_files = list(RAW_DATASETS_DIR.glob(f"{req.dataset_id}.*"))
    if not raw_files:
        raw_files = list(RAW_DATASETS_DIR.glob("*.jsonl"))

    if not raw_files:
        raise HTTPException(status_code=400, detail="No dataset available for training.")

    raw_path = raw_files[0]
    raw_records = dataset_manager.parse_raw_records(raw_path)
    normalized, _ = dataset_manager.validate_and_normalize(raw_records)

    split = dataset_manager.split_dataset_3way(normalized, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
    train_convs = split["train"]
    val_convs = split["validation"]

    # Train tokenizer on training dialogues
    tokenizer = WithMeTokenizer()
    all_texts = []
    for c in train_convs + val_convs:
        all_texts.append(tokenizer.format_conversation(c.get("messages", [])))
    tokenizer.train_from_corpus(all_texts, max_vocab_size=1500)

    cfg = req.dict()
    job = training_engine.create_job(
        model_name=req.model_name,
        config=cfg,
        train_conversations=train_convs,
        val_conversations=val_convs,
        tokenizer=tokenizer,
        resume_from=req.resume_from
    )
    job.start()

    return {
        "status": "started",
        "job_id": job.job_id,
        "model_name": job.model_name,
        "total_epochs": job.total_epochs,
        "train_samples": len(train_convs),
        "val_samples": len(val_convs),
        "tokenizer_vocab_size": tokenizer.vocab_size
    }


@app.get("/api/training/jobs", tags=["Training"])
def list_training_jobs():
    """List historical and active training jobs."""
    return training_engine.list_jobs()


@app.get("/api/training/jobs/{job_id}", tags=["Training"])
def get_training_job_status(job_id: str):
    """Get live training metrics, epoch, step, and loss curves."""
    job = training_engine.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Training job '{job_id}' not found.")
    return job.to_dict()


@app.post("/api/training/jobs/{job_id}/stop", tags=["Training"])
def stop_training_job(job_id: str):
    """Gracefully cancel training job and save checkpoint."""
    job = training_engine.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Training job '{job_id}' not found.")
    job.stop()
    return {"status": "stopping", "job_id": job_id, "message": "Cancellation signal sent."}


# ---------- CHAT & LIVE PLAYGROUND ----------

@app.post("/api/chat", tags=["Playground"])
def generate_chat_reply(req: ChatRequest):
    """Generate companion response using currently loaded model or hybrid engine."""
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    result = inference_engine.generate(
        messages=msgs,
        model_id=req.model_id,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        max_new_tokens=req.max_new_tokens,
        include_memories=req.include_memories
    )
    return result


# ---------- MULTI-SESSION CONVERSATIONS ----------

@app.get("/api/conversations", tags=["Conversations"])
def list_conversation_sessions():
    """List all saved conversation sessions with message counts."""
    return conversation_manager.list_conversations()


@app.post("/api/conversations", tags=["Conversations"])
def create_conversation_session(req: ConversationCreateRequest):
    """Create a new distinct conversation session."""
    return conversation_manager.create_conversation(title=req.title)


@app.get("/api/conversations/{conversation_id}", tags=["Conversations"])
def get_conversation_history(conversation_id: str):
    """Retrieve message history for a conversation session."""
    return conversation_manager.get_messages(conversation_id)


@app.delete("/api/conversations/{conversation_id}", tags=["Conversations"])
def delete_conversation_session(conversation_id: str):
    """Delete a conversation session and all its messages."""
    success = conversation_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found.")
    return {"status": "deleted", "conversation_id": conversation_id}


@app.post("/api/conversations/{conversation_id}/turn", tags=["Conversations"])
def process_conversation_turn(conversation_id: str, req: ConversationTurnRequest):
    """Process a dialogue turn with safety screening, context sliding, and memory injection."""
    return conversation_manager.process_turn(
        conversation_id=conversation_id,
        user_message=req.message,
        model_id=req.model_id
    )


# ---------- MEMORY VAULT ----------

@app.get("/api/memories", tags=["Memory"])
def list_memories(category: Optional[str] = None):
    """List user-approved memories stored in SQLite."""
    return memory_service.list_memories(category=category)


@app.post("/api/memories", tags=["Memory"])
def create_memory(req: MemoryCreateRequest):
    """Store explicit user memory."""
    expires_at = (time.time() + req.expires_in_seconds) if req.expires_in_seconds else None
    return memory_service.add_memory(
        content=req.content,
        category=req.category,
        tag=req.tag,
        user_approved=req.user_approved,
        expires_at=expires_at
    )


@app.delete("/api/memories/{memory_id}", tags=["Memory"])
def delete_memory(memory_id: str):
    """Delete a memory item."""
    success = memory_service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return {"status": "deleted", "id": memory_id}


@app.delete("/api/memories", tags=["Memory"])
def clear_all_memories():
    """Clear all memories (right to erasure)."""
    count = memory_service.clear_all_memories()
    return {"status": "cleared", "deleted_count": count}


@app.post("/api/memories/toggle-global", tags=["Memory"])
def toggle_global_memory(enabled: bool = True):
    """Enable or disable persistent memory globally."""
    res = memory_service.set_memory_enabled(enabled)
    return {"is_memory_enabled": res}


@app.post("/api/memories/{memory_id}/toggle-approval", tags=["Memory"])
def toggle_memory_approval(memory_id: str):
    """Toggle user approval on a memory record."""
    mem = memory_service.toggle_approval(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return mem


# ---------- PERSONALITY STUDIO ----------

@app.get("/api/personality", tags=["Personality"])
def get_personality():
    """Get active personality profile and presets."""
    return {
        "presets": personality_engine.get_presets(),
        "active": personality_engine.get_active_profile()
    }


@app.post("/api/personality", tags=["Personality"])
def update_personality(req: PersonalityUpdateRequest):
    """Update active personality preset or custom slider values."""
    return personality_engine.update_profile(
        preset_id=req.preset_id,
        custom_overrides=req.custom_overrides
    )


# ---------- ROBOT INTEGRATION & SIMULATION ----------

@app.get("/api/robot/status", tags=["Robot"])
def get_robot_status():
    """Get current virtual robot state and event logs."""
    return {
        "status": robot_service.get_status(),
        "event_logs": robot_service.get_event_logs()
    }


@app.post("/api/robot/action", tags=["Robot"])
def trigger_robot_action(payload: RobotActionPayload):
    """Validate and execute a permitted robot action."""
    return robot_service.validate_and_execute_action(
        action=payload.robot_action,
        emotion=payload.emotion,
        interaction_state=payload.interaction_state,
        parameters=payload.action_parameters
    )


@app.post("/api/robot/simulate-sensor", tags=["Robot"])
def simulate_sensor_event(req: SimulatedSensorRequest):
    """Simulate a hardware/vision event (person detected, distance, etc)."""
    return robot_service.trigger_simulated_sensor_event(req.event_type, req.details)


# ---------- EVALUATION LAB ----------

@app.get("/api/evaluation/benchmarks", tags=["Evaluation"])
def list_eval_benchmarks():
    """List standard evaluation prompts."""
    return evaluation_engine.list_benchmarks()


@app.get("/api/evaluation/results", tags=["Evaluation"])
def list_eval_results():
    """List historical evaluation runs."""
    return evaluation_engine.list_saved_evaluations()


@app.post("/api/evaluation/run", tags=["Evaluation"])
def run_evaluation(model_id: Optional[str] = None):
    """Run benchmark evaluation suite on selected or active model."""
    return evaluation_engine.run_evaluation(model_id=model_id)


@app.get("/api/evaluation/experiments", tags=["Evaluation"])
def list_experiments():
    """List all tracked training experiments."""
    return evaluation_engine.list_experiments()


@app.post("/api/evaluation/experiments/compare", tags=["Evaluation"])
def compare_experiments_endpoint(req: ExperimentCompareRequest):
    """Compare two training runs side-by-side."""
    return evaluation_engine.compare_experiments(req.experiment_id_1, req.experiment_id_2)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
