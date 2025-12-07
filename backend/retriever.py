"""FAISS-based retrieval for similar commands."""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import faiss

from backend.config import (
    FAISS_INDEX_PATH,
    METADATA_PATH,
    TOP_K_CANDIDATES,
)
from backend.embedder import get_embedder


class Retriever:
    """Manages FAISS index for semantic search of shell commands."""

    def __init__(self):
        self.index = None
        self.commands = []
        self.metadata = {}
        self.embedder = get_embedder()
        self.dimension = self.embedder.get_embedding_dim()

    def build_index(self, commands: List[str], save: bool = True) -> None:
        """
        Build FAISS index from a list of commands.

        Args:
            commands: List of shell commands
            save: Whether to save the index to disk
        """
        if not commands:
            raise ValueError("Cannot build index from empty command list")

        print(f"Building index for {len(commands)} commands...")

        # Generate embeddings
        embeddings = self.embedder.embed(commands)

        # Create FAISS index (using L2 distance for normalized vectors = cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype(np.float32))

        self.commands = commands
        self.metadata = {
            "num_commands": len(commands),
            "dimension": self.dimension,
            "index_type": "IndexFlatL2",
        }

        if save:
            self.save_index()

        print(f"Index built successfully with {len(commands)} commands")

    def load_index(self) -> bool:
        """
        Load FAISS index from disk.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not FAISS_INDEX_PATH.exists() or not METADATA_PATH.exists():
                print("Index files not found")
                return False

            # Load FAISS index
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))

            # Load metadata
            with open(METADATA_PATH, "r") as f:
                data = json.load(f)
                self.commands = data["commands"]
                self.metadata = data["metadata"]

            print(f"Loaded index with {len(self.commands)} commands")
            return True

        except Exception as e:
            print(f"Error loading index: {e}")
            return False

    def save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            # Ensure directory exists
            FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))

            # Save metadata and commands
            with open(METADATA_PATH, "w") as f:
                json.dump(
                    {"commands": self.commands, "metadata": self.metadata},
                    f,
                    indent=2,
                )

            print(f"Index saved to {FAISS_INDEX_PATH}")

        except Exception as e:
            print(f"Error saving index: {e}")
            raise

    def search(
        self, query: str, k: int = TOP_K_CANDIDATES, context: dict = None
    ) -> List[Dict[str, any]]:
        """
        Search for similar commands using semantic similarity.

        Args:
            query: Query string (partial command or description)
            k: Number of candidates to return
            context: Optional context dictionary

        Returns:
            List of dictionaries with 'command', 'score', and 'rank'
        """
        if self.index is None:
            raise RuntimeError(
                "Index not loaded. Call load_index() or build_index() first."
            )

        if self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedder.embed_command(query, context)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        # Convert L2 distance to similarity score (inverse relationship)
        # For normalized vectors, L2 distance is related to cosine similarity
        # similarity = 1 - (L2_distance^2 / 2)
        similarities = 1 - (distances[0] ** 2 / 2)

        # Build results
        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], similarities)):
            if idx < len(self.commands):
                results.append(
                    {"command": self.commands[idx], "score": float(score), "rank": rank}
                )

        return results

    def add_commands(self, new_commands: List[str], save: bool = True) -> None:
        """
        Add new commands to an existing index.

        Args:
            new_commands: List of new commands to add
            save: Whether to save the updated index
        """
        if not new_commands:
            return

        # Generate embeddings for new commands
        new_embeddings = self.embedder.embed(new_commands)

        # Add to index
        if self.index is None:
            self.build_index(new_commands, save=save)
        else:
            self.index.add(new_embeddings.astype(np.float32))
            self.commands.extend(new_commands)
            self.metadata["num_commands"] = len(self.commands)

            if save:
                self.save_index()

        print(f"Added {len(new_commands)} commands to index")

    def get_stats(self) -> Dict[str, any]:
        """Get statistics about the index."""
        if self.index is None:
            return {"loaded": False}

        return {
            "loaded": True,
            "num_commands": self.index.ntotal,
            "dimension": self.dimension,
            "metadata": self.metadata,
        }


# Global instance
_retriever = None


def get_retriever() -> Retriever:
    """Get the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
        _retriever.load_index()
    return _retriever
