"""Update embeddings incrementally for new commands."""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retriever import get_retriever
from backend.config import HISTORY_FILE, METADATA_PATH


def get_indexed_commands() -> set:
    """Get the set of commands already in the index."""
    if not METADATA_PATH.exists():
        return set()

    try:
        with open(METADATA_PATH, "r") as f:
            data = json.load(f)
            return set(data.get("commands", []))
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return set()


def get_history_commands() -> list:
    """Get commands from history file."""
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("commands", [])
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def main():
    """Update embeddings with new commands from history."""
    print("=" * 60)
    print("Smart Shell Assistant - Update Embeddings")
    print("=" * 60)

    # Get existing commands in index
    print("\nLoading indexed commands...")
    indexed_commands = get_indexed_commands()
    print(f"Found {len(indexed_commands)} commands in index")

    # Get current history
    print("\nLoading history...")
    history_commands = get_history_commands()
    print(f"Found {len(history_commands)} commands in history")

    # Find new commands
    new_commands = [cmd for cmd in history_commands if cmd not in indexed_commands]

    if not new_commands:
        print("\n✓ No new commands to add. Index is up to date.")
        return 0

    print(f"\nFound {len(new_commands)} new commands to add")

    # Get retriever and add commands
    retriever = get_retriever()

    if not retriever.load_index():
        print("\n✗ Error: Could not load existing index")
        print("Run build_index.py first to create an initial index")
        return 1

    print("\nAdding new commands to index...")
    try:
        retriever.add_commands(new_commands, save=True)
        print(f"\n✓ Successfully added {len(new_commands)} commands")

        # Show updated stats
        stats = retriever.get_stats()
        print(f"\nUpdated Index Statistics:")
        print(f"  Total commands: {stats['num_commands']}")
        print(f"  Embedding dimension: {stats['dimension']}")

        return 0

    except Exception as e:
        print(f"\n✗ Error updating embeddings: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
