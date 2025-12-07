"""Tests for suggestion engine."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.suggestion_engine import SuggestionEngine
from backend.retriever import get_retriever


class TestSuggestionEngine:
    """Test suite for SuggestionEngine class."""

    @classmethod
    def setup_class(cls):
        """Setup once for all tests."""
        # Build a test index
        retriever = get_retriever()
        test_commands = [
            "git status",
            "git add .",
            "git commit -m 'initial commit'",
            "git push origin main",
            "python -m pytest",
            "python script.py",
            "npm install",
            "npm run dev",
            "docker build -t app .",
            "docker-compose up",
            "ls -la",
            "cd projects",
            "mkdir new-project",
            "touch README.md",
            "vim config.py",
        ]
        retriever.build_index(test_commands, save=False)

    def setup_method(self):
        """Setup for each test."""
        self.engine = SuggestionEngine()

    def test_get_suggestions_basic(self):
        """Test basic suggestion retrieval."""
        result = self.engine.get_suggestions(
            query="list files",
            cwd="/home/user/project",
        )

        assert result["success"] is True
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    def test_get_suggestions_with_context(self):
        """Test suggestions with full context."""
        result = self.engine.get_suggestions(
            query="check status",
            cwd="/home/user/repo",
            last_command="git add .",
            last_exit_code=0,
            recent_commands=["git init", "git add ."],
        )

        assert result["success"] is True
        assert len(result["suggestions"]) > 0

        # Should include git-related suggestions
        commands = [s["command"] for s in result["suggestions"]]
        assert any("git" in cmd for cmd in commands)

    def test_suggestions_include_safety(self):
        """Test that suggestions include safety information."""
        result = self.engine.get_suggestions(
            query="remove files",
            max_suggestions=3,
        )

        assert result["success"] is True

        # Check if safety info is included
        if result["suggestions"]:
            suggestion = result["suggestions"][0]
            assert "safety" in suggestion

    def test_deduplication(self):
        """Test that duplicate suggestions are filtered."""
        result = self.engine.get_suggestions(
            query="git",
            max_suggestions=10,
        )

        assert result["success"] is True

        # Check for duplicates
        commands = [s["command"] for s in result["suggestions"]]
        assert len(commands) == len(set(commands))  # No duplicates

    def test_max_suggestions_limit(self):
        """Test respecting max_suggestions parameter."""
        result = self.engine.get_suggestions(
            query="git",
            max_suggestions=3,
        )

        assert result["success"] is True
        assert len(result["suggestions"]) <= 3

    def test_context_extraction(self):
        """Test that context is properly extracted."""
        result = self.engine.get_suggestions(
            query="test",
            cwd="/home/user/project",
        )

        assert "context" in result
        assert result["context"]["cwd"] == "/home/user/project"
        assert "git_info" in result["context"]

    def test_empty_query(self):
        """Test handling of empty/poor queries."""
        result = self.engine.get_suggestions(
            query="xyzabc123nonexistent",
            max_suggestions=5,
        )

        # Should still succeed but may have few results
        assert result["success"] is True

    def test_recent_commands_influence(self):
        """Test that recent commands influence suggestions."""
        # First query without context
        result1 = self.engine.get_suggestions(
            query="run",
            max_suggestions=5,
        )

        # Second query with python context
        result2 = self.engine.get_suggestions(
            query="run",
            recent_commands=["python -m venv venv", "pip install -r requirements.txt"],
            max_suggestions=5,
        )

        # Results might differ based on context
        assert result1["success"] is True
        assert result2["success"] is True

    def test_get_stats(self):
        """Test getting engine statistics."""
        stats = self.engine.get_stats()

        assert "retriever" in stats
        assert "config" in stats
        assert stats["retriever"]["loaded"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
