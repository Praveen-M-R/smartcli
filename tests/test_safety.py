"""Tests for safety checker."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.safety import SafetyChecker, SafetyLevel


class TestSafetyChecker:
    """Test suite for SafetyChecker class."""

    def setup_method(self):
        """Setup for each test."""
        self.checker = SafetyChecker()

    def test_safe_command(self):
        """Test detection of safe commands."""
        safe_commands = [
            "ls -la",
            "cd /home/user",
            "echo 'hello'",
            "cat file.txt",
            "grep 'pattern' file.txt",
        ]

        for cmd in safe_commands:
            result = self.checker.check_command(cmd)
            assert (
                result["level"] == SafetyLevel.SAFE
            ), f"Command '{cmd}' should be safe"
            assert result["warning"] is None

    def test_dangerous_rm_rf(self):
        """Test detection of dangerous rm -rf commands."""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /var",
            "rm -fr /home",
        ]

        for cmd in dangerous_commands:
            result = self.checker.check_command(cmd)
            assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]
            assert result["warning"] is not None
            assert len(result["reasons"]) > 0

    def test_dangerous_dd(self):
        """Test detection of dangerous dd commands."""
        dangerous_commands = [
            "dd if=/dev/zero of=/dev/sda",
            "sudo dd if=image.iso of=/dev/sdb",
        ]

        for cmd in dangerous_commands:
            result = self.checker.check_command(cmd)
            assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]
            assert result["warning"] is not None

    def test_dangerous_mkfs(self):
        """Test detection of filesystem formatting commands."""
        dangerous_commands = [
            "mkfs.ext4 /dev/sda1",
            "sudo mkfs -t ext4 /dev/sdb",
        ]

        for cmd in dangerous_commands:
            result = self.checker.check_command(cmd)
            assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]
            assert result["warning"] is not None

    def test_sudo_combinations(self):
        """Test detection of dangerous sudo combinations."""
        dangerous_commands = [
            "sudo rm -rf /home/user",
            "sudo chmod -R 777 /etc",
            "sudo chown -R user:group /",
        ]

        for cmd in dangerous_commands:
            result = self.checker.check_command(cmd)
            assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]

    def test_critical_paths(self):
        """Test detection of operations on critical paths."""
        critical_commands = [
            "rm -rf /etc",
            "rm -rf /bin",
            "dd if=/dev/zero of=/dev",
        ]

        for cmd in critical_commands:
            result = self.checker.check_command(cmd)
            assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]
            assert any(
                "critical path" in reason.lower() for reason in result["reasons"]
            )

    def test_no_preserve_root(self):
        """Test detection of --no-preserve-root flag."""
        cmd = "rm -rf --no-preserve-root /"
        result = self.checker.check_command(cmd)

        assert result["level"] == SafetyLevel.DANGEROUS
        assert any("preserve-root" in reason.lower() for reason in result["reasons"])

    def test_is_safe_method(self):
        """Test is_safe convenience method."""
        assert self.checker.is_safe("ls -la") is True
        assert self.checker.is_safe("rm -rf /") is False

    def test_get_warning_message(self):
        """Test get_warning_message method."""
        safe_msg = self.checker.get_warning_message("ls -la")
        assert safe_msg is None

        dangerous_msg = self.checker.get_warning_message("rm -rf /")
        assert dangerous_msg is not None
        assert (
            "⚠️" in dangerous_msg
            or "WARNING" in dangerous_msg
            or "DANGEROUS" in dangerous_msg
        )

    def test_case_insensitivity(self):
        """Test that checking is case-insensitive."""
        result1 = self.checker.check_command("rm -rf /")
        result2 = self.checker.check_command("RM -RF /")

        assert result1["level"] == result2["level"]

    def test_reasons_provided(self):
        """Test that reasons are provided for dangerous commands."""
        result = self.checker.check_command("sudo rm -rf /var")

        assert len(result["reasons"]) > 0
        assert all(isinstance(reason, str) for reason in result["reasons"])

    def test_whitespace_handling(self):
        """Test handling of extra whitespace."""
        cmd_with_spaces = "  sudo   rm   -rf   /home  "
        result = self.checker.check_command(cmd_with_spaces)

        assert result["level"] in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
