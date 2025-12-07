"""FastAPI backend service for Smart Shell Assistant."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from backend.suggestion_engine import get_suggestion_engine
from backend.error_fixes import get_error_fixer
from backend.config import API_HOST, API_PORT

# Initialize FastAPI app
app = FastAPI(
    title="Smart Shell Assistant API",
    description="Context-aware shell command suggestion service",
    version="0.1.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
suggestion_engine = get_suggestion_engine()
error_fixer = get_error_fixer()


# Request/Response Models
class SuggestionRequest(BaseModel):
    query: str
    cwd: Optional[str] = None
    last_command: Optional[str] = None
    last_exit_code: Optional[int] = None
    recent_commands: Optional[List[str]] = None
    max_suggestions: Optional[int] = 5


class ErrorFixRequest(BaseModel):
    error_message: str
    last_command: Optional[str] = None


class RebuildIndexRequest(BaseModel):
    commands: List[str]


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Smart Shell Assistant API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = suggestion_engine.get_stats()
    return {"status": "healthy", "stats": stats}


@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    """
    Get command suggestions based on query and context.

    Args:
        request: SuggestionRequest with query and context

    Returns:
        Suggestions with ranking and safety information
    """
    try:
        result = suggestion_engine.get_suggestions(
            query=request.query,
            cwd=request.cwd,
            last_command=request.last_command,
            last_exit_code=request.last_exit_code,
            recent_commands=request.recent_commands,
            max_suggestions=request.max_suggestions,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fix-error")
async def fix_error(request: ErrorFixRequest):
    """
    Get fix suggestions for an error message.

    Args:
        request: ErrorFixRequest with error message and context

    Returns:
        List of possible fixes with confidence scores
    """
    try:
        fixes = error_fixer.find_fixes(
            error_message=request.error_message,
            last_command=request.last_command,
        )

        quick_fix = error_fixer.get_quick_fix(
            error_message=request.error_message,
            last_command=request.last_command,
        )

        return {
            "success": True,
            "fixes": fixes,
            "quick_fix": quick_fix,
            "error_message": request.error_message,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebuild-index")
async def rebuild_index(request: RebuildIndexRequest):
    """
    Rebuild the FAISS index with new commands.

    Args:
        request: RebuildIndexRequest with list of commands

    Returns:
        Success status and index statistics
    """
    try:
        from backend.retriever import get_retriever

        retriever = get_retriever()
        retriever.build_index(request.commands, save=True)

        stats = retriever.get_stats()

        return {
            "success": True,
            "message": "Index rebuilt successfully",
            "stats": stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    return suggestion_engine.get_stats()


def main():
    """Run the FastAPI server."""
    print(f"Starting Smart Shell Assistant API on {API_HOST}:{API_PORT}")
    print(f"API docs available at http://{API_HOST}:{API_PORT}/docs")

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
