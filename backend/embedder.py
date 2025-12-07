"""Embedding generation using ONNXRuntime (lightweight inference)."""

from typing import List, Union
import numpy as np
from pathlib import Path
import onnxruntime as ort
from transformers import AutoTokenizer

from backend.config import (
    EMBEDDING_MODEL_PATH,
    EMBEDDING_DEVICE,
)


class Embedder:
    """Manages embedding model and generates embeddings for commands using ONNX."""

    _instance = None
    _session = None
    _tokenizer = None

    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the embedder with ONNX model."""
        if self._session is None:
            self._load_model()

    def _load_model(self):
        """Load the ONNX model and tokenizer."""
        try:
            onnx_model_path = EMBEDDING_MODEL_PATH / "model.onnx"

            if not onnx_model_path.exists():
                print(f"ONNX model not found at {onnx_model_path}")
                print("Please run: python scripts/export_to_onnx.py")
                raise FileNotFoundError(
                    f"ONNX model not found. Run 'python scripts/export_to_onnx.py' first."
                )

            # Load tokenizer
            print(f"Loading tokenizer from {EMBEDDING_MODEL_PATH}")
            self._tokenizer = AutoTokenizer.from_pretrained(str(EMBEDDING_MODEL_PATH))

            # Set up ONNX Runtime session
            providers = ["CPUExecutionProvider"]
            if EMBEDDING_DEVICE == "cuda":
                providers.insert(0, "CUDAExecutionProvider")

            print(f"Loading ONNX model from {onnx_model_path}")
            self._session = ort.InferenceSession(
                str(onnx_model_path), providers=providers
            )

            print(
                f"Model loaded successfully with providers: {self._session.get_providers()}"
            )

        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def _mean_pooling(
        self, token_embeddings: np.ndarray, attention_mask: np.ndarray
    ) -> np.ndarray:
        """Apply mean pooling to token embeddings."""
        # Expand attention mask to match token embeddings shape
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
        input_mask_expanded = np.broadcast_to(
            input_mask_expanded, token_embeddings.shape
        )

        # Sum embeddings and divide by number of tokens
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)

        return sum_embeddings / sum_mask

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize embeddings."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.clip(norms, a_min=1e-9, a_max=None)
    
    def embed(self, texts: Union[str, List[str]], batch_size: int = 1) -> np.ndarray:
        """
        Generate embeddings for one or more texts using batching.
        """
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []
        
        # Loop through the texts in chunks (batches)
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            
            try:
                # Tokenize ONLY the current batch
                encoded = self._tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="np",
                )

                # Prepare ONNX inputs
                onnx_inputs = {
                    "input_ids": encoded["input_ids"].astype(np.int64),
                    "attention_mask": encoded["attention_mask"].astype(np.int64),
                }

                # Dynamic Check for token_type_ids
                model_input_names = [x.name for x in self._session.get_inputs()]
                if "token_type_ids" in model_input_names and "token_type_ids" in encoded:
                    onnx_inputs["token_type_ids"] = encoded["token_type_ids"].astype(np.int64)

                # Run Inference on the batch
                outputs = self._session.run(None, onnx_inputs)

                # Get token embeddings & Pool
                token_embeddings = outputs[0]
                embeddings = self._mean_pooling(token_embeddings, encoded["attention_mask"])
                embeddings = self._normalize(embeddings)
                
                all_embeddings.append(embeddings)

            except Exception as e:
                print(f"Error generating embeddings for batch {i}: {e}")
                raise

        # Stack all batches back into a single numpy array
        if all_embeddings:
            return np.vstack(all_embeddings)
        else:
            return np.array([])

    def embed_command(self, command: str, context: dict = None) -> np.ndarray:
        """
        Generate embedding for a command, optionally with context.

        Args:
            command: The shell command
            context: Optional context dictionary

        Returns:
            numpy array embedding
        """
        # Create a rich text representation that includes context
        if context:
            context_str = self._context_to_string(context)
            text = f"{command} [Context: {context_str}]"
        else:
            text = command

        return self.embed(text)[0]  # Return single embedding

    def _context_to_string(self, context: dict) -> str:
        """Convert context dictionary to a string representation."""
        parts = []

        if context.get("directory_type"):
            parts.append(f"type:{context['directory_type']}")

        if context.get("git_info", {}).get("is_git_repo"):
            parts.append("git")

        if context.get("cwd_basename"):
            parts.append(f"dir:{context['cwd_basename']}")

        return " ".join(parts)

    def get_embedding_dim(self) -> int:
        """Get the dimensionality of the embeddings."""
        # MiniLM-L6-v2 has 384 dimensions
        return 384


# Global instance
_embedder = None


def get_embedder() -> Embedder:
    """Get the global embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
