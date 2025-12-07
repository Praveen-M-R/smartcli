"""Context-aware ranking of command candidates."""

from typing import List, Dict, Any
import re


class Ranker:
    """Ranks command candidates based on context and similarity."""

    def __init__(self):
        self.context_weights = {
            "semantic_similarity": 0.5,
            "git_match": 0.15,
            "directory_type_match": 0.15,
            "file_type_match": 0.10,
            "recency": 0.10,
        }

    def rank(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rank command candidates based on context.

        Args:
            candidates: List of candidate dictionaries from retriever
            context: Context dictionary from context_extractor
            max_results: Maximum number of results to return

        Returns:
            Ranked list of candidates with updated scores
        """
        if not candidates:
            return []

        # Score each candidate
        for candidate in candidates:
            context_score = self._compute_context_score(candidate, context)

            # Combine semantic similarity with context score
            semantic_score = candidate["score"]
            final_score = (
                self.context_weights["semantic_similarity"] * semantic_score
                + (1 - self.context_weights["semantic_similarity"]) * context_score
            )

            candidate["context_score"] = context_score
            candidate["final_score"] = final_score
            candidate["semantic_score"] = semantic_score

        # Sort by final score
        ranked = sorted(candidates, key=lambda x: x["final_score"], reverse=True)

        # Return top results
        return ranked[:max_results]

    def _compute_context_score(
        self, candidate: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """
        Compute context-specific score for a candidate.

        Args:
            candidate: Candidate dictionary
            context: Context dictionary

        Returns:
            Context score between 0 and 1
        """
        score = 0.0
        command = candidate["command"]

        # Git context matching
        if context.get("git_info", {}).get("is_git_repo"):
            if self._is_git_command(command):
                score += self.context_weights["git_match"] / (
                    1 - self.context_weights["semantic_similarity"]
                )

        # Directory type matching
        dir_type = context.get("directory_type", "")
        if dir_type and dir_type != "general":
            if self._matches_directory_type(command, dir_type):
                score += self.context_weights["directory_type_match"] / (
                    1 - self.context_weights["semantic_similarity"]
                )

        # File type matching
        file_types = context.get("file_types", {})
        if file_types:
            if self._matches_file_types(command, file_types):
                score += self.context_weights["file_type_match"] / (
                    1 - self.context_weights["semantic_similarity"]
                )

        # Normalize score to [0, 1]
        return min(score, 1.0)

    def _is_git_command(self, command: str) -> bool:
        """Check if command is a git command."""
        git_patterns = [
            r"^git\s",
            r"\bgit\s",
            r"git commit",
            r"git push",
            r"git pull",
            r"git checkout",
            r"git branch",
            r"git status",
            r"git add",
            r"git diff",
            r"git log",
            r"git merge",
            r"git rebase",
        ]
        return any(
            re.search(pattern, command, re.IGNORECASE) for pattern in git_patterns
        )

    def _matches_directory_type(self, command: str, dir_type: str) -> bool:
        """Check if command matches the directory type."""
        type_patterns = {
            "python": [
                r"\bpython\b",
                r"\bpip\b",
                r"\bpytest\b",
                r"\.py\b",
                r"\bvenv\b",
                r"\bconda\b",
                r"\bpoetry\b",
            ],
            "node": [
                r"\bnpm\b",
                r"\bnode\b",
                r"\byarn\b",
                r"\bpnpm\b",
                r"package\.json",
                r"\.js\b",
                r"\.ts\b",
            ],
            "rust": [r"\bcargo\b", r"\brushc\b", r"\.rs\b"],
            "go": [r"\bgo\s", r"\.go\b", r"go mod", r"go build", r"go test"],
            "java": [
                r"\bmvn\b",
                r"\bgradle\b",
                r"\.java\b",
                r"\.jar\b",
                r"\bjavac\b",
            ],
            "docker": [
                r"\bdocker\b",
                r"docker-compose",
                r"dockerfile",
                r"\.dockerfile\b",
            ],
        }

        # Check each type in dir_type (can be comma-separated)
        for dtype in dir_type.split(","):
            patterns = type_patterns.get(dtype.strip(), [])
            if any(re.search(pattern, command, re.IGNORECASE) for pattern in patterns):
                return True

        return False

    def _matches_file_types(self, command: str, file_types: Dict[str, int]) -> bool:
        """Check if command references file types present in the directory."""
        # Extract file extensions from the command
        command_lower = command.lower()

        for ext in file_types.keys():
            if ext == "no_extension":
                continue

            # Remove the dot from extension
            ext_name = ext.lstrip(".")

            # Check if extension appears in command
            if ext_name in command_lower or ext in command_lower:
                return True

        return False

    def explain_ranking(self, candidate: Dict[str, Any]) -> str:
        """Generate human-readable explanation of ranking."""
        parts = []

        parts.append(f"Semantic similarity: {candidate.get('semantic_score', 0):.2f}")
        parts.append(f"Context score: {candidate.get('context_score', 0):.2f}")
        parts.append(f"Final score: {candidate.get('final_score', 0):.2f}")

        return " | ".join(parts)


# Global instance
_ranker = None


def get_ranker() -> Ranker:
    """Get the global ranker instance."""
    global _ranker
    if _ranker is None:
        _ranker = Ranker()
    return _ranker
