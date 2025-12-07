"""Main suggestion engine that orchestrates retrieval and ranking."""

from typing import List, Dict, Any, Optional

from backend.context_extractor import ContextExtractor
from backend.retriever import get_retriever
from backend.ranker import get_ranker
from backend.safety import get_safety_checker
from backend.config import MAX_SUGGESTIONS, ENABLE_SAFETY_CHECK


class SuggestionEngine:
    """Orchestrates the suggestion pipeline: context -> retrieval -> ranking."""

    def __init__(self):
        self.context_extractor = ContextExtractor()
        self.retriever = get_retriever()
        self.ranker = get_ranker()
        self.safety_checker = get_safety_checker()

    def get_suggestions(
        self,
        query: str,
        cwd: Optional[str] = None,
        last_command: Optional[str] = None,
        last_exit_code: Optional[int] = None,
        recent_commands: Optional[List[str]] = None,
        max_suggestions: int = MAX_SUGGESTIONS,
    ) -> Dict[str, Any]:
        """
        Get command suggestions based on query and context.

        Args:
            query: Query string (partial command or description)
            cwd: Current working directory
            last_command: Last executed command
            last_exit_code: Exit code of last command
            recent_commands: List of recent commands
            max_suggestions: Maximum number of suggestions to return

        Returns:
            Dictionary with suggestions and metadata
        """
        # Extract context
        context = self.context_extractor.extract_context(
            cwd=cwd,
            last_command=last_command,
            last_exit_code=last_exit_code,
            recent_commands=recent_commands,
        )

        # Retrieve candidates
        try:
            candidates = self.retriever.search(query, context=context)
        except RuntimeError as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": [],
                "context": context,
            }

        if not candidates:
            return {
                "success": True,
                "suggestions": [],
                "context": context,
                "message": "No similar commands found",
            }

        # Rank candidates
        ranked = self.ranker.rank(candidates, context, max_results=max_suggestions)

        # Add safety warnings if enabled
        if ENABLE_SAFETY_CHECK:
            for suggestion in ranked:
                safety_info = self.safety_checker.check_command(suggestion["command"])
                suggestion["safety"] = safety_info

        # Filter out duplicates
        seen_commands = set()
        unique_suggestions = []
        for suggestion in ranked:
            cmd = suggestion["command"]
            if cmd not in seen_commands:
                seen_commands.add(cmd)
                unique_suggestions.append(suggestion)

        return {
            "success": True,
            "suggestions": unique_suggestions,
            "context": context,
            "total_candidates": len(candidates),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the suggestion engine."""
        return {
            "retriever": self.retriever.get_stats(),
            "config": {
                "max_suggestions": MAX_SUGGESTIONS,
                "safety_check_enabled": ENABLE_SAFETY_CHECK,
            },
        }


# Global instance
_suggestion_engine = None


def get_suggestion_engine() -> SuggestionEngine:
    """Get the global suggestion engine instance."""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine()
    return _suggestion_engine
