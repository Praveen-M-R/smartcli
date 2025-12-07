"""Safety checking for potentially destructive commands."""

import re
from typing import Dict, List, Optional
from enum import Enum


class SafetyLevel(Enum):
    """Safety levels for commands."""

    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"


class SafetyChecker:
    """Detects and warns about potentially destructive commands."""

    # Destructive commands and patterns
    DESTRUCTIVE_COMMANDS = {
        "rm": ["rm -rf", "rm -fr", "rm -r", "rm -f"],
        "dd": ["dd if=", "dd of="],
        "mkfs": ["mkfs.", "mkfs "],
        "fdisk": ["fdisk"],
        "parted": ["parted"],
        ">": ["> /dev/"],
        "format": ["format"],
        "shred": ["shred"],
        "wipefs": ["wipefs"],
    }

    # Dangerous patterns with sudo
    SUDO_DANGEROUS_PATTERNS = [
        r"sudo\s+rm\s+-[rf]+",
        r"sudo\s+dd",
        r"sudo\s+mkfs",
        r"sudo\s+chmod\s+-R\s+777",
        r"sudo\s+chown\s+-R",
    ]

    # Critical system paths
    CRITICAL_PATHS = [
        "/",
        "/bin",
        "/boot",
        "/dev",
        "/etc",
        "/lib",
        "/proc",
        "/root",
        "/sbin",
        "/sys",
        "/usr",
        "/var",
    ]

    def check_command(self, command: str) -> Dict[str, any]:
        """
        Check if a command is potentially dangerous.

        Args:
            command: The shell command to check

        Returns:
            Dictionary with safety information:
                - level: SafetyLevel enum
                - warning: Warning message if applicable
                - reasons: List of reasons for the safety rating
        """
        command_lower = command.strip().lower()
        reasons = []

        # Check for destructive commands
        for cmd, patterns in self.DESTRUCTIVE_COMMANDS.items():
            for pattern in patterns:
                if pattern in command_lower:
                    reasons.append(f"Contains destructive pattern: {pattern}")

        # Check for sudo + dangerous combinations
        for pattern in self.SUDO_DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower):
                reasons.append(f"Dangerous sudo command detected")

        # Check for operations on critical paths
        for critical_path in self.CRITICAL_PATHS:
            if f" {critical_path}" in command or command.startswith(critical_path):
                # Check if it's a destructive operation
                if any(
                    dangerous in command_lower
                    for dangerous in ["rm", "dd", "mkfs", ">"]
                ):
                    reasons.append(
                        f"Destructive operation on critical path: {critical_path}"
                    )

        # Check for no-preserve-root
        if "--no-preserve-root" in command_lower:
            reasons.append("Bypasses root protection (--no-preserve-root)")

        # Check for force flags on system operations
        if "sudo" in command_lower and ("-f" in command or "--force" in command):
            if any(cmd in command_lower for cmd in ["rm", "mkfs", "dd"]):
                reasons.append("Forced system operation")

        # Determine safety level
        if reasons:
            # Critical danger indicators
            if any(
                indicator in command_lower
                for indicator in ["rm -rf /", "dd of=/dev/sda", "mkfs."]
            ):
                level = SafetyLevel.DANGEROUS
                warning = (
                    "⚠️  DANGEROUS: This command could cause data loss or system damage!"
                )
            else:
                level = SafetyLevel.WARNING
                warning = (
                    "⚠️  WARNING: This command could be destructive. Use with caution."
                )
        else:
            level = SafetyLevel.SAFE
            warning = None

        return {"level": level, "warning": warning, "reasons": reasons}

    def is_safe(self, command: str) -> bool:
        """Quick check if a command is safe."""
        result = self.check_command(command)
        return result["level"] == SafetyLevel.SAFE

    def get_warning_message(self, command: str) -> Optional[str]:
        """Get warning message for a command, if any."""
        result = self.check_command(command)
        return result.get("warning")


# Global instance
_safety_checker = None


def get_safety_checker() -> SafetyChecker:
    """Get the global safety checker instance."""
    global _safety_checker
    if _safety_checker is None:
        _safety_checker = SafetyChecker()
    return _safety_checker
