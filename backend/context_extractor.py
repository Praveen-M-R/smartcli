"""Extract contextual information from the shell environment."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class ContextExtractor:
    """Extracts relevant context from the current shell environment."""

    def __init__(self):
        self.context_cache = {}

    def extract_context(
        self,
        cwd: Optional[str] = None,
        last_command: Optional[str] = None,
        last_exit_code: Optional[int] = None,
        recent_commands: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extract comprehensive context from the shell environment.

        Args:
            cwd: Current working directory
            last_command: Last executed command
            last_exit_code: Exit code of the last command
            recent_commands: List of recent commands

        Returns:
            Dictionary containing extracted context
        """
        cwd = cwd or os.getcwd()

        context = {
            "cwd": cwd,
            "cwd_basename": os.path.basename(cwd),
            "last_command": last_command,
            "last_exit_code": last_exit_code,
            "recent_commands": recent_commands or [],
            "git_info": self._extract_git_info(cwd),
            "file_types": self._extract_file_types(cwd),
            "directory_type": self._infer_directory_type(cwd),
            "env_hints": self._extract_env_hints(),
        }

        return context

    def _extract_git_info(self, cwd: str) -> Dict[str, Any]:
        """Extract git repository information if in a git repo."""
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                return {"is_git_repo": False}

            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
            )
            branch = (
                branch_result.stdout.strip() if branch_result.returncode == 0 else None
            )

            # Check if there are uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
            )
            has_changes = (
                bool(status_result.stdout.strip())
                if status_result.returncode == 0
                else None
            )

            # Get remote URL (if any)
            remote_result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
            )
            remote_url = (
                remote_result.stdout.strip() if remote_result.returncode == 0 else None
            )

            return {
                "is_git_repo": True,
                "branch": branch,
                "has_uncommitted_changes": has_changes,
                "remote_url": remote_url,
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return {"is_git_repo": False}

    def _extract_file_types(self, cwd: str, limit: int = 20) -> Dict[str, int]:
        """Extract file type distribution in the current directory."""
        try:
            file_types = {}
            path = Path(cwd)

            # Only scan files in the current directory (not recursive)
            for item in path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower() if item.suffix else "no_extension"
                    file_types[ext] = file_types.get(ext, 0) + 1

            # Sort by count and limit
            sorted_types = dict(
                sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:limit]
            )
            return sorted_types

        except (PermissionError, Exception):
            return {}

    def _infer_directory_type(self, cwd: str) -> str:
        """Infer the type of project/directory based on files present."""
        path = Path(cwd)

        markers = {
            "python": ["setup.py", "requirements.txt", "pyproject.toml", "Pipfile"],
            "node": ["package.json", "node_modules"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod", "go.sum"],
            "java": ["pom.xml", "build.gradle"],
            "docker": ["Dockerfile", "docker-compose.yml"],
            "terraform": ["main.tf", "*.tf"],
        }

        detected_types = []
        for dir_type, marker_files in markers.items():
            for marker in marker_files:
                if "*" in marker:
                    # Pattern matching
                    if list(path.glob(marker)):
                        detected_types.append(dir_type)
                        break
                elif (path / marker).exists():
                    detected_types.append(dir_type)
                    break

        return ",".join(detected_types) if detected_types else "general"

    def _extract_env_hints(self) -> Dict[str, Any]:
        """Extract hints from environment variables."""
        hints = {}

        # Check for virtual environment
        if os.getenv("VIRTUAL_ENV"):
            hints["python_venv"] = True

        # Check for conda
        if os.getenv("CONDA_DEFAULT_ENV"):
            hints["conda_env"] = os.getenv("CONDA_DEFAULT_ENV")

        # Check for common development tools
        if os.getenv("DOCKER_HOST"):
            hints["docker_enabled"] = True

        return hints
