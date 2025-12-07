"""Tests for FAISS retriever."""

import pytest
import numpy as np
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retriever import Retriever
from backend.embedder import get_embedder


class TestRetriever:
    """Test suite for Retriever class."""

    def setup_method(self):
        """Setup for each test."""
        self.retriever = Retriever()
        self.test_commands = [
            "git status",
            "git add .",
            "git commit -m 'message'",
            "git push origin main",
            "python -m pytest",
            "python script.py",
            "npm install",
            "npm run build",
            "docker build -t image .",
            "docker run container",
        ]

    def test_build_index(self):
        """Test building FAISS index."""
        self.retriever.build_index(self.test_commands, save=False)

        assert self.retriever.index is not None
        assert self.retriever.index.ntotal == len(self.test_commands)
        assert len(self.retriever.commands) == len(self.test_commands)

    def test_search_simple_query(self):
        """Test simple search query."""
        self.retriever.build_index(self.test_commands, save=False)

        results = self.retriever.search("git status", k=3)

        assert len(results) <= 3
        assert results[0]["command"] == "git status"  # Exact match should be top
        assert results[0]["score"] > 0.9  # Very high similarity

    def test_search_semantic_similarity(self):
        """Test semantic similarity search."""
        self.retriever.build_index(self.test_commands, save=False)

        # Search for conceptually similar command
        results = self.retriever.search("commit changes", k=5)

        # Should find git commit-related commands
        commands = [r["command"] for r in results]
        assert any("commit" in cmd for cmd in commands)

    def test_search_with_context(self):
        """Test search with context."""
        self.retriever.build_index(self.test_commands, save=False)

        context = {
            "directory_type": "python",
            "git_info": {"is_git_repo": True},
        }

        results = self.retriever.search("run tests", k=3, context=context)

        # Should find python test commands
        assert len(results) > 0

    def test_empty_query(self):
        """Test handling of empty results."""
        self.retriever.build_index(self.test_commands, save=False)

        results = self.retriever.search("xyzabc123nonexistent", k=5)

        # Should still return results (low similarity)
        assert len(results) > 0
        assert all(r["score"] < 0.5 for r in results)  # Low scores

    def test_add_commands(self):
        """Test adding new commands to existing index."""
        self.retriever.build_index(self.test_commands[:5], save=False)

        initial_count = self.retriever.index.ntotal

        new_commands = self.test_commands[5:]
        self.retriever.add_commands(new_commands, save=False)

        assert self.retriever.index.ntotal == len(self.test_commands)
        assert len(self.retriever.commands) == len(self.test_commands)

    def test_get_stats(self):
        """Test getting index statistics."""
        self.retriever.build_index(self.test_commands, save=False)

        stats = self.retriever.get_stats()

        assert stats["loaded"] is True
        assert stats["num_commands"] == len(self.test_commands)
        assert stats["dimension"] > 0

    def test_stats_without_index(self):
        """Test stats when no index is loaded."""
        empty_retriever = Retriever()
        stats = empty_retriever.get_stats()

        assert stats["loaded"] is False

    def test_duplicate_commands(self):
        """Test handling duplicate commands."""
        duplicates = self.test_commands + self.test_commands[:3]
        self.retriever.build_index(duplicates, save=False)

        # Should still build successfully
        assert self.retriever.index.ntotal == len(duplicates)

    def test_search_before_index(self):
        """Test search before building index."""
        empty_retriever = Retriever()

        with pytest.raises(RuntimeError, match="Index not loaded"):
            empty_retriever.search("test query")

    def test_ranking_by_score(self):
        """Test that results are ranked by similarity score."""
        self.retriever.build_index(self.test_commands, save=False)

        results = self.retriever.search("git", k=5)

        # Scores should be in descending order
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
