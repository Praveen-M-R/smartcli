"""Tests for context extraction."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.context_extractor import ContextExtractor


class TestContextExtractor:
    """Test suite for ContextExtractor class."""

    def setup_method(self):
        """Setup for each test."""
        self.extractor = ContextExtractor()

    def test_basic_context_extraction(self):
        """Test basic context extraction without special features."""
        context = self.extractor.extract_context(
            cwd="/home/user/project",
            last_command="ls -la",
            last_exit_code=0,
        )

        assert context["cwd"] == "/home/user/project"
        assert context["cwd_basename"] == "project"
        assert context["last_command"] == "ls -la"
        assert context["last_exit_code"] == 0
        assert "git_info" in context
        assert "file_types" in context

    @patch("subprocess.run")
    def test_git_repo_detection(self, mock_run):
        """Test git repository detection."""
        # Mock git commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true\n"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout="main\n"),  # current branch
            MagicMock(returncode=0, stdout="M file.txt\n"),  # status
            MagicMock(
                returncode=0, stdout="https://github.com/user/repo.git\n"
            ),  # remote
        ]

        git_info = self.extractor._extract_git_info("/home/user/repo")

        assert git_info["is_git_repo"] is True
        assert git_info["branch"] == "main"
        assert git_info["has_uncommitted_changes"] is True
        assert "github.com" in git_info["remote_url"]

    @patch("subprocess.run")
    def test_non_git_directory(self, mock_run):
        """Test directory that's not a git repo."""
        mock_run.return_value = MagicMock(returncode=128)  # Not a git repo

        git_info = self.extractor._extract_git_info("/home/user")

        assert git_info["is_git_repo"] is False

    def test_directory_type_inference_python(self, tmp_path):
        """Test inferring Python project."""
        # Create requirements.txt
        (tmp_path / "requirements.txt").touch()

        dir_type = self.extractor._infer_directory_type(str(tmp_path))

        assert "python" in dir_type

    def test_directory_type_inference_node(self, tmp_path):
        """Test inferring Node.js project."""
        # Create package.json
        (tmp_path / "package.json").touch()

        dir_type = self.extractor._infer_directory_type(str(tmp_path))

        assert "node" in dir_type

    def test_directory_type_inference_multiple(self, tmp_path):
        """Test inferring project with multiple types."""
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "Dockerfile").touch()

        dir_type = self.extractor._infer_directory_type(str(tmp_path))

        assert "python" in dir_type
        assert "docker" in dir_type

    def test_file_types_extraction(self, tmp_path):
        """Test extracting file types from directory."""
        # Create test files
        (tmp_path / "test.py").touch()
        (tmp_path / "test2.py").touch()
        (tmp_path / "README.md").touch()

        file_types = self.extractor._extract_file_types(str(tmp_path))

        assert ".py" in file_types
        assert file_types[".py"] == 2
        assert file_types[".md"] == 1

    @patch.dict("os.environ", {"VIRTUAL_ENV": "/home/user/venv"})
    def test_env_hints_venv(self):
        """Test detecting virtual environment."""
        hints = self.extractor._extract_env_hints()

        assert hints.get("python_venv") is True

    @patch.dict("os.environ", {"CONDA_DEFAULT_ENV": "myenv"})
    def test_env_hints_conda(self):
        """Test detecting conda environment."""
        hints = self.extractor._extract_env_hints()

        assert hints.get("conda_env") == "myenv"

    def test_recent_commands_context(self):
        """Test including recent commands in context."""
        recent = ["git status", "git add .", "git commit"]

        context = self.extractor.extract_context(
            cwd="/home/user/project",
            recent_commands=recent,
        )

        assert context["recent_commands"] == recent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
