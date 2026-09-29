"""
WithMe AI Core - Configuration and Hardware Environment Detector
Hardware-agnostic, local-first configuration manager.
"""

import os
import platform
import psutil
from pathlib import Path
from typing import Dict, Any

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "withme-data"

DATASETS_DIR = DATA_DIR / "datasets"
RAW_DATASETS_DIR = DATASETS_DIR / "raw"
PROCESSED_DATASETS_DIR = DATASETS_DIR / "processed"

MODELS_DIR = DATA_DIR / "models"
EXPERIMENTAL_MODELS_DIR = MODELS_DIR / "experimental"
PRETRAINED_MODELS_DIR = MODELS_DIR / "pretrained"
FINETUNED_MODELS_DIR = MODELS_DIR / "finetuned"
ADAPTERS_DIR = MODELS_DIR / "adapters"

CHECKPOINTS_DIR = DATA_DIR / "checkpoints"
EVALUATIONS_DIR = DATA_DIR / "evaluations"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
LOGS_DIR = DATA_DIR / "logs"
DATABASE_DIR = DATA_DIR / "database"
DB_PATH = DATABASE_DIR / "withme.db"
MANIFESTS_DIR = DATA_DIR / "manifests"
EXPERIMENTS_DIR = DATA_DIR / "experiments"

# Ensure all directories exist
for path in [
    DATA_DIR, DATASETS_DIR, RAW_DATASETS_DIR, PROCESSED_DATASETS_DIR,
    MODELS_DIR, EXPERIMENTAL_MODELS_DIR, PRETRAINED_MODELS_DIR,
    FINETUNED_MODELS_DIR, ADAPTERS_DIR, CHECKPOINTS_DIR,
    EVALUATIONS_DIR, CONVERSATIONS_DIR, LOGS_DIR, DATABASE_DIR, MANIFESTS_DIR, EXPERIMENTS_DIR
]:
    path.mkdir(parents=True, exist_ok=True)


def get_hardware_info() -> Dict[str, Any]:
    """Detect actual host compute environment (CPU, RAM, GPU, Disk)."""
    cuda_available = False
    device_name = "CPU"
    gpu_details = []
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            gpu_details = [
                {
                    "id": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_total_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2)
                }
                for i in range(torch.cuda.device_count())
            ]
    except Exception:
        pass

    # System Memory
    mem = psutil.virtual_memory()
    total_ram_gb = round(mem.total / (1024**3), 2)
    available_ram_gb = round(mem.available / (1024**3), 2)

    # Disk Space
    disk = psutil.disk_usage(str(DATA_DIR))
    total_disk_gb = round(disk.total / (1024**3), 2)
    free_disk_gb = round(disk.free / (1024**3), 2)

    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count_physical": psutil.cpu_count(logical=False) or 1,
        "cpu_count_logical": psutil.cpu_count(logical=True) or 1,
        "ram_total_gb": total_ram_gb,
        "ram_available_gb": available_ram_gb,
        "disk_total_gb": total_disk_gb,
        "disk_free_gb": free_disk_gb,
        "cuda_available": cuda_available,
        "compute_device": "CUDA" if cuda_available else "CPU",
        "device_name": device_name,
        "gpus": gpu_details
    }
