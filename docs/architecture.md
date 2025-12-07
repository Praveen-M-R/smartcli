# Architecture

## System Overview

Smart Shell Assistant is built as a client-server architecture with shell plugins communicating with a local backend service.

```
┌─────────────────────────────────────────────────────────────┐
│                      User's Shell (Zsh/Bash)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Shell Plugin (hooks & UI)                   │   │
│  └───────────────────┬─────────────────────────────────┘   │
└────────────────────────│─────────────────────────── ─────────┘
                         │ HTTP/JSON
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                  Backend Service (FastAPI)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Layer (REST endpoints)                         │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                        │
│  ┌──────────────────▼─────────────────────────────────┐    │
│  │         Suggestion Engine                           │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │  Context Extractor                       │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │  Retriever (FAISS Search)                │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │  Ranker (Context-Aware)                  │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │  Safety Checker                          │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  └──────────────────────────────────────────────────  ────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Error Fixer (Pattern Matching)                     │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                         │
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                       Data Layer                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │ Embeddings     │  │ FAISS Index    │  │ Error Fixes   │ │
│  │ Model (22MB)   │  │ (2-40MB)       │  │ DB (JSON)     │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Shell Plugin Layer

**Purpose**: Hooks into the shell to capture context and display suggestions

**Components**:
- `smart_assistant.zsh`: Zsh plugin with preexec/precmd hooks
- `smart_assistant.bash`: Bash plugin using DEBUG trap and PROMPT_COMMAND

**Responsibilities**:
- Capture command execution hooks
- Track recent commands and exit codes
- Make API requests to backend
- Display suggestions to user
- Provide keyboard shortcuts

### 2. Backend API Layer

**Purpose**: REST API for suggestion and error-fixing services

**Technology**: FastAPI with uvicorn

**Endpoints**:
- `POST /suggest`: Get command suggestions
- `POST /fix-error`: Get error fixes
- `GET /health`: Health check
- `POST /rebuild-index`: Rebuild FAISS index
- `GET /stats`: System statistics

### 3. Context Extractor

**Purpose**: Extract relevant context from the shell environment

**Extracted Information**:
- Current working directory
- Git repository status (branch, dirty state)
- File types in directory
- Directory type (python, node, docker, etc.)
- Environment variables (venv, conda)
- Recent command history

**Implementation**: Subprocess calls to git, file system analysis

### 4. Embedder

**Purpose**: Convert text to vector embeddings

**Technology**: sentence-transformers (all-MiniLM-L6-v2)

**Features**:
- Singleton pattern for efficient model loading
- L2 normalization for cosine similarity
- Batch processing support
- Device selection (CPU/CUDA)

**Embedding Dimension**: 384

### 5. Retriever

**Purpose**: Semantic search over command history

**Technology**: FAISS (Facebook AI Similarity Search)

**Index Type**: IndexFlatL2 (exact search)

**Process**:
1. Generate query embedding
2. Perform k-NN search (k=10 default)
3. Convert L2 distance to similarity score
4. Return ranked candidates

**Storage**: Persists index and metadata to disk

### 6. Ranker

**Purpose**: Context-aware ranking of candidates

**Scoring Weights**:
- Semantic similarity: 50%
- Git context match: 15%
- Directory type match: 15%
- File type match: 10%
- Recency: 10%

**Features**:
- Pattern matching for git, npm, docker, python commands
- File extension recognition
- Context-specific boosting

### 7. Safety Checker

**Purpose**: Detect potentially destructive commands

**Detection Patterns**:
- Destructive commands (rm -rf, dd, mkfs)
- Sudo combinations with dangerous operations
- Operations on critical paths (/etc, /bin, /)
- --no-preserve-root flag

**Safety Levels**:
- SAFE: No warnings
- WARNING: Potentially risky
- DANGEROUS: Critical risk

### 8. Error Fixer

**Purpose**: Match errors to known fixes

**Database**: JSON file with regex patterns and fix suggestions

**Categories**:
- Permissions
- Command not found
- File not found
- Git errors
- NPM/PIP/Docker errors
- Network errors

**Confidence Scoring**: Based on pattern specificity and command context

## Data Flow

### Suggestion Flow

```
User Query → Context Extraction → Embedding Generation → 
FAISS Search → Context Ranking → Safety Check → Display
```

### Error Fix Flow

```
Error Message → Pattern Matching → Confidence Calculation → 
Sorted Fixes → Display
```

## Performance Considerations

### Latency Targets
- Context extraction: < 50ms
- Embedding generation: < 100ms
- FAISS search: < 10ms
- Ranking: < 20ms
- **Total**: < 200ms for end-to-end suggestion

### Memory Usage
- Embedding model: ~90MB
- FAISS index: 2-40MB (depends on history size)
- Backend service: ~150-200MB total

### Scalability
- Index size: Tested with up to 50,000 commands
- Search complexity: O(n) for exact search (can upgrade to IVF for larger indexes)

## Security & Privacy

### Privacy
- **All data stays local**: No external API calls
- **History sanitization**: Removes passwords, tokens, API keys
- **No telemetry**: No usage data collection

### Safety
- **Command validation**: Checks before execution
- **Warning system**: Clear warnings for risky commands
- **No auto-execution**: All commands require manual confirmation

## Future Architecture Enhancements

### Planned Improvements
1. **Distributed Index**: Support for shared team indexes
2. **Plugin System**: Custom integrations for tools (k8s, terraform)
3. **Learning System**: Track command success rates
4. **Advanced Ranker**: ML-based ranker with user feedback
5. **Multi-Modal**: Support for explaining command outputs
