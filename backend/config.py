"""Configuration settings for the Smart Shell Assistant backend."""

import os
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).parent.parent.resolve()
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

# Model configuration (ONNX-based)
EMBEDDING_MODEL_PATH = MODELS_DIR / "embeddings_model"
FAISS_INDEX_PATH = MODELS_DIR / "faiss_index.bin"
METADATA_PATH = MODELS_DIR / "metadata.json"

# Data paths
HISTORY_DIR = DATA_DIR / "history"
HISTORY_FILE = HISTORY_DIR / "history.json"
ERROR_LOG_DIR = DATA_DIR / "error_log"
ERROR_LOG_FILE = ERROR_LOG_DIR / "errors.json"
ERROR_FIXES_DB = DATA_DIR / "error_fixes_db.json"
EXAMPLES_DIR = DATA_DIR / "examples"

# API settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8765"))

# Suggestion engine parameters
TOP_K_CANDIDATES = int(os.getenv("TOP_K_CANDIDATES", "10"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
MAX_SUGGESTIONS = int(os.getenv("MAX_SUGGESTIONS", "5"))

# Context parameters
MAX_RECENT_COMMANDS = int(os.getenv("MAX_RECENT_COMMANDS", "10"))
CONTEXT_FILE_TYPES_LIMIT = int(os.getenv("CONTEXT_FILE_TYPES_LIMIT", "20"))

# Safety settings
ENABLE_SAFETY_CHECK = os.getenv("ENABLE_SAFETY_CHECK", "true").lower() == "true"

# Embedding settings
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # or 'cuda'


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        MODELS_DIR,
        DATA_DIR,
        HISTORY_DIR,
        ERROR_LOG_DIR,
        EXAMPLES_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Create directories on import
ensure_directories()
