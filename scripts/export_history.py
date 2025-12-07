"""Export and sanitize shell history to JSON format."""

import json
import re
import sys
from pathlib import Path
from typing import List, Set
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import HISTORY_FILE, HISTORY_DIR


def get_shell_history_path() -> Path:
    """Determine the shell history file path."""
    home = Path.home()

    # Check for Zsh history
    zsh_history = home / ".zsh_history"
    if zsh_history.exists():
        return zsh_history

    # Check for Bash history
    bash_history = home / ".bash_history"
    if bash_history.exists():
        return bash_history

    # Try other common locations
    alternatives = [
        home / ".local/share/zsh/history",
        home / ".histfile",
    ]

    for alt in alternatives:
        if alt.exists():
            return alt

    raise FileNotFoundError("Could not find shell history file")


def parse_zsh_history(history_file: Path) -> List[str]:
    """Parse Zsh history format."""
    commands = []

    try:
        with open(history_file, "rb") as f:
            content = f.read().decode("utf-8", errors="ignore")

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Zsh extended history format: : timestamp:duration;command
            if line.startswith(":"):
                parts = line.split(";", 1)
                if len(parts) == 2:
                    command = parts[1].strip()
                    if command:
                        commands.append(command)
            else:
                # Simple history format
                commands.append(line)

    except Exception as e:
        print(f"Error parsing Zsh history: {e}")

    return commands


def parse_bash_history(history_file: Path) -> List[str]:
    """Parse Bash history format."""
    commands = []

    try:
        with open(history_file, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    commands.append(line)

    except Exception as e:
        print(f"Error parsing Bash history: {e}")

    return commands


def sanitize_command(command: str) -> str:
    """Sanitize a command to remove sensitive information."""

    # Patterns to sanitize (replace values with placeholders)
    patterns = [
        # API keys, tokens, passwords
        (r"(api[_-]?key|token|password|passwd|pwd)=[\w\-]+", r"\1=<REDACTED>"),
        (r"--password[\s=][\w\-]+", r"--password <REDACTED>"),
        (r"-p\s*[\w\-]+", r"-p <REDACTED>"),
        # URLs with credentials
        (r"https?://[^:]+:[^@]+@", r"https://<USER>:<PASS>@"),
        # Environment variables with secrets
        (r"export\s+\w*(SECRET|KEY|TOKEN|PASSWORD)\w*=.+", r"export \1=<REDACTED>"),
    ]

    sanitized = command
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


def filter_commands(commands: List[str]) -> List[str]:
    """Filter out unwanted commands."""
    filtered = []

    # Patterns to exclude
    exclude_patterns = [
        r"^cd\s*$",  # cd without arguments
        r"^ls\s*$",  # ls without arguments
        r"^pwd\s*$",  # pwd
        r"^exit\s*$",  # exit
        r"^clear\s*$",  # clear
        r"^history",  # history commands
        r"^\s*$",  # empty commands
        r"^#",  # comments
    ]

    for cmd in commands:
        # Skip if matches any exclude pattern
        if any(re.match(pattern, cmd) for pattern in exclude_patterns):
            continue

        # Skip very short commands (< 3 chars)
        if len(cmd.strip()) < 3:
            continue

        filtered.append(cmd)

    return filtered


def main():
    """Export shell history to JSON format."""
    print("=" * 60)
    print("Smart Shell Assistant - Export History")
    print("=" * 60)

    # Find history file
    try:
        history_path = get_shell_history_path()
        print(f"\nFound history file: {history_path}")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        return 1

    # Parse history based on shell type
    if "zsh" in str(history_path):
        print("Parsing Zsh history...")
        commands = parse_zsh_history(history_path)
    else:
        print("Parsing Bash history...")
        commands = parse_bash_history(history_path)

    print(f"Parsed {len(commands)} commands")

    # Filter commands
    print("Filtering commands...")
    commands = filter_commands(commands)
    print(f"After filtering: {len(commands)} commands")

    # Sanitize commands
    print("Sanitizing sensitive data...")
    commands = [sanitize_command(cmd) for cmd in commands]

    # Remove duplicates (keep last occurrence)
    seen: Set[str] = set()
    unique_commands = []
    for cmd in reversed(commands):
        if cmd not in seen:
            seen.add(cmd)
            unique_commands.append(cmd)

    unique_commands.reverse()
    print(f"After deduplication: {len(unique_commands)} unique commands")

    # Save to JSON
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    output_data = {
        "exported_at": datetime.now().isoformat(),
        "source_file": str(history_path),
        "total_commands": len(unique_commands),
        "commands": unique_commands,
    }

    with open(HISTORY_FILE, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ History exported to: {HISTORY_FILE}")
    print(f"\nNext step: Build the index with:")
    print("  python scripts/build_index.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
