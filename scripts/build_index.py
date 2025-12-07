"""Build FAISS index from shell history."""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retriever import get_retriever
from backend.config import HISTORY_FILE


def load_history(history_file: Path) -> list:
    """Load command history from JSON file."""
    if not history_file.exists():
        print(f"Error: History file not found: {history_file}")
        print("Please run export_history.py first to create the history file.")
        return []

    try:
        with open(history_file, "r") as f:
            data = json.load(f)
            commands = data.get("commands", [])
            print(f"Loaded {len(commands)} commands from history")
            return commands
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def main():
    """Build FAISS index from command history."""
    print("=" * 60)
    print("Smart Shell Assistant - Build Index")
    print("=" * 60)

    # Load history
    commands = load_history(HISTORY_FILE)

    if not commands:
        print("\nNo commands found. Cannot build index.")
        print("\nTo create a history file, run:")
        print("  python scripts/export_history.py")
        return 1

    # Remove duplicates while preserving order
    unique_commands = list(dict.fromkeys(commands))
    print(f"After deduplication: {len(unique_commands)} unique commands")

    # Build index
    print("\nBuilding FAISS index...")
    retriever = get_retriever()

    try:
        retriever.build_index(unique_commands, save=True)
        print("\n✓ Index built successfully!")

        # Show stats
        stats = retriever.get_stats()
        print(f"\nIndex Statistics:")
        print(f"  Total commands: {stats['num_commands']}")
        print(f"  Embedding dimension: {stats['dimension']}")
        print(f"  Index type: {stats['metadata'].get('index_type', 'N/A')}")

        return 0

    except Exception as e:
        print(f"\n✗ Error building index: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
