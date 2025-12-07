"""Error pattern matching and fix suggestions."""

import json
import re
from typing import List, Dict, Optional
from pathlib import Path

from backend.config import ERROR_FIXES_DB


class ErrorFixer:
    """Matches errors to known fixes using pattern matching."""

    def __init__(self):
        self.error_patterns = []
        self.load_error_database()

    def load_error_database(self) -> None:
        """Load error patterns and fixes from database."""
        if not ERROR_FIXES_DB.exists():
            print(f"Warning: Error fixes database not found at {ERROR_FIXES_DB}")
            self._create_default_database()
            return

        try:
            with open(ERROR_FIXES_DB, "r") as f:
                data = json.load(f)
                self.error_patterns = data.get("patterns", [])
            print(f"Loaded {len(self.error_patterns)} error patterns")
        except Exception as e:
            print(f"Error loading error database: {e}")
            self.error_patterns = []

    def _create_default_database(self) -> None:
        """Create a default error fixes database."""
        default_patterns = [
            {
                "pattern": r"permission denied",
                "category": "permissions",
                "fixes": [
                    "Try using sudo: sudo <command>",
                    "Check file permissions: ls -l <file>",
                    "Change permissions: chmod +x <file>",
                ],
                "description": "Permission error when executing command",
            },
            {
                "pattern": r"command not found",
                "category": "not_found",
                "fixes": [
                    "Install the command using your package manager",
                    "Check if the command is in your PATH: echo $PATH",
                    "Try using the full path to the executable",
                ],
                "description": "Command not found in PATH",
            },
            {
                "pattern": r"No such file or directory",
                "category": "file_not_found",
                "fixes": [
                    "Check the file path: ls <directory>",
                    "Create the directory: mkdir -p <directory>",
                    "Verify you're in the correct directory: pwd",
                ],
                "description": "File or directory does not exist",
            },
            {
                "pattern": r"git.*Your local changes.*would be overwritten",
                "category": "git",
                "fixes": [
                    "Stash your changes: git stash",
                    "Commit your changes: git add . && git commit -m 'message'",
                    "Discard changes: git checkout -- .",
                ],
                "description": "Git merge/pull would overwrite local changes",
            },
            {
                "pattern": r"git.*fatal: not a git repository",
                "category": "git",
                "fixes": [
                    "Initialize git repository: git init",
                    "Clone a repository: git clone <url>",
                    "Navigate to a git repository directory",
                ],
                "description": "Not inside a git repository",
            },
            {
                "pattern": r"npm.*EACCES.*permission denied",
                "category": "npm",
                "fixes": [
                    "Fix npm permissions: sudo chown -R $USER ~/.npm",
                    "Use npx instead of global install",
                    "Configure npm to use a different directory",
                ],
                "description": "NPM permission error",
            },
            {
                "pattern": r"pip.*externally-managed-environment",
                "category": "python",
                "fixes": [
                    "Use a virtual environment: python -m venv venv && source venv/bin/activate",
                    "Use pipx for tools: pipx install <package>",
                    "Use --break-system-packages (not recommended)",
                ],
                "description": "PIP externally managed environment (PEP 668)",
            },
            {
                "pattern": r"docker.*Cannot connect to the Docker daemon",
                "category": "docker",
                "fixes": [
                    "Start Docker daemon: sudo systemctl start docker",
                    "Add user to docker group: sudo usermod -aG docker $USER",
                    "Check Docker status: sudo systemctl status docker",
                ],
                "description": "Cannot connect to Docker daemon",
            },
            {
                "pattern": r"disk.*full|No space left on device",
                "category": "disk",
                "fixes": [
                    "Check disk usage: df -h",
                    "Find large files: du -sh * | sort -h",
                    "Clean package cache (Ubuntu/Debian): sudo apt-get clean",
                    "Clean Docker: docker system prune -a",
                ],
                "description": "Disk full error",
            },
            {
                "pattern": r"port.*already in use",
                "category": "network",
                "fixes": [
                    "Find process using port: lsof -i :<port>",
                    "Kill process: kill -9 <pid>",
                    "Use a different port in your configuration",
                ],
                "description": "Port already in use",
            },
        ]

        # Save default database
        ERROR_FIXES_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(ERROR_FIXES_DB, "w") as f:
            json.dump({"patterns": default_patterns}, f, indent=2)

        self.error_patterns = default_patterns
        print(f"Created default error database with {len(default_patterns)} patterns")

    def find_fixes(
        self, error_message: str, last_command: Optional[str] = None
    ) -> List[Dict]:
        """
        Find fixes for an error message.

        Args:
            error_message: The error message to match
            last_command: The command that produced the error (optional)

        Returns:
            List of matching fix dictionaries
        """
        matches = []

        for pattern_entry in self.error_patterns:
            pattern = pattern_entry["pattern"]

            try:
                if re.search(pattern, error_message, re.IGNORECASE):
                    match = {
                        "category": pattern_entry["category"],
                        "description": pattern_entry["description"],
                        "fixes": pattern_entry["fixes"],
                        "confidence": self._calculate_confidence(
                            pattern, error_message, last_command
                        ),
                    }
                    matches.append(match)
            except re.error as e:
                print(f"Invalid regex pattern: {pattern} - {e}")
                continue

        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        return matches

    def _calculate_confidence(
        self, pattern: str, error_message: str, last_command: Optional[str]
    ) -> float:
        """Calculate confidence score for a match."""
        # Base confidence for pattern match
        confidence = 0.7

        # Increase confidence if pattern is very specific
        if len(pattern) > 30:
            confidence += 0.1

        # Increase confidence if last_command context matches
        if last_command:
            # Extract key terms from pattern
            if "git" in pattern and "git" in last_command:
                confidence += 0.15
            elif "npm" in pattern and "npm" in last_command:
                confidence += 0.15
            elif "docker" in pattern and "docker" in last_command:
                confidence += 0.15
            elif "pip" in pattern and "pip" in last_command:
                confidence += 0.15

        return min(confidence, 1.0)

    def get_quick_fix(
        self, error_message: str, last_command: Optional[str] = None
    ) -> Optional[str]:
        """Get the most likely quick fix for an error."""
        matches = self.find_fixes(error_message, last_command)

        if matches and matches[0]["confidence"] > 0.6:
            # Return the first (most likely) fix
            return matches[0]["fixes"][0]

        return None


# Global instance
_error_fixer = None


def get_error_fixer() -> ErrorFixer:
    """Get the global error fixer instance."""
    global _error_fixer
    if _error_fixer is None:
        _error_fixer = ErrorFixer()
    return _error_fixer
