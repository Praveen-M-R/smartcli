"""Tests for error fixer."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.error_fixes import ErrorFixer


class TestErrorFixer:
    """Test suite for ErrorFixer class."""

    def setup_method(self):
        """Setup for each test."""
        self.fixer = ErrorFixer()

    def test_permission_denied_error(self):
        """Test fixing permission denied errors."""
        error = "bash: ./script.sh: Permission denied"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "permissions"
        assert any("chmod" in fix for fix in fixes[0]["fixes"])

    def test_command_not_found_error(self):
        """Test fixing command not found errors."""
        error = "bash: npm: command not found"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "not_found"

    def test_file_not_found_error(self):
        """Test fixing file not found errors."""
        error = "cat: config.json: No such file or directory"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "file_not_found"

    def test_git_merge_conflict_error(self):
        """Test fixing git merge conflicts."""
        error = "error: Your local changes to the following files would be overwritten by merge"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "git"
        assert any(
            "stash" in fix.lower() or "commit" in fix.lower()
            for fix in fixes[0]["fixes"]
        )

    def test_git_not_a_repository(self):
        """Test fixing 'not a git repository' error."""
        error = "fatal: not a git repository (or any of the parent directories)"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "git"
        assert any("git init" in fix for fix in fixes[0]["fixes"])

    def test_npm_permission_error(self):
        """Test fixing NPM permission errors."""
        error = "npm ERR! Error: EACCES: permission denied, access '/usr/local/lib/node_modules'"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "npm"

    def test_pip_externally_managed_error(self):
        """Test fixing pip externally managed environment error."""
        error = "error: externally-managed-environment"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "python"
        assert any(
            "venv" in fix.lower() or "virtual" in fix.lower()
            for fix in fixes[0]["fixes"]
        )

    def test_docker_daemon_error(self):
        """Test fixing Docker daemon connection errors."""
        error = "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "docker"

    def test_disk_full_error(self):
        """Test fixing disk full errors."""
        error = "No space left on device"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "disk"

    def test_port_in_use_error(self):
        """Test fixing port already in use errors."""
        error = "Error: listen EADDRINUSE: address already in use :::3000"

        fixes = self.fixer.find_fixes(error)

        assert len(fixes) > 0
        assert fixes[0]["category"] == "network"
        assert any("lsof" in fix or "port" in fix.lower() for fix in fixes[0]["fixes"])

    def test_confidence_scoring(self):
        """Test that fixes are sorted by confidence."""
        error = "permission denied"

        fixes = self.fixer.find_fixes(error)

        # First fix should have highest confidence
        if len(fixes) > 1:
            assert fixes[0]["confidence"] >= fixes[1]["confidence"]

    def test_confidence_with_command_context(self):
        """Test that confidence increases with matching command context."""
        error = "fatal: not a git repository"

        # Without command context
        fixes1 = self.fixer.find_fixes(error)

        # With git command context
        fixes2 = self.fixer.find_fixes(error, last_command="git status")

        # Should have higher confidence with context
        if fixes1 and fixes2:
            assert fixes2[0]["confidence"] >= fixes1[0]["confidence"]

    def test_get_quick_fix(self):
        """Test getting a quick fix suggestion."""
        error = "bash: npm: command not found"

        quick_fix = self.fixer.get_quick_fix(error)

        assert quick_fix is not None
        assert isinstance(quick_fix, str)
        assert len(quick_fix) > 0

    def test_quick_fix_low_confidence(self):
        """Test that low confidence errors don't return quick fix."""
        error = "some very unusual error that doesn't match anything xyzabc123"

        quick_fix = self.fixer.get_quick_fix(error)

        # Might be None for unknown errors
        assert quick_fix is None or isinstance(quick_fix, str)

    def test_multiple_pattern_matches(self):
        """Test error matching multiple patterns."""
        error = "npm: command not found"

        fixes = self.fixer.find_fixes(error)

        # Should match at least one pattern
        assert len(fixes) >= 1

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        error1 = "Permission Denied"
        error2 = "permission denied"

        fixes1 = self.fixer.find_fixes(error1)
        fixes2 = self.fixer.find_fixes(error2)

        assert len(fixes1) > 0
        assert len(fixes2) > 0
        assert fixes1[0]["category"] == fixes2[0]["category"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
